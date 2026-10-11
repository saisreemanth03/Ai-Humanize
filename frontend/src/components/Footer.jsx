import { Link } from 'react-router-dom';
import { Feather } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="footer">
      <Link className="brand footer-brand" to="/">
        <span className="brand-mark"><Feather size={18} /></span>
        <span>humanize<span className="brand-ai">ai</span></span>
      </Link>
      <p>Problem Track 02: AI Humanization & Natural Language Refinement</p>
      <div className="footer-meta">
        <span>FastAPI · React 18 · Whisper & Gemini · Entity Guardrails</span>
      </div>
      <small>Privacy note: Documents and media streams are processed in-memory and are not permanently stored.</small>
    </footer>
  );
}
