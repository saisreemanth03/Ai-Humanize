export const CONTEXTS = [
  'Recruiter Feedback & Rejection Emails',
  'Candidate Communication & Offer Letters',
  'Adaptive Interview Question Refinement',
  'Candidate Evaluation Summaries & Reports',
  'General Professional Writing',
  'Audio / Video Transcript & Spoken Dialogue'
];

export const TONES = ['Natural', 'Professional', 'Conversational', 'Polished', 'Concise'];

export const ROBOTIC_PATTERNS = [
  'delve into', 'delving into', 'can you delve into', 'testament to', 'stands as a testament',
  'rich tapestry', 'tapestry', 'in summary', 'in conclusion', 'to summarize',
  'pivotal role', 'pivotal', 'beacon of', 'beacon', 'furthermore', 'moreover',
  'it is worth noting', 'it should be noted', 'embark on', 'embark upon', 'foster',
  'streamline', 'leverage', 'vital role', 'crucial role', 'game-changer', 'plethora',
  'myriad', 'multifaceted', 'underpins', 'intertwined', 'unwavering', 'deep dive',
  'harness the power of', 'meticulous', 'commendable'
];

export function analyzeClientText(text) {
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

export function cleanTranscriptNoise(text) {
  if (!text) return '';
  return text
    .replace(/(?:^|\n|\s)\d{1,2}:\d{2}(?::\d{2})?\s*/g, ' ')
    .replace(/\[(?:music|crying|applause|laughter|cheering|sniffling|coughing|sighs?|gasp|groans?|inaudible)\]\s*/gi, '')
    .replace(/>\s*>\s*/g, ' ')
    .replace(/\b[A-Z]{2,}\b/g, (w) => (['API', 'SQL', 'AWS', 'GPA', 'HTML', 'CSS', 'REST'].includes(w) ? w : w.charAt(0) + w.slice(1).toLowerCase()))
    .replace(/\s+/g, ' ')
    .trim();
}

export const countWords = (s) => (s && s.trim() ? s.trim().split(/\s+/).length : 0);
