import { useState, useId } from 'react';
import {
  MessageSquare,
  Sparkles,
  LoaderCircle,
  AlertCircle,
  Copy,
  Check,
  ExternalLink,
  Info,
  X,
  Zap,
} from 'lucide-react';
import StudioWorkspace from '../../components/StudioWorkspace';
import { useHumanizeStudio } from '../../utils/useHumanizeStudio';
import { fetchChatLink, humanizeText } from '../../services/api';


export default function ChatLinkStudio() {
  const studio = useHumanizeStudio('General Professional Writing', 'Natural');
  const [chatUrl, setChatUrl] = useState('');
  const [isFetching, setIsFetching] = useState(false);
  const [fetchProgress, setFetchProgress] = useState('');
  const [toast, setToast] = useState(null); // { type: 'error' | 'success', title: string, message: string }
  const [autoRefine, setAutoRefine] = useState(true);
  const [detectedPlatform, setDetectedPlatform] = useState(null);
  const inputId = useId();

  // Show a non-intrusive, graceful floating toast
  const showToast = (type, title, message) => {
    setToast({ type, title, message });
    if (type === 'success') {
      setTimeout(() => setToast(null), 5000);
    }
  };

  const handleDismissToast = () => {
    setToast(null);
  };

  // Focus the input textarea for manual paste
  const handleFocusEditor = () => {
    studio.setError('');
    studio.setNotice(
      'Editor ready: Copy the text from your AI chat and paste it below, then click "Humanize text".'
    );
    const el = document.getElementById('source-input');
    if (el) {
      el.focus();
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    setToast(null);
  };

  // Detect platform as user types (for visual pill badge)
  const handleUrlChange = (val) => {
    setChatUrl(val);
    const clean = val.trim().toLowerCase();
    if (clean.includes('chatgpt.com') || clean.includes('openai.com')) {
      setDetectedPlatform('ChatGPT');
    } else if (clean.includes('gemini.google.com') || clean.includes('g.co')) {
      setDetectedPlatform('Gemini');
    } else if (clean.includes('claude.ai') || clean.includes('anthropic.com')) {
      setDetectedPlatform('Claude');
    } else if (clean.includes('perplexity.ai')) {
      setDetectedPlatform('Perplexity');
    } else if (clean.includes('deepseek.com')) {
      setDetectedPlatform('DeepSeek');
    } else {
      setDetectedPlatform(null);
    }
  };

  // Main fetch action (universal unrestricted extraction)
  async function handleFetchChat(urlOverride) {
    let targetUrl = (typeof urlOverride === 'string' ? urlOverride : chatUrl).trim();

    if (!targetUrl) {
      showToast(
        'error',
        'Link Required',
        'Please enter a URL to extract text from.'
      );
      return;
    }

    // Ensure URL has protocol
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      targetUrl = 'https://' + targetUrl;
    }

    try {
      new URL(targetUrl);
    } catch {
      showToast(
        'error',
        'Invalid URL',
        'Please enter a valid web URL (e.g. https://chatgpt.com/... or https://claude.ai/...).'
      );
      return;
    }

    setToast(null);
    studio.setError('');
    studio.setNotice('');
    studio.setOutput('');
    studio.setResult(null);
    setIsFetching(true);
    setFetchProgress('Fetching text...');

    try {
      const data = await fetchChatLink(targetUrl);
      const extracted = data.extracted_text || '';

      if (!extracted.trim()) {
        throw new Error('No visible text could be extracted from this URL.');
      }

      // Automatically inject the text into the primary text studio editor
      studio.setInput(extracted);

      const platformName = data.platform || detectedPlatform || 'Web Source';
      setDetectedPlatform(platformName);

      showToast(
        'success',
        `${platformName} Text Ingested`,
        `Extracted ${data.word_count || extracted.split(/\s+/).length} words. Ready to humanize.`
      );

      if (data.warnings?.length) {
        studio.setNotice(data.warnings.join(' '));
      }

      // Automatically trigger refinement pipeline if auto-refine is enabled
      if (autoRefine) {
        setFetchProgress('Triggering natural humanization pipeline...');
        setTimeout(async () => {
          try {
            studio.setBusy(true);
            const result = await humanizeText({
              text: extracted,
              context: studio.context,
              tone: studio.tone,
              minimal_rewrite: studio.minimal,
            });

            studio.setOutput(result.humanized_text);
            studio.setResult(result);
          } catch (err) {
            studio.setError(
              err.message || 'Text extracted, but refinement failed. Click "Humanize text" below to retry.'
            );
          } finally {
            studio.setBusy(false);
          }
        }, 150);
      }
    } catch (e) {
      const errorMsg = e.message || 'Could not fetch text from this URL.';
      studio.setError('');
      showToast(
        'error',
        'Could Not Extract Chat',
        `${errorMsg} Please manually copy and paste the chat text directly into the editor.`
      );
    } finally {
      setIsFetching(false);
      setFetchProgress('');
    }
  }


  // Pre-fill sample shared links for testing and demos
  const handleUseSample = (type) => {
    let sample = '';
    if (type === 'chatgpt') {
      sample = 'https://chatgpt.com/share/6703b41e-abcd-8001-9002-1234567890ab';
    } else {
      sample = 'https://gemini.google.com/share/9876543210ab';
    }
    setChatUrl(sample);
    handleUrlChange(sample);
  };

  // Top ingest card slot matching the visual language of YouTube and Media studios
  const chatLinkSlot = (
    <div className="chatlink-panel">
      {/* Toast Notification Error/Success Boundary */}
      {toast && (
        <div className={`chatlink-toast ${toast.type}`} role="alert">
          <div className="toast-icon">
            {toast.type === 'error' ? <AlertCircle size={18} /> : <Check size={18} />}
          </div>
          <div className="toast-body">
            <span className="toast-title">{toast.title}</span>
            <span className="toast-message">{toast.message}</span>
          </div>
          <div className="toast-actions">
            {toast.type === 'error' && (
              <button
                type="button"
                className="toast-action-btn"
                onClick={handleFocusEditor}
              >
                ✍️ Paste Manually
              </button>
            )}
            <button
              type="button"
              className="toast-close-btn"
              onClick={handleDismissToast}
              aria-label="Dismiss notification"
            >
              <X size={15} />
            </button>
          </div>
        </div>
      )}

      {/* Main Link Input Bar */}
      <div className="chatlink-input-wrap">
        <div className="chatlink-icon-tag" title={detectedPlatform || 'AI Chat Link'}>
          <MessageSquare size={18} />
        </div>

        <div className="chatlink-input-field-wrap">
          <input
            id={inputId}
            type="url"
            className="chatlink-url-input"
            placeholder="Paste ChatGPT, Gemini, Claude, or any AI chat URL..."
            value={chatUrl}
            onChange={(e) => handleUrlChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isFetching && handleFetchChat()}
            disabled={isFetching}
          />
          {detectedPlatform && (
            <span className={`platform-pill ${detectedPlatform.toLowerCase()}`}>
              {detectedPlatform}
            </span>
          )}
        </div>

        <button
          type="button"
          className="button secondary manual-paste-btn"
          onClick={handleFocusEditor}
          title="Directly paste conversation text into the editor"
        >
          ✍️ Manual Paste
        </button>

        <button
          type="button"
          className="button primary fetch-btn chatlink-fetch-btn"
          disabled={isFetching || !chatUrl.trim()}
          onClick={() => handleFetchChat()}
        >
          {isFetching ? (
            <>
              <LoaderCircle className="spin" size={15} /> Fetching…
            </>
          ) : (
            <>
              <Sparkles size={15} /> Fetch Chat
            </>
          )}
        </button>
      </div>

      {/* Sub-bar with samples & pipeline options */}
      <div className="chatlink-subbar">
        <div className="chatlink-hints">
          <span className="hint-label">Universal:</span>
          <span className="domain-chip">ChatGPT</span>
          <span className="domain-chip">Gemini</span>
          <span className="domain-chip">Claude</span>
          <span className="domain-chip">Perplexity</span>
          <span className="domain-chip">Any Web URL</span>
        </div>



        <div className="chatlink-toggles">
          <label className="auto-refine-label" title="Automatically trigger natural refinement when text is fetched">
            <input
              type="checkbox"
              checked={autoRefine}
              onChange={(e) => setAutoRefine(e.target.checked)}
            />
            <span>Auto-refine after fetch</span>
          </label>
        </div>
      </div>

      {/* Robust Loading State: Skeleton Loader & Spinner Bar */}
      {isFetching && (
        <div className="chatlink-loading-state" role="status">
          <div className="loading-spinner-row">
            <LoaderCircle className="spin" size={18} />
            <span className="loading-text">{fetchProgress || 'Fetching AI chat responses...'}</span>
          </div>

          <div className="skeleton-loader-card">
            <div className="skeleton-line skeleton-header pulse" />
            <div className="skeleton-line skeleton-body-1 pulse" />
            <div className="skeleton-line skeleton-body-2 pulse" />
            <div className="skeleton-line skeleton-body-3 pulse" />
          </div>
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
        setChatUrl('');
        setDetectedPlatform(null);
        setToast(null);
        studio.clearAll();
      }}
      topSlot={chatLinkSlot}
      inputTitle="AI Chat Transcript Preview"
      placeholder="Paste a ChatGPT or Gemini shared link above and click 'Fetch Chat' to automatically ingest AI responses into the editor…"
    />
  );
}
