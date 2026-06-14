import { Link } from 'react-router-dom'
import '../styles/auth.css'

interface Props {
  heading: string
  subheading?: string
  children: React.ReactNode
  footer?: React.ReactNode
}

export default function AuthLayout({ heading, subheading, children, footer }: Props) {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <Link to="/" className="auth-logo">
          <span className="auth-logo-mark">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z" />
            </svg>
          </span>
          <span className="auth-logo-text">CBC Guidance</span>
        </Link>

        <h1 className="auth-heading">{heading}</h1>
        {subheading && <p className="auth-subheading">{subheading}</p>}

        {children}
      </div>

      {footer && <div className="auth-footer">{footer}</div>}
    </div>
  )
}
