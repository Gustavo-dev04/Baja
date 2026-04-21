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
      <div className="relative overflow-hidden rounded-lg border border-slate-800 bg-black">
        <video
          ref={videoRef}
          className="w-full"
          playsInline
          muted
        />
        {live && (
          <div className="absolute left-3 top-3 flex items-center gap-2 rounded-full bg-red-600/90 px-3 py-1 text-xs font-semibold text-white shadow-lg">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-white" />
            </span>
            AO VIVO · {liveCount} frames
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center p-4 text-center text-sm text-red-400">
            {error}
          </div>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={captureOnce}
          disabled={!ready || disabled || live}
          className="rounded-md bg-emerald-600 px-4 py-2 font-medium text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Capturar frame
        </button>
        <button
          onClick={() => setLive((v) => !v)}
          disabled={!ready}
          className={`rounded-md px-4 py-2 font-medium text-white transition disabled:cursor-not-allowed disabled:opacity-50 ${
            live
              ? "bg-red-600 hover:bg-red-500"
              : "bg-blue-600 hover:bg-blue-500"
          }`}
        >
          {live ? "Parar modo ao vivo" : "Iniciar modo ao vivo"}
        </button>
      </div>
    </div>
  );
}
