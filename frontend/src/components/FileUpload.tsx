import { useRef, useState } from 'react';
import type { UploadResponse } from '../types';
import { uploadFile } from '../api/client';
import './FileUpload.css';

export interface FileUploadProps {
  onUploadComplete?: (response: UploadResponse) => void;
}

export default function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (file: File | undefined) => {
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileChange(e.target.files?.[0]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFileChange(e.dataTransfer.files[0]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await uploadFile(selectedFile);
      setResult(response);
      onUploadComplete?.(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'アップロードに失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setError(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  if (result) {
    return (
      <div className="file-upload-container">
        <div className="file-upload-success" aria-label="アップロード結果">
          <div className="file-upload-success-title">アップロード成功</div>
          <div className="file-upload-success-detail">
            ファイル名: {result.filename}
          </div>
          <div className="file-upload-success-detail">
            ドキュメントID: {result.document_id}
          </div>
        </div>
        <button className="file-upload-reset-btn" onClick={handleReset}>
          別のファイルをアップロード
        </button>
      </div>
    );
  }

  return (
    <div className="file-upload-container">
      <div
        className={`file-upload-dropzone${isDragOver ? ' file-upload-dropzone--dragover' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        aria-label="ファイルドロップゾーン"
      >
        <div className="file-upload-dropzone-icon">📄</div>
        <div className="file-upload-dropzone-text">
          クリックまたはドラッグ＆ドロップでファイルを選択
        </div>
        <div className="file-upload-dropzone-hint">.pdf, .txt に対応</div>
        <input
          ref={inputRef}
          type="file"
          className="file-upload-input"
          accept=".pdf,.txt"
          onChange={handleInputChange}
          aria-label="ファイルを選択"
        />
      </div>

      {selectedFile && (
        <div className="file-upload-selected">
          <span className="file-upload-selected-name" aria-label="選択されたファイル名">
            {selectedFile.name}
          </span>
        </div>
      )}

      {isLoading ? (
        <div className="file-upload-loading" aria-label="アップロード中">
          <div className="file-upload-spinner" />
          アップロード中...
        </div>
      ) : (
        <button
          className="file-upload-btn"
          onClick={handleUpload}
          disabled={!selectedFile}
          aria-label="アップロード"
        >
          アップロード
        </button>
      )}

      {error && (
        <div className="file-upload-error" aria-label="エラーメッセージ">
          {error}
        </div>
      )}
    </div>
  );
}
