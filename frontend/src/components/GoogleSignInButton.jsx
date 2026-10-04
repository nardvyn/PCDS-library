import { useEffect, useRef, useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { useNavigate } from 'react-router-dom'

import api from '../services/api'

function GoogleSignInButton({ onError, onLoading, onAuthenticated, text = 'signin_with' }) {
  const navigate = useNavigate()
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  const containerRef = useRef(null)
  const [buttonWidth, setButtonWidth] = useState(360)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return undefined

    const updateWidth = () => {
      setButtonWidth(Math.min(400, Math.floor(container.getBoundingClientRect().width)))
    }
    const observer = new ResizeObserver(updateWidth)
    observer.observe(container)
    updateWidth()

    return () => observer.disconnect()
  }, [])

  async function handleSuccess(response) {
    if (!response.credential) {
      onError?.('Google did not return a credential.')
      return
    }

    onLoading?.(true)
    onError?.('')

    try {
      const result = await api.post('/auth/google', { credential: response.credential })
      localStorage.setItem('access_token', result.data.access_token)
      localStorage.setItem('user', JSON.stringify(result.data.user))
      if (onAuthenticated) {
        onAuthenticated(result.data)
      } else {
        navigate(result.data.next_page || '/dashboard')
      }
    } catch (error) {
      const message = error.response?.data?.message || error.message || 'Unable to continue with Google.'
      const reason = error.response?.data?.reason
      onError?.(reason ? `${message} (${reason})` : message)
    } finally {
      onLoading?.(false)
    }
  }

  return (
    <div className="google-button-container" ref={containerRef}>
      {clientId ? <GoogleLogin
          type="standard"
          text={text}
          shape="rectangular"
          size="large"
          theme="outline"
          logo_alignment="left"
          width={String(buttonWidth)}
          onSuccess={handleSuccess}
          onError={() => onError?.('Google sign-in failed.')}
        /> : <span className="google-config-warning">Google setup required</span>}
    </div>
  )
}

export default GoogleSignInButton
