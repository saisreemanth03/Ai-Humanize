import { useRef, useState } from 'react';
import { FileUp, FileText, X, Upload } from 'lucide-react';
import StudioWorkspace from '../../components/StudioWorkspace';
import { useHumanizeStudio } from '../../utils/useHumanizeStudio';
import { extractDocument } from '../../services/api';

export default function DocumentStudio() {
  const studio = useHumanizeStudio();
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  async function handleFileSelect(f) {
    if (!f) return;
    studio.setError('');
    studio.setNotice('');

    if (!/\.(pdf|docx|txt)$/i.test(f.name)) {
      studio.setError('Please choose a valid PDF, DOCX, or TXT file.');
      return;
    }
    if (f.size > 5 * 1024 * 1024) {
      studio.setError('This document exceeds the 5 MB upload limit.');
      return;
    }

    setFile(f);
    studio.setInput('');
    studio.setOutput('');
    studio.setResult(null);
    studio.setBusy(true);

    try {
      const data = await extractDocument(f);
      studio.setInput(data.extracted_text || '');
      if (data.warnings?.length) {
        studio.setNotice(data.warnings.join(' '));
      }
    } catch (e) {
      setFile(null);
      studio.setError(e.message || 'Failed to extract text from document.');
    } finally {
      studio.setBusy(false);
    }
  }

  function handleRemoveFile() {
    setFile(null);
    studio.clearAll();
  }

  const dropzoneSlot = (
    <div
      className={`dropzone document-dropzone ${isDragging ? 'dragging' : ''}`}
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
          handleFileSelect(e.dataTransfer.files[0]);
        }
      }}
    >
      <input
        ref={fileInputRef}
        hidden
        type="file"
        accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
        onChange={(e) => {
          if (e.target.files?.[0]) handleFileSelect(e.target.files[0]);
        }}
      />

      {file ? (
        <div className="selected-file">
          <span className="file-icon"><FileText size={22} /></span>
          <div className="file-info">
            <b>{file.name}</b>
            <small>{(file.size / 1024).toFixed(0)} KB · Extracted document text populated below</small>
          </div>
          <button
            type="button"
            aria-label="Remove document"
            className="icon-btn remove-file-btn"
            disabled={studio.busy}
            onClick={handleRemoveFile}
          >
            <X size={17} />
          </button>
        </div>
      ) : (
        <div className="dropzone-empty" onClick={() => fileInputRef.current?.click()}>
          <div className="upload-icon"><Upload size={22} /></div>
          <b>Drop your candidate resume, offer letter, or report here</b>
          <span>PDF, DOCX, or TXT · up to 5 MB</span>
          <button
            type="button"
            className="browse-btn"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Browse document
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
        setFile(null);
        studio.clearAll();
      }}
      topSlot={dropzoneSlot}
      inputTitle="Extracted Document Text"
      placeholder="Select or drop a PDF, DOCX, or TXT document above to extract and humanize its contents…"
    />
  );
}
