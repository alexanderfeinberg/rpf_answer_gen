import { Link, Route, Routes } from "react-router-dom";
import DocsUploadPage from "./pages/DocsUploadPage";
import RfpUploadPage from "./pages/RfpUploadPage";

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand__mark" aria-hidden="true" />
          <div className="brand__text">
            <div className="brand__title">Answer UI</div>
            <div className="brand__subtitle">RFP ingestion and Q/A playground</div>
          </div>
        </div>
        <nav className="nav">
          <Link className="nav__link" to="/documents">
            Documents
          </Link>
          <Link className="nav__link" to="/rfp">
            RFP
          </Link>
        </nav>
      </header>

      <main className="main">
        {/* Route-level separation: document ingestion flow and RFP/answers flow. */}
        <Routes>
          <Route path="/" element={<DocsUploadPage />} />
          <Route path="/documents" element={<DocsUploadPage />} />
          <Route path="/rfp" element={<RfpUploadPage />} />
        </Routes>
      </main>

      <footer className="footer">
        <div className="footer__hint">
          Configure API bases via <code>VITE_DOC_API_BASE</code> and <code>VITE_ANSWER_API_BASE</code>.
        </div>
      </footer>
    </div>
  );
}
