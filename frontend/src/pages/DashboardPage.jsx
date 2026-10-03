import { useCallback, useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { googleLogout } from '@react-oauth/google'
import { Bell, BookOpen, BookOpenCheck, CalendarDays, ChevronRight, Clock3, History, LayoutDashboard, Library, LogOut, Menu, Search, UserRound, X } from 'lucide-react'

import api from '../services/api'
import './DashboardPage.css'

const initialSummary = { borrowed_books: 0, pending_requests: 0, overdue_books: 0, returned_books: 0, unread_notifications: 0, active_loans: [], recent_requests: [] }
const sectionPaths = {
  dashboard: '/dashboard', books: '/books', loans: '/my-loans', requests: '/my-requests',
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
    navigate(sectionPaths[section] || '/dashboard')
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
        <div className="sidebar-brand"><div className="sidebar-logo"><BookOpen size={23} /></div><div><h1>PCDS Library</h1><p>Management System</p></div><button className="mobile-close-button" onClick={() => setSidebarOpen(false)} aria-label="Close menu"><X size={20} /></button></div>
        <nav className="sidebar-navigation">{navItems.map(([Icon, label, section, badge]) => <button key={section} className={`navigation-button ${activeSection === section ? 'active' : ''}`} onClick={() => navigateTo(section)}><Icon size={19} />{label}{badge > 0 && <span className="navigation-badge">{badge}</span>}</button>)}</nav>
        <div className="sidebar-account"><div className="sidebar-avatar">{firstName.charAt(0).toUpperCase()}</div><div className="sidebar-user-details"><strong>{user.full_name || 'User'}</strong><span>{user.role || 'STUDENT'}</span></div></div>
        <button className="sign-out-button" onClick={handleSignOut}><LogOut size={18} />Sign out</button>
      </aside>

      <main className="dashboard-main">
        {activeSection !== 'dashboard' && <button className="mobile-menu-button section-menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open navigation menu"><Menu size={23} /></button>}
        {activeSection === 'dashboard' && <DashboardOverview user={user} firstName={firstName} summary={summary} loading={loading} error={dashboardError} onRetry={loadDashboard} borrowingPeriod={borrowingPeriod} isTeacher={isTeacher} onNavigate={navigateTo} setSidebarOpen={setSidebarOpen} />}
        {activeSection === 'books' && <BrowseBooks user={user} profileVerified={summary.verification_status === 'VERIFIED'} onRequestSubmitted={loadDashboard} />}
        {activeSection === 'loans' && <LoansSection summary={summary} loading={loading} onNavigate={navigateTo} />}
        {activeSection === 'requests' && <RequestsSection summary={summary} onNavigate={navigateTo} />}
        {activeSection === 'history' && <HistorySection summary={summary} />}
        {activeSection === 'notifications' && <NotificationsSection onUnreadCountChange={updateUnreadNotifications} />}
        {activeSection === 'profile' && <ProfileSection user={user} borrowingPeriod={borrowingPeriod} />}
      </main>
    </div>
  )
}

function DashboardOverview({ user, firstName, summary, loading, error, onRetry, borrowingPeriod, isTeacher, onNavigate, setSidebarOpen }) {
  return <>
    <header className="dashboard-header"><button className="mobile-menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open menu"><Menu size={23} /></button><div><p className="header-label">MEMBER DASHBOARD</p><h2>Good day, {firstName}!</h2><p className="header-description">Search books and monitor your borrowing activity.</p></div><div className="header-actions"><button className="notification-button" onClick={() => onNavigate('notifications')} aria-label="Open notifications"><Bell size={20} />{summary.unread_notifications > 0 && <span className="notification-dot" />}</button><div className="header-profile"><div className="header-avatar">{firstName.charAt(0).toUpperCase()}</div><div><strong>{user.full_name || 'Library User'}</strong><span>{user.role || 'STUDENT'}</span></div></div></div></header>
    {error && <div className="catalog-message error" role="alert">{error} <button type="button" className="text-action-button" onClick={onRetry}>Try again</button></div>}
    <section className="summary-grid"><SummaryCard icon={<BookOpenCheck size={22} />} label="Currently borrowed" value={summary.borrowed_books} color="blue" onClick={() => onNavigate('loans')} /><SummaryCard icon={<Clock3 size={22} />} label="Pending requests" value={summary.pending_requests} color="orange" onClick={() => onNavigate('requests')} /><SummaryCard icon={<CalendarDays size={22} />} label="Overdue books" value={summary.overdue_books} color="red" onClick={() => onNavigate('loans')} /><SummaryCard icon={<History size={22} />} label="Books returned" value={summary.returned_books} color="green" onClick={() => onNavigate('history')} /></section>
    <section className="dashboard-content-grid">
      <div className="dashboard-panel">
        <div className="panel-heading">
          <div><h3>Currently borrowed</h3><p>Books that are currently under your account</p></div>
          <button className="text-action-button" onClick={() => onNavigate('loans')}>View all <ChevronRight size={17} /></button>
        </div>
        {loading ? <DashboardLoading /> : summary.active_loans.length > 0
          ? <div className="loan-list">{summary.active_loans.slice(0, 3).map((loan) => <LoanItem key={loan.loan_id} loan={loan} />)}</div>
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
            <AccountRow label="Borrowing period" value={`${borrowingPeriod} days`} />
          </div>
        </div>
        <div className="borrowing-reminder">
          <div className="reminder-icon"><CalendarDays size={23} /></div>
          <div>
            <h3>Borrowing reminder</h3>
            <p>{isTeacher ? 'Teachers' : 'Students'} may borrow books for up to {borrowingPeriod} days. Return books on time to avoid a ₱{Number(summary.daily_penalty ?? 10).toLocaleString('en-PH', { maximumFractionDigits: 2 })} daily penalty.</p>
          </div>
        </div>
      </div>
    </section>
  </>
}

function SectionHeader({ title, description, icon }) { return <div className="section-page-heading"><div className="section-page-icon">{icon}</div><div><p className="header-label">LIBRARY MEMBER</p><h2>{title}</h2><p className="header-description">{description}</p></div></div> }
function BrowseBooks({ user, profileVerified, onRequestSubmitted }) {
  const [books, setBooks] = useState([])
  const [search, setSearch] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [catalogReloadKey, setCatalogReloadKey] = useState(0)
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [catalogError, setCatalogError] = useState('')
  const [requestingBookId, setRequestingBookId] = useState(null)
  const [requestedBookIds, setRequestedBookIds] = useState([])
  const [form, setForm] = useState({ title: '', author: '', call_number: '', accession_number: '' })
  const [bookPhoto, setBookPhoto] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    let cancelled = false
    api.get('/books', { params: { search: searchTerm } })
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
  }, [searchTerm, catalogReloadKey])

  function updateForm(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function submitRequest(event) {
    event.preventDefault()
    setMessage(null)
    if (!bookPhoto) {
      setMessage({ type: 'error', text: 'Choose a clear photo of the requested book.' })
      return
    }

    const requestData = new FormData()
    Object.entries(form).forEach(([key, value]) => requestData.append(key, value.trim()))
    requestData.append('book_image', bookPhoto)
    setLoading(true)
    try {
      const response = await api.post('/borrow-requests', requestData, { headers: { 'Content-Type': 'multipart/form-data' } })
      setMessage({ type: 'success', text: response.data.message })
      setForm({ title: '', author: '', call_number: '', accession_number: '' })
      setBookPhoto(null)
      event.target.reset()
      await onRequestSubmitted()
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.message || 'Unable to submit the borrow request.' })
    } finally {
      setLoading(false)
    }
  }

  async function requestCatalogBook(book) {
    setMessage(null)
    setRequestingBookId(book.book_id)
    try {
      const response = await api.post('/borrow-requests', { book_id: book.book_id })
      setRequestedBookIds((current) => [...current, book.book_id])
      setMessage({ type: 'success', text: response.data.message })
      await onRequestSubmitted()
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.message || 'Unable to submit the borrow request.' })
    } finally {
      setRequestingBookId(null)
    }
  }

  const canRequest = user.role === 'STUDENT' || user.role === 'TEACHER'
  return <>
    <SectionHeader title="Browse Books" description="Search the library collection and request an available copy." icon={<BookOpen size={24} />} />
    {!profileVerified && <div className="catalog-message" role="status">Your school profile must be verified before you can submit a borrow request.</div>}
    {!canRequest && <div className="catalog-message" role="status">Only student and teacher accounts can request books.</div>}
    {message && <div className={`catalog-message ${message.type}`} role="status">{message.text}</div>}
    <form className="catalog-search" onSubmit={(event) => { event.preventDefault(); setCatalogLoading(true); setSearchTerm(search.trim()); setCatalogReloadKey((current) => current + 1) }}>
      <Search size={19} aria-hidden="true" />
      <input aria-label="Search books" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by title, author, ISBN, or accession number" />
      <button type="submit">Search</button>
    </form>
    {catalogError && <div className="catalog-message error" role="alert">{catalogError} <button type="button" className="text-action-button" onClick={() => { setCatalogLoading(true); setCatalogReloadKey((current) => current + 1) }}>Try again</button></div>}
    {catalogLoading ? <div className="dashboard-panel section-placeholder"><DashboardLoading /></div> : books.length > 0
      ? <div className="book-catalog">{books.map((book) => {
        const unavailable = book.available_copies < 1
        const alreadyRequested = requestedBookIds.includes(book.book_id)
        return <article className="book-card" key={book.book_id}>
          <div className="book-card-icon"><BookOpen size={23} /></div>
          <div className="book-card-details">
            <h3>{book.title}</h3>
            <p>{book.author}{book.publication_year ? ` · ${book.publication_year}` : ''}</p>
            <span>Accession No. {book.accession_number}{book.call_number ? ` · Call No. ${book.call_number}` : ''}</span>
            <strong className={unavailable ? 'book-unavailable' : ''}>{unavailable ? 'Currently unavailable' : `${book.available_copies} ${book.available_copies === 1 ? 'copy' : 'copies'} available`}</strong>
          </div>
          <button className="request-book-button" type="button" onClick={() => requestCatalogBook(book)} disabled={!canRequest || !profileVerified || unavailable || alreadyRequested || requestingBookId === book.book_id}>
            {requestingBookId === book.book_id ? 'Requesting...' : alreadyRequested ? 'Requested' : 'Request book'}
          </button>
        </article>
      })}</div>
      : <div className="dashboard-panel section-placeholder"><Library size={34} /><h3>No books found</h3><p>Try another title, author, ISBN, or call number.</p></div>}
    <details className="manual-request-disclosure">
      <summary>Request a book not listed in the catalog</summary>
      <form className="borrow-request-form" onSubmit={submitRequest}>
        <div className="field"><label htmlFor="borrow-book-title">Title of the book</label><input id="borrow-book-title" name="title" value={form.title} onChange={updateForm} placeholder="Enter the book title" required /></div>
        <div className="field"><label htmlFor="borrow-call-number">Call number</label><input id="borrow-call-number" name="call_number" value={form.call_number} onChange={updateForm} placeholder="e.g. Cir. 005.B" required /></div>
        <div className="field-grid"><div className="field"><label htmlFor="borrow-accession">Accession number</label><input id="borrow-accession" name="accession_number" value={form.accession_number} onChange={updateForm} placeholder="e.g. 10,225" required /></div><div className="field"><label htmlFor="borrow-author">Author <span>Optional</span></label><input id="borrow-author" name="author" value={form.author} onChange={updateForm} placeholder="Book author" /></div></div>
        <div className="field"><label htmlFor="borrow-book-photo">Picture of the book</label><input id="borrow-book-photo" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setBookPhoto(event.target.files?.[0] || null)} required /><span className="form-help">JPG, PNG, or WebP. The photo is sent privately for staff review.</span></div>
        <button className="request-book-button borrow-submit" type="submit" disabled={!canRequest || !profileVerified || loading}>{loading ? 'Submitting request...' : 'Submit borrow request'}</button>
      </form>
    </details>
  </>
}
function LoansSection({ summary, loading, onNavigate }) { return <><SectionHeader title="My Borrowed Books" description="Track active loans and due dates from your account." icon={<BookOpenCheck size={24} />} /><div className="dashboard-panel section-list-panel">{loading ? <DashboardLoading /> : summary.active_loans.length ? summary.active_loans.map((loan) => <LoanItem key={loan.loan_id} loan={loan} />) : <EmptyState icon={<Library size={30} />} title="No borrowed books" description="You do not have any active loans." buttonText="Browse books" onClick={() => onNavigate('books')} />}</div></> }
function RequestsSection({ summary, onNavigate }) { return <><SectionHeader title="My Requests" description="Review the status of your borrowing requests." icon={<Clock3 size={24} />} /><div className="dashboard-panel section-list-panel">{summary.recent_requests?.length ? summary.recent_requests.map((request) => <RequestItem key={request.request_id} request={request} />) : <EmptyState icon={<Clock3 size={30} />} title="No borrow requests yet" description="Browse the catalog to request an available book." buttonText="Browse books" onClick={() => onNavigate('books')} />}</div></> }
function HistorySection({ summary }) { return <><SectionHeader title="Borrowing History" description="See the books you have previously returned." icon={<History size={24} />} /><div className="dashboard-panel section-list-panel">{summary.recent_returns?.length ? summary.recent_returns.map((loan) => <LoanItem key={loan.loan_id} loan={{ ...loan, due_date: loan.returned_at }} />) : <div className="section-placeholder"><History size={34} /><h3>No returned books yet</h3><p>Returned books will appear in your history.</p></div>}</div></> }
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
function ProfileSection({ user, borrowingPeriod }) { return <><SectionHeader title="My Profile" description="View your library account information." icon={<UserRound size={24} />} /><div className="dashboard-panel profile-panel"><AccountRow label="Full name" value={user.full_name || 'Library User'} /><AccountRow label="Account status" value={user.account_status || 'ACTIVE'} valueClass="active-status" /><AccountRow label="Role" value={user.role || 'STUDENT'} /><AccountRow label="School ID" value={user.school_id || 'Not available'} /><AccountRow label="Phone number" value={user.contact_number || 'Not available'} /><AccountRow label="Borrowing period" value={`${borrowingPeriod} days`} /></div></> }

function SummaryCard({ icon, label, value, color, onClick }) { return <button className="summary-card" onClick={onClick}><div className={`summary-icon ${color}`}>{icon}</div><div><span>{label}</span><strong>{value}</strong></div><ChevronRight size={18} className="summary-arrow" /></button> }
function AccountRow({ label, value, valueClass = '' }) { return <div className="account-row"><span>{label}</span><strong className={valueClass}>{value}</strong></div> }
function LoanItem({ loan }) { const dueDate = new Date(loan.due_date).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' }); return <div className="loan-item"><div className="loan-book-icon"><BookOpen size={21} /></div><div className="loan-information"><strong>{loan.book_title}</strong><span>Accession No. {loan.accession_number}</span></div><div className="loan-due-date"><span>Due date</span><strong>{dueDate}</strong></div></div> }
function RequestItem({ request }) { const requestedAt = new Date(request.requested_at).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' }); return <div className="loan-item"><div className="loan-book-icon"><Clock3 size={21} /></div><div className="loan-information"><strong>{request.book_title}</strong><span>Requested {requestedAt}</span></div><div className={`request-status ${request.status.toLowerCase()}`}>{request.status}</div></div> }
function EmptyState({ icon, title, description, buttonText, onClick }) { return <div className="dashboard-empty-state"><div className="empty-state-icon">{icon}</div><h4>{title}</h4><p>{description}</p><button onClick={onClick}>{buttonText}</button></div> }
function DashboardLoading() { return <div className="dashboard-loading">Loading your library information...</div> }

export default DashboardPage
