import { useState } from "react";
import type { AskResponse } from "../types";

interface ChatInterfaceProps {
  onAsk: (question: string) => Promise<void>;
  isAsking: boolean;
  result: AskResponse | null;
  selectedDocCount: number;
}

export function ChatInterface({ onAsk, isAsking, result, selectedDocCount }: ChatInterfaceProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isAsking && selectedDocCount > 0) {
      onAsk(input);
    }
  };

  return (
    <div className="chat-container glass-panel">

      <div className="chat-content">
        {!result && !isAsking && (
          <div className="empty-chat">
            <div className="logo-placeholder">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeOpacity="0.5">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 16v-4M12 8h.01"></path>
              </svg>
            </div>
            <h3>Sisteme Hoş Geldiniz</h3>
            <p>Analiz etmek istediğiniz belgeleri soldan seçin ve sorunuzu aşağıya yazın.</p>
          </div>
        )}

        {isAsking && (
          <div className="thinking-state">
            <div className="scanner"></div>
            <p>Belgeler taranıyor ve anlamlandırılıyor...</p>
          </div>
        )}

        {result && !isAsking && (
          <div className="result-card">
            <div className={`confidence-badge ${result.confidence > 0.7 ? "high" : "low"}`}>
              Güven Skoru: %{(result.confidence * 100).toFixed(0)}
            </div>

            <div className="answer-text">
              {result.answer}
            </div>

            {result.citations.length > 0 && (
              <div className="citations-grid">
                <h4>Referanslar (Citations)</h4>
                <div className="cards">
                  {result.citations.map((cit, idx) => (
                    <div key={idx} className="citation-card">
                      <div className="cit-header">
                        <span className="cit-file">{cit.filename}</span>
                        {cit.page && <span className="cit-page">Sayfa {cit.page}</span>}
                      </div>
                      <p className="cit-snippet">"...{cit.snippet}..."</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="input-area">
        <input
          type="text"
          className="input-field"
          placeholder={selectedDocCount > 0 ? "Sorunuzu buraya yazın..." : "Lütfen önce belge seçin"}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isAsking || selectedDocCount === 0}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!input.trim() || isAsking || selectedDocCount === 0}
        >
          {isAsking ? "..." : "Gönder"}
        </button>
      </form>

      <style>{`
        .chat-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          border-radius: var(--radius-lg);
          overflow: hidden;
          position: relative; /* Ensure positioning context */
        }
        .chat-content {
          flex: 1;
          padding: 2rem;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          /* Removed justify-content: center to fix scrolling issue */
          min-height: 0; /* Critical for nested flex scrolling */
        }
        .empty-chat {
          text-align: center;
          color: var(--color-text-muted);
          margin: auto; /* Center the empty state */
        }
        .logo-placeholder {
          margin-bottom: 1rem;
          color: var(--color-primary);
        }
        
        .thinking-state {
          text-align: center;
          animation: fadeIn 0.5s ease;
          margin: auto;
        }
        .scanner {
          height: 2px;
          width: 100%;
          max-width: 300px;
          background: var(--color-primary);
          box-shadow: 0 0 10px var(--color-primary);
          margin: 0 auto 1.5rem;
          animation: shimmer 2s infinite ease-in-out;
        }

        .result-card {
          background: rgba(255, 255, 255, 0.05);
          padding: 1.5rem;
          border-radius: var(--radius-md);
          border: 1px solid var(--color-border);
          animation: fadeIn 0.4s ease-out;
        }
        .confidence-badge {
          display: inline-block;
          font-size: 0.75rem;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          margin-bottom: 1rem;
          background: rgba(0, 0, 0, 0.3);
          border: 1px solid var(--color-border);
        }
        .confidence-badge.high { color: var(--color-success); border-color: var(--color-success); }
        .confidence-badge.low { color: var(--color-warning); border-color: var(--color-warning); }

        .answer-text {
          font-size: 1.1rem;
          line-height: 1.6;
          margin-bottom: 2rem;
          word-wrap: break-word; /* Prevent long words breaking layout */
        }
        
        .citations-grid h4 {
          font-size: 0.9rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--color-text-muted);
          margin-bottom: 1rem;
        }
        .cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
        }
        .citation-card {
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid var(--color-border);
          padding: 0.8rem;
          border-radius: var(--radius-sm);
          font-size: 0.85rem;
          overflow: hidden; /* Contain overflow */
        }
        .cit-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.5rem;
          color: var(--color-primary);
          font-weight: 500;
        }
        .cit-file, .cit-page {
           white-space: nowrap;
           overflow: hidden;
           text-overflow: ellipsis;
        }
        .cit-file {
           max-width: 70%;
        }
        .cit-snippet {
          margin: 0;
          color: var(--color-text-muted);
          font-style: italic;
          display: -webkit-box;
          -webkit-line-clamp: 4; /* Limit lines */
          -webkit-box-orient: vertical;
          overflow: hidden;
          word-break: break-word;
        }

        .input-area {
          padding: 1.5rem;
          background: rgba(13, 22, 35, 0.95); /* More solid background */
          display: flex;
          gap: 1rem;
          border-top: 1px solid var(--color-border);
          z-index: 10;
        }
      `}</style>
    </div>
  );
}
