import { useMemo, useRef, useState } from "react";

type Props = {
  mode: "single" | "multi";
  label: string;
  helper?: string;
  files: File[];
  onChange: (files: File[]) => void;
};

function formatBytes(n: number): string {
  const units = ["B", "KB", "MB", "GB"];
  let x = n;
  let i = 0;
  while (x >= 1024 && i < units.length - 1) {
    x /= 1024;
    i += 1;
  }
  return `${x.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function isPdfFile(f: File): boolean {
  // Browser-provided MIME is often correct; fall back to extension.
  if (f.type === "application/pdf") return true;
  return f.name.toLowerCase().endsWith(".pdf");
}

function dedupe(inFiles: File[]): File[] {
  const seen = new Set<string>();
  const out: File[] = [];
  for (const f of inFiles) {
    const k = `${f.name}::${f.size}::${f.lastModified}`;
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(f);
  }
  return out;
}

export default function PdfPicker({ mode, label, helper, files, onChange }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [hasRejectedSelection, setHasRejectedSelection] = useState(false);

  const pdfFiles = useMemo(() => files.filter(isPdfFile), [files]);

  function resetInput() {
    // Allow re-selecting the same filename (browser won't fire change if value doesn't change).
    if (inputRef.current) inputRef.current.value = "";
  }

  function addFiles(list: FileList | null) {
    if (!list) return;
    const next = Array.from(list);
    const onlyPdf = next.filter(isPdfFile);
    const hasNonPdf = next.length !== onlyPdf.length;
    setHasRejectedSelection(hasNonPdf);

    if (hasNonPdf) {
      // Reject the whole selection if any file is not a PDF.
      resetInput();
      return;
    }

    if (mode === "single") {
      onChange(onlyPdf.slice(0, 1));
      resetInput();
      return;
    }
    onChange(dedupe([...pdfFiles, ...onlyPdf]));
    resetInput();
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    addFiles(e.dataTransfer.files);
  }

  return (
    <div className="picker">
      <div className="picker__header">
        <div>
          <div className="picker__label">{label}</div>
          {helper ? <div className="picker__helper">{helper}</div> : null}
        </div>
        <div className="picker__actions">
          <button className="btn btn--ghost" type="button" onClick={() => inputRef.current?.click()}>
            Choose file{mode === "multi" ? "s" : ""}
          </button>
          {pdfFiles.length ? (
            <button
              className="btn btn--ghost"
              type="button"
              onClick={() => {
                onChange([]);
                setHasRejectedSelection(false);
                resetInput();
              }}
            >
              Clear
            </button>
          ) : null}
        </div>
      </div>

      <input
        ref={inputRef}
        className="picker__input"
        type="file"
        accept="application/pdf"
        multiple={mode === "multi"}
        onChange={(e) => addFiles(e.target.files)}
      />

      <div
        className={`drop ${dragOver ? "drop--over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onClick={() => inputRef.current?.click()}
      >
        <div className="drop__title">Drop PDFs here</div>
        <div className="drop__sub">or click to browse</div>
      </div>

      {hasRejectedSelection ? (
        <div className="alert alert--error">
          <div className="alert__title">Upload rejected</div>
          <div className="alert__body">
            We only support PDF uploads.
          </div>
        </div>
      ) : null}

      {pdfFiles.length ? (
        <div className="gallery">
          {pdfFiles.map((f) => (
            <div key={`${f.name}-${f.size}-${f.lastModified}`} className="pdfcard">
              <div className="pdfcard__icon" aria-hidden="true">
                PDF
              </div>
              <div className="pdfcard__meta">
                <div className="pdfcard__name" title={f.name}>
                  {f.name}
                </div>
                <div className="pdfcard__sub">
                  {formatBytes(f.size)} · {new Date(f.lastModified).toLocaleString()}
                </div>
              </div>
              <button
                className="pdfcard__rm"
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onChange(pdfFiles.filter((x) => x !== f));
                  resetInput();
                }}
                aria-label={`Remove ${f.name}`}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="muted small">No PDFs selected yet.</div>
      )}
    </div>
  );
}
