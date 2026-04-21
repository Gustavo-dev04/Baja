"use client";

import { useCallback, useEffect, useState } from "react";
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

  const handleBlob = useCallback(
    async (blob: Blob) => {
      setLoading(true);
      setError(null);
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
    },
    [],
  );

  const defectCount = result?.detections.length ?? 0;
  const status = loading
    ? { text: "Analisando...", color: "bg-amber-500" }
    : defectCount > 0
      ? {
          text: `${defectCount} ${defectCount === 1 ? "defeito" : "defeitos"} detectado${defectCount === 1 ? "" : "s"}`,
          color: "bg-red-500",
        }
      : result
        ? { text: "Sem defeitos", color: "bg-emerald-500" }
        : { text: "Aguardando", color: "bg-slate-500" };

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Inspeção de Pintura —{" "}
            <span className="text-emerald-400">Chassis BAJA</span>
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Captura em tempo real · YOLO · FastAPI · Next.js
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`flex items-center gap-2 rounded-full bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white ring-1 ring-slate-800`}
          >
            <span
              className={`h-2 w-2 rounded-full ${status.color}`}
              aria-hidden
            />
            {status.text}
          </span>
          <span
            className={`rounded-full px-3 py-1.5 text-xs font-medium ring-1 ${
              apiOk === null
                ? "bg-slate-900 text-slate-400 ring-slate-800"
                : apiOk
                  ? "bg-emerald-950 text-emerald-300 ring-emerald-800"
                  : "bg-red-950 text-red-300 ring-red-800"
            }`}
          >
            API:{" "}
            {apiOk === null ? "checando..." : apiOk ? "online" : "offline"}
          </span>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <CameraFeed onCapture={handleBlob} disabled={loading} />
          <UploadPanel onUpload={handleBlob} disabled={loading} />
        </div>
        <div className="space-y-4">
          <DetectionOverlay
            imageUrl={imageUrl}
            detections={result?.detections ?? []}
            imageSize={result?.image_size ?? null}
          />
          <ResultsPanel result={result} loading={loading} error={error} />
        </div>
      </section>
    </main>
  );
}
