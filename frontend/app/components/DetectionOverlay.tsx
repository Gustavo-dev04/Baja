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

    function draw() {
      const [w, h] = imageSize!;
      canvas!.width = w;
      canvas!.height = h;
      const ctx = canvas!.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, w, h);

      ctx.lineWidth = Math.max(2, Math.round(w / 320));
      ctx.font = `${Math.max(12, Math.round(w / 48))}px system-ui, sans-serif`;
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
          (metrics.actualBoundingBoxAscent || 12) +
          (metrics.actualBoundingBoxDescent || 4);
        ctx.fillStyle = color;
        ctx.fillRect(x1, y1 - textH - pad * 2, metrics.width + pad * 2, textH + pad * 2);
        ctx.fillStyle = "white";
        ctx.fillText(text, x1 + pad, y1 - textH - pad);
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
    </div>
  );
}
