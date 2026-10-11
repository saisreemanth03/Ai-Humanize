import { useState } from 'react';
import { Youtube, Sparkles, LoaderCircle } from 'lucide-react';
import StudioWorkspace from '../../components/StudioWorkspace';
import { useHumanizeStudio } from '../../utils/useHumanizeStudio';
import { extractYouTube } from '../../services/api';

export default function YouTubeStudio() {
  const studio = useHumanizeStudio('Audio / Video Transcript & Spoken Dialogue', 'Conversational');
  const [youtubeUrl, setYoutubeUrl] = useState('');

  async function handleFetchYouTube(urlOverride) {
    const targetUrl = (typeof urlOverride === 'string' ? urlOverride : youtubeUrl).trim();
    if (!targetUrl) {
      studio.setError('Please enter a valid YouTube video URL.');
      return;
    }
    studio.setError('');
    studio.setNotice('');
    studio.setInput('');
    studio.setOutput('');
    studio.setResult(null);
    studio.setTranscribing(true);

    try {
      const data = await extractYouTube(targetUrl);
      studio.setInput(data.extracted_text || '');
      studio.setContext('Audio / Video Transcript & Spoken Dialogue');
      studio.setTone('Conversational');
      if (data.warnings?.length) {
        studio.setNotice(data.warnings.join(' '));
      }
    } catch (e) {
      studio.setError(e.message || 'Could not retrieve YouTube transcript.');
    } finally {
      studio.setTranscribing(false);
    }
  }

  const [showGuide, setShowGuide] = useState(false);

  function handleFocusEditor() {
    studio.setError('');
    studio.setNotice('Editor ready: paste your YouTube transcript or subtitles below, then click "Humanize text".');
    const el = document.getElementById('source-input');
    if (el) {
      el.focus();
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function handleUseSample(sample = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ') {
    setYoutubeUrl(sample);
    handleFetchYouTube(sample);
  }

  const youtubeSlot = (
    <div className="youtube-panel">
      <div className="youtube-input-wrap">
        <div className="youtube-icon-tag"><Youtube size={18} /></div>
        <input
          type="url"
          className="youtube-url-input"
          placeholder="Paste YouTube link (e.g. https://www.youtube.com/watch?v=... or https://youtu.be/...)"
          value={youtubeUrl}
          onChange={(e) => setYoutubeUrl(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleFetchYouTube()}
        />
        <button
          type="button"
          className="button secondary manual-paste-btn"
          onClick={handleFocusEditor}
          title="Directly paste transcript or subtitles into the editor"
        >
          ✍️ Manual Paste
        </button>
        <button
          type="button"
          className="button primary fetch-btn"
          disabled={studio.transcribing || !youtubeUrl.trim()}
          onClick={() => handleFetchYouTube()}
        >
          {studio.transcribing ? (
            <><LoaderCircle className="spin" size={15} /> Fetching…</>
          ) : (
            <><Sparkles size={15} /> Fetch Transcript</>
          )}
        </button>
      </div>
      <div className="youtube-subbar">
        <span className="youtube-hint">
          Extracts captions or streams audio into the editor. Try sample:{" "}
          <button
            type="button"
            className="sample-link-btn"
            onClick={() => handleUseSample('https://www.youtube.com/watch?v=dQw4w9WgXcQ')}
          >
            Sample Video
          </button>
        </span>
        <button
          type="button"
          className="youtube-guide-toggle"
          onClick={() => setShowGuide(!showGuide)}
        >
          {showGuide ? 'Hide transcript guide ▴' : 'How to copy transcripts in 2 clicks ▾'}
        </button>
      </div>

      {showGuide && (
        <div className="youtube-guide-card">
          <div className="guide-heading">
            <b>⚡ How to grab any YouTube transcript in seconds:</b>
            <button type="button" className="guide-close-btn" onClick={() => setShowGuide(false)}>✕</button>
          </div>
          <ol className="guide-list">
            <li>Open the video on YouTube in your browser.</li>
            <li>Click <b>"… More"</b> below the video title/description, then select <b>"Show transcript"</b>.</li>
            <li>Copy the transcript lines and paste them directly into the editor below!</li>
          </ol>
        </div>
      )}
    </div>
  );

  return (
    <StudioWorkspace
      input={studio.input}
      setInput={studio.setInput}
      output={studio.output}
      setOutput={studio.setOutput}
      context={studio.context}
      setContext={studio.setContext}
      tone={studio.tone}
      setTone={studio.setTone}
      minimal={studio.minimal}
      setMinimal={studio.setMinimal}
      busy={studio.busy}
      transcribing={studio.transcribing}
      error={studio.error}
      notice={studio.notice}
      result={studio.result}
      onRun={studio.runHumanize}
      onClear={() => {
        setYoutubeUrl('');
        studio.clearAll();
      }}
      topSlot={youtubeSlot}
      inputTitle="YouTube Transcript Preview"
      placeholder="Paste a YouTube link above and click 'Fetch Transcript' to extract speech into the editor…"
    />
  );
}
