import { useMemo, useState } from "react";
import { getApiBases, postForm, postJson } from "../api/client";
import PdfPicker from "../components/PdfPicker";
import LoadingOverlay from "../components/LoadingOverlay";

type UploadResp = { rfp_id: number };
type AnswerDict = {
  id: number;
  content: string;
  created_at: string | null;
  question_id: number;
  answer_version_id: number | null;
};

type BulkAnswersResp = {
  rfp_id: number;
  questions: { id: number; content: string; answers: AnswerDict[] }[];
};

export default function RfpUploadPage() {
  const { docApiBase, answerApiBase } = getApiBases();
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<UploadResp | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [genBusy, setGenBusy] = useState(false);
  const [genErr, setGenErr] = useState<string | null>(null);
  const [answers, setAnswers] = useState<BulkAnswersResp | null>(null);

  // Keep endpoint wiring local to the page so env/base changes are reflected immediately.
  const uploadUrl = useMemo(() => `${docApiBase}/api/rfp/upload`, [docApiBase]);
  const bulkAnswersUrl = useMemo(
    () => `${answerApiBase}/api/answers/bulk-generate`,
    [answerApiBase],
  );

  async function onSubmit() {
    setErr(null);
    setResult(null);
    setGenErr(null);
    setAnswers(null);
    const file = files[0] || null;
    if (!file) {
      setErr("Pick a PDF file.");
      return;
    }
    const form = new FormData();
    form.append("rfp", file, file.name);

    setBusy(true);
    try {
      // Step 1: upload and parse RFP into stored questions.
      const resp = await postForm<UploadResp>(uploadUrl, form);
      setResult(resp);
      setFiles([]); // clear the picker after success

      // Immediately generate answers for the ingested RFP.
      setGenBusy(true);
      try {
        // Step 2: trigger bulk generation for all unanswered questions in that RFP.
        const bulk = await postJson<BulkAnswersResp>(bulkAnswersUrl, { rfp_id: resp.rfp_id });
        setAnswers(bulk);
      } catch (e) {
        setGenErr(e instanceof Error ? e.message : String(e));
      } finally {
        setGenBusy(false);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <LoadingOverlay
        message={busy ? "Extracting questions from RFP document..." : "Generating answers for RFP..."}
        visible={busy || genBusy}
      />
      <h1 className="h1">Upload an RFP</h1>
      <p className="muted">Parses questions via LLM and writes them to the DB.</p>

      <div className="form">
        <PdfPicker
          mode="single"
          label="RFP upload"
          helper="Select the RFP PDF. The backend extracts questions and stores them in the database."
          files={files}
          onChange={setFiles}
        />

        <div className="actions">
          <button className="btn" onClick={onSubmit} disabled={busy}>
            {busy ? "Uploading..." : "Upload"}
          </button>
          <div className="muted small">
            POST <code>{uploadUrl}</code>
          </div>
        </div>
      </div>

      {err ? (
        <div className="alert alert--error">
          <div className="alert__title">Upload failed</div>
          <div className="alert__body">{err}</div>
        </div>
      ) : null}

      {result ? (
        <div className="alert alert--ok">
          <div className="alert__title">RFP ingested</div>
          <div className="alert__body">
            RFP id: <code>{result.rfp_id}</code>
          </div>
        </div>
      ) : null}

      {genErr ? (
        <div className="alert alert--error">
          <div className="alert__title">Answer generation failed</div>
          <div className="alert__body">{genErr}</div>
        </div>
      ) : null}

      {answers ? (
        <div className="qa">
          <div className="actions">
            <h2 className="h2">Generated answers</h2>
            <button
              className="btn btn--ghost"
              type="button"
              onClick={() => {
                setAnswers(null);
                setGenErr(null);
              }}
            >
              Clear answers
            </button>
          </div>
          <div className="muted small">
            POST <code>{bulkAnswersUrl}</code>
          </div>
          <div className="qa__list">
            {answers.questions.map((q) => (
              <div key={q.id} className="qa__item card">
                <div className="qa__q">
                  <div className="qa__label">Question</div>
                  <div className="qa__text">{q.content}</div>
                </div>
                <div className="qa__a">
                  <div className="qa__label">Answer</div>
                  {q.answers.length ? (
                    q.answers.map((a) => (
                      <div key={a.id} className="qa__text">
                        {a.content}
                      </div>
                    ))
                  ) : (
                    <div className="muted small">No answer generated.</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
