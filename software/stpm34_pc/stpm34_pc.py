#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Captura y graficación en vivo de un STPM33/STPM34 (EVALSTPM33/34) por UART.

El programa:
  * detecta el puerto del CP210x de la placa,
  * habla el protocolo UART del STPM3x (9600 8N1, CRC opcional),
  * lee V/I RMS, potencia activa, energía y frecuencia,
  * muestra gráficas en vivo y guarda un CSV,
  * puede funcionar sin gráficas (--no-plot) y reconectarse solo (--wait).

Uso rápido:
    python stpm34_pc.py --list
    python stpm34_pc.py --plot
    python stpm34_pc.py --wait --plot
    python stpm34_pc.py --no-plot --duration 60 --csv datos.csv
    python stpm34_pc.py --plot-csv datos.csv --save grafica.png
    python stpm34_pc.py --demo --plot

Seguridad: la EVALSTPM33/34 se conecta a la red eléctrica. No toque la placa
mientras esté energizada. Use la alimentación y el aislamiento previstos por ST.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    print("Falta pyserial. Instale con: python -m pip install -r requirements.txt")
    raise

# ---------------------------------------------------------------------------
# Constantes del protocolo STPM3x
# ---------------------------------------------------------------------------

DCLK_HZ = 7812.5          # frecuencia de muestreo del DSP
FCLK_HZ = 125000.0        # reloj de 125 kHz para el medidor de período
FRAME_LEN_CRC = 5         # 4 datos + CRC
FRAME_LEN_NO_CRC = 4      # 4 datos
CRC8_POLY = 0x07

# Direcciones de lectura (espacio de 32 bits, una fila por dirección)
ADDR_DSP_CR3 = 0x04       # configuración (auto-latch)
ADDR_DSP_CR5 = 0x08       # CHV1
ADDR_DSP_CR6 = 0x0A       # CHC1
ADDR_DSP_CR7 = 0x0C       # CHV2
ADDR_DSP_CR8 = 0x0E       # CHC2
ADDR_DFE_CR1 = 0x18       # ganancia C1
ADDR_DFE_CR2 = 0x1A       # ganancia C2
ADDR_PERIOD = 0x2E        # período de línea
ADDR_RMS = 0x48           # V1 RMS [14:0] + C1 RMS [31:15]
ADDR_RMS2 = 0x4A          # V2 RMS [14:0] + C2 RMS [31:15]
ADDR_P1 = 0x5C            # PH1 Active Power
ADDR_E1 = 0x54            # PH1 Active Energy
ADDR_E2 = 0x6C            # PH2 Active Energy
ADDR_P2 = 0x74            # PH2 Active Power

# Direcciones de escritura (16 bits por media fila)
WR_DSP_CR3_LSW = 0x04
WR_DSP_CR3_MSW = 0x05

GAIN_MAP = {0: 2, 1: 4, 2: 8, 3: 16}


# ---------------------------------------------------------------------------
# CRC del protocolo UART del STPM3x
# ---------------------------------------------------------------------------

def _reverse_bits(value: int) -> int:
    value &= 0xFF
    value = ((value & 0xF0) >> 4) | ((value & 0x0F) << 4)
    value = ((value & 0xCC) >> 2) | ((value & 0x33) << 2)
    value = ((value & 0xAA) >> 1) | ((value & 0x55) << 1)
    return value & 0xFF


def crc8_spi(data: Sequence[int], poly: int = CRC8_POLY) -> int:
    """CRC8 poly 0x07, MSB first (el que usa el SPI del STPM3x)."""
    crc = 0
    for byte in data:
        b = byte & 0xFF
        for _ in range(8):
            if (b ^ crc) & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
            b = (b << 1) & 0xFF
    return crc & 0xFF


def crc8_uart(data: Sequence[int], poly: int = CRC8_POLY) -> int:
    """
    CRC del UART: se invierten los bits de la trama, se calcula el CRC8
    y se invierte el resultado (UM2066, sección 2.3.2).
    """
    reversed_frame = [_reverse_bits(b) for b in data]
    return _reverse_bits(crc8_spi(reversed_frame, poly))


# ---------------------------------------------------------------------------
# Excepciones
# ---------------------------------------------------------------------------

class STPM3xError(Exception):
    """Error genérico de comunicación con el STPM3x."""


class STPM3xTimeout(STPM3xError):
    """No llegaron los bytes esperados."""


class STPM3xCRCError(STPM3xError):
    """La respuesta llegó con CRC inválido."""


# ---------------------------------------------------------------------------
# Capa de comunicación
# ---------------------------------------------------------------------------

@dataclass
class Register:
    address: int
    value: int
    raw: bytes
    crc_ok: bool = True

    def __str__(self) -> str:
        return f"0x{self.address:02X}=0x{self.value:08X} ({self.raw.hex(' ')})"


class STPM3xUART:
    """
    Protocolo UART del STPM3x.

    Particularidad importante: la respuesta a una orden de lectura llega en la
    *siguiente* transacción (pipe-line).  Para leer N filas se envían N órdenes
    de lectura y una orden extra, y se descarta la primera respuesta.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        crc: bool = True,
        timeout: float = 0.6,
        gap: float = 0.004,
        verbose: bool = False,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.crc = crc
        self.timeout = timeout
        self.gap = gap
        self.verbose = verbose
        self.ser: Optional[serial.Serial] = None

    # -- ciclo de vida ------------------------------------------------------
    def open(self) -> None:
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
            write_timeout=1.0,
        )
        # DTR/RTS no se usan en la EVALSTPM33/34; dejarlos inactivos.
        try:
            self.ser.setDTR(False)
            self.ser.setRTS(False)
        except Exception:
            pass
        time.sleep(0.05)
        self.ser.reset_input_buffer()

    def close(self) -> None:
        if self.ser is not None:
            try:
                self.ser.close()
            finally:
                self.ser = None

    def __enter__(self) -> "STPM3xUART":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- tramas -------------------------------------------------------------
    def _make_frame(self, read_addr: int, write_addr: int, data: int) -> bytes:
        body = bytes(
            [
                read_addr & 0xFF,
                write_addr & 0xFF,
                data & 0xFF,
                (data >> 8) & 0xFF,
            ]
        )
        if self.crc:
            return body + bytes([crc8_uart(body)])
        return body

    def _read_response(self) -> Register:
        if self.ser is None:
            raise STPM3xError("Puerto no abierto")
        expected = FRAME_LEN_CRC if self.crc else FRAME_LEN_NO_CRC
        raw = bytearray()
        deadline = time.monotonic() + self.timeout
        while len(raw) < expected and time.monotonic() < deadline:
            chunk = self.ser.read(expected - len(raw))
            if chunk:
                raw.extend(chunk)
        if len(raw) != expected:
            raise STPM3xTimeout(
                f"Se esperaban {expected} bytes y llegaron {len(raw)}: "
                f"{bytes(raw).hex(' ') if raw else '(nada)'}"
            )
        if self.crc:
            ok = crc8_uart(raw[:4]) == raw[4]
            if self.verbose:
                print(f"RX {raw.hex(' ')}  crc={'OK' if ok else 'MAL'}")
            if not ok:
                raise STPM3xCRCError(f"CRC inválido en respuesta: {raw.hex(' ')}")
            value = int.from_bytes(raw[:4], "little")
        else:
            value = int.from_bytes(raw[:4], "little")
        return Register(0, value, bytes(raw), True)

    def _command(self, read_addr: int, write_addr: int, data: int) -> Register:
        if self.ser is None:
            raise STPM3xError("Puerto no abierto")
        frame = self._make_frame(read_addr, write_addr, data)
        if self.verbose:
            print(f"TX {frame.hex(' ')}")
        self.ser.write(frame)
        self.ser.flush()
        response = self._read_response()
        # Dejar un pequeño silencio entre tramas (frame delay del STPM3x).
        if self.gap:
            time.sleep(self.gap)
        return response

    # -- lectura / escritura ------------------------------------------------
    def read_rows(self, addresses: Sequence[int]) -> List[Register]:
        """
        Lee varias filas de 32 bits usando el pipe-line del STPM3x.

        Devuelve una lista en el mismo orden de `addresses`.  La primera
        respuesta (que corresponde a la orden anterior) se descarta.
        """
        addrs = list(addresses)
        if not addrs:
            return []

        # Descartar la respuesta pendiente de la orden anterior.
        self._command(addrs[0], 0xFF, 0xFFFF)

        results: List[Register] = []
        for addr in addrs[1:]:
            reg = self._command(addr, 0xFF, 0xFFFF)
            reg.address = addrs[len(results)]
            results.append(reg)

        # Orden extra para "empujar" la última lectura.
        reg = self._command(0xFF, 0xFF, 0xFFFF)
        reg.address = addrs[-1]
        results.append(reg)
        return results

    def read_row(self, address: int) -> Register:
        return self.read_rows([address])[0]

    def write_half(self, write_addr: int, data: int) -> None:
        # La escritura se ejecuta inmediatamente; la respuesta es la lectura
        # anterior y se descarta.
        self._command(0xFF, write_addr, data & 0xFFFF)

    def write_row(self, read_addr: int, value: int) -> None:
        self.write_half(read_addr, value & 0xFFFF)
        self.write_half(read_addr + 1, (value >> 16) & 0xFFFF)

    # -- configuración ------------------------------------------------------
    def ensure_auto_latch(self) -> int:
        """
        Activa el auto-latch (bit 23 de DSP_CR3) si no está activo.
        Devuelve el valor de DSP_CR3 leído antes de modificar.
        """
        before = self.read_row(ADDR_DSP_CR3).value
        if (before >> 23) & 1:
            return before
        # No reescribir bits de reset/latch que se autolimpian.
        after = (before & ~((1 << 20) | (1 << 21) | (1 << 22))) | (1 << 23)
        self.write_row(ADDR_DSP_CR3, after)
        check = self.read_row(ADDR_DSP_CR3).value
        if not ((check >> 23) & 1):
            raise STPM3xError(
                "No se pudo activar el auto-latch; revise la configuración "
                f"(DSP_CR3=0x{before:08X}, después=0x{check:08X})"
            )
        return before


# ---------------------------------------------------------------------------
# Escalas de la placa EVALSTPM33/34 V3
# ---------------------------------------------------------------------------

def _cal12(value: int) -> float:
    """Factor de calibración CHVx/CHCx (12 bits, 0x800 = 0.875)."""
    raw = value & 0xFFF
    return 0.75 + 0.125 * raw / 2048.0


@dataclass
class BoardConfig:
    """
    Constantes de la EVALSTPM33/34 V3:
      - divisor de tensión R1=810k (3x270k), R2=470
      - CT 4626-X002 2500:1 con carga 6R -> Ks=2.4 mV/A
      - shunt 0.3 mOhm -> Ks=0.3 mV/A
      - Vref típica 1.18 V (nominal 1.2 V)
    Si la placa o la calibración son distintas, use las opciones de línea.
    """

    vref: float = 1.18
    r1: float = 810_000.0
    r2: float = 470.0
    av: float = 2.0
    ks_ct: float = 6.0 / 2500.0          # V/A
    ks_shunt: float = 0.0003              # V/A (0.3 mOhm)
    gain1: int = 16
    gain2: int = 2
    calv1: float = 0.875
    cali1: float = 0.875
    calv2: float = 0.875
    cali2: float = 0.875
    sensor1: str = "auto"
    sensor2: str = "auto"

    def resolve_sensors(self) -> None:
        """
        Heurística para las placas estándar:
          - canal 1 con ganancia x16 -> shunt (EVALSTPM33)
          - canal 1 con ganancia x2  -> CT    (EVALSTPM34)
          - canal 2 con ganancia x2  -> CT
        Si el usuario pasó --sensor1/--sensor2, se respeta.
        """
        if self.sensor1 == "auto":
            self.sensor1 = "shunt" if self.gain1 >= 16 else "ct"
        if self.sensor2 == "auto":
            self.sensor2 = "ct" if self.gain2 <= 2 else "shunt"

    def ks(self, channel: int) -> float:
        sensor = self.sensor1 if channel == 1 else self.sensor2
        return self.ks_shunt if sensor == "shunt" else self.ks_ct

    def gain(self, channel: int) -> int:
        return self.gain1 if channel == 1 else self.gain2

    def cal_v(self, channel: int) -> float:
        return self.calv1 if channel == 1 else self.calv2

    def cal_i(self, channel: int) -> float:
        return self.cali1 if channel == 1 else self.cali2

    # LSB en unidades del SI
    def lsb_voltage(self, channel: int = 1) -> float:
        return (
            self.vref
            * (1.0 + self.r1 / self.r2)
            / (self.cal_v(channel) * self.av * 2**15)
        )

    def lsb_current(self, channel: int) -> float:
        return self.vref / (
            self.cal_i(channel)
            * self.gain(channel)
            * self.ks(channel)
            * 2**17
        )

    def lsb_power(self, channel: int) -> float:
        return (
            self.vref**2
            * (1.0 + self.r1 / self.r2)
            / (
                self.gain(channel)
                * self.av
                * self.ks(channel)
                * self.cal_v(channel)
                * self.cal_i(channel)
                * 2**28
            )
        )

    def lsb_energy(self, channel: int) -> float:
        """Wh por LSB del registro de energía."""
        return self.lsb_power(channel) * 2**28 / (
            3600.0 * DCLK_HZ * 2**17
        )

    def summary(self) -> str:
        return (
            f"Vref={self.vref:.3f} V, R1={self.r1/1000:.1f} k, R2={self.r2:.0f} Ohm\n"
            f"C1: {self.sensor1}, ganancia x{self.gain1}, Ks={self.ks(1)*1000:.3f} mV/A, "
            f"LSB={self.lsb_current(1)*1000:.4f} mA\n"
            f"C2: {self.sensor2}, ganancia x{self.gain2}, Ks={self.ks(2)*1000:.3f} mV/A, "
            f"LSB={self.lsb_current(2)*1000:.4f} mA\n"
            f"LSB V1={self.lsb_voltage(1)*1000:.4f} mV, "
            f"LSB P1={self.lsb_power(1)*1000:.4f} mW, "
            f"LSB E1={self.lsb_energy(1)*1e6:.4f} uWh"
        )


# ---------------------------------------------------------------------------
# Muestras y decodificación
# ---------------------------------------------------------------------------

def sign_extend(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value


@dataclass
class Sample:
    elapsed: float = 0.0
    v1: float = 0.0
    c1: float = 0.0
    v2: float = 0.0
    c2: float = 0.0
    p1: float = 0.0
    p2: float = 0.0
    s1: float = 0.0
    s2: float = 0.0
    q1: float = 0.0
    q2: float = 0.0
    pf1: float = 0.0
    pf2: float = 0.0
    f1: float = 0.0
    f2: float = 0.0
    e1_reg: float = 0.0
    e2_reg: float = 0.0
    e1_int: float = 0.0
    e2_int: float = 0.0
    raw: Dict[int, int] = field(default_factory=dict)


def decode_sample(regs: Sequence[Register], cfg: BoardConfig) -> Sample:
    if len(regs) != 7:
        raise ValueError(f"Se esperaban 7 registros y llegaron {len(regs)}")

    r48, r4a, r5c, r74, r2e, r54, r6c = (r.value for r in regs)

    v1_raw = r48 & 0x7FFF
    c1_raw = (r48 >> 15) & 0x1FFFF
    v2_raw = r4a & 0x7FFF
    c2_raw = (r4a >> 15) & 0x1FFFF

    p1_raw = sign_extend(r5c & 0x1FFFFFFF, 29)
    p2_raw = sign_extend(r74 & 0x1FFFFFFF, 29)

    period1 = r2e & 0xFFF
    period2 = (r2e >> 16) & 0xFFF
    f1 = FCLK_HZ / period1 if period1 else 0.0
    f2 = FCLK_HZ / period2 if period2 else 0.0

    v1 = v1_raw * cfg.lsb_voltage(1)
    c1 = c1_raw * cfg.lsb_current(1)
    v2 = v2_raw * cfg.lsb_voltage(2)
    c2 = c2_raw * cfg.lsb_current(2)
    p1 = p1_raw * cfg.lsb_power(1)
    p2 = p2_raw * cfg.lsb_power(2)

    s1 = v1 * c1
    s2 = v2 * c2
    q1 = math.sqrt(max(s1 * s1 - p1 * p1, 0.0))
    q2 = math.sqrt(max(s2 * s2 - p2 * p2, 0.0))
    pf1 = p1 / s1 if s1 > 1e-9 else 0.0
    pf2 = p2 / s2 if s2 > 1e-9 else 0.0
    pf1 = max(-1.0, min(1.0, pf1))
    pf2 = max(-1.0, min(1.0, pf2))

    e1 = (r54 & 0xFFFFFFFF) * cfg.lsb_energy(1)
    e2 = (r6c & 0xFFFFFFFF) * cfg.lsb_energy(2)

    return Sample(
        v1=v1,
        c1=c1,
        v2=v2,
        c2=c2,
        p1=p1,
        p2=p2,
        s1=s1,
        s2=s2,
        q1=q1,
        q2=q2,
        pf1=pf1,
        pf2=pf2,
        f1=f1,
        f2=f2,
        e1_reg=e1,
        e2_reg=e2,
        raw={
            ADDR_RMS: r48,
            ADDR_RMS2: r4a,
            ADDR_P1: r5c,
            ADDR_P2: r74,
            ADDR_PERIOD: r2e,
            ADDR_E1: r54,
            ADDR_E2: r6c,
        },
    )


# ---------------------------------------------------------------------------
# Fuentes de datos
# ---------------------------------------------------------------------------

class SerialSource:
    def __init__(
        self,
        device: STPM3xUART,
        cfg: BoardConfig,
        rate_hz: float = 5.0,
    ) -> None:
        self.device = device
        self.cfg = cfg
        self.rate_hz = rate_hz
        self.addresses = [
            ADDR_RMS,
            ADDR_RMS2,
            ADDR_P1,
            ADDR_P2,
            ADDR_PERIOD,
            ADDR_E1,
            ADDR_E2,
        ]

    def read(self) -> Sample:
        regs = self.device.read_rows(self.addresses)
        return decode_sample(regs, self.cfg)


class DemoSource:
    """Genera datos sintéticos para probar la interfaz sin placa."""

    def __init__(self, cfg: Optional[BoardConfig] = None, rate_hz: float = 5.0) -> None:
        self.cfg = cfg or BoardConfig()
        self.cfg.resolve_sensors()
        self.t0 = time.monotonic()
        self.e1 = 0.0
        self.e2 = 0.0
        self.last_t = 0.0
        self.rate_hz = rate_hz

    def read(self) -> Sample:
        t = time.monotonic() - self.t0
        dt = max(t - self.last_t, 1e-6)
        self.last_t = t

        v1 = 230.0 + 1.2 * math.sin(2 * math.pi * 0.07 * t) + 0.15 * math.sin(2 * math.pi * 3 * t)
        c1 = 5.0 + 0.35 * math.sin(2 * math.pi * 0.11 * t) + 0.03 * math.sin(2 * math.pi * 5 * t)
        p1 = v1 * c1 * 0.96
        v2 = 229.5 + 1.0 * math.sin(2 * math.pi * 0.05 * t + 0.5)
        c2 = 4.6 + 0.25 * math.sin(2 * math.pi * 0.09 * t + 1.0)
        p2 = v2 * c2 * 0.93

        self.e1 += p1 * dt / 3600.0
        self.e2 += p2 * dt / 3600.0

        s1 = v1 * c1
        s2 = v2 * c2
        q1 = math.sqrt(max(s1 * s1 - p1 * p1, 0.0))
        q2 = math.sqrt(max(s2 * s2 - p2 * p2, 0.0))

        def raw_v(v: float) -> int:
            return int(round(v / self.cfg.lsb_voltage(1))) & 0x7FFF

        def raw_i(c: float, ch: int) -> int:
            return int(round(c / self.cfg.lsb_current(ch))) & 0x1FFFF

        def raw_p(p: float, ch: int) -> int:
            return int(round(p / self.cfg.lsb_power(ch))) & 0x1FFFFFFF

        r48 = raw_v(v1) | (raw_i(c1, 1) << 15)
        r4a = raw_v(v2) | (raw_i(c2, 2) << 15)
        r5c = raw_p(p1, 1)
        r74 = raw_p(p2, 2)
        r2e = int(FCLK_HZ / 50.0) | (int(FCLK_HZ / 50.0) << 16)
        r54 = int(self.e1 / self.cfg.lsb_energy(1)) & 0xFFFFFFFF
        r6c = int(self.e2 / self.cfg.lsb_energy(2)) & 0xFFFFFFFF

        return Sample(
            elapsed=t,
            v1=v1,
            c1=c1,
            v2=v2,
            c2=c2,
            p1=p1,
            p2=p2,
            s1=s1,
            s2=s2,
            q1=q1,
            q2=q2,
            pf1=p1 / s1 if s1 else 0.0,
            pf2=p2 / s2 if s2 else 0.0,
            f1=50.0,
            f2=50.0,
            e1_reg=self.e1,
            e2_reg=self.e2,
            e1_int=self.e1,
            e2_int=self.e2,
            raw={
                ADDR_RMS: r48,
                ADDR_RMS2: r4a,
                ADDR_P1: r5c,
                ADDR_P2: r74,
                ADDR_PERIOD: r2e,
                ADDR_E1: r54,
                ADDR_E2: r6c,
            },
        )


# ---------------------------------------------------------------------------
# Detección y conexión
# ---------------------------------------------------------------------------

def list_serial_ports() -> List[str]:
    ports = list(list_ports.comports())
    if not ports:
        print("No hay puertos serie enumerados.")
        return []
    print("Puertos serie:")
    for p in ports:
        vid = f"{p.vid:04X}" if p.vid is not None else "----"
        pid = f"{p.pid:04X}" if p.pid is not None else "----"
        es_cp210x = (p.vid == 0x10C4 and p.pid == 0xEA60) or "CP210" in (p.description or "")
        marca = "  <-- CP210x (EVALSTPM33/34)" if es_cp210x else ""
        print(f"  {p.device:8s} VID:PID={vid}:{pid}  {p.description}{marca}")
    return [p.device for p in ports]


def find_cp210x() -> Optional[str]:
    for p in list_ports.comports():
        if (p.vid == 0x10C4 and p.pid == 0xEA60) or "CP210" in (p.description or ""):
            return p.device
    return None


def _probe_once(port: str, baudrate: int, crc: bool) -> bool:
    """Intenta abrir el puerto y leer la respuesta por defecto del STPM3x."""
    dev = STPM3xUART(port, baudrate=baudrate, crc=crc, timeout=0.5)
    try:
        dev.open()
        dev.ser.reset_input_buffer()
        # La primera respuesta tras el reset es 0xA0 00 00 04 75 (fila 0).
        reg = dev._command(0x04, 0xFF, 0xFFFF)
        if crc:
            # _command ya validó el CRC: si llegó, el dispositivo responde.
            return True
        # Sin CRC no hay validación; al menos descartar los patrones triviales.
        return reg.raw not in (b"\x00" * 4, b"\xFF" * 4)
    except (STPM3xError, serial.SerialException, OSError):
        return False
    finally:
        dev.close()


def probe_port(port: str) -> Tuple[int, bool]:
    """
    Busca la configuración del STPM3x.  Devuelve (baudrate, crc).
    Orden: 9600 con CRC (default), 9600 sin CRC, luego otros baudios.
    """
    for baudrate in (9600, 19200, 38400, 57600, 115200):
        for crc in (True, False):
            if _probe_once(port, baudrate, crc):
                return baudrate, crc
    raise STPM3xError(
        f"No hubo respuesta válida en {port}. Revise que el STPM3x GUI esté "
        "cerrado, que SW1 esté en UART y que la placa esté alimentada."
    )


def close_stpm_gui() -> None:
    """Cierra el GUI de ST si está abierto (Windows)."""
    import subprocess

    try:
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "STPM3x GUI.exe"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("STPM3x GUI cerrado.")
        else:
            print("STPM3x GUI no estaba abierto (o no se pudo cerrar).")
    except Exception as exc:
        print(f"No se pudo cerrar el STPM3x GUI: {exc}")


def connect(
    args: argparse.Namespace,
    verbose: bool = False,
) -> STPM3xUART:
    if getattr(args, "close_gui", False):
        close_stpm_gui()
    port = args.port
    if not port:
        port = find_cp210x()
    if not port:
        raise STPM3xError(
            "No se encontró el CP210x. Use --list para ver los puertos o "
            "--port COMx. Si la placa está conectada, cierre el STPM3x GUI."
        )

    if args.baud is None:
        if args.no_crc:
            baudrate, crc = 9600, False
        else:
            print(f"Detectando configuración UART en {port}...")
            baudrate, crc = probe_port(port)
    else:
        baudrate, crc = args.baud, not args.no_crc

    print(f"Puerto {port} @ {baudrate} bps, 8N1, CRC={'sí' if crc else 'no'}")
    dev = STPM3xUART(
        port,
        baudrate=baudrate,
        crc=crc,
        timeout=args.timeout,
        gap=args.gap,
        verbose=verbose,
    )
    dev.open()
    return dev


def open_device(
    args: argparse.Namespace,
    verbose: bool = False,
) -> Tuple[STPM3xUART, BoardConfig, "SerialSource"]:
    """Abre el puerto, activa auto-latch, lee la configuración y crea la fuente."""
    dev = connect(args, verbose=verbose)
    try:
        before = dev.ensure_auto_latch()
        print(f"Auto-latch DSP_CR3: 0x{before:08X} -> activado")
    except STPM3xError as exc:
        print(f"Advertencia: no se pudo activar auto-latch: {exc}")
    cfg = apply_cli_config(read_board_config(dev), args)
    source = SerialSource(dev, cfg, rate_hz=args.rate)
    return dev, cfg, source


def read_board_config(dev: STPM3xUART) -> BoardConfig:
    regs = dev.read_rows(
        [
            ADDR_DSP_CR3,
            ADDR_DSP_CR5,
            ADDR_DSP_CR6,
            ADDR_DSP_CR7,
            ADDR_DSP_CR8,
            ADDR_DFE_CR1,
            ADDR_DFE_CR2,
        ]
    )
    r04, r08, r0a, r0c, r0e, r18, r1a = (r.value for r in regs)

    cfg = BoardConfig(
        gain1=GAIN_MAP[(r18 >> 26) & 0x3],
        gain2=GAIN_MAP[(r1a >> 26) & 0x3],
        calv1=_cal12(r08),
        cali1=_cal12(r0a),
        calv2=_cal12(r0c),
        cali2=_cal12(r0e),
    )
    cfg.resolve_sensors()
    return cfg


def apply_cli_config(cfg: BoardConfig, args: argparse.Namespace) -> BoardConfig:
    if args.vref is not None:
        cfg.vref = args.vref
    if args.r1 is not None:
        cfg.r1 = args.r1
    if args.r2 is not None:
        cfg.r2 = args.r2
    if args.av is not None:
        cfg.av = args.av
    if args.ks_ct is not None:
        cfg.ks_ct = args.ks_ct / 1000.0
    if args.ks_shunt is not None:
        cfg.ks_shunt = args.ks_shunt / 1000.0
    if args.sensor1 is not None:
        cfg.sensor1 = args.sensor1
    if args.sensor2 is not None:
        cfg.sensor2 = args.sensor2
    cfg.resolve_sensors()
    return cfg


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "timestamp",
    "elapsed_s",
    "v1_rms_v",
    "c1_rms_a",
    "v2_rms_v",
    "c2_rms_a",
    "p1_w",
    "p2_w",
    "q1_var",
    "q2_var",
    "s1_va",
    "s2_va",
    "pf1",
    "pf2",
    "f1_hz",
    "f2_hz",
    "e1_reg_wh",
    "e2_reg_wh",
    "e1_int_wh",
    "e2_int_wh",
    "raw_48",
    "raw_4a",
    "raw_5c",
    "raw_74",
    "raw_2e",
    "raw_54",
    "raw_6c",
]


class CsvLogger:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.fh = open(path, "w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.fh, fieldnames=CSV_FIELDS)
        self.writer.writeheader()

    def write(self, sample: Sample) -> None:
        self.writer.writerow(
            {
                "timestamp": datetime.now().astimezone().isoformat(timespec="milliseconds"),
                "elapsed_s": f"{sample.elapsed:.6f}",
                "v1_rms_v": f"{sample.v1:.6f}",
                "c1_rms_a": f"{sample.c1:.6f}",
                "v2_rms_v": f"{sample.v2:.6f}",
                "c2_rms_a": f"{sample.c2:.6f}",
                "p1_w": f"{sample.p1:.6f}",
                "p2_w": f"{sample.p2:.6f}",
                "q1_var": f"{sample.q1:.6f}",
                "q2_var": f"{sample.q2:.6f}",
                "s1_va": f"{sample.s1:.6f}",
                "s2_va": f"{sample.s2:.6f}",
                "pf1": f"{sample.pf1:.6f}",
                "pf2": f"{sample.pf2:.6f}",
                "f1_hz": f"{sample.f1:.6f}",
                "f2_hz": f"{sample.f2:.6f}",
                "e1_reg_wh": f"{sample.e1_reg:.9f}",
                "e2_reg_wh": f"{sample.e2_reg:.9f}",
                "e1_int_wh": f"{sample.e1_int:.9f}",
                "e2_int_wh": f"{sample.e2_int:.9f}",
                "raw_48": f"0x{sample.raw.get(ADDR_RMS, 0):08X}",
                "raw_4a": f"0x{sample.raw.get(ADDR_RMS2, 0):08X}",
                "raw_5c": f"0x{sample.raw.get(ADDR_P1, 0):08X}",
                "raw_74": f"0x{sample.raw.get(ADDR_P2, 0):08X}",
                "raw_2e": f"0x{sample.raw.get(ADDR_PERIOD, 0):08X}",
                "raw_54": f"0x{sample.raw.get(ADDR_E1, 0):08X}",
                "raw_6c": f"0x{sample.raw.get(ADDR_E2, 0):08X}",
            }
        )
        self.fh.flush()

    def close(self) -> None:
        try:
            self.fh.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Gráficas en vivo
# ---------------------------------------------------------------------------

class LivePlot:
    def __init__(self, window_s: float = 120.0, title: str = "STPM34") -> None:
        import matplotlib.pyplot as plt  # importación perezosa

        self.plt = plt
        self.window_s = window_s
        self.maxlen = 5000
        self.t = deque(maxlen=self.maxlen)
        self.v1 = deque(maxlen=self.maxlen)
        self.v2 = deque(maxlen=self.maxlen)
        self.c1 = deque(maxlen=self.maxlen)
        self.c2 = deque(maxlen=self.maxlen)
        self.p1 = deque(maxlen=self.maxlen)
        self.p2 = deque(maxlen=self.maxlen)
        self.pf1 = deque(maxlen=self.maxlen)
        self.pf2 = deque(maxlen=self.maxlen)
        self.f1 = deque(maxlen=self.maxlen)

        plt.ion()
        self.fig, axes = plt.subplots(4, 1, sharex=True, figsize=(11.5, 9.5))
        self.fig.suptitle(title)
        self.ax_v, self.ax_i, self.ax_p, self.ax_pf = axes

        (self.ln_v1,) = self.ax_v.plot([], [], label="V1", color="#1f77b4")
        (self.ln_v2,) = self.ax_v.plot([], [], label="V2", color="#ff7f0e")
        (self.ln_c1,) = self.ax_i.plot([], [], label="C1", color="#2ca02c")
        (self.ln_c2,) = self.ax_i.plot([], [], label="C2", color="#d62728")
        (self.ln_p1,) = self.ax_p.plot([], [], label="P1", color="#9467bd")
        (self.ln_p2,) = self.ax_p.plot([], [], label="P2", color="#8c564b")
        (self.ln_pf1,) = self.ax_pf.plot([], [], label="PF1", color="#17becf")
        (self.ln_pf2,) = self.ax_pf.plot([], [], label="PF2", color="#e377c2")

        self.ax_v.set_ylabel("Tensión RMS [V]")
        self.ax_i.set_ylabel("Corriente RMS [A]")
        self.ax_p.set_ylabel("Potencia activa [W]")
        self.ax_pf.set_ylabel("Factor de potencia")
        self.ax_pf.set_xlabel("Tiempo [s]")
        self.ax_pf.set_ylim(-1.1, 1.1)
        for ax in axes:
            ax.grid(True, alpha=0.3)
            ax.legend(loc="upper left")
        self.fig.tight_layout(rect=(0, 0, 1, 0.96))

    def update(self, s: Sample) -> None:
        self.t.append(s.elapsed)
        self.v1.append(s.v1)
        self.v2.append(s.v2)
        self.c1.append(s.c1)
        self.c2.append(s.c2)
        self.p1.append(s.p1)
        self.p2.append(s.p2)
        self.pf1.append(s.pf1)
        self.pf2.append(s.pf2)
        self.f1.append(s.f1)

        for line, data in (
            (self.ln_v1, self.v1),
            (self.ln_v2, self.v2),
            (self.ln_c1, self.c1),
            (self.ln_c2, self.c2),
            (self.ln_p1, self.p1),
            (self.ln_p2, self.p2),
            (self.ln_pf1, self.pf1),
            (self.ln_pf2, self.pf2),
        ):
            line.set_data(self.t, data)

        if self.window_s and self.t:
            self.ax_v.set_xlim(max(0.0, self.t[-1] - self.window_s), max(self.window_s, self.t[-1]))
        for ax in (self.ax_v, self.ax_i, self.ax_p):
            ax.relim()
            ax.autoscale_view()
        self.fig.suptitle(
            f"STPM34  |  t={s.elapsed:7.1f} s  |  f1={s.f1:5.2f} Hz  |  "
            f"V1={s.v1:7.2f} V  I1={s.c1:6.3f} A  P1={s.p1:8.1f} W  PF1={s.pf1:5.3f}"
        )
        self.plt.pause(0.001)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(path, dpi=150, bbox_inches="tight")
        print(f"Gráfica guardada en {path}")

    def close(self) -> None:
        try:
            self.plt.ioff()
            self.plt.close(self.fig)
        except Exception:
            pass


def plot_csv(path: Path, save: Optional[Path] = None) -> None:
    import matplotlib

    if save is not None:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows: List[Dict[str, float]] = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            numeric: Dict[str, float] = {}
            for key, value in row.items():
                if key == "timestamp" or key.startswith("raw_") or value in (None, ""):
                    continue
                try:
                    numeric[key] = float(value)
                except (TypeError, ValueError):
                    continue
            if "elapsed_s" in numeric:
                rows.append(numeric)
    if not rows:
        raise SystemExit(f"No hay datos numéricos en {path}")

    t = [r["elapsed_s"] for r in rows]
    fig, axes = plt.subplots(4, 1, sharex=True, figsize=(11.5, 9.5))
    fig.suptitle(f"STPM34 — {path.name}")
    ax_v, ax_i, ax_p, ax_pf = axes
    for key, label, ax in (
        ("v1_rms_v", "V1", ax_v),
        ("v2_rms_v", "V2", ax_v),
        ("c1_rms_a", "C1", ax_i),
        ("c2_rms_a", "C2", ax_i),
        ("p1_w", "P1", ax_p),
        ("p2_w", "P2", ax_p),
        ("pf1", "PF1", ax_pf),
        ("pf2", "PF2", ax_pf),
    ):
        if key in rows[0]:
            ax.plot(t, [r[key] for r in rows], label=label)
    ax_v.set_ylabel("Tensión RMS [V]")
    ax_i.set_ylabel("Corriente RMS [A]")
    ax_p.set_ylabel("Potencia activa [W]")
    ax_pf.set_ylabel("Factor de potencia")
    ax_pf.set_xlabel("Tiempo [s]")
    ax_pf.set_ylim(-1.1, 1.1)
    for ax in axes:
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    if save is not None:
        save.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save, dpi=150, bbox_inches="tight")
        print(f"Gráfica guardada en {save}")
    else:
        plt.show()


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------

def default_csv_path() -> Path:
    base = Path(__file__).resolve().parent / "capturas"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return base / f"stpm34_{stamp}.csv"


def run_capture(args: argparse.Namespace) -> None:
    dev: Optional[STPM3xUART] = None
    source: object
    cfg: BoardConfig

    if args.demo:
        cfg = apply_cli_config(BoardConfig(), args)
        source = DemoSource(cfg, rate_hz=args.rate)
        print("Modo demostración: datos sintéticos, sin puerto serie.")
    else:
        while True:
            try:
                dev, cfg, source = open_device(args, verbose=args.verbose)
                break
            except (STPM3xError, serial.SerialException, OSError) as exc:
                if not args.wait:
                    raise SystemExit(
                        f"No se pudo conectar: {exc}\n"
                        "Cierre el STPM3x GUI, revise el cable/alimentación o use --wait."
                    )
                print(f"Sin conexión: {exc}")
                print("Reintentando en 2 s... Ctrl+C para salir.")
                time.sleep(2.0)

    print("\nConfiguración de escalas:")
    print(cfg.summary())
    print()

    logger: Optional[CsvLogger] = None
    csv_path = Path(args.csv) if args.csv else default_csv_path()
    if not args.no_csv:
        logger = CsvLogger(csv_path)
        print(f"CSV: {csv_path}")

    plot: Optional[LivePlot] = None
    if args.plot:
        try:
            plot = LivePlot(window_s=args.window, title="STPM34 — captura en vivo")
        except Exception as exc:
            print(f"No se pudo abrir la ventana de gráficas ({exc}); sigo sin gráfica.")
            plot = None

    t0 = time.monotonic()
    last_print = 0.0
    interval = 1.0 / args.rate if args.rate > 0 else 0.2
    e1_int = 0.0
    e2_int = 0.0
    last_sample_t = 0.0

    print("Capturando... Ctrl+C para detener.")
    try:
        while True:
            loop_start = time.monotonic()
            try:
                sample = source.read()  # type: ignore[attr-defined]
            except (STPM3xError, serial.SerialException, OSError) as exc:
                print(f"\nError de comunicación: {exc}")
                if not args.wait or args.demo:
                    raise
                # Reconectar hasta lograrlo, sin salir del bucle.
                while True:
                    if dev is not None:
                        try:
                            dev.close()
                        except Exception:
                            pass
                        dev = None
                    print("Reintentando en 2 s...")
                    time.sleep(2.0)
                    try:
                        dev, cfg, source = open_device(args, verbose=args.verbose)
                        last_sample_t = time.monotonic() - t0
                        break
                    except (STPM3xError, serial.SerialException, OSError) as exc2:
                        print(f"Sigue sin conexión: {exc2}")
                continue

            elapsed = time.monotonic() - t0
            sample.elapsed = elapsed
            dt = max(elapsed - last_sample_t, 1e-6)
            last_sample_t = elapsed
            e1_int += sample.p1 * dt / 3600.0
            e2_int += sample.p2 * dt / 3600.0
            sample.e1_int = e1_int
            sample.e2_int = e2_int

            if logger is not None:
                logger.write(sample)
            if plot is not None:
                plot.update(sample)

            if elapsed - last_print >= max(args.print_every, 0.2):
                last_print = elapsed
                print(
                    f"t={elapsed:7.1f}s  V1={sample.v1:7.2f}V  C1={sample.c1:7.3f}A  "
                    f"P1={sample.p1:9.2f}W  PF1={sample.pf1:5.3f}  f1={sample.f1:5.2f}Hz  "
                    f"V2={sample.v2:7.2f}V  C2={sample.c2:7.3f}A  P2={sample.p2:9.2f}W"
                )

            if args.duration and elapsed >= args.duration:
                break

            # Mantener el ritmo pedido
            sleep = interval - (time.monotonic() - loop_start)
            if sleep > 0:
                time.sleep(sleep)
    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")
    finally:
        if plot is not None:
            if args.save:
                plot.save(Path(args.save))
            plot.close()
        if logger is not None:
            logger.close()
            print(f"Datos guardados en {logger.path}")
        if dev is not None:
            dev.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Captura y grafica un STPM33/STPM34 (EVALSTPM33/34) por UART.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--list", action="store_true", help="Lista los puertos serie y sale.")
    p.add_argument("--port", help="Puerto serie (ej. COM3). Si no se indica, busca el CP210x.")
    p.add_argument("--baud", type=int, help="Baudios. Si no se indica, se detectan.")
    p.add_argument("--no-crc", action="store_true", help="Usar tramas sin CRC (4 bytes).")
    p.add_argument("--wait", action="store_true", help="Esperar/reconectar si la placa no está.")
    p.add_argument("--close-gui", action="store_true", help="Cerrar STPM3x GUI.exe antes de conectar (Windows).")
    p.add_argument("--timeout", type=float, default=0.6, help="Timeout de lectura serie [s].")
    p.add_argument("--gap", type=float, default=0.004, help="Pausa entre tramas [s].")
    p.add_argument("--rate", type=float, default=5.0, help="Muestras por segundo.")
    p.add_argument("--duration", type=float, default=0.0, help="Duración [s]; 0 = infinito.")
    p.add_argument("--window", type=float, default=120.0, help="Ventana de la gráfica [s].")
    p.add_argument("--plot", dest="plot", action="store_true", default=False, help="Mostrar gráficas en vivo.")
    p.add_argument("--no-plot", dest="plot", action="store_false", default=False, help="No mostrar gráficas (predeterminado).")
    p.add_argument("--save", help="Guardar la gráfica final en un PNG.")
    p.add_argument("--csv", help="Ruta del CSV de salida.")
    p.add_argument("--no-csv", action="store_true", help="No guardar CSV.")
    p.add_argument("--demo", action="store_true", help="Datos sintéticos, sin placa.")
    p.add_argument("--verbose", action="store_true", help="Mostrar tramas TX/RX.")
    p.add_argument("--print-every", type=float, default=1.0, help="Periodo del resumen en consola [s].")
    p.add_argument("--plot-csv", help="Graficar un CSV ya guardado y salir.")

    # Escalas
    p.add_argument("--vref", type=float, help="Vref interna [V] (típica 1.18, nominal 1.2).")
    p.add_argument("--r1", type=float, help="Resistencia superior del divisor [Ohm].")
    p.add_argument("--r2", type=float, help="Resistencia inferior del divisor [Ohm].")
    p.add_argument("--av", type=float, help="Ganancia del canal de tensión.")
    p.add_argument("--ks-ct", type=float, help="Sensibilidad del CT [mV/A] (6R/2500 = 2.4).")
    p.add_argument("--ks-shunt", type=float, help="Sensibilidad del shunt [mV/A] (0.3 mOhm = 0.3).")
    p.add_argument("--sensor1", choices=["auto", "ct", "shunt"], help="Sensor del canal 1.")
    p.add_argument("--sensor2", choices=["auto", "ct", "shunt"], help="Sensor del canal 2.")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        list_serial_ports()
        return 0

    if args.plot_csv:
        plot_csv(Path(args.plot_csv), Path(args.save) if args.save else None)
        return 0

    run_capture(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
