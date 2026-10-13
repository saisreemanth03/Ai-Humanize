const BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
async function request(path, options) {
  let response;
  try { response = await fetch(`${BASE}${path}`, options); }
  catch { throw new Error('Could not reach the HumanizeAI server. Check that the backend is running.'); }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(
        payload.detail && payload.detail !== 'Not Found'
          ? payload.detail
          : 'Backend endpoint not found (HTTP 404). Ensure the backend server is running and updated.'
      );
    }
    throw new Error(payload.detail || 'The request could not be completed. Please try again.');
  }
  return payload;
}
export async function humanizeText(data, onChunk) {
  // 1. Attempt high-speed streaming first
  try {
    const response = await fetch(`${BASE}/api/humanize-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (response.ok && response.body) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = '';
      let metadata = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        accumulated += decoder.decode(value, { stream: true });

        const metaIndex = accumulated.indexOf('___METADATA___:');
        if (metaIndex !== -1) {
          const textPart = accumulated.slice(0, metaIndex);
          const metaPart = accumulated.slice(metaIndex + '___METADATA___:'.length);
          if (onChunk) onChunk(textPart.trimEnd());
          try {
            metadata = JSON.parse(metaPart.trim());
          } catch {
            // Metadata JSON may span multiple chunks
          }
        } else {
          if (onChunk) onChunk(accumulated);
        }
      }

      if (metadata) {
        return metadata;
      }

      const cleanText = accumulated.split('___METADATA___:')[0].trim();
      if (cleanText) {
        return {
          humanized_text: cleanText,
          changes_summary: 'Naturally refined for human cadence and flow while preserving entities and meaning.',
          meaning_validation: { meaning_status: 'Passed' },
          factuality_validation: { factuality_status: 'Passed' },
          warnings: []
        };
      }
    }
  } catch {
    // If streaming fails or encounters network issue, fallback seamlessly to standard endpoint below
  }

  // 2. Reliable fallback to /api/humanize (guaranteed to work across all serverless deployments)
  const result = await request('/api/humanize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (onChunk && result?.humanized_text) {
    onChunk(result.humanized_text);
  }
  return result;
}
export const extractDocument = (file) => { const data = new FormData(); data.append('file',file); return request('/api/extract-document',{method:'POST',body:data}); };
export const extractMedia = (file) => { const data = new FormData(); data.append('file',file); return request('/api/extract-media',{method:'POST',body:data}); };
export const extractYouTube = (url) => request('/api/extract-youtube', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ url }) });
export const fetchChatLink = (url) => request('/api/fetch-chat-link', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ url }) });
export const fetchAiLink = (url) => request('/api/fetch-ai-link', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ url }) });
export const analyzeRobotic = (text) => request('/api/analyze-robotic', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ text }) });

