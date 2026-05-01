"use client";

import { useEffect, useRef } from "react";
import type { Detection } from "../lib/api";

type Props = {
  imageUrl: string | null;
  detections: Detection[];
  imageSize: [number, number] | null;
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

const SEVERITY_COLOR: Record<Severity, string> = {
  alto: "#b1352b",
  medio: "#b07515",
  baixo: "#3d6347",
};

function colorFor(label: string): string {
  const sev = SEVERITY_BY_LABEL[label] ?? "baixo";
  return SEVERITY_COLOR[sev];
}

export function DetectionOverlay({
  imageUrl,
  detections,
  imageSize,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img || !imageSize) return;

    function draw() {
      const [w, h] = imageSize!;
      canvas!.width = w;
      canvas!.height = h;
      const ctx = canvas!.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, w, h);

      const stroke = Math.max(3, Math.round(w / 220));
      ctx.lineWidth = stroke;
      const fontSize = Math.max(13, Math.round(w / 44));
      ctx.font = `600 ${fontSize}px ui-sans-serif, system-ui, sans-serif`;
      ctx.textBaseline = "top";

      for (const det of detections) {
        const [x1, y1, x2, y2] = det.bbox;
        const color = colorFor(det.label);

        ctx.strokeStyle = color;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        const text = `${det.label} · ${(det.confidence * 100).toFixed(0)}%`;
        const metrics = ctx.measureText(text);
        const pad = 6;
        const textH =
          (metrics.actualBoundingBoxAscent || fontSize) +
          (metrics.actualBoundingBoxDescent || 4);

        const labelW = metrics.width + pad * 2;
        const labelH = textH + pad * 2;
        const labelY = y1 - labelH < 0 ? y1 + 2 : y1 - labelH;

        ctx.fillStyle = color;
        ctx.fillRect(x1, labelY, labelW, labelH);
        ctx.fillStyle = "white";
        ctx.fillText(text, x1 + pad, labelY + pad);
      }
    }

    if (img.complete) draw();
    else img.onload = draw;
  }, [detections, imageSize, imageUrl]);

  if (!imageUrl) {
    return (
      <div className="flex aspect-[4/3] flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-line bg-stone-50 text-ink-subtle">
        <svg viewBox="0 0 24 24" fill="none" className="h-8 w-8" aria-hidden>
          <path
            d="M3 8.4c0-.8.7-1.4 1.4-1.4h1.7c.5 0 .9-.2 1.2-.6L9 4.6c.3-.4.7-.6 1.2-.6h3.6c.5 0 .9.2 1.2.6L16.7 6.4c.3.4.7.6 1.2.6h1.7c.7 0 1.4.6 1.4 1.4V18c0 .8-.7 1.4-1.4 1.4H4.4C3.7 19.4 3 18.8 3 18V8.4Z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
          <circle cx="12" cy="13" r="3.4" stroke="currentColor" strokeWidth="1.5" />
        </svg>
        <p className="text-sm">Aguardando imagem</p>
        <p className="-mt-2 max-w-xs text-center text-xs text-ink-subtle">
          Capture com a câmera ou faça o upload de uma foto para iniciar a
          análise.
        </p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-xl border border-line bg-stone-900">
      <img
        ref={imgRef}
        src={imageUrl}
        alt="Imagem inspecionada"
        className="block w-full"
      />
      <canvas
        ref={canvasRef}
        className="absolute inset-0 h-full w-full"
        style={{ pointerEvents: "none" }}
      />
      {detections.length > 0 && (
        <div className="absolute right-3 top-3 rounded-full bg-white/95 px-3 py-1 text-xs font-semibold text-ink shadow-card">
          {detections.length}{" "}
          {detections.length === 1 ? "defeito" : "defeitos"}
        </div>
      )}
    </div>
  );
}
