import { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Feather, ArrowRight, Menu, X } from 'lucide-react';

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  const closeMobile = () => setMobileOpen(false);

  return (
    <header className="nav">
      <Link className="brand" to="/" onClick={closeMobile}>
        <span className="brand-mark"><Feather size={20} /></span>
        <span>humanize<span className="brand-ai">ai</span></span>
      </Link>

      <button
        className="mobile-toggle"
        aria-label="Toggle navigation"
        aria-expanded={mobileOpen}
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        {mobileOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      {/* Desktop & Mobile Navigation Links */}
      <nav className={`nav-links ${mobileOpen ? 'open' : ''}`}>
        <NavLink
          to="/"
          end
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={closeMobile}
        >
          Home
        </NavLink>
        <NavLink
          to="/studio/text"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={closeMobile}
        >
          Text Studio
        </NavLink>
        <NavLink
          to="/studio/document"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={closeMobile}
        >
          Document
        </NavLink>
        <NavLink
          to="/studio/media"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={closeMobile}
        >
          Audio / Video
        </NavLink>
        <NavLink
          to="/studio/youtube"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          onClick={closeMobile}
        >
          YouTube
        </NavLink>
        
        {mobileOpen && (
          <Link className="mobile-cta-btn" to="/studio/text" onClick={closeMobile}>
            Launch Studio <ArrowRight size={16} />
          </Link>
        )}
      </nav>

      <Link className="nav-cta" to="/studio/text">
        Open Studio <ArrowRight size={16} />
      </Link>
    </header>
  );
}
