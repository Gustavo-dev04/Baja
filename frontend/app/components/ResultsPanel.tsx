"use client";

import type { InspectionResult } from "../lib/api";

type Props = {
  result: InspectionResult | null;
  loading: boolean;
  error: string | null;
};

export function ResultsPanel({ result, loading, error }: Props) {
  return (
    <section className="overflow-hidden rounded-3xl border border-white/10 bg-slate-900/70 shadow-xl shadow-slate-950/30 backdrop-blur">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="text-base font-semibold text-white">
          Resultado da inspeção
        </h2>
        <p className="text-sm text-slate-400">
          Resumo técnico da execução mais recente do backend.
        </p>
      </div>

      <div className="space-y-4 p-5">
        {loading && (
          <div className="rounded-2xl border border-sky-900/60 bg-sky-950/30 p-4 text-sm text-sky-200">
            Analisando imagem e aguardando resposta do modelo...
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-900/70 bg-red-950/30 p-4 text-sm text-red-200">
            {error}
          </div>
        )}

        {!loading && !error && !result && (
          <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-950/40 p-5 text-sm text-slate-400">
            Nenhuma inspeção executada ainda. Capture uma imagem ou envie uma
            foto para iniciar a análise.
          </div>
        )}

        {result && (
          <>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Detecções
                </div>
                <div className="mt-2 text-2xl font-semibold text-white">
                  {result.detections.length}
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Inferência
                </div>
                <div className="mt-2 text-2xl font-semibold text-white">
                  {result.inference_ms.toFixed(0)} ms
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                  Modelo
                </div>
                <div className="mt-2 truncate font-mono text-sm text-emerald-300">
                  {result.model}
                </div>
              </div>
            </div>

            {result.demo_mode && (
              <div className="rounded-2xl border border-amber-800/80 bg-amber-950/30 p-4 text-sm text-amber-100">
                <div className="font-semibold text-amber-200">Modo demonstração ativo</div>
                <p className="mt-1 leading-6 text-amber-100/90">
                  O sistema está validando o pipeline com um modelo genérico
                  pré-treinado. Para detectar defeitos reais de pintura, a
                  próxima etapa é treinar um checkpoint com imagens rotuladas do
                  chassi.
                </p>
              </div>
            )}

            {result.detections.length === 0 ? (
              <div className="rounded-2xl border border-emerald-800/80 bg-emerald-950/30 p-4 text-sm text-emerald-200">
                Nenhuma detecção retornada nesta execução.
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-sm font-medium text-slate-300">
                  Lista de detecções
                </div>
                <ul className="space-y-3">
                  {result.detections.map((det, i) => (
                    <li
                      key={`${det.label}-${i}`}
                      className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-slate-950/50 p-4 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-white">
                            {det.label}
                          </span>
                          <span className="rounded-full border border-slate-700 bg-slate-900 px-2 py-0.5 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                            raw {det.raw_label}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500">
                          bbox: {det.bbox.map((value) => value.toFixed(0)).join(", ")}
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-800">
                          <div
                            className="h-full rounded-full bg-emerald-400"
                            style={{ width: `${Math.max(6, det.confidence * 100)}%` }}
                          />
                        </div>
                        <div className="min-w-16 text-right font-mono text-sm text-emerald-300">
                          {(det.confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
