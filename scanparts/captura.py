"""Captura com a IMX219 no Jetson (GStreamer nvarguscamerasrc), com exposição e ganho travados."""
from __future__ import annotations

import cv2


def pipeline_gstreamer(sensor=0, largura=3280, altura=2464, exposicao_us=None, ganho=None, fps=21):
    extra = ""
    if exposicao_us:
        ns = int(exposicao_us * 1000)
        extra += f' exposuretimerange="{ns} {ns}" aelock=true'
    if ganho:
        extra += f' gainrange="{ganho} {ganho}"'
    return (f"nvarguscamerasrc sensor-id={sensor} wbmode=0 awblock=true{extra} ! "
            f"video/x-raw(memory:NVMM), width={largura}, height={altura}, framerate={fps}/1, format=NV12 ! "
            f"nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink drop=1")


def capturar(sensor=0, largura=3280, altura=2464, exposicao_us=None, ganho=None, descartar=15):
    """Abre a câmera, descarta alguns quadros (a exposição estabiliza) e devolve uma foto BGR."""
    cap = cv2.VideoCapture(pipeline_gstreamer(sensor, largura, altura, exposicao_us, ganho), cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        raise RuntimeError("Não abriu a câmera CSI. Confira o cabo de 22 pinos e rode: gst-launch-1.0 nvarguscamerasrc ! fakesink")
    img = None
    for _ in range(descartar + 1):
        ok, img = cap.read()
    cap.release()
    if img is None:
        raise RuntimeError("A câmera abriu, mas não entregou imagem.")
    return img
