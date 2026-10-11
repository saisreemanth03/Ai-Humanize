import { NavLink, Outlet } from 'react-router-dom';
import { Feather, FileUp, Video, Youtube, ShieldCheck } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function StudioLayout() {
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

          {/* Persistent Studio Sub-Navigation Tabs */}
          <nav className="workspace-tabs studio-mode-tabs" aria-label="Studio tools">
            <NavLink
              to="/studio/text"
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
              <Feather size={16} /> Write or paste text
            </NavLink>
            <NavLink
              to="/studio/document"
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
              <FileUp size={16} /> Upload document
            </NavLink>
            <NavLink
              to="/studio/media"
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
              <Video size={16} /> Upload Audio / Video
            </NavLink>
            <NavLink
              to="/studio/youtube"
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
              <Youtube size={16} /> YouTube Link
            </NavLink>
          </nav>

          {/* Child Tool Route */}
          <Outlet />
        </section>
      </main>

      <Footer />
    </div>
  );
}
