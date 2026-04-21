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
    <section className="overflow-hidden rounded-3xl border border-white/10 bg-slate-900/70 shadow-xl shadow-slate-950/30 backdrop-blur">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="text-base font-semibold text-white">
          Upload de imagem
        </h2>
        <p className="text-sm text-slate-400">
          Alternativa ao uso da webcam para testes com fotos do chassi.
        </p>
      </div>

      <div className="p-5">
        <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-950/40 p-6 text-center">
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={onChange}
            disabled={disabled}
          />

          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-slate-900 text-lg text-slate-300">
            ↑
          </div>

          <button
            onClick={() => inputRef.current?.click()}
            disabled={disabled}
            className="inline-flex items-center justify-center rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm font-semibold text-slate-100 transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Enviar imagem do dispositivo
          </button>

          <p className="mt-3 text-xs leading-5 text-slate-500">
            Envie uma foto JPG ou PNG para processar no backend e visualizar as
            marcações de inspeção.
          </p>
        </div>
      </div>
    </section>
  );
}
