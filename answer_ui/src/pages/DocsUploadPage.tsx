import { useMemo, useState } from "react";
import { getApiBases, postForm } from "../api/client";
import PdfPicker from "../components/PdfPicker";
import LoadingOverlay from "../components/LoadingOverlay";

type UploadResp = { inserted_document_ids: number[]; received: number };

export default function DocsUploadPage() {
  const { docApiBase } = getApiBases();
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<UploadResp | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Computed once per base URL change so UI always points to the active backend.
  const uploadUrl = useMemo(() => `${docApiBase}/api/documents/upload`, [docApiBase]);

  async function onSubmit() {
    setErr(null);
    setResult(null);
    if (!files.length) {
      setErr("Pick one or more PDF files.");
      return;
    }
    const form = new FormData();
    for (const f of files) form.append("documents", f, f.name);

    setBusy(true);
    try {
      // Backend handles per-document dedupe/chunk/embed; UI just submits selected files.
      const resp = await postForm<UploadResp>(uploadUrl, form);
      setResult(resp);
      setFiles([]); // clear selected files; success banner stays visible
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <LoadingOverlay message="Ingesting company documents..." visible={busy} />
      <h1 className="h1">Upload company documents</h1>
      <p className="muted">Sends PDFs to the document ingestion API for chunking + embedding.</p>

      <div className="form">
        <PdfPicker
          mode="multi"
          helper="Select multiple PDFs. You can drag-and-drop, remove individual files, or clear the whole set."
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
          <div className="alert__title">Upload complete</div>
          <div className="alert__body">
            Inserted document IDs: <code>{JSON.stringify(result.inserted_document_ids)}</code>
          </div>
        </div>
      ) : null}
    </section>
  );
}
