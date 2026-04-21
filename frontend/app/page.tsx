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

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">
            Inspeção de Pintura — Chassis BAJA
          </h1>
          <p className="text-sm text-slate-400">
            Abra esta interface por URL, capture uma imagem pela webcam ou
            envie uma foto e receba o resultado da inspeção pelo backend.
          </p>
        </div>
        <div
          className={`rounded-full px-3 py-1.5 text-xs font-medium ring-1 ${
            apiOk === null
              ? "bg-slate-900 text-slate-400 ring-slate-800"
              : apiOk
                ? "bg-emerald-950 text-emerald-300 ring-emerald-800"
                : "bg-red-950 text-red-300 ring-red-800"
          }`}
        >
          API: {apiOk === null ? "checando..." : apiOk ? "online" : "offline"}
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
