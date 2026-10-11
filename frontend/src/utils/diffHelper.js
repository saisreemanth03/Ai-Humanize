/**
 * Word-level diff calculation between source and target text.
 * Returns an array of chunks: { type: 'common' | 'added' | 'removed', text: string }
 */
export function computeWordDiff(source, target) {
  if (!source && !target) return [];
  if (!source) return [{ type: 'added', text: target }];
  if (!target) return [{ type: 'removed', text: source }];

  // Tokenize preserving whitespaces and punctuation
  const tokenize = (str) => {
    return str.match(/[\w'-]+|[^\w\s]+|\s+/g) || [];
  };

  const a = tokenize(source);
  const b = tokenize(target);

  // If either is very long (> 800 tokens), use a greedy chunked matching to avoid O(N*M) memory overhead
  if (a.length > 800 || b.length > 800) {
    return [
      { type: 'removed', text: source },
      { type: 'added', text: target }
    ];
  }

  // Classic LCS table
  const n = a.length;
  const m = b.length;
  const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));

  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      if (a[i - 1].toLowerCase() === b[j - 1].toLowerCase()) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to find diff chunks
  let i = n;
  let j = m;
  const rawDiff = [];

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && a[i - 1].toLowerCase() === b[j - 1].toLowerCase()) {
      // Unchanged / match (use target casing for humanized)
      rawDiff.push({ type: 'common', text: b[j - 1] });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      // Added in target
      rawDiff.push({ type: 'added', text: b[j - 1] });
      j--;
    } else if (i > 0 && (j === 0 || dp[i][j - 1] < dp[i - 1][j])) {
      // Removed from source
      rawDiff.push({ type: 'removed', text: a[i - 1] });
      i--;
    }
  }

  rawDiff.reverse();

  // Consolidate adjacent items with same type
  const consolidated = [];
  for (const item of rawDiff) {
    if (!item.text) continue;
    if (consolidated.length && consolidated[consolidated.length - 1].type === item.type) {
      consolidated[consolidated.length - 1].text += item.text;
    } else {
      consolidated.push({ ...item });
    }
  }

  return consolidated;
}
