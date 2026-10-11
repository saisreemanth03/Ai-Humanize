import { useState } from 'react';
import { Youtube, Sparkles, LoaderCircle } from 'lucide-react';
import StudioWorkspace from '../../components/StudioWorkspace';
import { useHumanizeStudio } from '../../utils/useHumanizeStudio';
import { extractYouTube } from '../../services/api';

export default function YouTubeStudio() {
  const studio = useHumanizeStudio('Audio / Video Transcript & Spoken Dialogue', 'Conversational');
  const [youtubeUrl, setYoutubeUrl] = useState('');

  async function handleFetchYouTube() {
    if (!youtubeUrl.trim()) {
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
      const data = await extractYouTube(youtubeUrl.trim());
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
          className="button primary fetch-btn"
          disabled={studio.transcribing || !youtubeUrl.trim()}
          onClick={handleFetchYouTube}
        >
          {studio.transcribing ? (
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
