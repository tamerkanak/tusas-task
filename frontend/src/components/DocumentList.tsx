import type { DocumentSummary } from "../types";

interface DocumentListProps {
    documents: DocumentSummary[];
    selectedIds: string[];
    onToggleSelect: (id: string) => void;
    isLoading: boolean;
    onRefresh: () => void;
}

export function DocumentList({
    documents,
    selectedIds,
    onToggleSelect,
    isLoading,
    onRefresh,
}: DocumentListProps) {
    return (
        <aside className="sidebar glass-panel">
            <header className="sidebar-header">
                <h2>Belgeler</h2>
                <button
                    onClick={onRefresh}
                    className="btn-icon"
                    disabled={isLoading}
                    title="Listeyi Yenile"
                >
                    <svg
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        className={isLoading ? "spinning" : ""}
                    >
                        <path d="M23 4v6h-6"></path>
                        <path d="M1 20v-6h6"></path>
                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                    </svg>
                </button>
            </header>

            <div className="doc-list-container">
                {documents.length === 0 ? (
                    <div className="empty-state">
                        <p>Henüz belge yüklenmedi.</p>
                    </div>
                ) : (
                    <ul className="doc-list">
                        {documents.map((doc) => {
                            const isSelected = selectedIds.includes(doc.id);
                            const isReady = doc.status === "indexed";

                            return (
                                <li
                                    key={doc.id}
                                    className={`doc-item ${isSelected ? "selected" : ""} ${!isReady ? "processing" : ""}`}
                                    onClick={() => isReady && onToggleSelect(doc.id)}
                                >
                                    <div className="doc-icon">
                                        {doc.file_type === "pdf" ? (
                                            <span className="icon-pdf">PDF</span>
                                        ) : (
                                            <span className="icon-img">IMG</span>
                                        )}
                                    </div>
                                    <div className="doc-info">
                                        <span className="doc-name" title={doc.filename}>{doc.filename}</span>
                                        <span className="doc-meta">
                                            {new Date(doc.created_at).toLocaleDateString("tr-TR")} • {doc.status}
                                        </span>
                                    </div>
                                    {isSelected && <div className="indicator"></div>}
                                </li>
                            );
                        })}
                    </ul>
                )}
            </div>

            <style>{`
        .sidebar {
          display: flex;
          flex-direction: column;
          height: 100%;
          border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
          border-left: none;
        }
        .sidebar-header {
          padding: 1.2rem;
          border-bottom: 1px solid var(--color-border);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .sidebar-header h2 {
          font-size: 1.2rem;
          margin: 0;
          font-weight: 600;
          letter-spacing: -0.02em;
        }
        .doc-list-container {
          flex: 1;
          overflow-y: auto;
          padding: 0.5rem;
        }
        .doc-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .doc-item {
          display: flex;
          align-items: center;
          gap: 0.8rem;
          padding: 0.8rem;
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: background 0.2s;
          position: relative;
          color: var(--color-text-muted);
        }
        .doc-item:hover {
          background: rgba(255, 255, 255, 0.03);
          color: var(--color-text-main);
        }
        .doc-item.selected {
          background: rgba(0, 212, 255, 0.1);
          color: #fff;
        }
        .doc-item.processing {
          opacity: 0.6;
          cursor: default;
        }
        .doc-icon {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.6rem;
          font-weight: bold;
          background: rgba(255, 255, 255, 0.1);
        }
        .icon-pdf { color: #ff6b6b; }
        .icon-img { color: #4ecdc4; }
        
        .doc-info {
          display: flex;
          flex-direction: column;
          overflow: hidden;
          flex: 1;
        }
        .doc-name {
          font-weight: 500;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .doc-meta {
          font-size: 0.75rem;
          opacity: 0.7;
        }
        .indicator {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--color-primary);
          box-shadow: 0 0 8px var(--color-primary);
        }
        .spinning {
          animation: spin 1s linear infinite;
        }
        .empty-state {
          padding: 2rem;
          text-align: center;
          color: var(--color-text-muted);
          font-size: 0.9rem;
        }
      `}</style>
        </aside>
    );
}
