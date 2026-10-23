import { useState, useId } from 'react';
import {
  MessageSquare,
  Sparkles,
  LoaderCircle,
  AlertCircle,
  Clipboard,
  Check,
  X,
  ShieldAlert,
} from 'lucide-react';
import StudioWorkspace from '../../components/StudioWorkspace';
import { useHumanizeStudio } from '../../utils/useHumanizeStudio';
import { fetchChatLink, humanizeText } from '../../services/api';

// Known anti-bot and CAPTCHA challenge phrases
const ANTIBOT_PATTERNS = [
  /just a moment\.\.\./i,
  /enable javascript and cookies to continue/i,
  /verify you are human/i,
  /attention required!\s*\|\s*cloudflare/i,
  /checking your browser before accessing/i,
  /cloudflare ray id/i,
  /please turn javascript on and reload the page/i,
  /please verify that you are not a robot/i,
  /cf-turnstile/i,
  /cf-browser-verification/i,
  /access denied/i,
  /security check to continue/i,
  /log in to get answers/i,
  /what's on your mind today\?/i,
  /what’s on your mind today\?/i,
  /what's on the agenda today\?/i,
  /sign up for free/i,
  /get responses tailored to you/i,
  /see plans and pricing/i,
  /gemini - direct access to google ai/i,
  /link doesn't exist/i,
  /conversation has been deleted/i,
  /share not found/i,
  /stay logged out/i,
];

// Validates that extracted payload is meaningful and not a challenge page
function isAntiBotOrJunk(text) {
  if (!text || typeof text !== 'string') return true;
  const trimmed = text.trim();
  if (trimmed.length < 40) return true;
  return ANTIBOT_PATTERNS.some((pattern) => pattern.test(trimmed));
}

// Cleans out Jina Reader metadata headers and navigation/footer boilerplate
function cleanMarkdownBoilerplate(text) {
  if (!text || typeof text !== 'string') return '';
  const lines = text.split('\n');
  const cleanedLines = [];
  let headerMode = true;

  for (const line of lines) {
    const trimmed = line.trim();

    if (headerMode) {
      if (
        trimmed.startsWith('Title:') ||
        trimmed.startsWith('URL Source:') ||
        trimmed.startsWith('Published Time:')
      ) {
        continue;
      }
      if (trimmed.startsWith('Markdown Content:')) {
        headerMode = false;
        continue;
      }
      if (!trimmed) continue;
      headerMode = false;
    }

    const lower = trimmed.toLowerCase();
    if (
      lower === '[skip to content]' ||
      lower === '[log in]' ||
      lower === '[sign up]' ||
      lower === 'terms & privacy policy' ||
      lower === 'terms' ||
      lower === 'privacy policy' ||
      lower === 'terms of service' ||
      lower === '[back to top]' ||
      lower === 'learn more' ||
      lower === 'stay logged out'
    ) {
      continue;
    }

    cleanedLines.push(line);
  }

  return cleanedLines.join('\n').replace(/\n{3,}/g, '\n\n').trim();
}

// Stage 1: Client-Side Jina Reader Fetch (with Cloud Browser Engine)
async function fetchStage1ClientJina(targetUrl) {
  const headers = {
    Accept: 'text/plain',
    'X-Return-Format': 'text',
    'X-Engine': 'browser',
    'X-Timeout': '30',
    'X-No-Cache': 'true',
  };

  const urlsToTry = [
    `https://r.jina.ai/${targetUrl}`,
    `https://r.jina.ai/${encodeURIComponent(targetUrl)}`,
  ];

  for (const jinaUrl of urlsToTry) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 28000);

    try {
      const res = await fetch(jinaUrl, {
        method: 'GET',
        headers,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        const rawText = await res.text();
        const clean = cleanMarkdownBoilerplate(rawText);

        if (!isAntiBotOrJunk(clean)) {
          return { success: true, text: clean };
        }
      }
    } catch {
      clearTimeout(timeoutId);
    }
  }

  return {
    success: false,
    reason: 'Client cloud fetch was restricted or link requires authentication',
  };
}

export default function ChatLinkStudio() {
  const studio = useHumanizeStudio('General Professional Writing', 'Natural');
  const [chatUrl, setChatUrl] = useState('');
  const [isFetching, setIsFetching] = useState(false);
  const [fetchProgress, setFetchProgress] = useState('');
  const [toast, setToast] = useState(null); // { type: 'error' | 'success', title: string, message: string, showClipboard?: boolean }
  const [blockedNotice, setBlockedNotice] = useState(null); // { platform: string, reason: string }
  const [autoRefine, setAutoRefine] = useState(true);
  const [detectedPlatform, setDetectedPlatform] = useState(null);
  const inputId = useId();

  const showToast = (type, title, message, showClipboard = false) => {
    setToast({ type, title, message, showClipboard });
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

  // 1-Click Clipboard Fallback: reads clipboard directly into input editor and triggers humanization
  const handlePasteFromClipboard = async () => {
    try {
      if (!navigator?.clipboard?.readText) {
        throw new Error('Clipboard API is not supported in this browser.');
      }
      const text = await navigator.clipboard.readText();
      const clean = text?.trim();
      if (!clean) {
        showToast(
          'error',
          'Clipboard Empty',
          'No text was found on your clipboard. Please copy your AI conversation text first, then click "Paste from Clipboard".'
        );
        return;
      }

      studio.setInput(clean);
      setBlockedNotice(null);
      setToast(null);

      showToast(
        'success',
        'Pasted from Clipboard',
        `Ingested ${clean.split(/\s+/).length} words from clipboard. Starting natural humanization...`
      );

      // Automatically trigger refinement if enabled
      // Automatically trigger refinement if enabled
      if (autoRefine) {
        setFetchProgress('Humanizing text naturally...');
        (async () => {
          try {
            studio.setBusy(true);
            studio.setOutput('');
            studio.setResult(null);
            const result = await humanizeText({
              text: clean,
              context: studio.context,
              tone: studio.tone,
              minimal_rewrite: studio.minimal,
            }, (chunkText) => {
              studio.setOutput(chunkText);
            });
            studio.setOutput(result.humanized_text);
            studio.setResult(result);
          } catch (err) {
            studio.setError(
              err.message || 'Text pasted, but refinement failed. Click "Humanize text" below to retry.'
            );
          } finally {
            studio.setBusy(false);
            setFetchProgress('');
          }
        })();
      }
    } catch {
      showToast(
        'error',
        'Clipboard Access Denied',
        'Browser permissions blocked automatic clipboard reading. Please click inside the editor and press Ctrl+V to paste manually.'
      );
      handleFocusEditor();
    }
  };

  // Platform detection for visual pill badge
  const handleUrlChange = (val) => {
    setChatUrl(val);
    const clean = val.trim().toLowerCase();
    if (clean.includes('chatgpt.com') || clean.includes('openai.com')) {
      setDetectedPlatform('ChatGPT');
    } else if (clean.includes('gemini.google.com') || clean.includes('g.co') || clean.includes('share.gemini.google')) {
      setDetectedPlatform('Gemini');
    } else if (clean.includes('claude.ai') || clean.includes('anthropic.com')) {
      setDetectedPlatform('Claude');
    } else if (clean.includes('perplexity.ai')) {
      setDetectedPlatform('Perplexity');
    } else if (clean.includes('deepseek.com')) {
      setDetectedPlatform('DeepSeek');
    } else if (clean.includes('huggingface.co')) {
      setDetectedPlatform('HuggingFace');
    } else if (clean.includes('youtube.com') || clean.includes('youtu.be')) {
      setDetectedPlatform('YouTube');
    } else {
      setDetectedPlatform(null);
    }
  };

  // Main 3-Tier Multi-Extraction Action
  async function handleFetchChat(urlOverride) {
    let targetUrl = (typeof urlOverride === 'string' ? urlOverride : chatUrl).trim();

    if (!targetUrl) {
      showToast(
        'error',
        'Link Required',
        'Please enter an AI chat share link to extract conversation text.'
      );
      return;
    }

    // Auto-prefix https:// if protocol is omitted
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      targetUrl = 'https://' + targetUrl;
    }

    try {
      new URL(targetUrl);
    } catch {
      showToast(
        'error',
        'Invalid URL Format',
        'Please enter a valid web URL (e.g. https://chatgpt.com/share/... or https://claude.ai/share/...).'
      );
      return;
    }

    const lowerTarget = targetUrl.toLowerCase();
    if (lowerTarget.includes('youtube.com') || lowerTarget.includes('youtu.be')) {
      showToast(
        'info',
        'YouTube Video Detected',
        'You entered a YouTube link! Please switch to the "YouTube Link" tab above for complete transcript extraction.'
      );
      return;
    }

    setToast(null);
    setBlockedNotice(null);
    studio.setError('');
    studio.setNotice('');
    studio.setOutput('');
    studio.setResult(null);
    setIsFetching(true);

    let extractedText = '';
    let resolvedPlatform = detectedPlatform || 'AI Chat';

    // ─────────────────────────────────────────────────────────────
    // FAST DIRECT CLOUD EXTRACTION (Backend Cascade with Direct SSR)
    // ─────────────────────────────────────────────────────────────
    setFetchProgress('Fetching conversation from link...');
    try {
      const backendData = await fetchChatLink(targetUrl);
      const rawBackendText = backendData.extracted_text || '';
      const cleanedBackendText = cleanMarkdownBoilerplate(rawBackendText);

      if (!cleanedBackendText || isAntiBotOrJunk(cleanedBackendText)) {
        throw new Error(
          'The conversation could not be extracted or requires login credentials. Please copy and paste the chat text directly.'
        );
      }

      extractedText = cleanedBackendText;
      if (backendData.platform) {
        resolvedPlatform = backendData.platform;
        setDetectedPlatform(backendData.platform);
      }
      if (backendData.warnings?.length) {
        studio.setNotice(backendData.warnings.join(' '));
      }
    } catch (backendError) {
      const rawErr = backendError?.message || '';
      let userFriendlyTitle = `${resolvedPlatform} Link Guidance`;
      let userFriendlyMessage = rawErr;

      if (rawErr.includes('Could not reach the HumanizeAI server')) {
        userFriendlyTitle = 'Backend Server Not Running';
        userFriendlyMessage =
          'Could not reach the HumanizeAI server. Please ensure the backend is running at http://localhost:8000.';
      } else if (rawErr.includes('expired') || rawErr.includes('removed') || rawErr.includes('not found') || rawErr.includes('404')) {
        userFriendlyTitle = `${resolvedPlatform} Link Expired or Unavailable`;
        userFriendlyMessage =
          'This shared conversation is expired, private, or was deleted by its author. Copy the conversation text and click "Paste from Clipboard".';
      }

      setBlockedNotice({
        platform: resolvedPlatform,
        title: userFriendlyTitle,
        reason: userFriendlyMessage,
        isBlocked: true,
      });

      setIsFetching(false);
      setFetchProgress('');
      return;
    }

    // ─────────────────────────────────────────────────────────────
    // TASK 4: Seamless UI Handoff & Auto-Refinement
    // ─────────────────────────────────────────────────────────────
    try {
      studio.setInput(extractedText);
      showToast(
        'success',
        `${resolvedPlatform} Text Ingested`,
        `Extracted ${extractedText.split(/\s+/).length} words. Ready to humanize.`
      );

      if (autoRefine) {
        setFetchProgress('Humanizing text naturally...');
        (async () => {
          try {
            studio.setBusy(true);
            studio.setOutput('');
            studio.setResult(null);
            const result = await humanizeText({
              text: extractedText,
              context: studio.context,
              tone: studio.tone,
              minimal_rewrite: studio.minimal,
            }, (chunkText) => {
              studio.setOutput(chunkText);
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
        })();
      }
    } finally {
      setIsFetching(false);
      setFetchProgress('');
    }
  }

  // Pre-fill sample shared links for testing and demos
  const handleUseSample = (type) => {
    let sample = '';
    if (type === 'chatgpt') {
      sample = 'https://chatgpt.com/s/t_6894038bb3d481919f367e49f310d1ca';
    } else {
      sample = 'https://gemini.google.com/share/9876543210ab';
    }
    setChatUrl(sample);
    handleUrlChange(sample);
  };

  // Top ingest slot component
  const chatLinkSlot = (
    <div className="chatlink-panel">
      {/* Toast Notification Error/Success Boundary with 1-Click Clipboard Fallback */}
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
            {toast.showClipboard && (
              <button
                type="button"
                className="toast-action-btn"
                onClick={handlePasteFromClipboard}
                title="Read text from clipboard and start humanization"
              >
                📋 Paste from Clipboard
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

      {/* Prominent Guidance Notice Card */}
      {blockedNotice && (
        <div className="chatlink-blocked-notice" role="alert">
          <div className="chatlink-blocked-content">
            <ShieldAlert size={20} className="chatlink-blocked-icon" />
            <div className="chatlink-blocked-text">
              <span className="chatlink-blocked-title">
                {blockedNotice.title || `${blockedNotice.platform} Link Notice`}
              </span>
              <span className="chatlink-blocked-desc">
                {blockedNotice.reason}
              </span>
            </div>
          </div>
          <div className="chatlink-blocked-actions">
            <button
              type="button"
              className="chatlink-blocked-paste-btn"
              onClick={handlePasteFromClipboard}
            >
              <Clipboard size={14} /> Paste from Clipboard
            </button>
            <button
              type="button"
              className="toast-close-btn"
              onClick={() => setBlockedNotice(null)}
              aria-label="Dismiss notice"
            >
              <X size={14} />
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
            placeholder="Paste any ChatGPT, Gemini, Claude, or AI share URL (http:// or https://)..."
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
          className="button secondary chatlink-clipboard-btn"
          onClick={handlePasteFromClipboard}
          title="Directly paste from clipboard and refine with 1 click"
        >
          <Clipboard size={14} /> Paste from Clipboard
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
          <span className="hint-label">Test with verified samples:</span>
          <button
            type="button"
            className="domain-chip sample-chip"
            onClick={() => handleUseSample('chatgpt')}
            title="Click to test with a verified live ChatGPT share link"
          >
            🐾 ChatGPT Live Sample
          </button>
          <span className="hint-label">Universal:</span>
          <span className="domain-chip">chatgpt.com/share/*</span>
          <span className="domain-chip">chatgpt.com/s/*</span>
          <span className="domain-chip">gemini.google.com/share/*</span>
          <span className="domain-chip">claude.ai/share/*</span>
        </div>

        <div className="chatlink-toggles">
          <label
            className="auto-refine-label"
            title="Automatically trigger natural refinement when text is fetched"
          >
            <input
              type="checkbox"
              checked={autoRefine}
              onChange={(e) => setAutoRefine(e.target.checked)}
            />
            <span>Auto-refine after fetch</span>
          </label>
        </div>
      </div>

      {/* Loading State: Skeleton Loader & Multi-Tier Status */}
      {isFetching && (
        <div className="chatlink-loading-state" role="status">
          <div className="loading-spinner-row">
            <LoaderCircle className="spin" size={18} />
            <span className="loading-text">{fetchProgress || 'Extracting conversation text...'}</span>
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
        setBlockedNotice(null);
        studio.clearAll();
      }}
      topSlot={chatLinkSlot}
      inputTitle="AI Chat Transcript Preview"
      placeholder="Paste any ChatGPT, Gemini, or Claude share link above and click 'Fetch Chat' to ingest, or use 'Paste from Clipboard'…"
    />
  );
}
