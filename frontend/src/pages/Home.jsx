import { Link } from 'react-router-dom';
import {
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Check,
  Video,
  FileText,
  Feather,
  Youtube,
  MessageSquare,
  Zap,
  Lock,
  RefreshCw,
  Sliders
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {
  return (
    <div className="app home-app">
      <Navbar />

      <main id="home-main">
        {/* HERO SECTION */}
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="eyebrow-dot" /> Multimodal Natural Language Refinement
            </div>
            <h1>Refine robotic AI text into <em>authentic human voice.</em></h1>
            <p>
              Engineered for text, documents, audio recordings, video interviews, and YouTube transcripts.
              Eliminates repetitive AI clichés while preserving 100% of candidate facts, dates, test scores, and tech stacks.
            </p>
            <div className="hero-actions">
              <Link className="button primary" to="/studio/text">
                Launch Writing Studio <ArrowRight size={17} />
              </Link>
              <Link className="button secondary" to="/studio/media">
                <Video size={17} /> Transcribe Media
              </Link>
            </div>
            <div className="hero-note">
              <ShieldCheck size={16} /> 100% Fact & Entity Guardrail · Local Audio/Video & YouTube Transcription
            </div>
          </div>

          <div className="hero-art" aria-hidden="true">
            <div className="art-orbit orbit-a" />
            <div className="art-orbit orbit-b" />
            <div className="art-card">
              <div className="art-card-top">
                <span>ROBOTIC INPUT</span>
                <span className="art-dash" />
              </div>
              <div className="fake-lines"><i /><i /><i className="short" /></div>
              <div className="art-spark"><Sparkles size={17} /></div>
              <div className="art-card-top after">
                <span>HUMANIZED OUTPUT</span>
                <span className="art-check"><Check size={12} /></span>
              </div>
              <div className="fake-lines warm"><i /><i /><i className="short" /></div>
            </div>
            <div className="art-flower flower-one">✳</div>
            <div className="art-flower flower-two">✿</div>
          </div>
        </section>

        {/* MODES SHOWCASE GRID */}
        <section className="tools-showcase-section">
          <div className="section-heading">
            <div>
              <div className="eyebrow">MULTIMODAL CHANNELS</div>
              <h2>Select your refinement studio mode.</h2>
            </div>
            <p className="showcase-subhead">
              Tailored workflows for recruiter feedback, offer letters, interviews, resumes, and video transcripts.
            </p>
          </div>

          <div className="tools-showcase-container">
            {/* FULL-WIDTH FEATURED ROW: Write or Paste Text */}
            <Link to="/studio/text" className="tool-card tool-card-featured">
              <div className="tool-featured-main">
                <div className="tool-icon-wrap tool-featured-icon">
                  <Feather size={26} />
                </div>
                <div className="tool-featured-content">
                  <span className="tool-featured-tag">Primary Studio · Direct Input</span>
                  <h3>Write or Paste Text</h3>
                  <p>
                    Type or paste recruiter messages, candidate evaluations, or cover letters with instant robotic score analysis, tone tuning, and live entity guardrails.
                  </p>
                </div>
              </div>
              <div className="tool-featured-action">
                <span className="tool-featured-cta">
                  Open Text Studio <ArrowRight size={16} />
                </span>
              </div>
            </Link>

            {/* REMAINING 4 MULTIMODAL CHANNELS */}
            <div className="tool-cards-subgrid">
              <Link to="/studio/chat-link" className="tool-card">
                <div className="tool-icon-wrap"><MessageSquare size={22} /></div>
                <h3>AI Chat Links</h3>
                <p>Paste a shared link from ChatGPT, Gemini, or Claude to automatically fetch and humanize the conversation.</p>
                <span className="tool-card-cta">Fetch AI Chat <ArrowRight size={14} /></span>
              </Link>

              <Link to="/studio/document" className="tool-card">
                <div className="tool-icon-wrap"><FileText size={22} /></div>
                <h3>Document Upload</h3>
                <p>Drag and drop PDF, DOCX, or TXT documents up to 5 MB for automatic structured text extraction and refinement.</p>
                <span className="tool-card-cta">Upload Document <ArrowRight size={14} /></span>
              </Link>

              <Link to="/studio/media" className="tool-card">
                <div className="tool-icon-wrap"><Video size={22} /></div>
                <h3>Audio & Video Media</h3>
                <p>Upload MP4, MOV, MP3, or WAV files up to 25 MB for AI speech transcription, tag cleanup, and voice humanization.</p>
                <span className="tool-card-cta">Transcribe Audio/Video <ArrowRight size={14} /></span>
              </Link>

              <Link to="/studio/youtube" className="tool-card">
                <div className="tool-icon-wrap"><Youtube size={22} /></div>
                <h3>YouTube Transcripts</h3>
                <p>Paste any YouTube link to fetch official or auto-generated captions, strip subtitle noise, and humanize.</p>
                <span className="tool-card-cta">Fetch YouTube <ArrowRight size={14} /></span>
              </Link>
            </div>
          </div>
        </section>

        {/* HOW IT WORKS PIPELINE */}
        <section id="how" className="how">
          <div className="section-heading">
            <div>
              <div className="eyebrow">A RIGOROUS TWO-PASS PIPELINE</div>
              <h2>Humanization with verifiable integrity.</h2>
            </div>
            <p className="how-intro">
              Designed for recruitment, evaluation, and interview transcripts, protecting candidate trust and data fidelity.
            </p>
          </div>
          <div className="steps">
            {[
              ['01', 'Multimodal Ingest & Pre-Analysis', 'Transcribes audio/video files, documents, or YouTube URLs, extracting technical stacks, names, scores, and identifying robotic clichés.'],
              ['02', 'Generation & Entity Guardrail', 'Rewrites using domain-specific recruitment tones. Verifies 100% entity preservation and triggers an automatic correction pass if needed.'],
              ['03', 'Independent Verification', 'An independent validation check computes meaning similarity and factual confidence, exposing changes via visual diff and inspection chips.']
            ].map(([n, t, d]) => (
              <article className="step" key={n}>
                <span className="step-number">{n}</span>
                <h3>{t}</h3>
                <p>{d}</p>
              </article>
            ))}
          </div>
        </section>

        {/* TRUST BANNER */}
        <section className="cta-banner">
          <div className="cta-banner-card">
            <h2>Ready to transform robotic drafts into natural human prose?</h2>
            <p>Experience the desktop dual-pane studio with real-time diffing and zero entity drift.</p>
            <div className="banner-actions">
              <Link to="/studio/text" className="button primary banner-btn">
                Open Studio Now <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
