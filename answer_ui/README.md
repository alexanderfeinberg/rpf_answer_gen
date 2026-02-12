# Answer UI

React SPA (Vite + TypeScript) for uploading documents/RFPs and checking API health.

## Configure

Set API bases via Vite env:

```bash
export VITE_DOC_API_BASE=http://localhost:9001
export VITE_ANSWER_API_BASE=http://localhost:9000
```

## Run

```bash
cd answer_ui
npm install
npm run dev
```

## Notes

Vite 5 expects Node 18+. This project is pinned to Vite 4 for compatibility with Node 16.
