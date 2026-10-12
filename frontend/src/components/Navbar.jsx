import { useState, useEffect } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Feather, ArrowRight, Menu, X } from 'lucide-react';

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  const closeMobile = () => setMobileOpen(false);

  // Close overlay on Escape key press
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && mobileOpen) {
        closeMobile();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileOpen]);

  // Prevent background scroll when mobile navigation overlay is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileOpen]);

  return (
    <header className="nav">
      <Link className="brand" to="/" onClick={closeMobile}>
        <span className="brand-mark"><Feather size={20} /></span>
        <span>humanize<span className="brand-ai">ai</span></span>
      </Link>

      {/* Dimmed Backdrop for Mobile Navigation Overlay */}
      {mobileOpen && (
        <div
          className="mobile-backdrop"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      {/* Desktop & Mobile Navigation Links Overlay */}
      <nav
        className={`nav-links ${mobileOpen ? 'open' : ''}`}
        aria-label="Main navigation"
        role={mobileOpen ? 'dialog' : undefined}
        aria-modal={mobileOpen ? 'true' : undefined}
      >
        {/* Mobile Overlay Header with Close (X) Icon Button */}
        {mobileOpen && (
          <div className="mobile-overlay-header">
            <div className="mobile-overlay-brand">
              <span className="brand-mark"><Feather size={18} /></span>
              <span>humanize<span className="brand-ai">ai</span></span>
            </div>
            <button
              type="button"
              className="mobile-overlay-close-btn"
              aria-label="Close navigation"
              onClick={closeMobile}
            >
              <X size={22} />
            </button>
          </div>
        )}

        {/* Center-aligned navigation links with >=44x44px touch targets */}
        <div className="nav-links-list">
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
        </div>

        {mobileOpen && (
          <div className="mobile-cta-wrap">
            <Link className="mobile-cta-btn" to="/studio/text" onClick={closeMobile}>
              Launch Studio <ArrowRight size={16} />
            </Link>
          </div>
        )}
      </nav>

      {/* Desktop CTA Button */}
      <Link className="nav-cta" to="/studio/text">
        Open Studio <ArrowRight size={16} />
      </Link>

      {/* Mobile Hamburger Toggle Button (Positioned at far right) */}
      <button
        type="button"
        className="mobile-toggle"
        aria-label="Open navigation menu"
        aria-expanded={mobileOpen}
        onClick={() => setMobileOpen(true)}
      >
        <Menu size={22} />
      </button>
    </header>
  );
}
