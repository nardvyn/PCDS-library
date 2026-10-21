import { useCallback, useDeferredValue, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { googleLogout } from '@react-oauth/google'
import { Bell, BookOpen, BookOpenCheck, CalendarDays, Check, ChevronRight, Clock3, Eye, History, LayoutDashboard, Library, LogOut, Menu, Search, ShoppingCart, UserRound, X } from 'lucide-react'

import api from '../services/api'
import pcdsSeal from '../assets/pcds-seal.png'
import './DashboardPage.css'

const initialSummary = { borrowed_books: 0, pending_requests: 0, overdue_books: 0, returned_books: 0, unread_notifications: 0, borrowing_limit: 3, borrowing_used: 0, borrowing_remaining: 3, active_loans: [], recent_requests: [] }
const sectionPaths = {
  dashboard: '/dashboard', books: '/books', loans: '/my-loans', dueSoon: '/my-loans', overdue: '/my-loans', requests: '/my-requests',
  history: '/history', notifications: '/notifications', profile: '/profile',
}
const pathSections = Object.fromEntries(Object.entries(sectionPaths).map(([section, path]) => [path, section]))

function DashboardPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [dashboardError, setDashboardError] = useState('')
  const [summary, setSummary] = useState(initialSummary)
  const loadDashboard = useCallback(async () => {
    setLoading(true)
    try {
      const response = await api.get('/borrower/dashboard')
      setSummary((current) => ({ ...current, ...initialSummary, ...response.data }))
      setDashboardError('')
    } catch (error) {
      console.error('Dashboard data is not available yet.', error)
      setDashboardError(error.response?.data?.message || 'Unable to load your dashboard. Check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }, [])
  const updateUnreadNotifications = useCallback((count) => {
    setSummary((current) => ({ ...current, unread_notifications: count }))
  }, [])
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const firstName = user.full_name?.split(' ')[0] || 'Library User'
  const isTeacher = user.role === 'TEACHER'
  const borrowingPeriod = summary.borrowing_period || (isTeacher ? 14 : 7)

  useEffect(() => {
    const initialLoad = window.setTimeout(loadDashboard, 0)
    const handleFocus = () => loadDashboard()
    window.addEventListener('focus', handleFocus)
    return () => {
      window.clearTimeout(initialLoad)
      window.removeEventListener('focus', handleFocus)
    }
  }, [loadDashboard])

  const activeSection = pathSections[location.pathname] || 'dashboard'

  useEffect(() => {
    api.get('/notifications')
      .then(({ data }) => setSummary((current) => ({ ...current, unread_notifications: data.unread_count || 0 })))
      .catch(() => {})
  }, [])

  function navigateTo(section) {
    setSidebarOpen(false)
    const routeState = section === 'dueSoon' || section === 'overdue' ? { loanFilter: section } : {}
    navigate(sectionPaths[section] || '/dashboard', { state: routeState })
    if (section === 'dashboard') loadDashboard()
  }
  function handleSignOut() {
    if (!window.confirm('Are you sure you want to sign out?')) return
    googleLogout()
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/', { replace: true })
  }

  const navItems = [
    [LayoutDashboard, 'Dashboard', 'dashboard'], [Search, 'Browse Books', 'books'], [BookOpenCheck, 'My Borrowed Books', 'loans'], [Clock3, 'My Requests', 'requests', summary.pending_requests], [History, 'Borrowing History', 'history'], [Bell, 'Notifications', 'notifications', summary.unread_notifications], [UserRound, 'My Profile', 'profile'],
  ]

  return (
    <div className="borrower-dashboard">
      {sidebarOpen && <button className="sidebar-overlay" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}
      <aside className={`dashboard-sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-brand"><div className="sidebar-logo"><img src={pcdsSeal} alt="PCDS seal" /></div><div><h1>PCDS Library</h1><p>Digital Library System</p></div><button className="mobile-close-button" onClick={() => setSidebarOpen(false)} aria-label="Close menu"><X size={20} /></button></div>
        <nav className="sidebar-navigation">{navItems.map(([Icon, label, section, badge]) => <button key={section} className={`navigation-button ${activeSection === section ? 'active' : ''}`} onClick={() => navigateTo(section)}><Icon size={19} />{label}{badge > 0 && <span className="navigation-badge">{badge}</span>}</button>)}</nav>
        <div className="sidebar-account"><div className="sidebar-avatar">{firstName.charAt(0).toUpperCase()}</div><div className="sidebar-user-details"><strong>{user.full_name || 'User'}</strong><span>{user.role || 'STUDENT'}</span></div></div>
        <button className="sign-out-button" onClick={handleSignOut}><LogOut size={18} />Sign out</button>
      </aside>

      <main className="dashboard-main">
        {activeSection !== 'dashboard' && <button className="mobile-menu-button section-menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open navigation menu"><Menu size={23} /></button>}
        {activeSection === 'dashboard' && <DashboardOverview user={user} firstName={firstName} summary={summary} loading={loading} error={dashboardError} onRetry={loadDashboard} borrowingPeriod={borrowingPeriod} isTeacher={isTeacher} onNavigate={navigateTo} setSidebarOpen={setSidebarOpen} />}
        {activeSection === 'books' && <BrowseBooks user={user} summary={summary} profileVerified={summary.verification_status === 'VERIFIED'} onRequestSubmitted={loadDashboard} />}
        {activeSection === 'loans' && <LoansSection key={location.state?.loanFilter || 'all'} summary={summary} loading={loading} error={dashboardError} onRetry={loadDashboard} onNavigate={navigateTo} initialFilter={location.state?.loanFilter || 'all'} />}
        {activeSection === 'requests' && <RequestsSection summary={summary} onNavigate={navigateTo} />}
        {activeSection === 'history' && <HistorySection summary={summary} />}
        {activeSection === 'notifications' && <NotificationsSection onUnreadCountChange={updateUnreadNotifications} />}
        {activeSection === 'profile' && <ProfileSection user={user} summary={summary} borrowingPeriod={borrowingPeriod} onProfileUpdated={loadDashboard} />}
      </main>
    </div>
  )
}

function DashboardOverview({ user, firstName, summary, loading, error, onRetry, borrowingPeriod, isTeacher, onNavigate, setSidebarOpen }) {
  const dueSoonCount = summary.active_loans.filter((loan) => {
    const timing = getLoanTiming(loan)
    return timing && !timing.isOverdue && timing.daysRemaining <= 3
  }).length
  const dayLabel = borrowingPeriod === 1 ? 'day' : 'days'
  return <>
    <header className="dashboard-header"><button className="mobile-menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open menu"><Menu size={23} /></button><div><p className="header-label">PCDS DIGITAL LIBRARY</p><h2>Good day, {firstName}!</h2><p className="header-description">Search books and monitor your borrowing activity.</p></div><div className="header-actions"><button className="notification-button" onClick={() => onNavigate('notifications')} aria-label="Open notifications"><Bell size={20} />{summary.unread_notifications > 0 && <span className="notification-dot" />}</button><div className="header-profile"><div className="header-avatar">{firstName.charAt(0).toUpperCase()}</div><div><strong>{user.full_name || 'Library User'}</strong><span>{user.role || 'STUDENT'}</span></div></div></div></header>
    {error && <div className="catalog-message error" role="alert">{error} <button type="button" className="text-action-button" onClick={onRetry}>Try again</button></div>}
    <section className="summary-grid">
      <SummaryCard icon={<BookOpenCheck size={22} />} label="Currently borrowed" value={summary.borrowed_books} color="blue" onClick={() => onNavigate('loans')} />
      <SummaryCard icon={<Clock3 size={22} />} label="Pending requests" value={summary.pending_requests} color="orange" onClick={() => onNavigate('requests')} />
      <SummaryCard icon={<CalendarDays size={22} />} label="Due soon · 3 days" value={dueSoonCount} color="orange" onClick={() => onNavigate('dueSoon')} />
      <SummaryCard icon={<CalendarDays size={22} />} label="Overdue books" value={summary.overdue_books} color="red" onClick={() => onNavigate('overdue')} />
      <SummaryCard icon={<History size={22} />} label="Books returned" value={summary.returned_books} color="green" onClick={() => onNavigate('history')} />
    </section>
    <section className="dashboard-content-grid">
      <div className="dashboard-panel">
        <div className="panel-heading">
          <div>
            <h3>{summary.active_loans.length ? 'Currently borrowed' : 'Recent activity'}</h3>
            <p>{summary.active_loans.length ? 'Books that are currently under your account' : 'Your latest borrowing request updates'}</p>
          </div>
          <button className="text-action-button" onClick={() => onNavigate(summary.active_loans.length ? 'loans' : 'requests')}>{summary.active_loans.length ? 'View all' : 'View requests'} <ChevronRight size={17} /></button>
        </div>
        {loading ? <DashboardLoading /> : summary.active_loans.length > 0
          ? <div className="loan-list">{summary.active_loans.slice(0, 3).map((loan) => <LoanItem key={loan.loan_id} loan={loan} />)}</div>
          : summary.recent_requests?.length > 0
            ? <div className="recent-activity-list">{summary.recent_requests.slice(0, 4).map((request) => <RequestItem key={request.request_id} request={request} />)}</div>
            : <EmptyState icon={<Library size={30} />} title="No borrowed books" description="Browse the collection and send your first borrowing request." buttonText="Browse books" onClick={() => onNavigate('books')} />}
      </div>
      <div className="right-panel-column">
        <div className="dashboard-panel">
          <div className="panel-heading"><div><h3>Account information</h3><p>Your library account status</p></div></div>
          <div className="account-information">
            <AccountRow label="Account status" value={user.account_status || 'ACTIVE'} valueClass="active-status" />
            <AccountRow label="Verification" value={summary.verification_status || 'PENDING_VERIFICATION'} valueClass={summary.verification_status === 'VERIFIED' ? 'active-status' : ''} />
            <AccountRow label="Account role" value={user.role || 'STUDENT'} />
            <AccountRow label="School ID" value={user.school_id || 'Not available'} />
            <AccountRow label="Borrowing period" value={`${borrowingPeriod} ${dayLabel}`} />
          </div>
        </div>
        <div className="borrowing-reminder">
          <div className="reminder-icon"><CalendarDays size={23} /></div>
          <div>
            <h3>Borrowing reminder</h3>
            <p>{isTeacher ? 'Teachers' : 'Students'} may borrow books for up to {borrowingPeriod} {dayLabel}. Return books on time to avoid a ₱{Number(summary.daily_penalty ?? 10).toLocaleString('en-PH', { maximumFractionDigits: 2 })} daily penalty.</p>
          </div>
        </div>
      </div>
    </section>
  </>
}

function SectionHeader({ title, description, icon }) { return <div className="section-page-heading"><div className="section-page-icon">{icon}</div><div><p className="header-label">LIBRARY MEMBER</p><h2>{title}</h2><p className="header-description">{description}</p></div></div> }
function BrowseBooks({ user, summary, profileVerified, onRequestSubmitted }) {
  const [books, setBooks] = useState([])
  const [search, setSearch] = useState('')
  const deferredSearch = useDeferredValue(search.trim().toLocaleLowerCase())
  const [categoryFilter, setCategoryFilter] = useState('')
  const [availableOnly, setAvailableOnly] = useState(false)
  const [sortOrder, setSortOrder] = useState('title-asc')
  const [catalogReloadKey, setCatalogReloadKey] = useState(0)
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [catalogError, setCatalogError] = useState('')
  const [cartBooks, setCartBooks] = useState([])
  const [cartSubmitting, setCartSubmitting] = useState(false)
  const [requestedBookIds, setRequestedBookIds] = useState([])
  const [message, setMessage] = useState(null)
  const [selectedBook, setSelectedBook] = useState(null)
  const detailsDialogRef = useRef(null)
  const borrowingLimit = Number(summary.borrowing_limit ?? 3)
  const borrowingUsed = Number(summary.borrowing_used ?? ((summary.active_loans?.length || 0) + (summary.pending_requests || 0)))
  const remainingAfterCart = Math.max(borrowingLimit - borrowingUsed - cartBooks.length, 0)
  const cartLimitReached = borrowingUsed + cartBooks.length >= borrowingLimit
  const borrowingUsagePercent = Math.min(100, ((borrowingUsed + cartBooks.length) / Math.max(borrowingLimit, 1)) * 100)

  useEffect(() => {
    let cancelled = false
    api.get('/books')
      .then(({ data }) => {
        if (!cancelled) {
          setBooks(data.books || [])
          setCatalogError('')
        }
      })
      .catch((error) => {
        if (!cancelled) setCatalogError(error.response?.data?.message || 'Unable to load the book catalog.')
      })
      .finally(() => {
        if (!cancelled) setCatalogLoading(false)
      })
    return () => { cancelled = true }
  }, [catalogReloadKey])

  useEffect(() => {
    const dialog = detailsDialogRef.current
    if (!dialog || !selectedBook) return undefined
    dialog.showModal()
    return () => {
      if (dialog.open) dialog.close()
    }
  }, [selectedBook])

  const categories = useMemo(
    () => [...new Set(books.map((book) => book.category).filter(Boolean))].sort((left, right) => left.localeCompare(right)),
    [books],
  )
  const filteredBooks = useMemo(() => {
    const normalized = (value) => String(value || '').toLocaleLowerCase()
    const searchRank = (book) => {
      if (!deferredSearch) return 0
      const title = normalized(book.title)
      if (title.startsWith(deferredSearch)) return 0
      if (title.split(/\s+/).some((word) => word.startsWith(deferredSearch))) return 1
      if (title.includes(deferredSearch)) return 2
      if (normalized(book.author).includes(deferredSearch)) return 3
      if (normalized(book.category).includes(deferredSearch)) return 4
      if (normalized(book.isbn).includes(deferredSearch)) return 5
      if (normalized(book.accession_number).includes(deferredSearch)) return 6
      return Number.POSITIVE_INFINITY
    }
    const result = books
      .map((book) => ({ ...book, searchRank: searchRank(book) }))
      .filter((book) => Number.isFinite(book.searchRank))
      .filter((book) => !categoryFilter || book.category === categoryFilter)
      .filter((book) => !availableOnly || book.available_copies > 0)
    result.sort((left, right) => {
      if (deferredSearch && left.searchRank !== right.searchRank) return left.searchRank - right.searchRank
      if (sortOrder === 'title-desc') return right.title.localeCompare(left.title)
      if (sortOrder === 'newest') return (right.publication_year || 0) - (left.publication_year || 0) || left.title.localeCompare(right.title)
      return left.title.localeCompare(right.title)
    })
    return result
  }, [availableOnly, books, categoryFilter, deferredSearch, sortOrder])

  function toggleCartBook(book) {
    setMessage(null)
    setCartBooks((current) => {
      if (current.some((item) => item.book_id === book.book_id)) return current.filter((item) => item.book_id !== book.book_id)
      if (borrowingUsed + current.length >= borrowingLimit) {
        setMessage({ type: 'error', text: `You have reached your ${borrowingLimit}-book borrowing limit. Pending requests and currently borrowed books count toward this limit.` })
        return current
      }
      return [...current, book]
    })
  }

  function removeCartBook(bookId) {
    setCartBooks((current) => current.filter((book) => book.book_id !== bookId))
  }

  async function submitCart() {
    if (!cartBooks.length || cartSubmitting) return
    setMessage(null)
    setCartSubmitting(true)
    const submittedBookIds = []
    const failures = []
    try {
      for (const book of cartBooks) {
        try {
          await api.post('/borrow-requests', { book_id: book.book_id })
          submittedBookIds.push(book.book_id)
        } catch (error) {
          failures.push({
            title: book.title,
            reason: error.response?.data?.message || 'Unable to submit this borrow request.',
          })
        }
      }

      if (submittedBookIds.length) {
        setRequestedBookIds((current) => [...new Set([...current, ...submittedBookIds])])
        setCartBooks((current) => current.filter((book) => !submittedBookIds.includes(book.book_id)))
        await onRequestSubmitted()
      }

      if (failures.length) {
        const submittedCount = submittedBookIds.length
        const submittedMessage = submittedCount
          ? `${submittedCount} ${submittedCount === 1 ? 'request was' : 'requests were'} submitted. `
          : ''
        setMessage({
          type: 'error',
          text: `${submittedMessage}Unable to submit: ${failures.map(({ title, reason }) => `${title} — ${reason}`).join(' ')}`,
        })
      } else {
        setMessage({
          type: 'success',
          text: `${submittedBookIds.length} ${submittedBookIds.length === 1 ? 'borrow request was' : 'borrow requests were'} submitted.`,
        })
      }
    } finally {
      setCartSubmitting(false)
    }
  }

  const canRequest = user.role === 'STUDENT' || user.role === 'TEACHER'
  return <>
    <SectionHeader title="Browse Books" description="Search the library collection and request an available copy." icon={<BookOpen size={24} />} />
    {!profileVerified && <div className="catalog-message" role="status">Your school profile must be verified before you can submit a borrow request.</div>}
    {!canRequest && <div className="catalog-message" role="status">Only student and teacher accounts can request books.</div>}
    {message && <div className={`catalog-message ${message.type}`} role="status">{message.text}</div>}
    <form className="catalog-search" role="search" onSubmit={(event) => { event.preventDefault(); setSearch(search.trim()) }}>
      <Search size={19} aria-hidden="true" />
      <input aria-label="Search books" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by title, author, ISBN, accession number, or category" />
      {search && <button className="catalog-search-clear" type="button" onClick={() => setSearch('')} aria-label="Clear book search"><X size={18} aria-hidden="true" /></button>}
      <button className="catalog-search-submit" type="submit">Search</button>
    </form>
    <div className="catalog-toolbar" aria-label="Catalog filters and sorting">
      <label className="catalog-filter-field">
        <span>Category</span>
        <select aria-label="Filter by category" value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}>
          <option value="">All categories</option>
          {categories.map((category) => <option value={category} key={category}>{category}</option>)}
        </select>
      </label>
      <label className="available-filter">
        <input type="checkbox" checked={availableOnly} onChange={(event) => setAvailableOnly(event.target.checked)} />
        <span>Available only</span>
      </label>
      <label className="catalog-filter-field catalog-sort-field">
        <span>Sort by</span>
        <select aria-label="Sort books" value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}>
          <option value="title-asc">Title A–Z</option>
          <option value="title-desc">Title Z–A</option>
          <option value="newest">Publication year: newest</option>
        </select>
      </label>
    </div>
    <section className={`borrow-cart ${cartBooks.length ? 'has-items' : ''}`} aria-labelledby="borrow-cart-title">
      <div className="borrow-cart-heading">
        <div className="borrow-cart-icon"><ShoppingCart size={20} aria-hidden="true" /></div>
        <div className="borrow-cart-summary">
          <span className="borrow-cart-eyebrow">BORROW REQUEST</span>
          <h3 id="borrow-cart-title">Your request cart <span>{cartBooks.length}</span></h3>
          <p>{cartBooks.length ? 'Review your selected books before submitting.' : 'Select available books from the catalog below.'}</p>
        </div>
        <button className="submit-cart-button" type="button" onClick={submitCart} disabled={!canRequest || !profileVerified || cartSubmitting || cartBooks.length === 0}>
          {cartSubmitting ? 'Submitting...' : cartBooks.length ? <><Check size={17} aria-hidden="true" /> Submit {cartBooks.length} {cartBooks.length === 1 ? 'request' : 'requests'}</> : 'Cart is empty'}
        </button>
      </div>
      <div className="borrow-limit" aria-label={`${borrowingUsed + cartBooks.length} of ${borrowingLimit} borrowing slots used`}>
        <div className="borrow-limit-label"><span>Borrowing capacity</span><strong>{borrowingUsed + cartBooks.length} / {borrowingLimit} used · {remainingAfterCart} remaining</strong></div>
        <div className="borrow-limit-track" role="progressbar" aria-valuemin="0" aria-valuemax={borrowingLimit} aria-valuenow={borrowingUsed + cartBooks.length}><span style={{ width: `${borrowingUsagePercent}%` }} /></div>
        <small>Pending requests and currently borrowed books are included in your limit.</small>
      </div>
      {cartBooks.length > 0 && <ul className="borrow-cart-items">
        {cartBooks.map((book, index) => <li key={book.book_id}>
          <div className="borrow-cart-item-icon" aria-hidden="true"><BookOpen size={18} /></div>
          <div className="borrow-cart-item-details"><span>Selection {index + 1}</span><strong>{book.title}</strong><small>{book.author || 'Unknown author'} · Accession No. {book.accession_number}</small></div>
          <button type="button" onClick={() => removeCartBook(book.book_id)} disabled={cartSubmitting} aria-label={`Remove ${book.title} from cart`} title="Remove from cart"><X size={17} aria-hidden="true" /></button>
        </li>)}
      </ul>}
    </section>
    {catalogError && <div className="catalog-message error" role="alert">{catalogError} <button type="button" className="text-action-button" onClick={() => { setCatalogLoading(true); setCatalogReloadKey((current) => current + 1) }}>Try again</button></div>}
    {catalogLoading ? <div className="dashboard-panel section-placeholder"><DashboardLoading /></div> : filteredBooks.length > 0
      ? <div className="book-catalog" aria-live="polite">{filteredBooks.map((book) => {
        const unavailable = book.available_copies < 1
        const alreadyRequested = requestedBookIds.includes(book.book_id)
        const inCart = cartBooks.some((item) => item.book_id === book.book_id)
        const limitBlocksAddition = cartLimitReached && !inCart
        return <article className="book-card" key={book.book_id}>
          <BookCover book={book} />
          <div className="book-card-details">
            <h3>{book.title}</h3>
            <p>{book.author}{book.publication_year ? ` · ${book.publication_year}` : ''}</p>
            {book.description && <p className="book-description">{book.description}</p>}
            {book.category && <span className="book-category">{book.category}</span>}
            <span className="book-identifiers">Accession No. {book.accession_number}{book.call_number ? ` · Call No. ${book.call_number}` : ''}</span>
            <strong className={`book-availability ${unavailable ? 'book-unavailable' : ''}`}>{unavailable ? 'Currently borrowed' : `Available: ${book.available_copies} ${book.available_copies === 1 ? 'copy' : 'copies'}`}</strong>
          </div>
          <div className="book-card-actions">
            <button className="book-details-button" type="button" onClick={() => setSelectedBook(book)}><Eye size={16} aria-hidden="true" /> View details</button>
            <button className={`request-book-button add-to-cart-button ${inCart ? 'in-cart' : ''}`} type="button" onClick={() => toggleCartBook(book)} disabled={!canRequest || !profileVerified || unavailable || alreadyRequested || cartSubmitting || limitBlocksAddition} title={limitBlocksAddition ? `Borrowing limit reached (${borrowingLimit})` : undefined}>
              {alreadyRequested ? <><Check size={16} aria-hidden="true" /> Requested</> : inCart ? <><Check size={16} aria-hidden="true" /> In cart</> : limitBlocksAddition ? <>Limit reached</> : <><ShoppingCart size={16} aria-hidden="true" /> Add to cart</>}
            </button>
          </div>
        </article>
      })}</div>
      : <div className="dashboard-panel section-placeholder"><Library size={34} /><h3>No books found</h3><p>{deferredSearch ? `No books match “${search.trim()}”. Clear the search or try another keyword.` : 'Choose a different category or turn off “Available only”.'}</p></div>}
    <dialog className="book-details-dialog" ref={detailsDialogRef} aria-labelledby="book-details-title" onClose={() => setSelectedBook(null)} onClick={(event) => { if (event.target === event.currentTarget) event.currentTarget.close() }}>
      {selectedBook && <>
        <div className="book-details-dialog-header">
          <div><p className="header-label">BOOK DETAILS</p><h2 id="book-details-title">{selectedBook.title}</h2></div>
          <button className="book-details-close" type="button" onClick={() => detailsDialogRef.current?.close()} aria-label="Close book details"><X size={20} /></button>
        </div>
        <div className="book-details-dialog-body">
          <BookCover book={selectedBook} />
          <div className="book-details-content">
            <p className="book-details-author">{selectedBook.author}{selectedBook.publication_year ? ` · ${selectedBook.publication_year}` : ''}</p>
            <p className={`book-details-availability ${selectedBook.available_copies > 0 ? 'available' : 'unavailable'}`}>
              {selectedBook.available_copies > 0 ? `Available: ${selectedBook.available_copies} ${selectedBook.available_copies === 1 ? 'copy' : 'copies'}` : 'Currently borrowed'}
            </p>
            <dl className="book-details-metadata">
              <div><dt>Category / subject</dt><dd>{selectedBook.category || 'Not specified'}</dd></div>
              <div><dt>Call number</dt><dd>{selectedBook.call_number || 'Not specified'}</dd></div>
              <div><dt>Accession number</dt><dd>{selectedBook.accession_number || 'Not specified'}</dd></div>
              <div><dt>ISBN</dt><dd>{selectedBook.isbn || 'Not specified'}</dd></div>
              <div><dt>Copies</dt><dd>{selectedBook.available_copies} available of {selectedBook.total_copies}</dd></div>
            </dl>
            <section className="book-details-description"><h3>Description</h3><p>{selectedBook.description || 'No description is available for this book yet.'}</p></section>
          </div>
        </div>
      </>}
    </dialog>
  </>
}

function BookCover({ book }) {
  const [coverUrl, setCoverUrl] = useState('')

  useEffect(() => {
    if (!book.cover_image) return undefined

    let cancelled = false
    let objectUrl
    api.get(`/books/${book.book_id}/cover-image`, { responseType: 'blob' })
      .then(({ data }) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(data)
        setCoverUrl(objectUrl)
      })
      .catch((error) => {
        if (error.response?.status !== 404) console.error(`Unable to load the cover image for "${book.title}".`, error)
      })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [book.book_id, book.cover_image, book.title])

  if (book.cover_image && coverUrl) return <div className="book-card-cover book-card-cover-image"><img src={coverUrl} alt={`Cover of ${book.title} by ${book.author}`} loading="lazy" /></div>
  return <div className="book-card-cover book-card-cover-image book-card-default-cover">
    <img src="/pcds-library-icon.png" alt={`Default PCDS Library cover for ${book.title}`} loading="lazy" />
  </div>
}
function LoansSection({ summary, loading, error, onRetry, onNavigate, initialFilter }) {
  const allLoans = summary.active_loans || []
  const dueSoonCount = allLoans.filter((loan) => {
    const timing = getLoanTiming(loan)
    return timing && !timing.isOverdue && timing.daysRemaining <= 3
  }).length
  const overdueCount = allLoans.filter((loan) => getLoanTiming(loan)?.isOverdue).length
  const loans = allLoans.filter((loan) => {
    const timing = getLoanTiming(loan)
    if (initialFilter === 'overdue') return timing?.isOverdue
    if (initialFilter === 'dueSoon') return timing && !timing.isOverdue && timing.daysRemaining <= 3
    return true
  })
  const filters = [['all', 'All', allLoans.length], ['dueSoon', 'Due Soon', dueSoonCount], ['overdue', 'Overdue', overdueCount]]
  return <>
    <SectionHeader title="My Borrowed Books" description="Track active loans, due dates, and return status from your account." icon={<BookOpenCheck size={24} />} />
    <div className="loan-summary-grid" aria-label="Borrowed books summary">
      <div className="loan-summary-card"><BookOpenCheck size={22} aria-hidden="true" /><span>Active Loans</span><strong>{allLoans.length}</strong></div>
      <div className="loan-summary-card due-soon"><Clock3 size={22} aria-hidden="true" /><span>Due Soon</span><strong>{dueSoonCount}</strong></div>
      <div className="loan-summary-card overdue"><CalendarDays size={22} aria-hidden="true" /><span>Overdue</span><strong>{overdueCount}</strong></div>
    </div>
    <div className="loan-filter-tabs" role="tablist" aria-label="Filter borrowed books">
      {filters.map(([key, label, count]) => <button key={key} type="button" role="tab" aria-selected={initialFilter === key} className={initialFilter === key ? 'active' : ''} onClick={() => onNavigate(key === 'all' ? 'loans' : key)}>{label}<span>{count}</span></button>)}
    </div>
    {loading ? <div className="dashboard-panel loan-state-panel"><DashboardLoading /></div>
      : error ? <div className="dashboard-panel loan-state-panel"><div className="section-placeholder"><Library size={34} /><h3>Unable to load borrowed books</h3><p>{error}</p><button className="request-book-button" type="button" onClick={onRetry}>Try again</button></div></div>
        : loans.length ? <div className="loan-card-grid">{loans.map((loan) => <BorrowedBookCard key={loan.loan_id} loan={loan} />)}</div>
          : <div className="dashboard-panel loan-state-panel"><EmptyState icon={<Library size={30} />} title={initialFilter === 'overdue' ? 'No overdue books' : initialFilter === 'dueSoon' ? 'Nothing due soon' : "You haven't borrowed any books yet"} description={initialFilter === 'all' ? 'Browse the library collection and request your first book.' : 'There are no books in this category right now.'} buttonText={initialFilter === 'all' ? 'Browse Books' : 'View All Loans'} onClick={() => initialFilter === 'all' ? onNavigate('books') : onNavigate('loans')} /></div>}
  </>
}
function RequestsSection({ summary, onNavigate }) { return <><SectionHeader title="My Requests" description="Review the status of your borrowing requests." icon={<Clock3 size={24} />} /><div className="dashboard-panel section-list-panel">{summary.recent_requests?.length ? summary.recent_requests.map((request) => <RequestItem key={request.request_id} request={request} />) : <EmptyState icon={<Clock3 size={30} />} title="No borrow requests yet" description="Browse the catalog to request an available book." buttonText="Browse books" onClick={() => onNavigate('books')} />}</div></> }
function HistorySection({ summary }) { return <><SectionHeader title="Borrowing History" description="See the books you have previously returned." icon={<History size={24} />} />{summary.recent_returns?.length ? <div className="book-catalog history-card-list">{summary.recent_returns.map((loan) => <ReturnedLoanItem key={loan.loan_id} loan={loan} />)}</div> : <div className="dashboard-panel section-placeholder"><History size={34} /><h3>No returned books yet</h3><p>Returned books will appear in your history.</p></div>}</> }
function NotificationsSection({ onUnreadCountChange }) {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/notifications')
      .then(({ data }) => {
        setNotifications(data.notifications || [])
        onUnreadCountChange(data.unread_count || 0)
      })
      .catch((requestError) => setError(requestError.response?.data?.message || 'Unable to load notifications.'))
      .finally(() => setLoading(false))
  }, [onUnreadCountChange])

  async function markRead(notificationId) {
    try {
      await api.patch(`/notifications/${notificationId}/read`)
      setNotifications((current) => current.map((item) => item.notification_id === notificationId ? { ...item, is_read: true } : item))
      onUnreadCountChange(notifications.filter((item) => !item.is_read && item.notification_id !== notificationId).length)
    } catch (requestError) {
      setError(requestError.response?.data?.message || 'Unable to update notification.')
    }
  }

  const unreadCount = notifications.filter((item) => !item.is_read).length
  return <><SectionHeader title="Notifications" description="Account verification and borrowing updates." icon={<Bell size={24} />} /><div className="notifications-summary">{unreadCount} unread</div>{error && <div className="catalog-message" role="alert">{error}</div>}{loading ? <div className="dashboard-panel section-placeholder"><DashboardLoading /></div> : notifications.length === 0 ? <div className="dashboard-panel section-placeholder"><Bell size={34} /><h3>You're all caught up</h3><p>Verification and borrowing updates will appear here.</p></div> : <div className="notifications-list">{notifications.map((notification) => <article className={`notification-item ${notification.is_read ? 'read' : 'unread'}`} key={notification.notification_id}><div className="notification-item-mark"><Bell size={18} /></div><div className="notification-item-content"><h3>{notification.title}</h3><p>{notification.message}</p><time>{new Date(notification.created_at).toLocaleString('en-PH', { dateStyle: 'medium', timeStyle: 'short' })}</time></div>{!notification.is_read && <button className="mark-read-button" onClick={() => markRead(notification.notification_id)}>Mark read</button>}</article>)}</div>}</>
}
function ProfileSection({ user, summary, borrowingPeriod, onProfileUpdated }) {
  const [schoolIdFile, setSchoolIdFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState(null)
  const canReplaceSchoolId = ['STUDENT', 'TEACHER'].includes(user.role) && !summary.school_id_image_available

  async function handleSchoolIdUpload(event) {
    event.preventDefault()
    if (!schoolIdFile) {
      setMessage({ type: 'error', text: 'Choose a JPG, PNG, or WebP School ID photo first.' })
      return
    }

    const form = event.currentTarget
    const formData = new FormData()
    formData.append('school_id', schoolIdFile)
    setUploading(true)
    setMessage(null)
    try {
      const { data } = await api.post('/auth/profile/school-id', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setSchoolIdFile(null)
      form.reset()
      setMessage({ type: 'success', text: data.message })
      await onProfileUpdated()
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.message || 'Unable to upload your School ID photo. Please try again.' })
    } finally {
      setUploading(false)
    }
  }

  return <>
    <SectionHeader title="My Profile" description="View your library account information." icon={<UserRound size={24} />} />
    <div className="dashboard-panel profile-panel">
      <AccountRow label="Full name" value={user.full_name || 'Library User'} />
      <AccountRow label="Account status" value={user.account_status || 'ACTIVE'} valueClass="active-status" />
      <AccountRow label="Role" value={user.role || 'STUDENT'} />
      <AccountRow label="School ID" value={user.school_id || 'Not available'} />
      <AccountRow label="Phone number" value={user.contact_number || 'Not available'} />
      <AccountRow label="Verification" value={summary.verification_status || 'PENDING_VERIFICATION'} />
      <AccountRow label="Borrowing period" value={`${borrowingPeriod} ${borrowingPeriod === 1 ? 'day' : 'days'}`} />
    </div>
    {canReplaceSchoolId && <section className="dashboard-panel school-id-reupload">
      <h3>School ID photo unavailable</h3>
      <p>Your profile was submitted, but the library cannot access its School ID photo. Upload it again so an administrator can review your account.</p>
      {message && <div className={`catalog-message ${message.type}`} role={message.type === 'error' ? 'alert' : 'status'}>{message.text}</div>}
      <form onSubmit={handleSchoolIdUpload}>
        <label htmlFor="replace-school-id">Choose School ID photo (JPG, PNG, or WebP; max 5 MB)</label>
        <input id="replace-school-id" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setSchoolIdFile(event.target.files?.[0] || null)} required />
        <button className="request-book-button school-id-upload-button" type="submit" disabled={uploading || !schoolIdFile}>{uploading ? 'Uploading...' : 'Upload School ID photo'}</button>
      </form>
    </section>}
  </>
}

function SummaryCard({ icon, label, value, color, onClick }) { return <button type="button" className="summary-card" onClick={onClick} aria-label={`${label}: ${value}. View details`}><div className={`summary-icon ${color}`} aria-hidden="true">{icon}</div><div><span>{label}</span><strong>{value}</strong></div><ChevronRight size={18} className="summary-arrow" aria-hidden="true" /></button> }
function AccountRow({ label, value, valueClass = '' }) { return <div className="account-row"><span>{label}</span><strong className={valueClass}>{value}</strong></div> }
function getLoanTiming(loan) {
  const dueDate = new Date(loan.due_date)
  if (!loan.due_date || Number.isNaN(dueDate.getTime())) return null
  const difference = dueDate.getTime() - Date.now()
  return {
    dueDate,
    isOverdue: difference < 0,
    daysRemaining: Math.max(0, Math.ceil(difference / 86_400_000)),
    daysOverdue: Math.max(1, Math.ceil(Math.abs(difference) / 86_400_000)),
  }
}

function BorrowedBookCard({ loan }) {
  const timing = getLoanTiming(loan)
  const formatDate = (value) => {
    const date = value ? new Date(value) : null
    return date && !Number.isNaN(date.getTime())
      ? date.toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })
      : 'Unavailable'
  }
  const status = timing?.isOverdue ? 'Overdue' : timing?.daysRemaining === 0 ? 'Due today' : timing?.daysRemaining <= 3 ? 'Due soon' : 'Active'
  const remainingLabel = timing?.isOverdue
    ? `${timing.daysOverdue} ${timing.daysOverdue === 1 ? 'day' : 'days'} overdue`
    : timing?.daysRemaining === 0
      ? 'Return today'
      : `${timing?.daysRemaining ?? 0} ${timing?.daysRemaining === 1 ? 'day' : 'days'} remaining`
  const book = { book_id: loan.book_id, title: loan.book_title, author: loan.book_author || 'Unknown author', cover_image: loan.cover_image }

  return <article className={`borrowed-book-card ${timing?.isOverdue ? 'is-overdue' : timing?.daysRemaining <= 3 ? 'is-due-soon' : ''}`}>
    <BookCover book={book} />
    <div className="borrowed-book-content">
      <div className="borrowed-book-heading"><div><h3>{loan.book_title}</h3><p>{loan.book_author || 'Unknown author'}</p></div><span className={`loan-status-badge ${timing?.isOverdue ? 'overdue' : timing?.daysRemaining <= 3 ? 'due-soon' : 'active'}`}>{status}</span></div>
      <dl className="borrowed-book-dates">
        <div><dt>Date borrowed</dt><dd>{formatDate(loan.borrowed_at)}</dd></div>
        <div><dt>Due date</dt><dd>{formatDate(loan.due_date)}</dd></div>
      </dl>
      <div className="borrowed-book-footer"><span>Accession No. {loan.accession_number}</span><strong>{remainingLabel}</strong></div>
    </div>
  </article>
}

function LoanItem({ loan }) {
  const timing = getLoanTiming(loan)
  const dueDateLabel = timing
    ? timing.dueDate.toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })
    : 'Due date unavailable'
  const timingLabel = !timing
    ? ''
    : timing.isOverdue
      ? `Overdue by ${timing.daysOverdue} ${timing.daysOverdue === 1 ? 'day' : 'days'}`
      : timing.daysRemaining === 0
        ? 'Due today'
        : `Due in ${timing.daysRemaining} ${timing.daysRemaining === 1 ? 'day' : 'days'}`
  return <div className={`loan-item ${timing?.isOverdue ? 'loan-item-overdue' : ''}`}>
    <div className="loan-book-icon"><BookOpen size={21} /></div>
    <div className="loan-information"><strong>{loan.book_title}</strong><span>Accession No. {loan.accession_number}</span></div>
    <div className={`loan-due-date ${timing?.isOverdue ? 'overdue' : timing?.daysRemaining <= 3 ? 'due-soon' : ''}`}>
      <span>Due date</span><strong>{dueDateLabel}</strong>
      {timingLabel && <span className="loan-timing-label" role="status">{timingLabel}</span>}
    </div>
  </div>
}
function ReturnedLoanItem({ loan }) {
  const returnedAt = loan.returned_at ? new Date(loan.returned_at) : null
  const dueDate = loan.due_date ? new Date(loan.due_date) : null
  const hasReturnedDate = returnedAt && !Number.isNaN(returnedAt.getTime())
  const hasDueDate = dueDate && !Number.isNaN(dueDate.getTime())
  const returnedDay = String(loan.returned_at || '').slice(0, 10)
  const dueDay = String(loan.due_date || '').slice(0, 10)
  const lateDays = hasReturnedDate && hasDueDate
    ? Math.max(0, Math.round((Date.parse(`${returnedDay}T00:00:00Z`) - Date.parse(`${dueDay}T00:00:00Z`)) / 86_400_000))
    : 0
  const returnedDateLabel = hasReturnedDate
    ? returnedAt.toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })
    : 'Date unavailable'
  const timingLabel = lateDays > 0
    ? `Returned ${lateDays} ${lateDays === 1 ? 'day' : 'days'} late`
    : 'Returned on time'

  return <article className={`book-card returned-book-card ${lateDays > 0 ? 'returned-book-card-late' : ''}`}>
    <div className="book-card-cover returned-book-cover" aria-hidden="true">
      <BookOpen size={48} />
      <span>RETURNED</span>
    </div>
    <div className="book-card-details">
      <h3>{loan.book_title}</h3>
      <p>Returned {returnedDateLabel}</p>
      <span className="book-identifiers">Accession No. {loan.accession_number}</span>
      <strong className={`returned-book-status ${lateDays > 0 ? 'is-late' : 'is-on-time'}`} role="status">{timingLabel}</strong>
      <span className={`returned-book-penalty ${Number(loan.penalty_amount || 0) > 0 ? 'has-penalty' : ''}`}>Penalty: {Number(loan.penalty_amount || 0).toLocaleString('en-PH', { style: 'currency', currency: 'PHP' })}{loan.penalty_status && loan.penalty_status !== 'NONE' ? ` · ${loan.penalty_status}` : ''}</span>
    </div>
  </article>
}
function RequestItem({ request }) { const requestedAt = new Date(request.requested_at).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' }); return <div className="loan-item"><div className="loan-book-icon"><Clock3 size={21} /></div><div className="loan-information"><strong>{request.book_title}</strong><span>Requested {requestedAt}</span></div><div className={`request-status ${request.status.toLowerCase()}`}>{request.status}</div></div> }
function EmptyState({ icon, title, description, buttonText, onClick }) { return <div className="dashboard-empty-state"><div className="empty-state-icon">{icon}</div><h4>{title}</h4><p>{description}</p><button onClick={onClick}>{buttonText}</button></div> }
function DashboardLoading() { return <div className="dashboard-loading">Loading your library information...</div> }

export default DashboardPage
