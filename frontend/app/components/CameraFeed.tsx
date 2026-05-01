"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Props = {
  onCapture: (blob: Blob) => void;
  disabled?: boolean;
};

const LIVE_INTERVAL_MS = 1500;

export function CameraFeed({ onCapture, disabled }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [live, setLive] = useState(false);
  const [liveCount, setLiveCount] = useState(0);

  useEffect(() => {
    let stream: MediaStream | null = null;

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
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setReady(true);
        }
      } catch (e) {
        setError(
          e instanceof Error ? e.message : "Falha ao acessar a câmera.",
        );
      }
    }
    start();

    return () => {
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const captureOnce = useCallback(() => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
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
      0.85,
    );
  }, [onCapture]);

  useEffect(() => {
    if (!live || !ready) return;
    setLiveCount(0);
    const id = window.setInterval(() => {
      captureOnce();
      setLiveCount((c) => c + 1);
    }, LIVE_INTERVAL_MS);
    captureOnce();
    return () => window.clearInterval(id);
  }, [live, ready, captureOnce]);

  return (
    <div className="space-y-3">
      <div className="relative aspect-[4/3] overflow-hidden rounded-xl border border-line bg-stone-900">
        <video
          ref={videoRef}
          className="h-full w-full object-cover"
          playsInline
          muted
        />
        {live && (
          <div className="absolute left-3 top-3 flex items-center gap-2 rounded-full bg-magnus-700/95 px-2.5 py-1 text-xs font-medium text-white shadow-card">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white opacity-70" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-white" />
            </span>
            Ao vivo · {liveCount}
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-stone-900/95 p-6 text-center text-sm text-stone-300">
            {error}
          </div>
        )}
        {!ready && !error && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-stone-400">
            Iniciando câmera…
          </div>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={captureOnce}
          disabled={!ready || disabled || live}
          className="btn-primary"
        >
          Capturar frame
        </button>
        <button
          onClick={() => setLive((v) => !v)}
          disabled={!ready}
          className={live ? "btn-primary !bg-rose-600 hover:!bg-rose-500" : "btn-secondary"}
        >
          {live ? "Parar ao vivo" : "Iniciar ao vivo"}
        </button>
      </div>
    </div>
  );
}
