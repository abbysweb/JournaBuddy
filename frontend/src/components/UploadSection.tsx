import React, { useRef, useState } from 'react';
import { UploadCloud, FileType, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface UploadSectionProps {
  onUploadSuccess: (taskId: string, filename: string) => void;
}

export const UploadSection: React.FC<UploadSectionProps> = ({ onUploadSuccess }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
      setError(null);
    } else {
      setError("Please upload a valid PDF file.");
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUploadClick = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Failed to upload manuscript.');
      }
      
      const data = await response.json();
      onUploadSuccess(data.task_id, file.name);
    } catch (err: any) {
      setError(err.message || 'An error occurred during upload.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
      <h2 style={{ marginBottom: '8px' }}>Upload Manuscript</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
        Select or drag a PDF research paper to begin analysis.
      </p>

      <div 
        className={`upload-zone ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? 'var(--accent-primary)' : 'var(--glass-border)'}`,
          borderRadius: '12px',
          padding: '48px 24px',
          cursor: 'pointer',
          background: isDragging ? 'rgba(59, 130, 246, 0.1)' : 'rgba(0, 0, 0, 0.2)',
          transition: 'all 0.3s ease',
          marginBottom: '24px',
          position: 'relative'
        }}
      >
        <input 
          type="file" 
          accept="application/pdf" 
          style={{ display: 'none' }} 
          ref={fileInputRef}
          onChange={handleFileSelect}
        />
        
        {file ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <FileType size={48} color="var(--accent-primary)" />
            <div>
              <p style={{ fontWeight: 600 }}>{file.name}</p>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
            <CheckCircle size={24} color="var(--success)" style={{ marginTop: '8px' }} />
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
            <UploadCloud size={48} color="var(--text-secondary)" />
            <p style={{ fontWeight: 500 }}>Drag and drop your PDF here</p>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              or click to browse from your computer
            </p>
          </div>
        )}
      </div>

      {error && (
        <div style={{ 
          display: 'flex', alignItems: 'center', gap: '8px', 
          color: 'var(--danger)', marginBottom: '24px', justifyContent: 'center' 
        }}>
          <AlertCircle size={20} />
          <p>{error}</p>
        </div>
      )}

      <button 
        className="glass-button" 
        style={{ width: '100%', padding: '16px', fontSize: '1.1rem' }}
        disabled={!file || isUploading}
        onClick={handleUploadClick}
      >
        {isUploading ? (
          <>
            <Loader2 className="animate-spin" size={24} style={{ animation: 'spin 1s linear infinite' }} />
            Initializing Analysis...
          </>
        ) : (
          'Analyze Manuscript'
        )}
      </button>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};
