import { useEffect, useMemo, useState } from "react";
import { askQuestion, fetchDocuments, uploadDocuments } from "./api";
import type { AskResponse, DocumentSummary, UploadResponse } from "./types";

function toLocalDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.valueOf())) {
    return iso;
  }
  return date.toLocaleString("tr-TR");
}

function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [question, setQuestion] = useState("");

  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [qaResult, setQaResult] = useState<AskResponse | null>(null);

  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const indexedDocuments = useMemo(
    () => documents.filter((doc) => doc.status === "indexed"),
    [documents],
  );

  async function refreshDocuments(): Promise<void> {
    try {
      setLoadingDocuments(true);
      const response = await fetchDocuments();
      setDocuments(response);
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setLoadingDocuments(false);
    }
  }

  useEffect(() => {
    void refreshDocuments();
  }, []);

  async function handleUpload(): Promise<void> {
    if (!selectedFiles.length) {
      setErrorMessage("Lutfen en az bir dosya secin.");
      return;
    }

    setErrorMessage(null);
    setUploadResult(null);

    try {
      setUploading(true);
      const result = await uploadDocuments(selectedFiles);
      setUploadResult(result);
      setSelectedFiles([]);
      await refreshDocuments();
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk(): Promise<void> {
    if (!question.trim()) {
      setErrorMessage("Soru alani bos birakilamaz.");
      return;
    }

    if (!selectedDocumentIds.length) {
      setErrorMessage("Soru icin en az bir indexed belge secin.");
      return;
    }

    setErrorMessage(null);
    setQaResult(null);

    try {
      setAsking(true);
      const result = await askQuestion({
        question: question.trim(),
        document_ids: selectedDocumentIds,
      });
      setQaResult(result);
    } catch (error) {
      setErrorMessage((error as Error).message);
    } finally {
      setAsking(false);
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="badge">TUSAS Case Study MVP</p>
        <h1>Belge Analiz ve Soru-Cevap Sistemi</h1>
        <p>
          PDF/JPG/PNG dosyalari yukleyin, sistem metinleri indexlesin ve dogal dil
          sorularinizi belge baglamina dayali yanitlasin.
        </p>
      </section>

      {errorMessage && <div className="alert error">Hata: {errorMessage}</div>}

      <section className="panel">
        <header>
          <h2>1) Belge Yukleme</h2>
          <p>Desteklenen formatlar: PDF, JPG, PNG</p>
        </header>

        <div className="upload-row">
          <input
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={(event) => {
              const picked = event.target.files ? Array.from(event.target.files) : [];
              setSelectedFiles(picked);
            }}
          />
          <button type="button" disabled={uploading} onClick={() => void handleUpload()}>
            {uploading ? "Yukleniyor..." : "Dosyalari Yukle"}
          </button>
        </div>

        {selectedFiles.length > 0 && (
          <ul className="compact-list">
            {selectedFiles.map((file) => (
              <li key={`${file.name}-${file.size}`}>{file.name}</li>
            ))}
          </ul>
        )}

        {uploadResult && (
          <div className="result-grid">
            <article>
              <h3>Kabul Edilenler</h3>
              <ul className="compact-list">
                {uploadResult.accepted_files.length === 0 && <li>-</li>}
                {uploadResult.accepted_files.map((item) => (
                  <li key={item.document_id}>
                    {item.filename} ({item.status})
                  </li>
                ))}
              </ul>
            </article>
            <article>
              <h3>Reddedilenler</h3>
              <ul className="compact-list">
                {uploadResult.rejected_files.length === 0 && <li>-</li>}
                {uploadResult.rejected_files.map((item) => (
                  <li key={`${item.filename}-${item.reason}`}>
                    {item.filename}: {item.reason}
                  </li>
                ))}
              </ul>
            </article>
          </div>
        )}
      </section>

      <section className="panel">
        <header>
          <h2>2) Belge Listesi</h2>
          <button type="button" className="ghost" onClick={() => void refreshDocuments()}>
            {loadingDocuments ? "Yenileniyor..." : "Yenile"}
          </button>
        </header>

        <div className="doc-grid">
          {documents.length === 0 && <p>Henuz belge yok.</p>}
          {documents.map((doc) => {
            const isChecked = selectedDocumentIds.includes(doc.id);
            const canSelect = doc.status === "indexed";

            return (
              <label key={doc.id} className={`doc-card ${canSelect ? "" : "disabled"}`}>
                <input
                  type="checkbox"
                  disabled={!canSelect}
                  checked={isChecked}
                  onChange={(event) => {
                    if (event.target.checked) {
                      setSelectedDocumentIds((prev) => [...prev, doc.id]);
                    } else {
                      setSelectedDocumentIds((prev) => prev.filter((id) => id !== doc.id));
                    }
                  }}
                />
                <div>
                  <strong>{doc.filename}</strong>
                  <p>ID: {doc.id.slice(0, 12)}...</p>
                  <p>Tip: {doc.file_type.toUpperCase()}</p>
                  <p>Dil: {doc.language}</p>
                  <p>Durum: {doc.status}</p>
                  <p>Olusturma: {toLocalDate(doc.created_at)}</p>
                </div>
              </label>
            );
          })}
        </div>
      </section>

      <section className="panel">
        <header>
          <h2>3) Soru-Cevap</h2>
          <p>Yalnizca indexed belgeler secilebilir.</p>
        </header>

        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ornek: Belgede TUSAS merkezinin hangi sehirde oldugu yaziyor mu?"
          rows={5}
        />

        <button type="button" disabled={asking} onClick={() => void handleAsk()}>
          {asking ? "Sorgulaniyor..." : "Soru Sor"}
        </button>

        {qaResult && (
          <article className="qa-result">
            <div className="mode-line">
              <span className={`mode ${qaResult.mode}`}>{qaResult.mode}</span>
              <span>Confidence: {qaResult.confidence}</span>
              <span>Used Chunks: {qaResult.used_chunks}</span>
            </div>
            <p className="answer">{qaResult.answer}</p>

            <h3>Citations</h3>
            <ul className="compact-list">
              {qaResult.citations.length === 0 && <li>-</li>}
              {qaResult.citations.map((citation) => (
                <li key={citation.chunk_id}>
                  <strong>{citation.filename}</strong>
                  {citation.page ? ` (sayfa ${citation.page})` : ""} - {citation.snippet}
                </li>
              ))}
            </ul>
          </article>
        )}
      </section>
    </main>
  );
}

export default App;
