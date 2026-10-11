import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowDown,
  Clipboard,
  ChevronDown,
  LoaderCircle,
  RotateCcw,
  Sparkles,
  Split
} from 'lucide-react';
import { CONTEXTS, TONES, analyzeClientText, cleanTranscriptNoise, countWords } from '../utils/constants';
import { computeWordDiff } from '../utils/diffHelper';
import InspectionDrawer from './InspectionDrawer';

export default function StudioWorkspace({
  input,
  setInput,
  output,
  setOutput,
  context,
  setContext,
  tone,
  setTone,
  minimal,
  setMinimal,
  busy,
  transcribing,
  error,
  notice,
  result,
  onRun,
  onClear,
  topSlot,
  inputTitle = 'Your original text',
  placeholder = 'Paste text, upload an interview recording, or fetch a YouTube transcript to refine…'
}) {
  const [showDiff, setShowDiff] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  // Client-side instant analysis
  const clientAnalysis = useMemo(() => analyzeClientText(input), [input]);

  // Visual diff chunks
  const diffChunks = useMemo(() => {
    if (!showDiff || !output || !input) return [];
    return computeWordDiff(input, output);
  }, [showDiff, input, output]);

  async function handleCopy() {
    if (!output) return;
    try {
      await navigator.clipboard.writeText(output);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch {
      // fallback
    }
  }

  function handleDownload() {
    if (!output) return;
    const blob = new Blob([output], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'humanized-text.txt';
    a.click();
    URL.revokeObjectURL(url);
  }

  const hasTranscriptArtifacts = useMemo(() => {
    return /(?:\[(?:music|crying|applause|laughter|cheering|sniffling)\]|>>|\b\d{1,2}:\d{2}\b)/i.test(input || '');
  }, [input]);

  return (
    <div className="workspace-card">
      {/* Tool-Specific Ingest Slot (e.g. Dropzone or YouTube bar) */}
      {topSlot && <div className="studio-top-slot">{topSlot}</div>}

      {/* DUAL-PANE WRITING STUDIO GRID (Independent Scrolling) */}
      <div className="editor-grid">
        {/* INPUT PANE */}
        <div className="editor-pane input-pane">
          <div className="pane-head">
            <label htmlFor="source-input">{inputTitle}</label>
            <div className="head-indicators">
              {input.trim() && hasTranscriptArtifacts && (
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
              <LoaderCircle className="spin" size={28} />
              <b>Extracting & Transcribing Media Audio…</b>
              <span>Analyzing speech stream and generating clean verbatim transcript…</span>
            </div>
          ) : (
            <textarea
              id="source-input"
              className="studio-textarea custom-scrollbar"
              value={input}
              maxLength={20000}
              onChange={(e) => setInput(e.target.value)}
              placeholder={placeholder}
            />
          )}

          <div className="pane-foot">
            <span>{countWords(input)} words · {input.length.toLocaleString()} / 20,000 characters</span>
            <span className="editable-hint">Editable Input</span>
          </div>
        </div>

        {/* OUTPUT PANE */}
        <div className="editor-pane output-pane">
          <div className="pane-head">
            <div className="output-pane-title">
              <label htmlFor="output-target">Humanized version</label>
              <span className="output-label"><Sparkles size={12} /> OUTPUT</span>
            </div>
            {output && (
              <div className="view-toggle-wrap">
                <button
                  type="button"
                  className={`diff-toggle-btn ${showDiff ? 'active' : ''}`}
                  onClick={() => setShowDiff(!showDiff)}
                  title="Toggle between clean prose and visual word comparison"
                >
                  <Split size={13} /> {showDiff ? 'Clean Text' : 'Visual Diff'}
                </button>
              </div>
            )}
          </div>

          {busy && (
            <div className="loading-state">
              <LoaderCircle className="spin" size={24} />
              <span>Executing natural generation & strict entity guardrail…</span>
            </div>
          )}

          {showDiff && output ? (
            <div className="diff-view-area custom-scrollbar">
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
              id="output-target"
              className="studio-textarea custom-scrollbar"
              aria-label="Humanized output"
              value={output}
              readOnly
              placeholder="Your refined writing with preserved facts, scores, metrics, and natural human flow will appear here…"
            />
          )}

          <div className="pane-foot">
            <span>{countWords(output)} words · {output.length.toLocaleString()} characters</span>
            {output && (
              <div className="output-actions">
                <button type="button" onClick={handleCopy} className={copySuccess ? 'copied' : ''}>
                  <Clipboard size={14} /> {copySuccess ? 'Copied!' : 'Copy'}
                </button>
                <button type="button" onClick={handleDownload}>
                  <ArrowDown size={14} /> Download
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* STICKY BOTTOM TOOLBAR */}
      <div className="controls sticky-toolbar">
        <label className="select-control context-control">
          <span>Domain Writing Context</span>
          <div className="select-wrap">
            <select value={context} onChange={(e) => setContext(e.target.value)}>
              {CONTEXTS.map((x) => <option key={x} value={x}>{x}</option>)}
            </select>
            <ChevronDown size={15} />
          </div>
        </label>

        <label className="select-control tone-control">
          <span>Tone Preset</span>
          <div className="select-wrap">
            <select value={tone} onChange={(e) => setTone(e.target.value)}>
              {TONES.map((x) => <option key={x} value={x}>{x}</option>)}
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
          <button type="button" className="clear-btn" onClick={onClear} disabled={busy || transcribing}>
            <RotateCcw size={15} /> Clear
          </button>
          <button
            type="button"
            className="button primary humanize-btn"
            onClick={onRun}
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

      {/* Notices & Errors */}
      {(error || notice) && (
        <div role="status" className={error ? 'notice error' : 'notice'}>
          <div className="notice-content-wrap">
            <span className="notice-text">{error || notice}</span>
            {error && /youtube/i.test(error) && (
              <div className="notice-actions-strip">
                <button
                  type="button"
                  className="notice-action-btn primary"
                  onClick={() => {
                    const el = document.getElementById('source-input');
                    if (el) {
                      el.focus();
                      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                  }}
                >
                  ✍️ Paste Transcript Directly
                </button>
                <Link to="/studio/media" className="notice-action-btn secondary">
                  🎙️ Upload Audio/Video Instead
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Two-Pass Inspection & Verification Drawer */}
      <InspectionDrawer result={result} clientAnalysis={clientAnalysis} />
    </div>
  );
}
