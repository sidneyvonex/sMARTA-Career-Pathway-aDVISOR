import { Link } from 'react-router-dom'
import '../styles/auth.css'

interface Props {
  heading: string
  subheading?: string
  children: React.ReactNode
  footer?: React.ReactNode
  /** Brand panel background photo (left panel on desktop). */
  brandImage?: string
  brandImageAlt?: string
  /** Short line above the brand quote, e.g. "Free for all students". Optional secondary meta chip. */
  brandEyebrow?: string
  /** Main brand-panel quote, e.g. "Welcome back to". */
  brandQuote?: string
  /** Script-font accent that follows brandQuote, e.g. "your pathway." */
  brandQuoteAccent?: string
}

export default function AuthLayout({
  heading,
  subheading,
  children,
  footer,
  brandImage = '/img/chinga-boys.jpg',
  brandImageAlt = 'Students at a Smarta Shauri partner school',
  brandEyebrow = 'Free for all students',
  brandQuote = 'Discover your',
  brandQuoteAccent = 'pathway.',
}: Props) {
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <img src={brandImage} alt={brandImageAlt} loading="eager" />
        <div className="auth-brand__content">
          <Link to="/" className="auth-brand__logo">
            <img src="/logo.png" alt="Smarta Shauri logo" />
            Smarta Shauri
          </Link>
        </div>
        <p className="auth-brand__quote">
          {brandQuote}
          <span className="script">{brandQuoteAccent}</span>
        </p>
        <div className="auth-brand__meta">
          <span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path d="M9 12l2 2 4-4M12 3l8 4v5c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V7l8-4z" />
            </svg>
            {brandEyebrow}
          </span>
          <span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 7v5l3 3" />
            </svg>
            Takes 2 minutes
          </span>
        </div>
      </div>

      <div className="auth-panel">
        <div className="auth-panel__inner">
          <Link to="/" className="back-link">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
              <path d="M15 6l-6 6 6 6" />
            </svg>
            Back to home
          </Link>

          <h1 className="auth-heading">{heading}</h1>
          {subheading && <p className="auth-subheading">{subheading}</p>}

          {children}

          {footer && <div className="auth-footer">{footer}</div>}
        </div>
      </div>
    </div>
  )
}
