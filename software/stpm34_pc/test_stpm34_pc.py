# -*- coding: utf-8 -*-
"""
Pruebas básicas del protocolo y de las escalas del STPM3x.

Ejecutar:
    python -m unittest -v test_stpm34_pc.py
"""

import unittest

import stpm34_pc as s


class TestCRC(unittest.TestCase):
    def test_crc_uart_default_response(self):
        # Respuesta inicial del STPM3x: A0 00 00 04 75
        self.assertEqual(s.crc8_uart([0xA0, 0x00, 0x00, 0x04]), 0x75)

    def test_crc_uart_write_example(self):
        # UM2066: trama 0xFF 08 FA F7 -> CRC UART 0xFC
        self.assertEqual(s.crc8_uart([0xFF, 0x08, 0xFA, 0xF7]), 0xFC)

    def test_crc_spi_write_example(self):
        # UM2066: misma trama en SPI -> CRC 0xDD
        self.assertEqual(s.crc8_spi([0xFF, 0x08, 0xFA, 0xF7]), 0xDD)


class TestEscalas(unittest.TestCase):
    def setUp(self):
        self.cfg = s.BoardConfig()
        self.cfg.resolve_sensors()

    def test_voltage_lsb(self):
        # 35.484 mV/LSB para R1=810k, R2=470, Vref=1.18, calV=0.875, Av=2
        self.assertAlmostEqual(self.cfg.lsb_voltage(1), 0.035484044, places=8)

    def test_current_lsb(self):
        # Canal 1 (shunt x16) y canal 2 (CT x2): 2.1435 mA/LSB
        self.assertAlmostEqual(self.cfg.lsb_current(1), 0.0021435, places=6)
        self.assertAlmostEqual(self.cfg.lsb_current(2), 0.0021435, places=6)

    def test_power_lsb(self):
        # 1.217 mW/LSB
        self.assertAlmostEqual(self.cfg.lsb_power(1), 0.001217, places=5)

    def test_energy_lsb(self):
        # 8.86e-8 Wh/LSB
        self.assertAlmostEqual(self.cfg.lsb_energy(1), 8.86e-8, places=10)


class TestDecode(unittest.TestCase):
    def setUp(self):
        self.cfg = s.BoardConfig()
        self.cfg.resolve_sensors()

    def test_sign_extend(self):
        self.assertEqual(s.sign_extend(0x1FFFFFFF, 29), -1)
        self.assertEqual(s.sign_extend(0x0FFFFFFF, 29), 0x0FFFFFFF)

    def test_decode_sample(self):
        v1_raw = int(round(230.0 / self.cfg.lsb_voltage(1)))
        c1_raw = int(round(5.0 / self.cfg.lsb_current(1)))
        c2_raw = int(round(4.0 / self.cfg.lsb_current(2)))
        p1_raw = int(round(1100.0 / self.cfg.lsb_power(1)))
        p2_raw = int(round(900.0 / self.cfg.lsb_power(2)))

        r48 = (v1_raw & 0x7FFF) | ((c1_raw & 0x1FFFF) << 15)
        r4a = ((c2_raw & 0x1FFFF) << 15)
        r5c = p1_raw & 0x1FFFFFFF
        r74 = p2_raw & 0x1FFFFFFF
        r2e = 2500 | (2500 << 16)
        r54 = 0
        r6c = 0

        regs = [
            s.Register(s.ADDR_RMS, r48, b""),
            s.Register(s.ADDR_RMS2, r4a, b""),
            s.Register(s.ADDR_P1, r5c, b""),
            s.Register(s.ADDR_P2, r74, b""),
            s.Register(s.ADDR_PERIOD, r2e, b""),
            s.Register(s.ADDR_E1, r54, b""),
            s.Register(s.ADDR_E2, r6c, b""),
        ]
        sample = s.decode_sample(regs, self.cfg)
        self.assertAlmostEqual(sample.v1, 230.0, delta=0.05)
        self.assertAlmostEqual(sample.c1, 5.0, delta=0.005)
        self.assertAlmostEqual(sample.c2, 4.0, delta=0.005)
        self.assertAlmostEqual(sample.p1, 1100.0, delta=2.0)
        self.assertAlmostEqual(sample.p2, 900.0, delta=2.0)
        self.assertAlmostEqual(sample.f1, 50.0, places=6)
        self.assertAlmostEqual(sample.f2, 50.0, places=6)


class FakeSerial:
    """Emula el pipe-line del STPM3x: la respuesta es la orden anterior."""

    def __init__(self, rows):
        self.rows = dict(rows)
        self.pending = 0x040000A0
        self.out = b""
        self.last_addr = 0

    def write(self, frame):
        ra = frame[0]
        # La respuesta que sale ahora es la pendiente
        body = self.pending.to_bytes(4, "little")
        self.out = body + bytes([s.crc8_uart(body)])
        if s.crc8_uart(frame[:4]) != frame[4]:
            raise AssertionError("CRC de escritura inválido")
        if ra != 0xFF:
            self.last_addr = ra
            self.pending = self.rows.get(ra, 0)
        else:
            # lectura incremental: siguiente fila (solo para la prueba)
            self.last_addr = (self.last_addr + 2) & 0xFF
            self.pending = self.rows.get(self.last_addr, 0)

    def read(self, n):
        data = self.out[:n]
        self.out = self.out[n:]
        return data

    def flush(self):
        pass


class TestPipeline(unittest.TestCase):
    def test_read_rows_order(self):
        rows = {0x48: 0x11223344, 0x4A: 0x55667788}
        dev = s.STPM3xUART("COMX", timeout=0.1, gap=0.0)
        dev.ser = FakeSerial(rows)
        dev.crc = True
        regs = dev.read_rows([0x48, 0x4A])
        self.assertEqual([r.value for r in regs], [0x11223344, 0x55667788])
        self.assertEqual([r.address for r in regs], [0x48, 0x4A])


if __name__ == "__main__":
    unittest.main()
