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
export const humanizeText = (data) => request('/api/humanize', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) });
export const extractDocument = (file) => { const data = new FormData(); data.append('file',file); return request('/api/extract-document',{method:'POST',body:data}); };
export const extractMedia = (file) => { const data = new FormData(); data.append('file',file); return request('/api/extract-media',{method:'POST',body:data}); };
export const extractYouTube = (url) => request('/api/extract-youtube', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ url }) });
export const fetchChatLink = (url) => request('/api/fetch-chat-link', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ url }) });
export const fetchAiLink = (url) => request('/api/fetch-ai-link', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ url }) });
export const analyzeRobotic = (text) => request('/api/analyze-robotic', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ text }) });

