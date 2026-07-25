import { Link } from 'react-router-dom'

export default function LandingFooter() {
  return (
    <footer className="landing-footer">
      <p className="landing-footer__wordmark">Smarta Shauri</p>
      <nav className="landing-footer__links" aria-label="Footer">
        <a href="#explore-your-pathway">Pathways</a>
        <Link to="/login">Login</Link>
        <Link to="/register">Register</Link>
      </nav>
    </footer>
  )
}
