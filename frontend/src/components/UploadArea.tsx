import { useState, useCallback } from "react";
import type { UploadResponse } from "../types";

interface UploadAreaProps {
  onUploadStart: () => void;
  onUploadComplete: (result: UploadResponse) => void;
  onError: (msg: string) => void;
  isUploading: boolean;
  onFilesSelected: (files: File[]) => void;
}

export function UploadArea({
  onUploadStart,
  onUploadComplete,
  onError,
  isUploading,
  onFilesSelected,
}: UploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [localFiles, setLocalFiles] = useState<File[]>([]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files).filter((f) =>
        /\.(pdf|jpg|jpeg|png)$/i.test(f.name)
      );
      if (files.length > 0) {
        setLocalFiles(files);
        onFilesSelected(files);
      }
    },
    [onFilesSelected]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        const files = Array.from(e.target.files);
        setLocalFiles(files);
        onFilesSelected(files);
      }
    },
    [onFilesSelected]
  );

  return (
    <div
      className={`upload-zone glass-panel ${isDragging ? "dragging" : ""}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="file-upload"
        multiple
        accept=".pdf,.jpg,.jpeg,.png"
        className="hidden-input"
        onChange={handleFileSelect}
        disabled={isUploading}
      />
      
      <div className="upload-content">
        <div className={`upload-icon-wrapper ${isUploading ? "pulsing" : ""}`}>
          <svg 
            width="48" 
            height="48" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
            className="feather feather-upload-cloud"
          >
            <polyline points="16 16 12 12 8 16"></polyline>
            <line x1="12" y1="12" x2="12" y2="21"></line>
            <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"></path>
            <polyline points="16 16 12 12 8 16"></polyline>
          </svg>
        </div>

        {isUploading ? (
          <div className="upload-status">
            <h3>Belgeler İşleniyor</h3>
            <p>AI analiz için metin çıkarıyor...</p>
            <div className="progress-bar">
              <div className="progress-fill shimmer"></div>
            </div>
          </div>
        ) : localFiles.length > 0 ? (
          <div className="selected-files">
            <h3>{localFiles.length} Dosya Seçildi</h3>
            <ul className="file-preview-list">
              {localFiles.map((f, i) => (
                <li key={i}>{f.name}</li>
              ))}
            </ul>
            <p className="hint">Yüklemek için butona basın</p>
          </div>
        ) : (
          <div className="drop-prompt">
            <h3>Belgeleri Buraya Sürükleyin</h3>
            <p>veya seçmek için <label htmlFor="file-upload" className="link-text">tıklayın</label></p>
            <span className="file-types">PDF, JPG, PNG</span>
          </div>
        )}
      </div>

      <style>{`
        .upload-zone {
          padding: 2rem;
          text-align: center;
          border: 2px dashed rgba(255, 255, 255, 0.1);
          transition: all 0.3s ease;
          position: relative;
          overflow: hidden;
        }
        .upload-zone.dragging {
          border-color: var(--color-primary);
          background: rgba(0, 212, 255, 0.05);
        }
        .hidden-input {
          display: none;
        }
        .upload-icon-wrapper {
          color: var(--color-primary);
          margin-bottom: 1rem;
          transition: transform 0.3s;
        }
        .pulsing {
          animation: pulse-glow 2s infinite;
        }
        .link-text {
          color: var(--color-primary);
          cursor: pointer;
          text-decoration: underline;
        }
        .file-types {
          display: block;
          margin-top: 0.5rem;
          font-size: 0.8rem;
          color: var(--color-text-muted);
        }
        .progress-bar {
          height: 6px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          width: 100%;
          max-width: 300px;
          margin: 1rem auto 0;
          overflow: hidden;
        }
        .progress-fill {
          height: 100%;
          background: var(--color-primary);
          width: 60%; /* Indeterminate loading */
          animation: shimmer 1s infinite linear;
          background-image: linear-gradient(
            90deg, 
            var(--color-primary) 0%, 
            #fff 50%, 
            var(--color-primary) 100%
          );
          background-size: 200% 100%;
        }
        .file-preview-list {
          list-style: none;
          padding: 0;
          margin: 0.5rem 0;
          max-height: 100px;
          overflow-y: auto;
          font-size: 0.9rem;
          color: var(--color-text-muted);
        }
      `}</style>
    </div>
  );
}
