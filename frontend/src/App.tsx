import { useEffect, useMemo, useState } from "react";
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
                onUploadStart={() => { }}
                onUploadComplete={() => { }}
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

