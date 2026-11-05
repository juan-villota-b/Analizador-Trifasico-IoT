#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor de la página de formas de onda del STPM34.

Tiene dos fuentes por WebSocket:

  /ws/demo   Onda sintética de 7.8125 kS/s (para pruebas de la interfaz).
  /ws/uart   STPM34 real por el CP210x. Lee las muestras instantáneas
             (0x30–0x36) y los registros de RMS/potencia/frecuencia.

La página estática se sirve en http://localhost:8000/.

Uso:
    python server.py
    python server.py --line 60
    python server.py --close-gui
    python server.py --port 8010

El puerto UART se puede pasar en la URL:
    ws://localhost:8000/ws/uart?port=COM3&baud=auto&crc=1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import time
from pathlib import Path
from typing import Optional

from aiohttp import web

from stpm34_uart import (
    INSTANT_ADDRS,
    METRIC_ADDRS,
    STPM3xError,
    close_stpm_gui,
    decode_instantaneous,
    decode_metrics,
    open_uart,
)

DIR = Path(__file__).resolve().parent
FS = 7812.5
FRAME_HZ = 60.0

DEMO_CLIENTS: set[web.WebSocketResponse] = set()
UART_CLIENTS: set[web.WebSocketResponse] = set()
UART_TASK: Optional[asyncio.Task] = None
UART_PARAMS: dict = {}
UART_LOCK = asyncio.Lock()


class DemoWave:
    def __init__(self, line_freq: float) -> None:
        self.line_freq = line_freq
        self.phase = 0.0
        self.n = max(1, round(FS / FRAME_HZ))
        self.omega = 2 * math.pi * line_freq

    def batch(self) -> dict:
        n = self.n
        v1 = [0.0] * n
        i1 = [0.0] * n
        v2 = [0.0] * n
        i2 = [0.0] * n
        ph1 = math.radians(-25.0)
        ph2 = math.radians(-40.0)

        for k in range(n):
            t = self.phase + k / FS
            s1 = math.sin(self.omega * t)
            s2 = math.sin(self.omega * t + 0.10)
            v1[k] = round(325 * s1 + 6.5 * math.sin(3 * self.omega * t + 0.4) + random.uniform(-0.18, 0.18), 4)
            i1[k] = round(7.07 * math.sin(self.omega * t + ph1)
                          + 0.212 * math.sin(3 * self.omega * t + ph1 + 0.8)
                          + random.uniform(-0.006, 0.006), 5)
            v2[k] = round(325 * s2 + 5.85 * math.sin(3 * self.omega * t + 0.9) + random.uniform(-0.18, 0.18), 4)
            i2[k] = round(6.36 * math.sin(self.omega * t + 0.10 + ph2)
                          + 0.159 * math.sin(3 * self.omega * t + ph2 + 1.2)
                          + random.uniform(-0.005, 0.005), 5)

        self.phase += n / FS
        if self.phase > 20:
            self.phase -= 20

        return {
            "type": "samples",
            "fs": FS,
            "ch1": {"v": v1, "i": i1},
            "ch2": {"v": v2, "i": i2},
        }


async def broadcast(clients: set[web.WebSocketResponse], message: dict) -> None:
    if not clients:
        return
    payload = json.dumps(message, separators=(",", ":"))
    dead: list[web.WebSocketResponse] = []
    for ws in list(clients):
        try:
            await ws.send_str(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)


async def broadcast_status(clients: set[web.WebSocketResponse], text: str) -> None:
    await broadcast(clients, {"type": "status", "message": text})


async def broadcast_error(clients: set[web.WebSocketResponse], text: str) -> None:
    await broadcast(clients, {"type": "error", "message": text})


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

async def ws_demo_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=20.0, max_msg_size=8 * 1024 * 1024)
    await ws.prepare(request)
    DEMO_CLIENTS.add(ws)
    try:
        async for _ in ws:
            pass
    finally:
        DEMO_CLIENTS.discard(ws)
    return ws


async def demo_loop(wave: DemoWave) -> None:
    period = 1.0 / FRAME_HZ
    while True:
        if DEMO_CLIENTS:
            await broadcast(DEMO_CLIENTS, wave.batch())
        await asyncio.sleep(period)


# ---------------------------------------------------------------------------
# UART real
# ---------------------------------------------------------------------------

def _uart_params(request: web.Request) -> dict:
    port = (request.query.get("port") or "").strip()
    baud = (request.query.get("baud") or "auto").strip()
    crc = (request.query.get("crc") or "1").strip().lower() not in ("0", "false", "no")
    return {"port": port, "baud": baud, "crc": crc}


async def uart_reader(params: dict) -> None:
    """Lee el STPM34 real y publica muestras + métricas a los clientes UART."""
    dev = None
    clients = UART_CLIENTS
    failed = False
    try:
        await broadcast_status(clients, "Abriendo UART...")
        dev, cfg = await asyncio.to_thread(
            open_uart,
            params["port"] or None,
            params["baud"],
            params["crc"],
            0.6,
            0.002,
        )
        await broadcast_status(
            clients,
            f"UART {dev.port} @ {dev.baudrate} 8N1, CRC={'sí' if dev.crc else 'no'}",
        )

        last_metrics = 0.0
        fs_ema = 0.0

        while clients:
            t0 = time.monotonic()
            regs = await asyncio.to_thread(dev.read_rows, INSTANT_ADDRS)
            dt = time.monotonic() - t0
            fs = 1.0 / dt if dt > 0 else 0.0
            fs_ema = fs if fs_ema <= 0 else 0.9 * fs_ema + 0.1 * fs
            inst = decode_instantaneous(regs, cfg)

            await broadcast(
                clients,
                {
                    "type": "samples",
                    "fs": round(fs_ema, 3),
                    "uart": {
                        "port": dev.port,
                        "baud": dev.baudrate,
                        "crc": dev.crc,
                    },
                    "ch1": {
                        "v": [round(inst[1]["v"], 4)],
                        "i": [round(inst[1]["i"], 6)],
                    },
                    "ch2": {
                        "v": [round(inst[2]["v"], 4)],
                        "i": [round(inst[2]["i"], 6)],
                    },
                },
            )

            now = time.monotonic()
            if now - last_metrics >= 0.2:
                last_metrics = now
                mregs = await asyncio.to_thread(dev.read_rows, METRIC_ADDRS)
                metrics = decode_metrics(mregs, cfg)
                await broadcast(
                    clients,
                    {
                        "type": "metrics",
                        "ch1": metrics[1],
                        "ch2": metrics[2],
                    },
                )
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        failed = True
        await broadcast_error(clients, str(exc))
    finally:
        if dev is not None:
            try:
                dev.close()
            except Exception:
                pass
        if not failed and clients:
            await broadcast_error(clients, "UART detenido.")


async def ws_uart_handler(request: web.Request) -> web.WebSocketResponse:
    global UART_TASK, UART_PARAMS

    ws = web.WebSocketResponse(heartbeat=20.0, max_msg_size=8 * 1024 * 1024)
    await ws.prepare(request)
    params = _uart_params(request)

    async with UART_LOCK:
        if UART_TASK is None or UART_TASK.done():
            UART_PARAMS = params
            UART_CLIENTS.add(ws)
            UART_TASK = asyncio.create_task(uart_reader(params))
        else:
            if params != UART_PARAMS:
                await ws.send_json(
                    {
                        "type": "error",
                        "message": "El UART ya está en uso con otra configuración.",
                    }
                )
                await ws.close()
                return ws
            UART_CLIENTS.add(ws)

    try:
        async for _ in ws:
            pass
    finally:
        UART_CLIENTS.discard(ws)
        if not UART_CLIENTS:
            async with UART_LOCK:
                if UART_TASK is not None:
                    UART_TASK.cancel()
                    try:
                        await UART_TASK
                    except asyncio.CancelledError:
                        pass
                    UART_TASK = None
    return ws


# ---------------------------------------------------------------------------
# Web
# ---------------------------------------------------------------------------

async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(DIR / "index.html")


def build_app(line_freq: float) -> web.Application:
    app = web.Application()
    app.router.add_get("/ws", ws_demo_handler)
    app.router.add_get("/ws/demo", ws_demo_handler)
    app.router.add_get("/ws/uart", ws_uart_handler)
    app.router.add_get("/", index)
    app.router.add_static("/", DIR, show_index=False)

    wave = DemoWave(line_freq)

    async def on_startup(_app: web.Application) -> None:
        _app["demo_task"] = asyncio.create_task(demo_loop(wave))

    async def on_cleanup(_app: web.Application) -> None:
        task = _app.get("demo_task")
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        global UART_TASK
        if UART_TASK is not None:
            UART_TASK.cancel()
            try:
                await UART_TASK
            except asyncio.CancelledError:
                pass
            UART_TASK = None

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor web + UART del STPM34.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--line", type=float, default=60.0, choices=[50.0, 60.0])
    parser.add_argument("--close-gui", action="store_true", help="Cerrar STPM3x GUI antes de arrancar.")
    args = parser.parse_args()

    if args.close_gui:
        close_stpm_gui()

    print(f"Página:    http://localhost:{args.port}/")
    print(f"Demo WS:   ws://localhost:{args.port}/ws/demo")
    print(f"UART WS:   ws://localhost:{args.port}/ws/uart?port=COM3&baud=auto&crc=1")
    print(f"Línea demo: {args.line:.0f} Hz")
    web.run_app(build_app(args.line), host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
