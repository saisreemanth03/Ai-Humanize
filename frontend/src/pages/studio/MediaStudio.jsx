import { useRef, useState } from 'react';
import { Video, Music, X } from 'lucide-react';
import StudioWorkspace from '../../components/StudioWorkspace';
import { useHumanizeStudio } from '../../utils/useHumanizeStudio';
import { extractMedia } from '../../services/api';

export default function MediaStudio() {
  const studio = useHumanizeStudio('Audio / Video Transcript & Spoken Dialogue', 'Conversational');
  const [mediaFile, setMediaFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const mediaPickerRef = useRef(null);

  async function handleMediaSelect(f) {
    if (!f) return;
    studio.setError('');
    studio.setNotice('');

    if (!/\.(mp4|mov|webm|mkv|mp3|wav|m4a|aac|flac)$/i.test(f.name)) {
      studio.setError('Please choose a valid Audio or Video file (.mp4, .mov, .webm, .mp3, .wav, .m4a).');
      return;
    }
    if (f.size > 25 * 1024 * 1024) {
      studio.setError('This media file exceeds the 25 MB upload limit.');
      return;
    }

    setMediaFile(f);
    studio.setInput('');
    studio.setOutput('');
    studio.setResult(null);
    studio.setTranscribing(true);

    try {
      const data = await extractMedia(f);
      studio.setInput(data.extracted_text || '');
      studio.setContext('Audio / Video Transcript & Spoken Dialogue');
      studio.setTone('Conversational');
      if (data.warnings?.length) {
        studio.setNotice(data.warnings.join(' '));
      }
    } catch (e) {
      setMediaFile(null);
      studio.setError(e.message || 'Media transcription failed.');
    } finally {
      studio.setTranscribing(false);
    }
  }

  function handleRemoveMedia() {
    setMediaFile(null);
    studio.clearAll();
  }

  const dropzoneSlot = (
    <div
      className={`dropzone media-dropzone ${isDragging ? 'dragging' : ''}`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragEnter={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setIsDragging(false);
      }}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer?.files?.[0]) {
          handleMediaSelect(e.dataTransfer.files[0]);
        }
      }}
    >
      <input
        ref={mediaPickerRef}
        hidden
        type="file"
        accept=".mp4,.mov,.webm,.mkv,.mp3,.wav,.m4a,.aac,.flac,video/*,audio/*"
        onChange={(e) => {
          if (e.target.files?.[0]) handleMediaSelect(e.target.files[0]);
        }}
      />

      {mediaFile ? (
        <div className="selected-file">
          <span className="file-icon">
            {/\.(mp3|wav|m4a|aac|flac)$/i.test(mediaFile.name) ? <Music size={22} /> : <Video size={22} />}
          </span>
          <div className="file-info">
            <b>{mediaFile.name}</b>
            <small>{(mediaFile.size / (1024 * 1024)).toFixed(1)} MB · Transcribed speech populated in editor</small>
          </div>
          <button
            type="button"
            aria-label="Remove media"
            className="icon-btn remove-file-btn"
            disabled={studio.transcribing || studio.busy}
            onClick={handleRemoveMedia}
          >
            <X size={17} />
          </button>
        </div>
      ) : (
        <div className="dropzone-empty" onClick={() => mediaPickerRef.current?.click()}>
          <div className="upload-icon media-upload-icon"><Video size={22} /></div>
          <b>Drop your video interview or audio recording here</b>
          <span>MP4, MOV, WEBM, MP3, WAV, M4A · up to 25 MB</span>
          <button
            type="button"
            className="browse-btn"
            onClick={(e) => {
              e.stopPropagation();
              mediaPickerRef.current?.click();
            }}
          >
            Browse Audio/Video
          </button>
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
        setMediaFile(null);
        studio.clearAll();
      }}
      topSlot={dropzoneSlot}
      inputTitle="Transcribed Audio/Video Speech"
      placeholder="Drop an audio file or interview video above to generate a transcript, or paste spoken speech directly…"
    />
  );
}
