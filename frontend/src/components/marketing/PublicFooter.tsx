import { Link } from 'react-router-dom'
import '../../styles/marketing.css'

export default function PublicFooter() {
  return (
    <footer className="mk-footer">
      <p className="mk-footer__tagline">
        <span>Discover.</span> <span>Plan.</span> <span>Choose.</span> <span>Succeed.</span>
      </p>

      <div className="mk-footer__meta">
        <span>Smarta Shauri &middot; Est. 2026 &middot; Kenya</span>
        <span>One pathway at a time</span>
      </div>

      <div className="mk-footer__cols">
        <div>
          <p className="mk-footer__brand">
            <img src="/logo.png" alt="Smarta Shauri logo" />
            Smarta Shauri
          </p>
          <p className="mk-footer__brand-desc">
            Built for learners in this five-county pilot who want clearer evidence and a
            better-supported pathway conversation.
          </p>
        </div>

        <div className="mk-footer__col">
          <p className="mk-footer__col-heading">Product</p>
          <Link to="/about">About</Link>
          <Link to="/pathways">Pathways</Link>
          <Link to="/how-it-works">How it works</Link>
          <a href="/#community">Community</a>
          <Link to="/for-schools">For Schools</Link>
        </div>

        <div className="mk-footer__col">
          <p className="mk-footer__col-heading">Account</p>
          <Link to="/login">Login</Link>
          <Link to="/register">Register</Link>
        </div>
      </div>

      <div className="mk-footer__pilot-note">
        <p>
          Smarta Shauri is an advisory five-county pilot for Kiambu, Murang&apos;a, Nyeri,
          Kirinyaga and Nyandarua. It does not predict success, determine placement or submit
          official Senior School choices.
        </p>
        <nav aria-label="Official guidance sources">
          <a
            href="https://selection-placement.kemis.go.ke/uploads/catalogue.pdf"
            target="_blank"
            rel="noreferrer"
          >
            Current pilot catalogue
          </a>
          <a
            href="https://placements.education.go.ke"
            target="_blank"
            rel="noreferrer"
          >
            Official placement service
          </a>
          <a
            href="https://kicd.ac.ke/curriculum-reform/"
            target="_blank"
            rel="noreferrer"
          >
            KICD curriculum reform
          </a>
        </nav>
      </div>

      <div className="mk-footer__credits">
        <p>Photography credits (Wikimedia Commons)</p>
        <p>
          &bull; &quot;Students at Chinga Boys High School&quot;, Stephen Wanjau,{' '}
          <a href="https://commons.wikimedia.org/wiki/File:Students_at_Chinga_Boys_High_School.jpg">
            CC BY-SA 3.0
          </a>
        </p>
        <p>
          &bull; &quot;Biology class&quot; (Alliance High School), Eric Gitonga,{' '}
          <a href="https://commons.wikimedia.org/wiki/File:Biology_class.jpg">CC BY-SA 4.0</a>
        </p>
        <p>
          &bull; &quot;AHS Scouts&quot; (Alliance High School), Eric Gitonga,{' '}
          <a href="https://commons.wikimedia.org/wiki/File:AHS_Scouts.jpg">CC BY-SA 4.0</a>
        </p>
        <p>&bull; &quot;Alliance Girls High School dininghall&quot;, African Girls, Public Domain</p>
        <p>
          &bull; &quot;Mang&apos;u students&quot;, Andygroove,{' '}
          <a href="https://commons.wikimedia.org/wiki/File:Mang%27u_students.jpeg">CC BY-SA 3.0</a>
        </p>
        <p>
          &bull; &quot;View of the school compound&quot; (Gachoire Girls High School), SuSanA Secretariat,{' '}
          <a href="https://commons.wikimedia.org/wiki/File:View_of_the_school_compound_(5363415784).jpg">
            CC BY 2.0
          </a>
        </p>
        <p>
          &bull; &quot;L1030090&quot; (Kiambu High School academic complex), Roger Ndichu,{' '}
          <a href="https://commons.wikimedia.org/wiki/File:L1030090.jpg">CC BY-SA 4.0</a>
        </p>
        <p>
          &bull; &quot;Kagumo High School&quot;, Rupumped,{' '}
          <a href="https://commons.wikimedia.org/wiki/File:Kagumo_High_School.jpg">CC BY-SA 4.0</a>
        </p>
        <p>
          &bull; &quot;Pupils at Mahiga Girls School&quot;, SuSanA Secretariat,{' '}
          <a href="https://commons.wikimedia.org/wiki/File:Pupils_at_Mahiga_Girls_School_(3504556398).jpg">
            CC BY 2.0
          </a>
        </p>
      </div>
    </footer>
  )
}
