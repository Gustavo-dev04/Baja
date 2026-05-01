"use client";

import { useCallback, useEffect, useState } from "react";
import { CameraFeed } from "./components/CameraFeed";
import { DetectionOverlay } from "./components/DetectionOverlay";
import { Logo } from "./components/Logo";
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

  const handleBlob = useCallback(async (blob: Blob) => {
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
  }, []);

  const defectCount = result?.detections.length ?? 0;

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-line bg-canvas/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Logo withWordmark />
          <ApiBadge ok={apiOk} />
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
        <section className="mb-8 sm:mb-12">
          <h1 className="text-balance text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            Inspeção de pintura assistida por IA.
          </h1>
          <p className="mt-3 max-w-2xl text-pretty text-base text-ink-muted sm:text-lg">
            Magnus analisa imagens da pintura de chassis BAJA e identifica
            defeitos como escorrimento, casca de laranja, bolhas e manchas
            d&apos;água em tempo real.
          </p>
        </section>

        <StatusBar result={result} loading={loading} />

        <section className="mt-6 grid gap-5 lg:grid-cols-5">
          <div className="space-y-5 lg:col-span-2">
            <Panel title="Captura" subtitle="Webcam ou upload de arquivo">
              <CameraFeed onCapture={handleBlob} disabled={loading} />
              <div className="mt-4 border-t border-line pt-4">
                <UploadPanel onUpload={handleBlob} disabled={loading} />
              </div>
            </Panel>
          </div>

          <div className="space-y-5 lg:col-span-3">
            <Panel
              title="Resultado"
              subtitle={
                defectCount === 0 && result
                  ? "Sem defeitos identificados"
                  : defectCount > 0
                    ? `${defectCount} ${defectCount === 1 ? "defeito" : "defeitos"} identificado${defectCount === 1 ? "" : "s"}`
                    : loading
                      ? "Analisando..."
                      : "Aguardando captura"
              }
            >
              <DetectionOverlay
                imageUrl={imageUrl}
                detections={result?.detections ?? []}
                imageSize={result?.image_size ?? null}
              />
              <div className="mt-4">
                <ResultsPanel result={result} loading={loading} error={error} />
              </div>
            </Panel>
          </div>
        </section>

        <footer className="mt-16 border-t border-line pt-6 text-xs text-ink-subtle">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span>
              Magnus · IA fine-tunada com YOLOv8 · FastAPI · Next.js · Supabase
            </span>
            <span>
              Protótipo científico-tecnológico · Projeto BAJA
            </span>
          </div>
        </footer>
      </main>
    </div>
  );
}

function Panel({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <article className="card p-5 sm:p-6">
      <header className="mb-4 flex items-end justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-ink">{title}</h2>
          {subtitle && (
            <p className="mt-0.5 text-sm text-ink-muted">{subtitle}</p>
          )}
        </div>
      </header>
      {children}
    </article>
  );
}

function ApiBadge({ ok }: { ok: boolean | null }) {
  const [label, dotClass] =
    ok === null
      ? ["verificando", "bg-stone-300"]
      : ok
        ? ["online", "bg-magnus-500"]
        : ["offline", "bg-rose-500"];

  return (
    <span className="chip">
      <span className={`h-1.5 w-1.5 rounded-full ${dotClass}`} aria-hidden />
      API · {label}
    </span>
  );
}

function StatusBar({
  result,
  loading,
}: {
  result: InspectionResult | null;
  loading: boolean;
}) {
  const mode = result
    ? result.demo_mode
      ? "demo"
      : "treinado"
    : loading
      ? "processando"
      : "ocioso";

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <Stat
        label="Modo"
        value={mode}
        valueClass={
          mode === "treinado"
            ? "text-magnus-700"
            : mode === "demo"
              ? "text-amber-700"
              : "text-ink"
        }
      />
      <Stat
        label="Última inferência"
        value={result ? `${result.inference_ms.toFixed(0)} ms` : "—"}
      />
      <Stat
        label="Detecções"
        value={result ? String(result.detections.length) : "—"}
      />
      <Stat
        label="Modelo"
        value={result ? prettyModelName(result.model) : "—"}
        valueClass="font-mono text-sm"
      />
    </div>
  );
}

function Stat({
  label,
  value,
  valueClass = "",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="card px-4 py-3">
      <div className="text-[10px] font-medium uppercase tracking-wider text-ink-subtle">
        {label}
      </div>
      <div
        className={`mt-1 truncate text-lg font-semibold capitalize text-ink ${valueClass}`}
      >
        {value}
      </div>
    </div>
  );
}

function prettyModelName(model: string): string {
  if (model.startsWith("hf://")) {
    const parts = model.replace("hf://", "").split("/");
    return parts[parts.length - 1] ?? model;
  }
  return model;
}
