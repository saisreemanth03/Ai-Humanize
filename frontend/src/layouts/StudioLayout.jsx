import { useLocation, useNavigate, NavLink, Outlet } from 'react-router-dom';
import { Feather, FileUp, Video, Youtube, MessageSquare, ShieldCheck, ChevronDown } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const STUDIO_MODES = [
  {
    path: '/studio/text',
    label: 'Write or paste text',
    shortLabel: 'Text',
    icon: Feather,
  },
  {
    path: '/studio/chat-link',
    label: 'AI Chat Links',
    shortLabel: 'AI Chat',
    icon: MessageSquare,
  },
  {
    path: '/studio/document',
    label: 'Upload document',
    shortLabel: 'Document',
    icon: FileUp,
  },
  {
    path: '/studio/media',
    label: 'Upload Audio / Video',
    shortLabel: 'Media',
    icon: Video,
  },
  {
    path: '/studio/youtube',
    label: 'YouTube Link',
    shortLabel: 'YouTube',
    icon: Youtube,
  },
];


export default function StudioLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  // Determine current active mode
  const currentMode =
    STUDIO_MODES.find((m) => location.pathname === m.path) || STUDIO_MODES[0];
  const CurrentIcon = currentMode.icon;

  return (
    <div className="app studio-app">
      <Navbar />

      <main className="studio-main">
        <section className="workspace-section studio-page-section">
          {/* Studio Header (Clean, focused, no marketing hero) */}
          <div className="section-heading studio-heading">
            <div>
              <div className="eyebrow">MULTIMODAL WRITING STUDIO</div>
              <h2>Humanize, audit, and safeguard your prose.</h2>
            </div>
            <span className="secure-label">
              <ShieldCheck size={15} /> Entity-Preserving Verification Active
            </span>
          </div>

          {/* Desktop Navigation Tabs (>= 768px Viewports) */}
          <nav className="workspace-tabs studio-mode-tabs desktop-only-tabs" aria-label="Desktop Studio tools">
            {STUDIO_MODES.map((mode) => {
              const Icon = mode.icon;
              return (
                <NavLink
                  key={mode.path}
                  to={mode.path}
                  className={({ isActive }) => (isActive ? 'active' : '')}
                >
                  <Icon size={16} /> {mode.label}
                </NavLink>
              );
            })}
          </nav>

          {/* Mobile Navigation Studio Switcher (< 768px Viewports): Compact Segmented Control with SVG Icons */}
          <div className="studio-mobile-nav-wrap mobile-only-nav">
            <nav className="studio-segmented-control" aria-label="Mobile Studio Navigation">
              {STUDIO_MODES.map((mode) => {
                const Icon = mode.icon;
                const isActive = location.pathname === mode.path;
                return (
                  <NavLink
                    key={mode.path}
                    to={mode.path}
                    className={`segmented-pill ${isActive ? 'active' : ''}`}
                    aria-label={mode.label}
                    title={mode.label}
                  >
                    <Icon size={17} className="segmented-icon" />
                    <span className="segmented-label">{mode.shortLabel}</span>
                  </NavLink>
                );
              })}
            </nav>

            {/* Mobile Dropdown Selector Alternative for accessibility */}
            <div className="studio-dropdown-selector-box">
              <span className="dropdown-icon-lead">
                <CurrentIcon size={16} />
              </span>
              <select
                id="mobile-studio-selector"
                value={currentMode.path}
                onChange={(e) => navigate(e.target.value)}
                className="studio-dropdown-select"
                aria-label="Select Studio Mode"
              >
                {STUDIO_MODES.map((mode) => (
                  <option key={mode.path} value={mode.path}>
                    Mode: {mode.label}
                  </option>
                ))}
              </select>
              <ChevronDown size={15} className="dropdown-chevron-tail" />
            </div>
          </div>

          {/* Child Tool Route */}
          <Outlet />
        </section>
      </main>

      <Footer />
    </div>
  );
}
