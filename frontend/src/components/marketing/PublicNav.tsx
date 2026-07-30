import { useState } from 'react'
import { Link } from 'react-router-dom'
import '../../styles/marketing.css'

export default function PublicNav() {
  const [isOpen, setIsOpen] = useState(false)

  const closeMenu = () => setIsOpen(false)

  return (
    <>
      <div className="mk-notice-bar">
        <div className="mk-notice-bar__wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 8v5M12 16h.01" />
          </svg>
          <span>
            Smarta Shauri helps you decide. It doesn&apos;t submit your official Senior School
            choices. That&apos;s done at{' '}
            <a href="https://placements.education.go.ke" target="_blank" rel="noopener noreferrer">
              placements.education.go.ke
            </a>
            .
          </span>
        </div>
      </div>

      <header className="mk-nav">
        <div className="mk-nav__inner">
          <Link className="mk-nav__logo" to="/">
            <span className="mk-nav__logo-mark">
              <img src="/logo.png" alt="Smarta Shauri logo" />
            </span>
            Smarta Shauri
          </Link>

          <nav
            className={`mk-nav__center${isOpen ? ' is-open' : ''}`}
            id="nav-center"
          >
            <Link to="/about" onClick={closeMenu}>About</Link>
            <Link to="/pathways" onClick={closeMenu}>Pathways</Link>
            <Link to="/how-it-works" onClick={closeMenu}>How it works</Link>
            <a href="/#community" onClick={closeMenu}>Community</a>
            <div className="mk-nav__mobile-ctas">
              <Link className="mk-btn mk-btn-outline" to="/login" onClick={closeMenu}>Login</Link>
              <Link className="mk-btn mk-btn-dark" to="/register" onClick={closeMenu}>Get Started</Link>
            </div>
          </nav>

          <div className="mk-nav__right">
            <Link className="mk-btn mk-btn-outline" to="/login">Login</Link>
            <Link className="mk-btn mk-btn-dark" to="/register">Get Started</Link>
          </div>

          <button
            className="mk-nav__toggle"
            aria-label="Toggle menu"
            aria-expanded={isOpen}
            aria-controls="nav-center"
            onClick={() => setIsOpen((open) => !open)}
          >
            <svg className="mk-icon-hamburger" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} aria-hidden="true">
              <path d="M3 6h18M3 12h18M3 18h18" />
            </svg>
            <svg className="mk-icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>
      </header>
    </>
  )
}
