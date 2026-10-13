import { useState } from 'react';
import { humanizeText } from '../services/api';
import { CONTEXTS, TONES } from './constants';

export function useHumanizeStudio(defaultContext = CONTEXTS[0], defaultTone = TONES[0]) {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [context, setContext] = useState(defaultContext);
  const [tone, setTone] = useState(defaultTone);
  const [minimal, setMinimal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [result, setResult] = useState(null);

  async function runHumanize() {
    if (!input.trim()) {
      setError('Please add or transcribe some text before humanizing.');
      return;
    }
    setBusy(true);
    setError('');
    setNotice('');
    setOutput('');
    setResult(null);
    try {
      const data = await humanizeText(
        {
          text: input,
          context,
          tone,
          minimal_rewrite: minimal
        },
        (chunkText) => {
          setOutput(chunkText);
        }
      );
      setOutput(data.humanized_text);
      setResult(data);
    } catch (e) {
      setError(e.message || 'An error occurred during humanization.');
    } finally {
      setBusy(false);
    }
  }

  function clearAll() {
    setInput('');
    setOutput('');
    setResult(null);
    setError('');
    setNotice('');
  }

  return {
    input,
    setInput,
    output,
    setOutput,
    context,
    setContext,
    tone,
    setTone,
    minimal,
    setMinimal,
    busy,
    setBusy,
    transcribing,
    setTranscribing,
    error,
    setError,
    notice,
    setNotice,
    result,
    setResult,
    runHumanize,
    clearAll
  };
}
