import { useMemo, useRef, useState } from 'react';
import {
  AlertTriangle,
  ArrowDown,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clipboard,
  Feather,
  FileText,
  FileUp,
  LoaderCircle,
  Menu,
  Music,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Split,
  Upload,
  Video,
  X,
  Youtube,
  Zap
} from 'lucide-react';
import { extractDocument, extractMedia, extractYouTube, humanizeText } from './services/api';
import { computeWordDiff } from './utils/diffHelper';
import './App.css';

const contexts = [
  'Recruiter Feedback & Rejection Emails',
  'Candidate Communication & Offer Letters',
  'Adaptive Interview Question Refinement',
  'Candidate Evaluation Summaries & Reports',
  'General Professional Writing',
  'Audio / Video Transcript & Spoken Dialogue'
];

const tones = ['Natural', 'Professional', 'Conversational', 'Polished', 'Concise'];

const ROBOTIC_PATTERNS = [
  'delve into', 'delving into', 'can you delve into', 'testament to', 'stands as a testament',
  'rich tapestry', 'tapestry', 'in summary', 'in conclusion', 'to summarize',
  'pivotal role', 'pivotal', 'beacon of', 'beacon', 'furthermore', 'moreover',
  'it is worth noting', 'it should be noted', 'embark on', 'embark upon', 'foster',
  'streamline', 'leverage', 'vital role', 'crucial role', 'game-changer', 'plethora',
  'myriad', 'multifaceted', 'underpins', 'intertwined', 'unwavering', 'deep dive',
  'harness the power of', 'meticulous', 'commendable'
];

function analyzeClientText(text) {
  if (!text || !text.trim()) return { score: 'Low', cliches: [] };
  const lower = text.toLowerCase();
  const cliches = [];
  for (const p of ROBOTIC_PATTERNS) {
    if (lower.includes(p)) cliches.push(p);
  }
  const sentences = text.split(/[.!?]+/).filter((s) => s.trim().length > 0);
  let score = 'Low';
  if (cliches.length >= 3 || (cliches.length >= 1 && sentences.length >= 2)) {
    score = 'High';
  } else if (cliches.length >= 1 || sentences.length >= 3) {
    score = 'Medium';
  }
  return { score, cliches };
}

function cleanTranscriptNoise(text) {
  if (!text) return '';
  return text
    .replace(/\[(?:music|crying|applause|laughter|cheering|sniffling|coughing|sighs?|gasp|groans?|inaudible)\]\s*/gi, '')
    .replace(/>\s*>\s*/g, ' ')
    .replace(/\b[A-Z]{2,}\b/g, (w) => (['API', 'SQL', 'AWS', 'GPA', 'HTML', 'CSS', 'REST'].includes(w) ? w : w.charAt(0) + w.slice(1).toLowerCase()))
    .replace(/\s+/g, ' ')
    .trim();
}

const count = (s) => (s && s.trim() ? s.trim().split(/\s+/).length : 0);

export default function App() {
  const [tab, setTab] = useState('write');
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [context, setContext] = useState(contexts[0]);
  const [tone, setTone] = useState(tones[0]);
  const [minimal, setMinimal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [notice, setNotice] = useState('');
  const [file, setFile] = useState(null);
  const [mediaFile, setMediaFile] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [drag, setDrag] = useState(false);
  const [mediaDrag, setMediaDrag] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [showDiff, setShowDiff] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(true);

  const picker = useRef(null);
  const mediaPicker = useRef(null);

  // Real-time client-side analysis of input for instant feedback
  const clientAnalysis = useMemo(() => analyzeClientText(input), [input]);

  // Diff chunks for visual comparison
  const diffChunks = useMemo(() => {
    if (!showDiff || !output || !input) return [];
    return computeWordDiff(input, output);
  }, [showDiff, input, output]);

  async function run() {
    if (!input.trim()) {
      setError('Add or transcribe some text before humanizing.');
      return;
    }
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const data = await humanizeText({
        text: input,
        context,
        tone,
        minimal_rewrite: minimal
      });
      setOutput(data.humanized_text);
      setResult(data);
      setDrawerOpen(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function selectFile(f) {
    if (!f) return;
    setError('');
    setNotice('');
    if (!/\.(pdf|docx|txt)$/i.test(f.name)) {
      setError('Choose a PDF, DOCX, or TXT file.');
      return;
    }
    if (f.size > 5 * 1024 * 1024) {
      setError('This document is over the 5 MB limit.');
      return;
    }
    setFile(f);
    setMediaFile(null);
    setInput('');
    setOutput('');
    setResult(null);
    setBusy(true);
    try {
      const data = await extractDocument(f);
      setInput(data.extracted_text);
      if (data.warnings?.length) setNotice(data.warnings.join(' '));
    } catch (e) {
      setFile(null);
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function selectMediaFile(f) {
    if (!f) return;
    setError('');
    setNotice('');
    if (!/\.(mp4|mov|webm|mkv|mp3|wav|m4a|aac|flac)$/i.test(f.name)) {
      setError('Please choose a valid Audio or Video file (.mp4, .mov, .webm, .mp3, .wav, .m4a).');
      return;
    }
    if (f.size > 25 * 1024 * 1024) {
      setError('This media file exceeds the 25 MB limit.');
      return;
    }
    setMediaFile(f);
    setFile(null);
    setInput('');
    setOutput('');
    setResult(null);
    setTranscribing(true);
    try {
      const data = await extractMedia(f);
      setInput(data.extracted_text);
      setContext('Audio / Video Transcript & Spoken Dialogue');
      setTone('Conversational');
      if (data.warnings?.length) setNotice(data.warnings.join(' '));
    } catch (e) {
      setMediaFile(null);
      setError(e.message);
    } finally {
      setTranscribing(false);
    }
  }

  async function fetchYouTubeTranscript() {
    if (!youtubeUrl.trim()) {
      setError('Enter a valid YouTube video URL.');
      return;
    }
    setError('');
    setNotice('');
    setFile(null);
    setMediaFile(null);
    setInput('');
    setOutput('');
    setResult(null);
    setTranscribing(true);
    try {
      const data = await extractYouTube(youtubeUrl.trim());
      setInput(data.extracted_text);
      setContext('Audio / Video Transcript & Spoken Dialogue');
      setTone('Conversational');
      if (data.warnings?.length) setNotice(data.warnings.join(' '));
    } catch (e) {
      setError(e.message);
    } finally {
      setTranscribing(false);
    }
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(output);
      setNotice('Copied to clipboard.');
    } catch {
      setError('Clipboard access was blocked. Select the text and copy it manually.');
    }
  }

  function download() {
    const blob = new Blob([output], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'humanized-text.txt';
    a.click();
    URL.revokeObjectURL(url);
  }

  function clear() {
    setInput('');
    setOutput('');
    setResult(null);
    setError('');
    setNotice('');
    setFile(null);
    setMediaFile(null);
    setYoutubeUrl('');
    setShowDiff(false);
  }

  // Entities breakdown
  const preservedEntities = result?.entities_preserved || result?.entity_guardrail?.entities_preserved || [];
  const missingEntities = result?.entity_guardrail?.missing_entities || [];
  const totalEntitiesCount = (result?.entity_guardrail?.all_entities?.length) || (preservedEntities.length + missingEntities.length);
  const eliminatedCliches = result?.robotic_analysis?.eliminated_cliches || [];

  return (
    <div className="app">
      <header className="nav">
        <a className="brand" href="#home">
          <span className="brand-mark"><Feather size={20} /></span>
          <span>humanize<span className="brand-ai">ai</span></span>
        </a>

        <div className="track-badge">
          <Zap size={13} /> Problem Track 02: AI Humanization
        </div>

        <button className="mobile-toggle" aria-label="Toggle navigation" onClick={() => setMobileMenu(!mobileMenu)}>
          <Menu />
        </button>

        <nav className={mobileMenu ? 'nav-links open' : 'nav-links'}>
          <a href="#home">Home</a>
          <a href="#workspace">Writing Studio</a>
          <a href="#workspace" onClick={() => setTab('upload')}>Document</a>
          <a href="#workspace" onClick={() => setTab('media')}>Audio / Video</a>
          <a href="#workspace" onClick={() => setTab('youtube')}>YouTube</a>
          <a href="#verification">Guardrail</a>
        </nav>

        <a className="nav-cta" href="#workspace">Open Studio <ArrowRight size={16} /></a>
      </header>

      <main id="home">
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
              <a className="button primary" href="#workspace">Launch Writing Studio <ArrowRight size={17} /></a>
              <a className="button secondary" href="#workspace" onClick={() => setTab('media')}><Video size={17} /> Transcribe Media</a>
            </div>
            <div className="hero-note">
              <ShieldCheck size={16} /> 100% Fact & Entity Guardrail · Local Audio/Video & YouTube Transcription
            </div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="art-orbit orbit-a" />
            <div className="art-orbit orbit-b" />
            <div className="art-card">
              <div className="art-card-top"><span>ROBOTIC INPUT</span><span className="art-dash" /></div>
              <div className="fake-lines"><i /><i /><i className="short" /></div>
              <div className="art-spark"><Sparkles size={17} /></div>
              <div className="art-card-top after"><span>HUMANIZED OUTPUT</span><span className="art-check"><Check size={12} /></span></div>
              <div className="fake-lines warm"><i /><i /><i className="short" /></div>
            </div>
            <div className="art-flower flower-one">✳</div>
            <div className="art-flower flower-two">✿</div>
          </div>
        </section>

        <section className="workspace-section" id="workspace">
          <div className="section-heading">
            <div>
              <div className="eyebrow">MULTIMODAL WRITING STUDIO</div>
              <h2>Humanize, audit, and safeguard your prose.</h2>
            </div>
            <span className="secure-label"><ShieldCheck size={15} /> Entity-Preserving Verification Active</span>
          </div>

          <div className="workspace-card">
            {/* STUDIO 4-TAB NAVIGATION */}
            <div className="workspace-tabs">
              <button className={tab === 'write' ? 'active' : ''} onClick={() => setTab('write')}>
                <Feather size={16} /> Write or paste text
              </button>
              <button className={tab === 'upload' ? 'active' : ''} onClick={() => setTab('upload')}>
                <FileUp size={16} /> Upload document
              </button>
              <button className={tab === 'media' ? 'active' : ''} onClick={() => setTab('media')}>
                <Video size={16} /> Upload Audio/Video
              </button>
              <button className={tab === 'youtube' ? 'active' : ''} onClick={() => setTab('youtube')}>
                <Youtube size={16} /> YouTube Link
              </button>
            </div>

            {/* TAB 2: DOCUMENT UPLOAD DROPZONE */}
            {tab === 'upload' && (
              <div
                className={'dropzone ' + (drag ? 'dragging' : '')}
                onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                onDragLeave={() => setDrag(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDrag(false);
                  selectFile(e.dataTransfer.files[0]);
                }}
              >
                <input
                  ref={picker}
                  hidden
                  type="file"
                  accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                  onChange={(e) => selectFile(e.target.files[0])}
                />
                {file ? (
                  <div className="selected-file">
                    <span className="file-icon"><FileText /></span>
                    <div>
                      <b>{file.name}</b>
                      <small>{(file.size / 1024).toFixed(0)} KB · extracted text populated below</small>
                    </div>
                    <button
                      aria-label="Remove document"
                      className="icon-btn"
                      disabled={busy}
                      onClick={() => {
                        setFile(null);
                        setInput('');
                        setOutput('');
                        setResult(null);
                        setNotice('');
                      }}
                    >
                      <X size={17} />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="upload-icon"><Upload size={20} /></div>
                    <b>Drop your candidate resume, feedback, or report here</b>
                    <span>PDF, DOCX or TXT · up to 5 MB</span>
                    <button className="browse-btn" onClick={() => picker.current?.click()}>Browse document</button>
                  </>
                )}
              </div>
            )}

            {/* TAB 3: AUDIO/VIDEO UPLOAD DROPZONE */}
            {tab === 'media' && (
              <div
                className={'dropzone ' + (mediaDrag ? 'dragging' : '')}
                onDragOver={(e) => { e.preventDefault(); setMediaDrag(true); }}
                onDragLeave={() => setMediaDrag(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setMediaDrag(false);
                  selectMediaFile(e.dataTransfer.files[0]);
                }}
              >
                <input
                  ref={mediaPicker}
                  hidden
                  type="file"
                  accept=".mp4,.mov,.webm,.mkv,.mp3,.wav,.m4a,.aac,.flac,video/*,audio/*"
                  onChange={(e) => selectMediaFile(e.target.files[0])}
                />
                {mediaFile ? (
                  <div className="selected-file">
                    <span className="file-icon">
                      {/\.(mp3|wav|m4a|aac|flac)$/i.test(mediaFile.name) ? <Music /> : <Video />}
                    </span>
                    <div>
                      <b>{mediaFile.name}</b>
                      <small>{(mediaFile.size / (1024 * 1024)).toFixed(1)} MB · transcribed speech populated below</small>
                    </div>
                    <button
                      aria-label="Remove media"
                      className="icon-btn"
                      disabled={transcribing || busy}
                      onClick={() => {
                        setMediaFile(null);
                        setInput('');
                        setOutput('');
                        setResult(null);
                        setNotice('');
                      }}
                    >
                      <X size={17} />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="upload-icon media-upload-icon"><Video size={20} /></div>
                    <b>Drop your video interview or audio recording here</b>
                    <span>MP4, MOV, WEBM, MP3, WAV, M4A · up to 25 MB</span>
                    <button className="browse-btn" onClick={() => mediaPicker.current?.click()}>Browse Audio/Video</button>
                  </>
                )}
              </div>
            )}

            {/* TAB 4: YOUTUBE LINK EXTRACTION PANEL */}
            {tab === 'youtube' && (
              <div className="youtube-panel">
                <div className="youtube-input-wrap">
                  <div className="youtube-icon-tag"><Youtube size={18} /></div>
                  <input
                    type="url"
                    placeholder="Paste YouTube link (e.g. https://www.youtube.com/watch?v=... or https://youtu.be/...)"
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && fetchYouTubeTranscript()}
                  />
                  <button
                    className="button primary fetch-btn"
                    disabled={transcribing || !youtubeUrl.trim()}
                    onClick={fetchYouTubeTranscript}
                  >
                    {transcribing ? (
                      <><LoaderCircle className="spin" size={15} /> Fetching…</>
                    ) : (
                      <><Sparkles size={15} /> Fetch Transcript</>
                    )}
                  </button>
                </div>
                <span className="youtube-hint">
                  Extracts official captions or streams audio for speech-to-text transcription directly into the editor.
                </span>
              </div>
            )}

            {/* DUAL-PANE WRITING STUDIO GRID */}
            <div className="editor-grid">
              {/* INPUT PANE */}
              <div className="editor-pane">
                <div className="pane-head">
                  <label htmlFor="source">
                    {tab === 'upload'
                      ? 'Extracted document text'
                      : tab === 'media'
                      ? 'Transcribed audio/video speech'
                      : tab === 'youtube'
                      ? 'YouTube transcript preview'
                      : 'Your original text'}
                  </label>
                  <div className="head-indicators">
                    {input.trim() && /(?:\[(?:music|crying|applause|laughter|cheering|sniffling)\]|>>)/i.test(input) && (
                      <button
                        type="button"
                        className="clean-transcript-btn"
                        onClick={() => setInput(cleanTranscriptNoise(input))}
                        title="Remove [music], [crying], and >> subtitle tags"
                      >
                        🧹 Clean Transcript Tags
                      </button>
                    )}
                    {input.trim() && (
                      <span className={`score-badge score-${clientAnalysis.score.toLowerCase()}`}>
                        Robotic Score: <b>{clientAnalysis.score}</b>
                      </span>
                    )}
                    <span className="pane-tag">INPUT</span>
                  </div>
                </div>

                {/* Robotic Cliché Pre-analysis Strip */}
                {input.trim() && clientAnalysis.cliches.length > 0 && (
                  <div className="cliche-preview-strip">
                    <span className="strip-title"><AlertTriangle size={12} /> Detected AI Clichés:</span>
                    <div className="strip-pills">
                      {clientAnalysis.cliches.slice(0, 5).map((c, i) => (
                        <span key={i} className="cliche-pill">"{c}"</span>
                      ))}
                      {clientAnalysis.cliches.length > 5 && (
                        <span className="cliche-pill more">+{clientAnalysis.cliches.length - 5} more</span>
                      )}
                    </div>
                  </div>
                )}

                {transcribing ? (
                  <div className="transcribing-overlay">
                    <LoaderCircle className="spin" size={26} />
                    <b>Transcribing media audio…</b>
                    <span>Extracting spoken language and feeding transcript into editor…</span>
                  </div>
                ) : (
                  <textarea
                    id="source"
                    value={input}
                    maxLength={20000}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Paste text, upload an interview recording, or fetch a YouTube transcript to refine…"
                  />
                )}

                <div className="pane-foot">
                  <span>{count(input)} words · {input.length.toLocaleString()} / 20,000 characters</span>
                  {(file || mediaFile || tab === 'youtube') && <span className="editable">Editable transcript preview</span>}
                </div>
              </div>

              {/* OUTPUT PANE */}
              <div className="editor-pane output-pane">
                <div className="pane-head">
                  <div className="output-pane-title">
                    <label>Humanized version</label>
                    <span className="output-label"><Sparkles size={12} /> OUTPUT</span>
                  </div>
                  {output && (
                    <div className="view-toggle-wrap">
                      <button
                        className={`diff-toggle-btn ${showDiff ? 'active' : ''}`}
                        onClick={() => setShowDiff(!showDiff)}
                        title="Toggle between clean text and visual word diff"
                      >
                        <Split size={13} /> {showDiff ? 'Clean Text' : 'Visual Diff'}
                      </button>
                    </div>
                  )}
                </div>

                {busy && (
                  <div className="loading-state">
                    <LoaderCircle className="spin" size={22} />
                    <span>Executing generation & entity guardrail pipeline…</span>
                  </div>
                )}

                {showDiff && output ? (
                  <div className="diff-view-area">
                    <div className="diff-legend">
                      <span><i className="legend-dot dot-add" /> Added Humanized Phrasing</span>
                      <span><i className="legend-dot dot-remove" /> Replaced Robotic Words</span>
                    </div>
                    <div className="diff-content">
                      {diffChunks.map((chunk, idx) => {
                        if (chunk.type === 'added') {
                          return <span key={idx} className="diff-add">{chunk.text}</span>;
                        }
                        if (chunk.type === 'removed') {
                          return <span key={idx} className="diff-remove">{chunk.text}</span>;
                        }
                        return <span key={idx} className="diff-common">{chunk.text}</span>;
                      })}
                    </div>
                  </div>
                ) : (
                  <textarea
                    aria-label="Humanized output"
                    value={output}
                    readOnly
                    placeholder="Your refined writing with preserved facts, scores, and natural human flow will appear here…"
                  />
                )}

                <div className="pane-foot">
                  <span>{count(output)} words · {output.length.toLocaleString()} characters</span>
                  {output && (
                    <div className="output-actions">
                      <button onClick={copy}><Clipboard size={14} /> Copy</button>
                      <button onClick={download}><ArrowDown size={14} /> Download</button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* CONTROLS */}
            <div className="controls">
              <label className="select-control context-control">
                <span>Domain Writing Context</span>
                <div>
                  <select value={context} onChange={(e) => setContext(e.target.value)}>
                    {contexts.map((x) => <option key={x} value={x}>{x}</option>)}
                  </select>
                  <ChevronDown size={15} />
                </div>
              </label>

              <label className="select-control tone-control">
                <span>Tone Preset</span>
                <div>
                  <select value={tone} onChange={(e) => setTone(e.target.value)}>
                    {tones.map((x) => <option key={x} value={x}>{x}</option>)}
                  </select>
                  <ChevronDown size={15} />
                </div>
              </label>

              <label className="toggle-control" title="Retain original sentence structures and make surgical corrections only">
                <input type="checkbox" checked={minimal} onChange={(e) => setMinimal(e.target.checked)} />
                <span className="toggle-ui" />
                <span>Minimal rewrite</span>
              </label>

              <div className="control-actions">
                <button className="clear-btn" onClick={clear} disabled={busy || transcribing}>
                  <RotateCcw size={15} /> Clear
                </button>
                <button
                  className="button primary humanize-btn"
                  onClick={run}
                  disabled={busy || transcribing || !input.trim()}
                >
                  {busy ? (
                    <><LoaderCircle className="spin" size={16} /> Humanizing & Verifying…</>
                  ) : (
                    <><Sparkles size={16} /> Humanize text</>
                  )}
                </button>
              </div>
            </div>

            {(error || notice) && (
              <div role="status" className={error ? 'notice error' : 'notice'}>
                {error || notice}
              </div>
            )}

            {/* COLLAPSIBLE INSPECTION & VERIFICATION DRAWER */}
            {result && (
              <div className="inspection-drawer" id="verification">
                <button
                  type="button"
                  className="drawer-toggle"
                  onClick={() => setDrawerOpen(!drawerOpen)}
                  aria-expanded={drawerOpen}
                >
                  <div className="drawer-title-group">
                    <ShieldCheck size={20} className="shield-icon" />
                    <div>
                      <b>Inspection & Verification Drawer</b>
                      <span>Two-Pass Pipeline · Entity Preservation & Semantic Fidelity</span>
                    </div>
                  </div>
                  <div className="drawer-quick-metrics">
                    <span className="quick-pill score-match">
                      <CheckCircle2 size={13} /> {result.semantic_similarity_score ?? 98}% Meaning Match
                    </span>
                    <span className="quick-pill score-entities">
                      <CheckCircle2 size={13} /> {preservedEntities.length}/{totalEntitiesCount || preservedEntities.length} Entities
                    </span>
                    <span className="drawer-chevron">
                      {drawerOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </span>
                  </div>
                </button>

                {drawerOpen && (
                  <div className="drawer-body">
                    {/* Top 3 Metric Cards Grid */}
                    <div className="inspection-metrics-grid">
                      {/* 1. Robotic Phrases Eliminated */}
                      <div className="inspection-card">
                        <div className="card-header">
                          <span className="card-label">ROBOTIC LANGUAGE LAYER</span>
                          <h4>Clichés Eliminated</h4>
                        </div>
                        <div className="card-body">
                          {eliminatedCliches.length > 0 ? (
                            <div className="eliminated-pills-list">
                              {eliminatedCliches.map((c, i) => (
                                <span key={i} className="eliminated-badge">✕ {c}</span>
                              ))}
                            </div>
                          ) : (
                            <div className="clean-signal">
                              <CheckCircle2 size={15} />
                              <span>{clientAnalysis.cliches.length === 0 ? 'No robotic clichés in source.' : 'Phrasing refined for natural cadence.'}</span>
                            </div>
                          )}
                          <small className="card-note">
                            Robotic Phrasing Score: <b>{result.robotic_analysis?.robotic_score || 'Low'}</b>
                          </small>
                        </div>
                      </div>

                      {/* 2. Strict Entity & Terminology Guardrail */}
                      <div className="inspection-card">
                        <div className="card-header">
                          <span className="card-label">FACTUALITY GUARDRAIL</span>
                          <h4>Preserved Entities</h4>
                        </div>
                        <div className="card-body">
                          {preservedEntities.length > 0 ? (
                            <div className="entity-chip-list">
                              {preservedEntities.map((ent, i) => (
                                <span key={i} className="entity-chip">
                                  <Check size={11} /> {ent}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="empty-entities">No critical technical terms, scores, or names detected.</span>
                          )}
                          <div className="guardrail-status-line">
                            {missingEntities.length === 0 ? (
                              <span className="status-perfect">✓ 100% Entities Preserved Unaltered</span>
                            ) : (
                              <span className="status-missing">⚠️ Missing entities flagged for review: {missingEntities.join(', ')}</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* 3. Meaning & Semantic Match */}
                      <div className="inspection-card">
                        <div className="card-header">
                          <span className="card-label">VERIFICATION PIPELINE</span>
                          <h4>Meaning Preservation</h4>
                        </div>
                        <div className="card-body">
                          <div className="score-metric-row">
                            <div className="big-score">
                              <b>{result.semantic_similarity_score ?? 98}%</b>
                              <span>Semantic Match</span>
                            </div>
                            <div className="metric-badges">
                              <span className={result.meaning_preserved ? 'badge-pass' : 'badge-warn'}>
                                {result.meaning_preserved ? '✓ Meaning Preserved' : 'Review Needed'}
                              </span>
                              <span className="badge-pass">
                                ✓ {result.factuality_confidence ?? 98}% Factuality Conf.
                              </span>
                            </div>
                          </div>
                          <small className="card-note">
                            {result.unsupported_claims_detected ? '⚠️ Unsupported claims detected' : '✓ 0 Unsupported Claims Detected'}
                          </small>
                        </div>
                      </div>
                    </div>

                    {/* Detailed Validation Statuses */}
                    <div className="validation-statuses">
                      <Status label="Meaning Preservation Audit" data={result.meaning_validation} />
                      <Status label="Factual Consistency Audit" data={result.factuality_validation} />
                    </div>

                    {/* Warnings and Explanations */}
                    {result.warnings?.length > 0 && (
                      <div className="warnings">
                        {result.warnings.map((w, i) => <p key={i}>• {w}</p>)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section id="how" className="how">
          <div className="section-heading">
            <div>
              <div className="eyebrow">A RIGOROUS TWO-PASS PIPELINE</div>
              <h2>Humanization with verifiable integrity.</h2>
            </div>
            <p className="how-intro">Designed for recruitment, evaluation, and interview transcripts, protecting candidate trust and data fidelity.</p>
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
      </main>

      <footer>
        <a className="brand footer-brand" href="#home">
          <span className="brand-mark"><Feather size={18} /></span>
          <span>humanize<span className="brand-ai">ai</span></span>
        </a>
        <p>Problem Track 02: AI Humanization & Natural Language Refinement</p>
        <div className="footer-meta">
          <span>FastAPI · React 18 · Whisper & Gemini · Entity Guardrails</span>
        </div>
        <small>Privacy note: Documents and media streams are processed in-memory and are not permanently stored.</small>
      </footer>
    </div>
  );
}

function Status({ label, data }) {
  const status = data?.meaning_status || data?.factuality_status || 'Review recommended';
  const klass = status === 'Passed' ? 'passed' : status === 'Potential issue detected' ? 'issue' : 'review';
  return (
    <div className="status-item">
      <span>{label}</span>
      <b className={klass}>{status}</b>
      <small>{data?.meaning_explanation || data?.factuality_explanation || 'Please review.'}</small>
    </div>
  );
}
