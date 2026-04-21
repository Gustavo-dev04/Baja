"use client";

import type { InspectionResult } from "../lib/api";

type Props = {
  result: InspectionResult | null;
  loading: boolean;
  error: string | null;
};

type Severity = "alto" | "medio" | "baixo";

const SEVERITY_BY_LABEL: Record<string, Severity> = {
  escorrimento: "alto",
  falha_cobertura: "alto",
  oxidacao: "alto",
  bolha: "medio",
  casca_de_laranja: "medio",
  risco: "baixo",
  desgaste_generico: "baixo",
};

const SEVERITY_STYLE: Record<Severity, string> = {
  alto: "bg-red-500/20 text-red-300 border-red-500/40",
  medio: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  baixo: "bg-sky-500/20 text-sky-300 border-sky-500/40",
};

const SEVERITY_LABEL: Record<Severity, string> = {
  alto: "Alto",
  medio: "Médio",
  baixo: "Baixo",
};

function severityFor(label: string): Severity {
  return SEVERITY_BY_LABEL[label] ?? "baixo";
}

export function ResultsPanel({ result, loading, error }: Props) {
  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950/40 p-4 text-sm text-red-300">
        {error}
      </div>
    );
  }
  if (!result && loading) {
    return (
      <div className="rounded-lg border border-slate-800 p-4 text-sm text-slate-300">
        Analisando imagem...
      </div>
    );
  }
  if (!result) {
    return null;
  }

  const counts = result.detections.reduce<Record<Severity, number>>(
    (acc, d) => {
      const s = severityFor(d.label);
      acc[s] = (acc[s] ?? 0) + 1;
      return acc;
    },
    { alto: 0, medio: 0, baixo: 0 },
  );

  const avgConfidence =
    result.detections.length === 0
      ? 0
      : result.detections.reduce((s, d) => s + d.confidence, 0) /
        result.detections.length;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-2">
        <Stat label="Alto" value={counts.alto} tone="red" />
        <Stat label="Médio" value={counts.medio} tone="amber" />
        <Stat label="Baixo" value={counts.baixo} tone="sky" />
      </div>

      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>
          Modelo: <span className="font-mono">{result.model}</span>
        </span>
        <span>
          {result.inference_ms.toFixed(0)} ms · conf. média{" "}
          {(avgConfidence * 100).toFixed(0)}%
        </span>
      </div>

      {result.demo_mode && (
        <div className="rounded-md border border-amber-800 bg-amber-950/40 p-3 text-xs text-amber-200">
          Modo demo: YOLO pré-treinado (COCO) com rótulos remapeados. Os
          defeitos reais serão detectados após fine-tuning com imagens de
          chassis.
        </div>
      )}

      {result.detections.length === 0 ? (
        <div className="rounded-lg border border-emerald-800 bg-emerald-950/30 p-4 text-sm text-emerald-200">
          Nenhum defeito detectado nesta imagem.
        </div>
      ) : (
        <ul className="divide-y divide-slate-800 rounded-lg border border-slate-800">
          {result.detections.map((det, i) => {
            const sev = severityFor(det.label);
            return (
              <li
                key={i}
                className="flex items-center justify-between gap-3 px-4 py-2 text-sm"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex shrink-0 rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${SEVERITY_STYLE[sev]}`}
                    >
                      {SEVERITY_LABEL[sev]}
                    </span>
                    <span className="truncate font-medium text-slate-100">
                      {det.label}
                    </span>
                  </div>
                  <div className="mt-0.5 text-xs text-slate-500">
                    raw: {det.raw_label}
                  </div>
                </div>
                <div className="font-mono text-emerald-400">
                  {(det.confidence * 100).toFixed(1)}%
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "red" | "amber" | "sky";
}) {
  const toneClass = {
    red: "border-red-500/30 bg-red-500/10 text-red-300",
    amber: "border-amber-500/30 bg-amber-500/10 text-amber-300",
    sky: "border-sky-500/30 bg-sky-500/10 text-sky-300",
  }[tone];

  return (
    <div
      className={`rounded-lg border p-3 text-center ${toneClass}`}
    >
      <div className="text-2xl font-bold tabular-nums">{value}</div>
      <div className="text-[10px] uppercase tracking-wider opacity-80">
        {label}
      </div>
    </div>
  );
}
