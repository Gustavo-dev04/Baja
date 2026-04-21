"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  onCapture: (blob: Blob) => void;
  disabled?: boolean;
};

export function CameraFeed({ onCapture, disabled }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let stream: MediaStream | null = null;
    let cancelled = false;

    async function start() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: { ideal: "environment" },
          },
          audio: false,
        });

        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setReady(true);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof Error ? e.message : "Falha ao acessar a câmera.",
          );
        }
      }
    }

    start();

    return () => {
      cancelled = true;
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  function capture() {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (blob) onCapture(blob);
      },
      "image/jpeg",
      0.9,
    );
  }

  return (
    <section className="overflow-hidden rounded-3xl border border-white/10 bg-slate-900/70 shadow-xl shadow-slate-950/30 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
        <div>
          <h2 className="text-base font-semibold text-white">
            Captura por câmera
          </h2>
          <p className="text-sm text-slate-400">
            Use a webcam para capturar um frame e enviar para inspeção.
          </p>
        </div>

        <div
          className={`rounded-full px-3 py-1 text-xs font-medium ring-1 ${
            error
              ? "bg-red-950/60 text-red-300 ring-red-800"
              : ready
                ? "bg-emerald-950/60 text-emerald-300 ring-emerald-800"
                : "bg-slate-950/70 text-slate-300 ring-slate-700"
          }`}
        >
          {error ? "Câmera indisponível" : ready ? "Câmera pronta" : "Solicitando acesso"}
        </div>
      </div>

      <div className="space-y-4 p-5">
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-black/80 shadow-inner">
          <video
            ref={videoRef}
            className="aspect-video w-full object-cover"
            playsInline
            muted
            autoPlay
          />
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-950/70 p-6 text-center text-sm text-red-300">
              {error}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <button
            onClick={capture}
            disabled={!ready || disabled}
            className="inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-emerald-500/30 disabled:text-slate-400"
          >
            Capturar e inspecionar
          </button>
          <p className="text-xs leading-5 text-slate-500 sm:max-w-xs sm:text-right">
            Em celular, o navegador normalmente exige HTTPS e permissão de
            câmera para liberar a captura.
          </p>
        </div>
      </div>
    </section>
  );
}
