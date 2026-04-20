"use client";

import { useRef } from "react";

type Props = {
  onUpload: (blob: Blob) => void;
  disabled?: boolean;
};

export function UploadPanel({ onUpload, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="rounded-lg border border-dashed border-slate-700 p-4 text-center">
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={onChange}
        disabled={disabled}
      />
      <button
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
        className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-slate-100 transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Enviar imagem do disco
      </button>
      <p className="mt-2 text-xs text-slate-400">
        Alternativa ao feed da webcam: envie uma foto do chassi.
      </p>
    </div>
  );
}
