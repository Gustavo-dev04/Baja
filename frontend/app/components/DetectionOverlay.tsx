"use client";

import { useEffect, useRef } from "react";
import type { Detection } from "../lib/api";

type Props = {
  imageUrl: string | null;
  detections: Detection[];
  imageSize: [number, number] | null;
};

const PALETTE = [
  "#ef4444",
  "#f59e0b",
  "#10b981",
  "#3b82f6",
  "#a855f7",
  "#ec4899",
];

function colorFor(label: string): string {
  let hash = 0;
  for (let i = 0; i < label.length; i++) {
    hash = (hash * 31 + label.charCodeAt(i)) >>> 0;
  }
  return PALETTE[hash % PALETTE.length];
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

    const [w, h] = imageSize;
    const safeCanvas = canvas;

    function draw() {
      safeCanvas.width = w;
      safeCanvas.height = h;
      const ctx = safeCanvas.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, w, h);

      ctx.lineWidth = Math.max(2, Math.round(w / 320));
      const fontSize = Math.max(12, Math.round(w / 48));
      ctx.font = `${fontSize}px system-ui, sans-serif`;
      ctx.textBaseline = "top";

      for (const det of detections) {
        const [x1, y1, x2, y2] = det.bbox;
        const color = colorFor(det.label);
        ctx.strokeStyle = color;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        const text = `${det.label} ${(det.confidence * 100).toFixed(0)}%`;
        const metrics = ctx.measureText(text);
        const pad = 4;
        const textH =
          (metrics.actualBoundingBoxAscent || fontSize) +
          (metrics.actualBoundingBoxDescent || 4);
        const labelH = textH + pad * 2;
        const labelW = metrics.width + pad * 2;
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
      <div className="flex h-80 items-center justify-center rounded-lg border border-dashed border-slate-800 text-slate-500">
        Nenhuma imagem inspecionada ainda.
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
          {detections.length} {detections.length === 1 ? "detecção" : "detecções"}
        </div>
      )}
    </div>
  );
}
