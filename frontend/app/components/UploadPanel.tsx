"use client";

import { useRef, useState } from "react";

type Props = {
  onUpload: (blob: Blob) => void;
  disabled?: boolean;
};

export function UploadPanel({ onUpload, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [hovering, setHovering] = useState(false);

  function handleFile(file: File | undefined) {
    if (file && file.type.startsWith("image/")) onUpload(file);
    if (inputRef.current) inputRef.current.value = "";
  }

  function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    handleFile(e.target.files?.[0]);
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setHovering(false);
    if (disabled) return;
    handleFile(e.dataTransfer.files?.[0]);
  }

  return (
    <div className="space-y-2">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setHovering(true);
        }}
        onDragLeave={() => setHovering(false)}
        onDrop={onDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed py-6 px-4 text-center transition ${
          hovering
            ? "border-magnus-500 bg-magnus-50"
            : "border-line bg-stone-50 hover:bg-stone-100"
        } ${disabled ? "cursor-not-allowed opacity-50" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={onChange}
          disabled={disabled}
        />
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className="h-6 w-6 text-ink-muted"
          aria-hidden
        >
          <path
            d="M12 16V4m0 0L8 8m4-4 4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <p className="mt-2 text-sm font-medium text-ink">
          Enviar uma imagem
        </p>
        <p className="text-xs text-ink-muted">
          Arraste e solte ou clique para escolher
        </p>
      </div>
    </div>
  );
}
