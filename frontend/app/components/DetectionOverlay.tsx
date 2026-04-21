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
  risco: "baixo",
  desgaste_generico: "baixo",
};

const SEVERITY_COLOR: Record<Severity, string> = {
  alto: "#ef4444",
  medio: "#f59e0b",
  baixo: "#38bdf8",
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

      const stroke = Math.max(3, Math.round(w / 200));
      ctx.lineWidth = stroke;
      const fontSize = Math.max(14, Math.round(w / 40));
      ctx.font = `bold ${fontSize}px system-ui, sans-serif`;
      ctx.textBaseline = "top";

      for (const det of detections) {
        const [x1, y1, x2, y2] = det.bbox;
        const color = colorFor(det.label);

        ctx.shadowColor = color;
        ctx.shadowBlur = 12;
        ctx.strokeStyle = color;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        ctx.shadowBlur = 0;

        const text = `${det.label} ${(det.confidence * 100).toFixed(0)}%`;
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
      <div className="flex h-80 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-slate-800 text-slate-500">
        <div className="text-4xl opacity-30">📷</div>
        <div className="text-sm">Aguardando captura ou upload</div>
      </div>
    );
  }

  return (
    <div className="relative">
      <img
        ref={imgRef}
        src={imageUrl}
        alt="Imagem inspecionada"
        className="w-full rounded-lg border border-slate-800"
      />
      <canvas
        ref={canvasRef}
        className="absolute inset-0 h-full w-full"
        style={{ pointerEvents: "none" }}
      />
      {detections.length > 0 && (
        <div className="absolute right-3 top-3 rounded-full bg-slate-900/90 px-3 py-1 text-xs font-semibold text-white shadow-lg ring-1 ring-white/10">
          {detections.length}{" "}
          {detections.length === 1 ? "defeito" : "defeitos"}
        </div>
      )}
    </div>
  );
}
