import StudioWorkspace from '../../components/StudioWorkspace';
import { useHumanizeStudio } from '../../utils/useHumanizeStudio';

export default function TextStudio() {
  const studio = useHumanizeStudio();

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
      onClear={studio.clearAll}
      inputTitle="Write or paste your text"
      placeholder="Paste recruiter feedback, interview question drafts, evaluation summaries, or any AI text to humanize…"
    />
  );
}
