"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, X, AlertCircle } from "lucide-react";

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
  label?: string;
}

export default function FileUpload({
  onFilesSelected,
  maxFiles = 1,
  acceptedTypes = [".pdf", ".docx", ".xlsx"],
  label = "Upload Pitch Deck",
}: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      setError(null);

      const droppedFiles = Array.from(e.dataTransfer.files);
      validateAndSetFiles(droppedFiles);
    },
    [maxFiles]
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    if (e.target.files) {
      const selected = Array.from(e.target.files);
      validateAndSetFiles(selected);
    }
  };

  const validateAndSetFiles = (newFiles: File[]) => {
    // Check file count
    if (newFiles.length > maxFiles) {
      setError(`Maximum ${maxFiles} file(s) allowed`);
      return;
    }

    // Check file types
    const validFiles = newFiles.filter((file) => {
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      return acceptedTypes.includes(ext);
    });

    if (validFiles.length !== newFiles.length) {
      setError(`Only ${acceptedTypes.join(", ")} files are supported`);
    }

    if (validFiles.length > 0) {
      setFiles(validFiles);
      onFilesSelected(validFiles);
    }
  };

  const removeFile = (index: number) => {
    const updated = files.filter((_, i) => i !== index);
    setFiles(updated);
    onFilesSelected(updated);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  };

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium text-slate-300">{label}</label>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
          isDragOver
            ? "border-blue-500 bg-blue-500/10"
            : "border-slate-700 hover:border-slate-500 bg-slate-900/50"
        }`}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <Upload
          className={`h-10 w-10 mx-auto mb-3 ${
            isDragOver ? "text-blue-400" : "text-slate-500"
          }`}
        />
        <p className="text-sm text-slate-300">
          Drag & drop your files here, or{" "}
          <span className="text-blue-400 font-medium">browse</span>
        </p>
        <p className="text-xs text-slate-500 mt-1">
          Supports {acceptedTypes.join(", ")} • Max {maxFiles} file(s) • 50MB
          limit
        </p>
        <input
          id="file-input"
          type="file"
          multiple={maxFiles > 1}
          accept={acceptedTypes.join(",")}
          onChange={handleFileInput}
          className="hidden"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 rounded-lg px-3 py-2">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between bg-slate-800/50 rounded-lg px-4 py-3 border border-slate-700"
            >
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-blue-400" />
                <div>
                  <p className="text-sm text-slate-200 font-medium">
                    {file.name}
                  </p>
                  <p className="text-xs text-slate-500">
                    {formatSize(file.size)}
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(index);
                }}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-4 w-4 text-slate-400" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
