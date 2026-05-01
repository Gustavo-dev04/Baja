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
  water_spotting: "medio",
  risco: "baixo",
  desgaste_generico: "baixo",
};

const SEVERITY_STYLE: Record<Severity, string> = {
  alto: "border-rose-200 bg-rose-50 text-rose-800",
  medio: "border-amber-200 bg-amber-50 text-amber-800",
  baixo: "border-magnus-200 bg-magnus-50 text-magnus-800",
};

const SEVERITY_DOT: Record<Severity, string> = {
  alto: "bg-rose-500",
  medio: "bg-amber-500",
  baixo: "bg-magnus-500",
};

const SEVERITY_LABEL: Record<Severity, string> = {
  alto: "Alto",
  medio: "Médio",
  baixo: "Baixo",
};

const FRIENDLY_LABEL: Record<string, string> = {
  casca_de_laranja: "Casca de laranja",
  escorrimento: "Escorrimento",
  bolha: "Bolha",
  water_spotting: "Mancha de água",
  falha_cobertura: "Falha de cobertura",
  risco: "Risco",
  oxidacao: "Oxidação",
  desgaste_generico: "Desgaste genérico",
};

function severityFor(label: string): Severity {
  return SEVERITY_BY_LABEL[label] ?? "baixo";
}

function friendlyName(label: string): string {
  return FRIENDLY_LABEL[label] ?? label;
}

export function ResultsPanel({ result, loading, error }: Props) {
  if (error) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
        {error}
      </div>
    );
  }
  if (!result && loading) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-line bg-stone-50 px-4 py-3 text-sm text-ink-muted">
        <Spinner /> Analisando imagem...
      </div>
    );
  }
  if (!result) return null;

  if (result.detections.length === 0) {
    return (
      <div className="rounded-xl border border-magnus-200 bg-magnus-50 px-4 py-3 text-sm text-magnus-900">
        Nenhum defeito detectado nesta imagem.
      </div>
    );
  }

  const counts = result.detections.reduce<Record<Severity, number>>(
    (acc, d) => {
      const s = severityFor(d.label);
      acc[s] = (acc[s] ?? 0) + 1;
      return acc;
    },
    { alto: 0, medio: 0, baixo: 0 },
  );

  return (
    <div className="space-y-4">
      {result.demo_mode && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900">
          Modo demo — Magnus está usando o YOLO genérico (COCO) com rótulos
          remapeados. Resultados reais aparecem após carregar um modelo
          fine-tunado.
        </div>
      )}

      <div className="grid grid-cols-3 gap-3">
        <SeverityCard label="Alto" value={counts.alto} severity="alto" />
        <SeverityCard label="Médio" value={counts.medio} severity="medio" />
        <SeverityCard label="Baixo" value={counts.baixo} severity="baixo" />
      </div>

      <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line">
        {result.detections.map((det, i) => {
          const sev = severityFor(det.label);
          return (
            <li
              key={i}
              className="flex items-center gap-3 bg-white px-4 py-3 text-sm"
            >
              <span
                className={`h-2 w-2 shrink-0 rounded-full ${SEVERITY_DOT[sev]}`}
                aria-hidden
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate font-medium text-ink">
                    {friendlyName(det.label)}
                  </span>
                  <span
                    className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${SEVERITY_STYLE[sev]}`}
                  >
                    {SEVERITY_LABEL[sev]}
                  </span>
                </div>
                {det.raw_label !== det.label && (
                  <div className="mt-0.5 truncate text-xs text-ink-subtle">
                    raw: {det.raw_label}
                  </div>
                )}
              </div>
              <div className="shrink-0 font-mono text-sm text-ink-muted">
                {(det.confidence * 100).toFixed(1)}%
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function SeverityCard({
  label,
  value,
  severity,
}: {
  label: string;
  value: number;
  severity: Severity;
}) {
  const tone = {
    alto: "border-rose-200 bg-rose-50",
    medio: "border-amber-200 bg-amber-50",
    baixo: "border-magnus-200 bg-magnus-50",
  }[severity];

  const accent = {
    alto: "text-rose-800",
    medio: "text-amber-800",
    baixo: "text-magnus-800",
  }[severity];

  return (
    <div className={`rounded-xl border px-4 py-3 ${tone}`}>
      <div className={`text-2xl font-semibold tabular-nums ${accent}`}>
        {value}
      </div>
      <div className={`text-[11px] font-medium uppercase tracking-wider ${accent} opacity-80`}>
        {label}
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin text-magnus-700"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
    >
      <circle
        cx="12"
        cy="12"
        r="9"
        stroke="currentColor"
        strokeOpacity="0.25"
        strokeWidth="3"
      />
      <path
        d="M21 12a9 9 0 0 0-9-9"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
