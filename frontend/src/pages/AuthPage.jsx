import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, Eye, EyeOff, LibraryBig, LoaderCircle } from 'lucide-react'

import api from '../services/api'
import GoogleSignInButton from '../components/GoogleSignInButton'
import './AuthPage.css'

function AuthPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const isCompletingProfile = location.pathname === '/complete-profile'
  const isForgotPassword = location.pathname === '/forgot-password'
  const isResetPassword = location.pathname === '/reset-password'
  const resetToken = new URLSearchParams(location.search).get('token') || ''
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loginData, setLoginData] = useState({ email: '', password: '' })
  const [forgotEmail, setForgotEmail] = useState('')
  const [resetData, setResetData] = useState({ password: '', confirmPassword: '' })
  const [profileData, setProfileData] = useState({ user_type: 'STUDENT', school_id_number: '', course: '', year_level: '', section: '', department: '', contact_number: '', address: '', password: '' })
  const [schoolIdFile, setSchoolIdFile] = useState(null)

  function updateLogin(event) {
    const { name, value } = event.target
    setLoginData((current) => ({ ...current, [name]: value }))
  }

  function updateProfile(event) {
    const { name, value } = event.target
    setProfileData((current) => ({ ...current, [name]: value }))
  }

  function updateResetData(event) {
    const { name, value } = event.target
    setResetData((current) => ({ ...current, [name]: value }))
  }

  function handleGoogleAuthenticated(data) {
    if (data.profile_required) {
      navigate('/complete-profile')
      return
    }
    navigate('/dashboard')
  }

  function handleGoogleError(text) {
    setMessage(text ? { type: 'error', text } : null)
  }

  async function handleProfileSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setMessage(null)
    try {
      const formData = new FormData()
      Object.entries(profileData).forEach(([key, value]) => formData.append(key, value))
      if (schoolIdFile) formData.append('school_id', schoolIdFile)
      const { data } = await api.put('/auth/profile', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      if (data.user) localStorage.setItem('user', JSON.stringify(data.user))
      setMessage({ type: 'success', text: data.message })
      setTimeout(() => navigate('/dashboard', { replace: true }), 700)
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.message || 'Unable to save your profile.' })
    } finally {
      setLoading(false)
    }
  }

  async function handleLogin(event) {
    event.preventDefault()
    setLoading(true)
    setMessage(null)

    try {
      const { data } = await api.post('/auth/login', loginData)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      navigate(data.next_page || (data.user.role === 'LIBRARIAN' ? '/librarian' : data.user.role === 'ADMIN' ? '/admin' : '/dashboard'))
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.message || 'Unable to connect to the server.' })
    } finally {
      setLoading(false)
    }
  }

  async function handleForgotPassword(event) {
    event.preventDefault()
    setLoading(true)
    setMessage(null)
    try {
      const { data } = await api.post('/auth/forgot-password', { email: forgotEmail })
      setMessage({ type: 'success', text: data.message })
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.message || 'Unable to request a password reset right now.' })
    } finally {
      setLoading(false)
    }
  }

  async function handleResetPassword(event) {
    event.preventDefault()
    if (!resetToken) {
      setMessage({ type: 'error', text: 'This password reset link is missing its token. Request a new link.' })
      return
    }
    if (resetData.password !== resetData.confirmPassword) {
      setMessage({ type: 'error', text: 'The passwords do not match.' })
      return
    }

    setLoading(true)
    setMessage(null)
    try {
      const { data } = await api.post('/auth/reset-password', { token: resetToken, password: resetData.password })
      setMessage({ type: 'success', text: data.message })
      setResetData({ password: '', confirmPassword: '' })
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.message || 'Unable to reset your password right now.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-shell">
        <section className="auth-intro">
          <div className="brand-mark"><BookOpen size={22} strokeWidth={2.2} /></div>
          <div className="eyebrow"><LibraryBig size={15} /> PCDS Library</div>
          <div className="intro-copy">
            <p className="kicker">A quieter way to learn</p>
            <h1>Make room for your next good read.</h1>
            <p>Search the collection, manage borrowing requests, and keep your library life in one calm place.</p>
          </div>
          <div className="intro-footer"><span className="footer-dot" /> Polytechnic College of Davao del Sur</div>
        </section>

        <section className="auth-panel" aria-labelledby="auth-heading">
          {message && <div className={`message ${message.type}`} role="status">{message.text}</div>}

          {isCompletingProfile ? (
            <ProfileSetupForm profileData={profileData} updateProfile={updateProfile} handleSubmit={handleProfileSubmit} loading={loading} onFileChange={setSchoolIdFile} showPassword={showPassword} setShowPassword={setShowPassword} />
          ) : isForgotPassword ? (
            <form onSubmit={handleForgotPassword}>
              <p className="form-kicker">Account recovery</p>
              <h2 id="auth-heading">Reset your password</h2>
              <p className="form-description">Enter the email connected to your account. If it is registered, we will send a reset link.</p>
              <div className="field"><label htmlFor="forgot-email">Email address</label><input id="forgot-email" type="email" value={forgotEmail} onChange={(event) => setForgotEmail(event.target.value)} placeholder="Enter your email address" autoComplete="email" required /></div>
              <button className="submit-button" type="submit" disabled={loading}>{loading && <LoaderCircle className="spinner" size={18} />}{loading ? 'Sending link...' : 'Send reset link'}</button>
              <button className="text-button auth-back-button" type="button" onClick={() => { setMessage(null); navigate('/') }}>Back to sign in</button>
            </form>
          ) : isResetPassword ? (
            <form onSubmit={handleResetPassword}>
              <p className="form-kicker">Account recovery</p>
              <h2 id="auth-heading">Choose a new password</h2>
              <p className="form-description">Your password must contain at least 8 characters.</p>
              {message?.type === 'success' ? (
                <button className="submit-button" type="button" onClick={() => navigate('/')}>Back to sign in</button>
              ) : resetToken ? (
                <>
                  <div className="field"><label htmlFor="reset-password">New password</label><div className="password-field"><input id="reset-password" name="password" type={showPassword ? 'text' : 'password'} value={resetData.password} onChange={updateResetData} autoComplete="new-password" minLength="8" required /><button className="icon-button" type="button" onClick={() => setShowPassword((current) => !current)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={19} /> : <Eye size={19} />}</button></div></div>
                  <div className="field"><label htmlFor="reset-confirm-password">Confirm new password</label><div className="password-field"><input id="reset-confirm-password" name="confirmPassword" type={showConfirmPassword ? 'text' : 'password'} value={resetData.confirmPassword} onChange={updateResetData} autoComplete="new-password" minLength="8" required /><button className="icon-button" type="button" onClick={() => setShowConfirmPassword((current) => !current)} aria-label={showConfirmPassword ? 'Hide password confirmation' : 'Show password confirmation'}>{showConfirmPassword ? <EyeOff size={19} /> : <Eye size={19} />}</button></div></div>
                  <button className="submit-button" type="submit" disabled={loading}>{loading && <LoaderCircle className="spinner" size={18} />}{loading ? 'Saving password...' : 'Reset password'}</button>
                </>
              ) : (
                <>
                  <p className="form-description">This reset link is incomplete. Request a new one to continue.</p>
                  <button className="submit-button" type="button" onClick={() => navigate('/forgot-password')}>Request a new link</button>
                </>
              )}
            </form>
          ) : (
            <form onSubmit={handleLogin}>
              <p className="form-kicker">Welcome back</p>
              <h2 id="auth-heading">Sign in to your account</h2>
              <p className="form-description">Use your email address to continue to the library.</p>
              <div className="field"><label htmlFor="login-email">Email address</label><input id="login-email" name="email" type="email" value={loginData.email} onChange={updateLogin} placeholder="Enter your email address" autoComplete="email" required /></div>
              <div className="field"><label htmlFor="login-password">Password</label><div className="password-field"><input id="login-password" name="password" type={showPassword ? 'text' : 'password'} value={loginData.password} onChange={updateLogin} placeholder="Enter your password" autoComplete="current-password" required /><button className="icon-button" type="button" onClick={() => setShowPassword((current) => !current)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={19} /> : <Eye size={19} />}</button></div></div>
              <div className="form-options"><label className="check-label"><input type="checkbox" /> Remember me</label><button type="button" className="text-button" onClick={() => { setForgotEmail(loginData.email); setMessage(null); navigate('/forgot-password') }}>Forgot password?</button></div>
              <button className="submit-button" type="submit" disabled={loading}>{loading && <LoaderCircle className="spinner" size={18} />}{loading ? 'Signing in...' : 'Sign in'}</button>
              <GoogleSignInButton onAuthenticated={handleGoogleAuthenticated} onError={handleGoogleError} onLoading={setLoading} text="signin_with" />
            </form>
          )}
          <p className="secure-note"><span className="lock-mark">✦</span> Your account is protected by secure sign-in.</p>
        </section>
      </div>
    </main>
  )
}

export default AuthPage

function ProfileSetupForm({ profileData, updateProfile, handleSubmit, loading, onFileChange, showPassword, setShowPassword }) {
  return <form onSubmit={handleSubmit}>
    <p className="form-kicker">One more step</p>
    <h2 id="auth-heading">Complete your profile</h2>
    <p className="form-description">Your profile will be reviewed before you can submit borrow requests.</p>
    <div className="field"><label htmlFor="user-type">Account type</label><select id="user-type" name="user_type" value={profileData.user_type} onChange={updateProfile}><option value="STUDENT">Student</option><option value="TEACHER">Teacher</option></select></div>
    <div className="field"><label htmlFor="school-id-number">School ID / Employee ID</label><input id="school-id-number" name="school_id_number" value={profileData.school_id_number} onChange={updateProfile} required /></div>
    {profileData.user_type === 'STUDENT' ? <div className="field-grid"><div className="field"><label htmlFor="course">Course</label><input id="course" name="course" value={profileData.course} onChange={updateProfile} required /></div><div className="field"><label htmlFor="year-level">Year level</label><input id="year-level" name="year_level" value={profileData.year_level} onChange={updateProfile} required /></div></div> : <div className="field"><label htmlFor="department">Department</label><input id="department" name="department" value={profileData.department} onChange={updateProfile} required /></div>}
    {profileData.user_type === 'STUDENT' && <div className="field"><label htmlFor="section">Section</label><input id="section" name="section" value={profileData.section} onChange={updateProfile} required /></div>}
    <div className="field"><label htmlFor="profile-contact">Phone number</label><input id="profile-contact" name="contact_number" type="tel" value={profileData.contact_number} onChange={updateProfile} placeholder="e.g. 09XX XXX XXXX" autoComplete="tel" required /></div>
    <div className="field"><label htmlFor="profile-password">Create password</label><div className="password-field"><input id="profile-password" name="password" type={showPassword ? 'text' : 'password'} value={profileData.password} onChange={updateProfile} placeholder="At least 8 characters" autoComplete="new-password" minLength="8" required /><button className="icon-button" type="button" onClick={() => setShowPassword((current) => !current)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={19} /> : <Eye size={19} />}</button></div><p className="password-hint">Use this password when signing in with your email.</p></div>
    <div className="field"><label htmlFor="profile-address">Address <span>Optional</span></label><input id="profile-address" name="address" value={profileData.address} onChange={updateProfile} /></div>
    <div className="field"><label htmlFor="school-id-upload">Front picture of School ID</label><input id="school-id-upload" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => onFileChange(event.target.files?.[0] || null)} required /></div>
    <button className="submit-button" type="submit" disabled={loading}>{loading && <LoaderCircle className="spinner" size={18} />}{loading ? 'Saving profile...' : 'Submit for verification'}</button>
  </form>
}
