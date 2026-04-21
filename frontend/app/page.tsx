"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CameraFeed } from "./components/CameraFeed";
import { DetectionOverlay } from "./components/DetectionOverlay";
import { ResultsPanel } from "./components/ResultsPanel";
import { UploadPanel } from "./components/UploadPanel";
import { health, inspectImage, type InspectionResult } from "./lib/api";

export default function Home() {
  const [result, setResult] = useState<InspectionResult | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  useEffect(() => {
    health()
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false));
  }, []);

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  const handleBlob = useCallback(async (blob: Blob) => {
    setLoading(true);
    setError(null);
    setResult(null);

    const nextUrl = URL.createObjectURL(blob);
    setImageUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return nextUrl;
    });

    try {
      const r = await inspectImage(blob);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro desconhecido.");
    } finally {
      setLoading(false);
    }
  }, []);

  const summary = useMemo(() => {
    return {
      detections: result?.detections.length ?? 0,
      inference: result ? `${result.inference_ms.toFixed(0)} ms` : "--",
      mode: result?.demo_mode ? "Demonstração" : result ? "Treinado" : "Aguardando",
    };
  }, [result]);

  return (
    <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="space-y-6">
        <header className="overflow-hidden rounded-3xl border border-white/10 bg-slate-900/70 shadow-2xl shadow-slate-950/40 backdrop-blur">
          <div className="grid gap-6 px-6 py-6 lg:grid-cols-[1.8fr_1fr] lg:px-8">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">
                  Protótipo científico-tecnológico
                </span>
                <span className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-300">
                  Inspeção visual assistida por IA
                </span>
              </div>

              <div className="space-y-2">
                <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                  Inspeção de Pintura — Chassis BAJA
                </h1>
                <p className="max-w-3xl text-sm leading-6 text-slate-300 sm:text-base">
                  Ambiente de demonstração para captura, envio e análise de
                  imagens do chassi em uma interface única, com retorno visual
                  das detecções processadas pelo backend em nuvem.
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Status da API
                </div>
                <div className="mt-2 flex items-center gap-2 text-sm font-medium text-white">
                  <span
                    className={`inline-flex h-2.5 w-2.5 rounded-full ${
                      apiOk === null
                        ? "bg-slate-500"
                        : apiOk
                          ? "bg-emerald-400"
                          : "bg-red-400"
                    }`}
                  />
                  {apiOk === null ? "Checando" : apiOk ? "Online" : "Offline"}
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Última inferência
                </div>
                <div className="mt-2 text-lg font-semibold text-white">
                  {summary.inference}
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Modo de operação
                </div>
                <div className="mt-2 text-lg font-semibold text-white">
                  {summary.mode}
                </div>
              </div>
            </div>
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-6">
            <CameraFeed onCapture={handleBlob} disabled={loading} />
            <UploadPanel onUpload={handleBlob} disabled={loading} />
          </div>

          <div className="space-y-6">
            <section className="overflow-hidden rounded-3xl border border-white/10 bg-slate-900/70 shadow-xl shadow-slate-950/30 backdrop-blur">
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
                <div>
                  <h2 className="text-base font-semibold text-white">
                    Visualização da inspeção
                  </h2>
                  <p className="text-sm text-slate-400">
                    Overlay com marcações sobre a imagem processada.
                  </p>
                </div>
                <div className="rounded-full border border-slate-700 bg-slate-950/70 px-3 py-1 text-xs text-slate-300">
                  {summary.detections} {summary.detections === 1 ? "detecção" : "detecções"}
                </div>
              </div>
              <div className="p-4 sm:p-5">
                <DetectionOverlay
                  imageUrl={imageUrl}
                  detections={result?.detections ?? []}
                  imageSize={result?.image_size ?? null}
                />
              </div>
            </section>

            <ResultsPanel result={result} loading={loading} error={error} />
          </div>
        </section>
      </div>
    </main>
  );
}
