"use client";

import { useCallback, useState } from "react";
import { CameraFeed } from "./components/CameraFeed";
import { DetectionOverlay } from "./components/DetectionOverlay";
import { ResultsPanel } from "./components/ResultsPanel";
import { UploadPanel } from "./components/UploadPanel";
import { inspectImage, type InspectionResult } from "./lib/api";

export default function Home() {
  const [result, setResult] = useState<InspectionResult | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleBlob = useCallback(async (blob: Blob) => {
    setLoading(true);
    setError(null);
    setResult(null);
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    setImageUrl(URL.createObjectURL(blob));

    try {
      const r = await inspectImage(blob);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro desconhecido.");
    } finally {
      setLoading(false);
    }
  }, [imageUrl]);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">
          Inspeção de Pintura — Chassis BAJA
        </h1>
        <p className="text-sm text-slate-400">
          Capture uma imagem pela webcam da câmara ou envie uma foto. O
          backend executa o modelo YOLO e devolve os defeitos detectados.
        </p>
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
