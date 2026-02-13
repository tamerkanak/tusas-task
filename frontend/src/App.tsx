import { useEffect, useState } from "react";
import { askQuestion, fetchDocuments, uploadDocuments } from "./api";
import type { AskResponse, DocumentSummary, UploadResponse } from "./types";

import { DocumentList } from "./components/DocumentList";
import { UploadArea } from "./components/UploadArea";
import { ChatInterface } from "./components/ChatInterface";

function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);

  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [qaResult, setQaResult] = useState<AskResponse | null>(null);

  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
    if (!selectedFiles.length) return;

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

  async function handleAsk(question: string): Promise<void> {
    if (!selectedDocumentIds.length) {
      setErrorMessage("Soru sormak için en az bir belge seçmelisiniz.");
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

  const toggleDocumentSelect = (id: string) => {
    setSelectedDocumentIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  return (
    <div className="app-container">
      <DocumentList
        documents={documents}
        selectedIds={selectedDocumentIds}
        onToggleSelect={toggleDocumentSelect}
        isLoading={loadingDocuments}
        onRefresh={() => void refreshDocuments()}
      />

      <main className="main-content">
        <header className="top-bar">
          <div className="brand">
            <h1>TUSAŞ <span className="highlight">Analiz</span></h1>
            <p className="subtitle">Yapay Zeka Destekli Belge Asistanı</p>
          </div>
        </header>

        <div className="workspace">
          {errorMessage && (
            <div className="error-banner">
              ⚠️ {errorMessage}
              <button onClick={() => setErrorMessage(null)}>✕</button>
            </div>
          )}

          <div className="workspace-grid">
            <section className="upload-section">
              <UploadArea
                selectedFiles={selectedFiles}
                onError={(msg) => setErrorMessage(msg)}
                isUploading={uploading}
                onFilesSelected={(files) => setSelectedFiles(files)}
              />

              {selectedFiles.length > 0 && !uploading && (
                <button
                  className="btn btn-primary start-upload-btn"
                  onClick={() => void handleUpload()}
                >
                  Yüklemeyi Başlat
                </button>
              )}

              {uploadResult && (
                <div className="upload-result glass-panel">
                  <div className="upload-result-header">
                    <span>Son yükleme</span>
                    <span className="upload-result-metrics">
                      <span className="ok">✅ {uploadResult.accepted_files.length} kabul</span>
                      <span className="bad">❌ {uploadResult.rejected_files.length} red</span>
                    </span>
                  </div>

                  {uploadResult.rejected_files.length > 0 && (
                    <ul className="upload-rejections">
                      {uploadResult.rejected_files.map((f, i) => (
                        <li key={`${f.filename}-${i}`}>
                          <span className="file">{f.filename}</span>: {f.reason}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </section>

            <section className="chat-section">
              <ChatInterface
                onAsk={handleAsk}
                isAsking={asking}
                result={qaResult}
                selectedDocCount={selectedDocumentIds.length}
              />
            </section>
          </div>
        </div>
      </main>

      <style>{`
        .main-content {
          display: flex;
          flex-direction: column;
          height: 100vh;
          overflow: hidden;
          padding: 1.5rem;
          gap: 1.5rem;
        }
        .top-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .brand h1 {
          margin: 0;
          font-weight: 700;
          letter-spacing: -0.05em;
        }
        .highlight {
          color: var(--color-primary);
        }
        .subtitle {
          margin: 0;
          font-size: 0.8rem;
          color: var(--color-text-muted);
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }
        .workspace {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 1rem;
          overflow: hidden;
        }
        .workspace-grid {
          display: grid;
          grid-template-rows: auto 1fr;
          gap: 1.5rem;
          height: 100%;
          min-height: 0; /* Ensure grid itself doesn't overflow */
        }
        .upload-section {
           min-height: 0;
           display: flex;
           flex-direction: column;
        }
        .chat-section {
           min-height: 0; /* Critical for grid item scrolling */
           overflow: hidden;
           display: flex;
           flex-direction: column;
        }
        .error-banner {
          background: rgba(239, 68, 68, 0.2);
          border: 1px solid var(--color-error);
          padding: 0.8rem;
          border-radius: var(--radius-md);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
         .start-upload-btn {
           margin-top: 1rem;
           width: 100%;
           justify-content: center;
           animation: fadeIn 0.3s;
         }
         .upload-result {
           margin-top: 1rem;
           padding: 1rem;
         }
         .upload-result-header {
           display: flex;
           justify-content: space-between;
           align-items: center;
           margin-bottom: 0.75rem;
           color: var(--color-text-muted);
           font-size: 0.85rem;
           text-transform: uppercase;
           letter-spacing: 0.06em;
         }
         .upload-result-metrics {
           display: flex;
           gap: 0.75rem;
         }
         .upload-result .ok { color: var(--color-success); }
         .upload-result .bad { color: var(--color-error); }
         .upload-rejections {
           margin: 0;
           padding-left: 1.2rem;
           font-size: 0.9rem;
           color: var(--color-text-muted);
         }
         .upload-rejections li {
           margin: 0.25rem 0;
         }
         .upload-rejections .file {
           color: var(--color-text);
           font-weight: 600;
         }
         
         @media (min-width: 1200px) {
            .workspace-grid {
              grid-template-columns: 350px 1fr;
             grid-template-rows: 1fr;
           }
        }
      `}</style>
    </div>
  );
}

export default App;
