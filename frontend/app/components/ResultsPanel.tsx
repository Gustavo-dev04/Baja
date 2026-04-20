"use client";

import type { InspectionResult } from "../lib/api";

type Props = {
  result: InspectionResult | null;
  loading: boolean;
  error: string | null;
};

export function ResultsPanel({ result, loading, error }: Props) {
  if (loading) {
    return (
      <div className="rounded-lg border border-slate-800 p-4 text-sm text-slate-300">
        Analisando imagem...
      </div>
    );
  }
  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950/40 p-4 text-sm text-red-300">
        {error}
      </div>
    );
  }
  if (!result) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>
          Modelo: <span className="font-mono">{result.model}</span>
        </span>
        <span>{result.inference_ms.toFixed(0)} ms</span>
      </div>

      {result.demo_mode && (
        <div className="rounded-md border border-amber-800 bg-amber-950/40 p-3 text-xs text-amber-200">
          Modo demo: modelo pré-treinado (COCO) com rótulos remapeados. Faça
          fine-tuning com imagens reais de chassis para detecções
          específicas de defeitos de pintura.
        </div>
      )}

      {result.detections.length === 0 ? (
        <div className="rounded-lg border border-emerald-800 bg-emerald-950/30 p-4 text-sm text-emerald-200">
          Nenhum defeito detectado.
        </div>
      ) : (
        <ul className="divide-y divide-slate-800 rounded-lg border border-slate-800">
          {result.detections.map((det, i) => (
            <li
              key={i}
              className="flex items-center justify-between px-4 py-2 text-sm"
            >
              <div>
                <div className="font-medium text-slate-100">{det.label}</div>
                <div className="text-xs text-slate-500">
                  raw: {det.raw_label}
                </div>
              </div>
              <div className="font-mono text-emerald-400">
                {(det.confidence * 100).toFixed(1)}%
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
