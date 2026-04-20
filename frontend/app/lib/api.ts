export type Detection = {
  label: string;
  raw_label: string;
  confidence: number;
  bbox: [number, number, number, number];
};

export type InspectionResult = {
  detections: Detection[];
  image_size: [number, number];
  inference_ms: number;
  model: string;
  demo_mode: boolean;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

export async function inspectImage(blob: Blob): Promise<InspectionResult> {
  const form = new FormData();
  form.append("file", blob, "frame.jpg");

  const res = await fetch(`${API_URL}/inspect`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Inspection failed (${res.status}): ${detail}`);
  }
  return (await res.json()) as InspectionResult;
}

export async function health(): Promise<{
  status: string;
  model: string;
  demo_mode: boolean;
}> {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}
