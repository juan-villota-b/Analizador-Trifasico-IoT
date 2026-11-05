(() => {
  "use strict";

  // -------------------------------------------------------------------------
  // DOM
  // -------------------------------------------------------------------------
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const els = {
    sourcePill: $("#sourcePill"),
    connPill: $("#connPill"),
    fpsText: $("#fpsText"),
    fsPill: $("#fsPill"),
    freqPill: $("#freqPill"),
    tabs: $$(".tab"),
    viewToggle: $("#viewToggle"),
    cyclesSelect: $("#cyclesSelect"),
    lineFreqSelect: $("#lineFreqSelect"),
    triggerSelect: $("#triggerSelect"),
    pauseBtn: $("#pauseBtn"),
    clearBtn: $("#clearBtn"),
    chartTitle: $("#chartTitle"),
    chartSubtitle: $("#chartSubtitle"),
    phaseReadout: $("#phaseReadout"),
    separateCharts: $("#separateCharts"),
    combinedChart: $("#combinedChart"),
    voltageCanvas: $("#voltageCanvas"),
    currentCanvas: $("#currentCanvas"),
    combinedCanvas: $("#combinedCanvas"),
    vLabelHint: $("#vLabelHint"),
    iLabelHint: $("#iLabelHint"),
    sampleInfo: $("#sampleInfo"),
    rxInfo: $("#rxInfo"),
    tableUpdated: $("#tableUpdated"),
    statVrms: $("#statVrms"),
    statIrms: $("#statIrms"),
    statVpeak: $("#statVpeak"),
    statIpeak: $("#statIpeak"),
    statVpp: $("#statVpp"),
    statIpp: $("#statIpp"),
    statFreq: $("#statFreq"),
    statPhase: $("#statPhase"),
    statPf: $("#statPf"),
    statP: $("#statP"),
    statS: $("#statS"),
    statQ: $("#statQ"),
    statN: $("#statN"),
    autoV: $("#autoV"),
    vScaleRange: $("#vScaleRange"),
    vScaleInput: $("#vScaleInput"),
    autoI: $("#autoI"),
    iScaleRange: $("#iScaleRange"),
    iScaleInput: $("#iScaleInput"),
    sourceSelect: $("#sourceSelect"),
    wsUrl: $("#wsUrl"),
    connectBtn: $("#connectBtn"),
    sourceHint: $("#sourceHint"),
    uartControls: $("#uartControls"),
    uartPort: $("#uartPort"),
    uartBaud: $("#uartBaud"),
    uartCrc: $("#uartCrc"),
  };

  // -------------------------------------------------------------------------
  // Constantes y estado
  // -------------------------------------------------------------------------
  const COLORS = {
    voltage: "#38bdf8",
    current: "#f59e0b",
    grid: "#1e293b",
    gridSoft: "#162235",
    zero: "#334155",
    text: "#cbd5e1",
    muted: "#8ca0b8",
    faint: "#64748b",
    plotBg: "#0b1322",
  };

  const CAPACITY = 32768;
  const MIN_FRAME_MS = 1000 / 60 - 1;

  const state = {
    channel: 1,
    view: "separate",
    cycles: 2,
    lineFreq: 60,
    trigger: "auto",
    paused: false,
    source: "demo",
    fs: 7812.5,
    fps: 0,
    rxSamples: 0,
    lastStatsAt: 0,
    lastStatusAt: 0,
    stats: { 1: null, 2: null },
    chipMetrics: { 1: null, 2: null },
    uartStatus: "",
    sourceError: false,
    channels: {
      1: { autoV: true, autoI: true, vMax: 400, iMax: 10 },
      2: { autoV: true, autoI: true, vMax: 400, iMax: 10 },
    },
  };

  // -------------------------------------------------------------------------
  // Utilidades
  // -------------------------------------------------------------------------
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

  function niceCeil(value, minimum) {
    if (!Number.isFinite(value) || value <= 0) return minimum;
    const exp = Math.floor(Math.log10(value));
    const base = 10 ** exp;
    const m = value / base;
    const step = m <= 1 ? 1 : m <= 1.5 ? 1.5 : m <= 2 ? 2 : m <= 2.5 ? 2.5
      : m <= 3 ? 3 : m <= 4 ? 4 : m <= 5 ? 5 : m <= 6 ? 6 : m <= 8 ? 8 : 10;
    return Math.max(minimum, step * base);
  }

  function fmt(value, digits = 2) {
    return Number.isFinite(value) ? value.toFixed(digits) : "—";
  }

  function signed(value, digits = 1) {
    if (!Number.isFinite(value)) return "—";
    return `${value >= 0 ? "+" : ""}${value.toFixed(digits)}`;
  }

  function nowLabel() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  // -------------------------------------------------------------------------
  // Buffer circular
  // -------------------------------------------------------------------------
  class RingBuffer {
    constructor(capacity) {
      this.capacity = capacity;
      this.t = new Float64Array(capacity);
      this.v = new Float32Array(capacity);
      this.i = new Float32Array(capacity);
      this.count = 0;
      this.head = 0;
    }

    clear() {
      this.count = 0;
      this.head = 0;
    }

    push(t, v, i) {
      const k = this.head;
      this.t[k] = t;
      this.v[k] = v;
      this.i[k] = i;
      this.head = (k + 1) % this.capacity;
      if (this.count < this.capacity) this.count += 1;
    }

    lastTime() {
      if (!this.count) return 0;
      const idx = (this.head - 1 + this.capacity) % this.capacity;
      return this.t[idx];
    }

    firstTime() {
      if (!this.count) return 0;
      const idx = (this.head - this.count + this.capacity) % this.capacity;
      return this.t[idx];
    }

    tAt(logical) {
      const idx = (this.head - this.count + logical + this.capacity * 2) % this.capacity;
      return this.t[idx];
    }

    vAt(logical) {
      const idx = (this.head - this.count + logical + this.capacity * 2) % this.capacity;
      return this.v[idx];
    }

    iAt(logical) {
      const idx = (this.head - this.count + logical + this.capacity * 2) % this.capacity;
      return this.i[idx];
    }

    lowerBound(time) {
      let lo = 0;
      let hi = this.count;
      while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (this.tAt(mid) < time) lo = mid + 1;
        else hi = mid;
      }
      return lo;
    }

    windowIndices(t0, t1) {
      if (!this.count) return { start: 0, end: -1 };
      const start = this.lowerBound(t0);
      let end = this.lowerBound(t1);
      if (end < this.count && this.tAt(end) <= t1) end += 1;
      return { start, end: Math.min(this.count, end) - 1 };
    }
  }

  const buffers = { 1: new RingBuffer(CAPACITY), 2: new RingBuffer(CAPACITY) };
  const timeCursor = { 1: 0, 2: 0 };

  // -------------------------------------------------------------------------
  // Fuente demo de alta tasa
  // -------------------------------------------------------------------------
  class DemoSource {
    constructor() {
      this.fs = 7812.5;
      this.running = false;
      this.phase = 0;
    }

    start() {
      this.running = true;
      this.phase = 0;
    }

    stop() {
      this.running = false;
    }

    reset() {
      this.phase = 0;
    }

    pump(dt, lineFreq) {
      if (!this.running) return null;
      const n = Math.max(1, Math.round(this.fs * clamp(dt, 0.001, 0.05)));
      const v1 = new Float32Array(n);
      const i1 = new Float32Array(n);
      const v2 = new Float32Array(n);
      const i2 = new Float32Array(n);
      const w = 2 * Math.PI * lineFreq;
      const ph1 = -25 * Math.PI / 180;
      const ph2 = -40 * Math.PI / 180;

      for (let k = 0; k < n; k += 1) {
        const t = this.phase + k / this.fs;
        const s1 = Math.sin(w * t);
        const s2 = Math.sin(w * t + 0.10);
        v1[k] = 325 * s1 + 0.02 * 325 * Math.sin(3 * w * t + 0.4) + (Math.random() - 0.5) * 0.35;
        i1[k] = 7.07 * Math.sin(w * t + ph1) + 0.03 * 7.07 * Math.sin(3 * w * t + ph1 + 0.8) + (Math.random() - 0.5) * 0.012;
        v2[k] = 325 * s2 + 0.018 * 325 * Math.sin(3 * w * t + 0.9) + (Math.random() - 0.5) * 0.35;
        i2[k] = 6.36 * Math.sin(w * t + 0.10 + ph2) + 0.025 * 6.36 * Math.sin(3 * w * t + ph2 + 1.2) + (Math.random() - 0.5) * 0.010;
      }

      this.phase += n / this.fs;
      if (this.phase > 20) this.phase -= 20;

      return {
        fs: this.fs,
        ch1: { v: v1, i: i1 },
        ch2: { v: v2, i: i2 },
      };
    }
  }

  const demo = new DemoSource();

  // -------------------------------------------------------------------------
  // Fuente WebSocket
  // -------------------------------------------------------------------------
  class WebSocketSource {
    constructor(onBatch, onMetrics, onStatus) {
      this.onBatch = onBatch;
      this.onMetrics = onMetrics;
      this.onStatus = onStatus;
      this.ws = null;
      this.url = "";
      this.keepAlive = false;
      this.connected = false;
      this.retryTimer = null;
    }

    connect(url) {
      this.close();
      this.url = url;
      this.keepAlive = true;
      this._open();
    }

    _open() {
      if (!this.keepAlive) return;
      let ws;
      try {
        ws = new WebSocket(this.url);
      } catch (err) {
        this.onStatus("disconnected", String(err));
        this._scheduleRetry();
        return;
      }
      this.ws = ws;
      ws.onopen = () => {
        this.connected = true;
        this.onStatus("connected");
      };
      ws.onmessage = (event) => {
        let msg;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }
        if (!msg) return;
        if (msg.type === "metrics") {
          this.onMetrics(msg);
          return;
        }
        if (msg.type === "status" || msg.type === "error") {
          this.onStatus(msg.type, msg.message);
          return;
        }
        if (msg.type === "samples" || msg.ch1 || msg.ch2) {
          this.onBatch(msg);
        }
      };
      ws.onerror = () => {
        this.connected = false;
      };
      ws.onclose = () => {
        this.connected = false;
        this.onStatus("disconnected");
        this.ws = null;
        this._scheduleRetry();
      };
    }

    _scheduleRetry() {
      if (!this.keepAlive) return;
      clearTimeout(this.retryTimer);
      this.retryTimer = setTimeout(() => this._open(), 2000);
    }

    close() {
      this.keepAlive = false;
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
      if (this.ws) {
        try { this.ws.close(); } catch { /* noop */ }
        this.ws = null;
      }
      this.connected = false;
    }
  }

  const wsSource = new WebSocketSource(
    (batch) => ingestBatch(batch),
    (msg) => ingestMetrics(msg),
    (status, detail) => {
      updateSourceStatus(status, detail);
    },
  );

  // -------------------------------------------------------------------------
  // Ingesta de datos
  // -------------------------------------------------------------------------
  function ingestBatch(batch) {
    if (state.paused) return;

    const fs = Number(batch.fs) || state.fs;
    if (Number.isFinite(fs) && fs > 0.5 && Math.abs(fs - state.fs) / state.fs > 0.5) {
      state.fs = fs;
      clearBuffers(false);
    } else if (Number.isFinite(fs) && fs > 0.5) {
      state.fs = fs;
    }

    for (const ch of [1, 2]) {
      const data = batch[`ch${ch}`];
      if (!data || !data.v || !data.i) continue;
      const n = Math.min(data.v.length, data.i.length);
      if (!n) continue;

      let cursor = timeCursor[ch];
      if (!cursor) cursor = performance.now() / 1000;

      const buf = buffers[ch];
      for (let k = 0; k < n; k += 1) {
        buf.push(cursor, Number(data.v[k]), Number(data.i[k]));
        cursor += 1 / state.fs;
      }
      timeCursor[ch] = cursor;
      state.rxSamples += n;
    }
  }

  function ingestMetrics(msg) {
    for (const ch of [1, 2]) {
      state.chipMetrics[ch] = msg[`ch${ch}`] || null;
    }
    if (state.paused) return;
    updateStatsAndScales();
  }

  function clearBuffers(update = true) {
    buffers[1].clear();
    buffers[2].clear();
    timeCursor[1] = 0;
    timeCursor[2] = 0;
    state.rxSamples = 0;
    state.stats[1] = null;
    state.stats[2] = null;
    state.chipMetrics[1] = null;
    state.chipMetrics[2] = null;
    if (update) {
      updateTable();
      updateStatus();
    }
  }

  // -------------------------------------------------------------------------
  // Gráfica Canvas
  // -------------------------------------------------------------------------
  class WaveChart {
    constructor(canvas, options = {}) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d", { alpha: false });
      this.options = options;
      this.w = 0;
      this.h = 0;
      this.dpr = 1;
      this._resize = this.resize.bind(this);
      window.addEventListener("resize", this._resize, { passive: true });
      if (typeof ResizeObserver !== "undefined") {
        this.observer = new ResizeObserver(() => this.resize());
        this.observer.observe(canvas);
      }
      this.resize();
    }

    resize() {
      const rect = this.canvas.getBoundingClientRect();
      const parentWidth = this.canvas.parentElement ? this.canvas.parentElement.clientWidth : 600;
      this.w = Math.max(1, rect.width || parentWidth || 600);
      this.h = Math.max(1, rect.height || 250);
      this.dpr = Math.min(window.devicePixelRatio || 1, 2);
      this.canvas.width = Math.round(this.w * this.dpr);
      this.canvas.height = Math.round(this.h * this.dpr);
      this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    }

    draw(buffer, cfg) {
      const ctx = this.ctx;
      const w = this.w;
      const h = this.h;
      const left = w < 520 ? 48 : 58;
      const right = cfg.showRight ? (w < 520 ? 48 : 58) : 18;
      const top = 22;
      const bottom = 30;
      const plotW = Math.max(10, w - left - right);
      const plotH = Math.max(10, h - top - bottom);
      const midY = top + plotH / 2;
      const yLeft = (value) => midY - (value / cfg.yLeftMax) * (plotH / 2);
      const yRight = (value) => midY - (value / cfg.yRightMax) * (plotH / 2);
      const xOfDeg = (deg) => left + (deg / cfg.xMaxDeg) * plotW;

      ctx.fillStyle = COLORS.plotBg;
      ctx.fillRect(0, 0, w, h);

      if (!buffer.count) {
        ctx.fillStyle = COLORS.faint;
        ctx.font = "12px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("Esperando datos…", w / 2, h / 2);
        return;
      }

      const tEnd = cfg.tEnd;
      const tStart = cfg.tStart;
      const { start, end } = buffer.windowIndices(tStart, tEnd);
      if (end < start) {
        ctx.fillStyle = COLORS.faint;
        ctx.font = "12px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("Esperando datos…", w / 2, h / 2);
        return;
      }

      // Rejilla
      ctx.lineWidth = 1;
      ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
      const xGridStep = 90;
      const xLabelStep = cfg.xMaxDeg <= 720 ? 180 : 360;
      ctx.textAlign = "center";
      ctx.textBaseline = "alphabetic";

      for (let deg = 0; deg <= cfg.xMaxDeg + 0.1; deg += xGridStep) {
        const x = Math.round(xOfDeg(deg)) + 0.5;
        ctx.strokeStyle = COLORS.gridSoft;
        ctx.beginPath();
        ctx.moveTo(x, top);
        ctx.lineTo(x, top + plotH);
        ctx.stroke();
        if (Math.abs(deg % xLabelStep) < 0.1 || Math.abs(deg - cfg.xMaxDeg) < 0.1) {
          ctx.fillStyle = COLORS.faint;
          ctx.fillText(`${Math.round(deg)}°`, x, h - 10);
        }
      }

      for (let k = 0; k <= 4; k += 1) {
        const y = Math.round(top + (k * plotH) / 4) + 0.5;
        ctx.strokeStyle = k === 2 ? COLORS.zero : COLORS.grid;
        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(left + plotW, y);
        ctx.stroke();

        const frac = 1 - k / 2;
        const vLabel = frac * cfg.yLeftMax;
        ctx.fillStyle = cfg.leftColor;
        ctx.textAlign = "right";
        ctx.fillText(formatAxis(vLabel, cfg.yLeftMax), left - 8, y + 3);

        if (cfg.showRight) {
          const iLabel = frac * cfg.yRightMax;
          ctx.fillStyle = cfg.rightColor;
          ctx.textAlign = "left";
          ctx.fillText(formatAxis(iLabel, cfg.yRightMax), left + plotW + 8, y + 3);
        }
      }

      // Etiquetas de eje
      ctx.font = "10px Inter, system-ui, sans-serif";
      ctx.textAlign = "left";
      ctx.fillStyle = cfg.leftColor;
      ctx.fillText(cfg.leftLabel, left, top - 8);
      if (cfg.showRight) {
        ctx.textAlign = "right";
        ctx.fillStyle = cfg.rightColor;
        ctx.fillText(cfg.rightLabel, left + plotW, top - 8);
      }

      // Series
      ctx.save();
      ctx.beginPath();
      ctx.rect(left, top, plotW, plotH);
      ctx.clip();

      for (const series of cfg.series) {
        const yOf = series.axis === "right" ? yRight : yLeft;
        const dataFn = series.key === "v" ? (idx) => buffer.vAt(idx) : (idx) => buffer.iAt(idx);
        this._drawSeries(buffer, start, end, tStart, cfg, xOfDeg, yOf, dataFn, series.color, plotW);
      }

      // Marcadores de cruce por cero en la vista combinada
      if (cfg.showRight) {
        this._drawCrossMarker(buffer, start, end, tStart, cfg, xOfDeg, top, plotH, "v", "V₀", COLORS.voltage);
        this._drawCrossMarker(buffer, start, end, tStart, cfg, xOfDeg, top, plotH, "i", "I₀", COLORS.current);
      }

      ctx.restore();

      // Borde del área de dibujo
      ctx.strokeStyle = COLORS.grid;
      ctx.lineWidth = 1;
      ctx.strokeRect(left + 0.5, top + 0.5, plotW - 1, plotH - 1);
    }

    _drawSeries(buffer, start, end, tStart, cfg, xOfDeg, yOf, dataFn, color, plotW) {
      const ctx = this.ctx;
      const n = end - start + 1;
      if (n <= 0) return;

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";

      if (n === 1) {
        const t = buffer.tAt(start);
        const deg = Math.max(0, Math.min(cfg.xMaxDeg, (t - tStart) * cfg.freq * 360));
        const x = xOfDeg(deg);
        const y = yOf(dataFn(start));
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 2.2, 0, Math.PI * 2);
        ctx.fill();
        return;
      }

      const step = n > plotW * 2 ? Math.ceil(n / (plotW * 2)) : 1;
      ctx.beginPath();
      let started = false;
      for (let idx = start; idx <= end; idx += step) {
        const t = buffer.tAt(idx);
        const deg = (t - tStart) * cfg.freq * 360;
        const x = xOfDeg(clamp(deg, -10, cfg.xMaxDeg + 10));
        const y = yOf(dataFn(idx));
        if (!started) {
          ctx.moveTo(x, y);
          started = true;
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    }

    _drawCrossMarker(buffer, start, end, tStart, cfg, xOfDeg, top, plotH, key, label, color) {
      const ctx = this.ctx;
      let prev = null;
      let prevT = null;
      let crossing = null;

      for (let idx = start; idx <= end; idx += 1) {
        const value = key === "v" ? buffer.vAt(idx) : buffer.iAt(idx);
        const t = buffer.tAt(idx);
        if (prev !== null && prev < 0 && value >= 0) {
          const frac = value !== prev ? -prev / (value - prev) : 0;
          crossing = prevT + frac * (t - prevT);
          break;
        }
        prev = value;
        prevT = t;
      }

      if (crossing === null) return;
      const deg = (crossing - tStart) * cfg.freq * 360;
      if (deg < 0 || deg > cfg.xMaxDeg) return;
      const x = Math.round(xOfDeg(deg)) + 0.5;

      ctx.save();
      ctx.strokeStyle = color;
      ctx.globalAlpha = 0.45;
      ctx.setLineDash([4, 5]);
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, top + plotH);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.globalAlpha = 1;
      ctx.fillStyle = color;
      ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
      ctx.textAlign = x < this.w / 2 ? "left" : "right";
      ctx.fillText(label, x + (x < this.w / 2 ? 4 : -4), top + 10);
      ctx.restore();
    }
  }

  function formatAxis(value, max) {
    if (Math.abs(value) < 0.0001) return "0";
    if (max < 1) return value.toFixed(2);
    if (max < 10) return value.toFixed(1);
    return value.toFixed(0);
  }

  const voltageChart = new WaveChart(els.voltageCanvas);
  const currentChart = new WaveChart(els.currentCanvas);
  const combinedChart = new WaveChart(els.combinedCanvas);

  // -------------------------------------------------------------------------
  // Ventana de visualización con trigger
  // -------------------------------------------------------------------------
  function getDisplayWindow(buffer, windowSec) {
    const last = buffer.lastTime();
    if (!buffer.count || state.trigger === "free") {
      return { tStart: last - windowSec, tEnd: last, triggered: false };
    }

    // Buscar el último cruce ascendente de tensión que deje una ventana
    // completa por delante. Así la onda queda fija en el eje.
    const searchStart = last - windowSec * 2.5;
    const { start, end } = buffer.windowIndices(searchStart, last);
    if (end < start) {
      return { tStart: last - windowSec, tEnd: last, triggered: false };
    }

    let trigger = null;
    let prevV = null;
    let prevT = null;
    let armed = false;
    const hysteresis = 1.0; // V: evita disparos por ruido alrededor de cero

    for (let idx = start; idx <= end; idx += 1) {
      const t = buffer.tAt(idx);
      const v = buffer.vAt(idx);
      if (v < -hysteresis) armed = true;
      if (armed && prevV !== null && prevV < 0 && v >= 0) {
        const frac = v !== prevV ? -prevV / (v - prevV) : 0;
        const crossing = prevT + frac * (t - prevT);
        if (crossing + windowSec <= last + 1e-9) trigger = crossing;
        armed = false;
      }
      prevV = v;
      prevT = t;
    }

    if (trigger !== null) {
      return { tStart: trigger, tEnd: trigger + windowSec, triggered: true };
    }
    return { tStart: last - windowSec, tEnd: last, triggered: false };
  }

  // -------------------------------------------------------------------------
  // Estadísticas
  // -------------------------------------------------------------------------
  function computeStats(buffer, tStart, tEnd, freqNominal) {
    const { start, end } = buffer.windowIndices(tStart, tEnd);
    const n = end - start + 1;
    if (n < 4) return null;

    let sumV2 = 0;
    let sumI2 = 0;
    let sumP = 0;
    let vMin = Infinity;
    let vMax = -Infinity;
    let iMin = Infinity;
    let iMax = -Infinity;
    let prevV = null;
    let prevVT = null;
    let prevI = null;
    let prevIT = null;
    const crossV = [];
    const crossI = [];

    for (let idx = start; idx <= end; idx += 1) {
      const t = buffer.tAt(idx);
      const v = buffer.vAt(idx);
      const i = buffer.iAt(idx);
      sumV2 += v * v;
      sumI2 += i * i;
      sumP += v * i;
      if (v < vMin) vMin = v;
      if (v > vMax) vMax = v;
      if (i < iMin) iMin = i;
      if (i > iMax) iMax = i;

      if (prevV !== null && prevV < 0 && v >= 0) {
        const frac = v !== prevV ? -prevV / (v - prevV) : 0;
        crossV.push(prevVT + frac * (t - prevVT));
      }
      if (prevI !== null && prevI < 0 && i >= 0) {
        const frac = i !== prevI ? -prevI / (i - prevI) : 0;
        crossI.push(prevIT + frac * (t - prevIT));
      }

      prevV = v;
      prevVT = t;
      prevI = i;
      prevIT = t;
    }

    const vrms = Math.sqrt(sumV2 / n);
    const irms = Math.sqrt(sumI2 / n);
    const p = sumP / n;
    const s = vrms * irms;
    let pf = s > 1e-9 ? p / s : 0;
    pf = clamp(pf, -1, 1);

    let f = freqNominal;
    if (crossV.length >= 2) {
      const first = crossV[0];
      const last = crossV[crossV.length - 1];
      if (last > first) f = (crossV.length - 1) / (last - first);
    }
    if (!Number.isFinite(f) || f < 20 || f > 100) f = freqNominal;

    // Fasores fundamentales para el desfase
    let vRe = 0;
    let vIm = 0;
    let iRe = 0;
    let iIm = 0;
    const omega = 2 * Math.PI * f;
    for (let idx = start; idx <= end; idx += 1) {
      const t = buffer.tAt(idx) - tStart;
      const ang = omega * t;
      const c = Math.cos(ang);
      const sn = Math.sin(ang);
      const v = buffer.vAt(idx);
      const i = buffer.iAt(idx);
      vRe += v * c;
      vIm -= v * sn;
      iRe += i * c;
      iIm -= i * sn;
    }
    let phase = Math.atan2(vIm, vRe) - Math.atan2(iIm, iRe);
    while (phase > Math.PI) phase -= 2 * Math.PI;
    while (phase < -Math.PI) phase += 2 * Math.PI;
    const phaseDeg = phase * 180 / Math.PI;

    const vpeak = Math.max(Math.abs(vMin), Math.abs(vMax));
    const ipeak = Math.max(Math.abs(iMin), Math.abs(iMax));
    const q = Math.sqrt(Math.max(s * s - p * p, 0));

    return {
      n,
      tStart,
      tEnd,
      vrms,
      irms,
      vpeak,
      ipeak,
      vpp: vMax - vMin,
      ipp: iMax - iMin,
      f,
      phase: phaseDeg,
      pf,
      p,
      s,
      q,
    };
  }

  function updateStatsAndScales() {
    const windowSec = state.cycles / state.lineFreq;

    for (const ch of [1, 2]) {
      const win = getDisplayWindow(buffers[ch], windowSec);
      const stats = computeStats(buffers[ch], win.tStart, win.tEnd, state.lineFreq);
      state.stats[ch] = stats;

      const chip = state.chipMetrics[ch];
      const sc = state.channels[ch];

      if (sc.autoV) {
        const peak = chip && chip.vrms > 0
          ? Math.SQRT2 * chip.vrms
          : (stats ? stats.vpeak : 0);
        if (peak > 0) sc.vMax = clamp(niceCeil(peak * 1.12, 10), 10, 2000);
      }
      if (sc.autoI) {
        const peak = chip && chip.irms > 0
          ? Math.SQRT2 * chip.irms
          : (stats ? stats.ipeak : 0);
        if (peak > 0) sc.iMax = clamp(niceCeil(peak * 1.12, 0.1), 0.1, 500);
      }
    }

    loadScaleUI();
    updateTable();
    updateStatus();
  }

  // -------------------------------------------------------------------------
  // Tabla y textos
  // -------------------------------------------------------------------------
  function updateTable() {
    const stats = state.stats[state.channel];
    const chip = state.chipMetrics[state.channel];

    if (!stats && !chip) {
      for (const el of [els.statVrms, els.statIrms, els.statVpeak, els.statIpeak, els.statVpp,
        els.statIpp, els.statFreq, els.statPhase, els.statPf, els.statP, els.statS, els.statQ, els.statN]) {
        el.textContent = "—";
      }
      els.phaseReadout.textContent = "Desfase — · FP —";
      els.sampleInfo.textContent = "— muestras en ventana";
      els.tableUpdated.textContent = "—";
      return;
    }

    const vrms = chip ? chip.vrms : stats.vrms;
    const irms = chip ? chip.irms : stats.irms;
    const p = chip ? chip.p : stats.p;
    const q = chip ? chip.q : stats.q;
    const s = chip ? chip.s : stats.s;
    const pf = chip ? chip.pf : stats.pf;
    const phase = chip ? chip.phase : stats.phase;
    const freq = chip ? chip.f : stats.f;
    const n = stats ? stats.n : null;
    const canPeak = stats && stats.n >= 20;

    els.statVrms.textContent = fmt(vrms, 2);
    els.statIrms.textContent = fmt(irms, 3);
    els.statVpeak.textContent = canPeak ? fmt(stats.vpeak, 1) : "—";
    els.statIpeak.textContent = canPeak ? fmt(stats.ipeak, 3) : "—";
    els.statVpp.textContent = canPeak ? fmt(stats.vpp, 1) : "—";
    els.statIpp.textContent = canPeak ? fmt(stats.ipp, 3) : "—";
    els.statFreq.textContent = fmt(freq, 2);
    els.statPhase.textContent = signed(phase, 1);
    els.statPf.textContent = fmt(pf, 3);
    els.statP.textContent = fmt(p, 1);
    els.statS.textContent = fmt(s, 1);
    els.statQ.textContent = fmt(q, 1);
    els.statN.textContent = n !== null ? String(n) : "—";

    const dir = phase >= 0 ? "I atrasa" : "I adelanta";
    els.phaseReadout.textContent = `Desfase ${signed(phase, 1)}° (${dir}) · FP ${fmt(pf, 3)}`;
    els.sampleInfo.textContent = n !== null ? `${n} muestras en ventana` : "— muestras en ventana";
    els.tableUpdated.textContent = nowLabel();
  }

  function updateTexts() {
    const ch = state.channel;
    const trig = state.trigger === "auto" ? " · Trigger V" : " · Libre";
    els.chartTitle.textContent = `Canal ${ch}`;
    els.chartSubtitle.textContent = `V${ch} y C${ch} · ${state.cycles} ciclos · ${state.lineFreq} Hz${trig}`;
    els.vLabelHint.textContent = `V${ch} [V] · eje izquierdo`;
    els.iLabelHint.textContent = `C${ch} [A] · eje izquierdo`;
    updateTable();
  }

  function updateStatus() {
    const stats = state.stats[state.channel];
    const chip = state.chipMetrics[state.channel];
    const freq = chip ? chip.f : (stats ? stats.f : state.lineFreq);

    els.fpsText.textContent = `${state.fps.toFixed(0)} FPS`;
    els.fsPill.textContent = state.fs <= 0
      ? "—"
      : (state.fs >= 1000
        ? `${(state.fs / 1000).toFixed(2)} kS/s`
        : `${state.fs.toFixed(1)} S/s`);
    els.freqPill.textContent = `${fmt(freq, 2)} Hz`;
    els.rxInfo.textContent = `${state.rxSamples.toLocaleString()} muestras recibidas`;

    const dot = els.connPill.querySelector(".dot");
    const ok = state.source === "demo" ? true : (wsSource.connected && !state.sourceError);
    dot.classList.toggle("ok", ok);
    dot.classList.toggle("bad", !ok);

    if (state.source === "demo") {
      els.sourcePill.textContent = state.paused ? "Demo · pausado" : "Demo";
    } else if (state.source === "uart") {
      els.sourcePill.textContent = state.sourceError
        ? "UART · error"
        : (wsSource.connected ? "UART" : "UART · sin conexión");
    } else {
      els.sourcePill.textContent = state.sourceError
        ? "WebSocket · error"
        : (wsSource.connected ? "WebSocket" : "WebSocket · sin conexión");
    }
  }

  function updateSourceStatus(status, detail) {
    const dot = els.connPill.querySelector(".dot");
    if (state.source === "demo") return;

    const isUart = state.source === "uart";
    const label = isUart ? "UART" : "WebSocket";

    if (status === "connected") {
      state.sourceError = false;
      dot.classList.remove("bad");
      dot.classList.add("ok");
      els.sourcePill.textContent = label;
      els.sourceHint.textContent = isUart
        ? "Conectado. Abriendo el UART…"
        : "Conectado. Recibiendo muestras por WebSocket.";
      return;
    }

    if (status === "status") {
      state.sourceError = false;
      dot.classList.remove("bad");
      dot.classList.add("ok");
      els.sourcePill.textContent = label;
      if (isUart) state.uartStatus = detail || "";
      els.sourceHint.textContent = detail || label;
      return;
    }

    if (status === "error") {
      state.sourceError = true;
      dot.classList.remove("ok");
      dot.classList.add("bad");
      els.sourcePill.textContent = `${label} · error`;
      els.sourceHint.textContent = `Error: ${detail || "sin detalle"}`;
      if (isUart) state.uartStatus = "";
      return;
    }

    state.sourceError = false;
    dot.classList.remove("ok");
    dot.classList.add("bad");
    els.sourcePill.textContent = `${label} · sin conexión`;
    els.sourceHint.textContent = detail
      ? `Sin conexión: ${detail}. Reintentando cada 2 s.`
      : "Sin conexión. Reintentando cada 2 s.";
  }

  // -------------------------------------------------------------------------
  // Controles
  // -------------------------------------------------------------------------
  function activeScale() {
    return state.channels[state.channel];
  }

  function loadScaleUI() {
    const sc = activeScale();
    els.autoV.checked = sc.autoV;
    els.autoI.checked = sc.autoI;
    els.vScaleRange.disabled = sc.autoV;
    els.vScaleInput.disabled = sc.autoV;
    els.iScaleRange.disabled = sc.autoI;
    els.iScaleInput.disabled = sc.autoI;

    if (document.activeElement !== els.vScaleRange) {
      els.vScaleRange.value = String(clamp(sc.vMax, Number(els.vScaleRange.min), Number(els.vScaleRange.max)));
    }
    if (document.activeElement !== els.vScaleInput) {
      els.vScaleInput.value = String(Math.round(sc.vMax * 10) / 10);
    }
    if (document.activeElement !== els.iScaleRange) {
      els.iScaleRange.value = String(clamp(sc.iMax, Number(els.iScaleRange.min), Number(els.iScaleRange.max)));
    }
    if (document.activeElement !== els.iScaleInput) {
      els.iScaleInput.value = String(Math.round(sc.iMax * 10) / 10);
    }
  }

  function setView(view) {
    state.view = view;
    for (const btn of els.viewToggle.querySelectorAll("button")) {
      btn.classList.toggle("active", btn.dataset.view === view);
    }
    const separate = view === "separate";
    els.separateCharts.classList.toggle("hidden", !separate);
    els.combinedChart.classList.toggle("hidden", separate);
    requestAnimationFrame(() => {
      voltageChart.resize();
      currentChart.resize();
      combinedChart.resize();
    });
  }

  function applySourceUI() {
    const isDemo = state.source === "demo";
    const isUart = state.source === "uart";
    els.sourceSelect.value = state.source;
    els.uartControls.classList.toggle("hidden", !isUart);
    els.wsUrl.disabled = isDemo;
    els.connectBtn.textContent = isDemo ? "Reiniciar" : "Conectar";

    if (isDemo) {
      els.sourceHint.textContent = "Demo: onda sintética de 50/60 Hz, dos canales y 7.8125 kS/s. Para el STPM34 real seleccione UART.";
    } else if (isUart) {
      els.sourceHint.textContent = "UART real: elija COM y baudios. La tabla usa RMS/potencia del chip; la onda muestra solo las muestras que entrega el UART.";
    } else {
      els.sourceHint.textContent = "WebSocket: ingrese la URL y presione Conectar. Formato: {type:'samples', fs, ch1:{v:[],i:[]}, ch2:{v:[],i:[]}}.";
    }
  }

  function startDemo() {
    wsSource.close();
    state.source = "demo";
    state.paused = false;
    state.sourceError = false;
    state.uartStatus = "";
    state.fs = demo.fs;
    els.pauseBtn.textContent = "Pausar";
    demo.reset();
    demo.start();
    clearBuffers();
    applySourceUI();
    updateTexts();
    updateStatus();
  }

  function startWebSocket() {
    const url = els.wsUrl.value.trim();
    if (!url) {
      els.sourceHint.textContent = "Escriba una URL WebSocket válida.";
      return;
    }
    demo.stop();
    state.source = "ws";
    state.paused = false;
    state.sourceError = false;
    state.uartStatus = "";
    state.fs = 0;
    els.pauseBtn.textContent = "Pausar";
    clearBuffers();
    applySourceUI();
    updateTexts();
    updateStatus();
    wsSource.connect(url);
    els.sourceHint.textContent = `Conectando a ${url}…`;
  }

  function startUart() {
    const baseText = els.wsUrl.value.trim() || "ws://localhost:8000/ws";
    let base;
    try {
      base = new URL(baseText);
    } catch {
      els.sourceHint.textContent = "La URL base del servidor WebSocket no es válida.";
      return;
    }
    base.pathname = "/ws/uart";
    base.search = "";
    const params = new URLSearchParams();
    const port = els.uartPort.value.trim();
    if (port) params.set("port", port);
    params.set("baud", els.uartBaud.value);
    params.set("crc", els.uartCrc.checked ? "1" : "0");
    base.search = params.toString();

    demo.stop();
    state.source = "uart";
    state.paused = false;
    state.sourceError = false;
    state.uartStatus = "Conectando UART...";
    state.fs = 0;
    els.pauseBtn.textContent = "Pausar";
    clearBuffers();
    applySourceUI();
    updateTexts();
    updateStatus();
    wsSource.connect(base.toString());
    els.sourceHint.textContent = `Conectando a ${base.toString()}…`;
  }

  // -------------------------------------------------------------------------
  // Dibujo y bucle principal
  // -------------------------------------------------------------------------
  function drawCharts() {
    const ch = state.channel;
    const buffer = buffers[ch];
    const sc = activeScale();
    const windowSec = state.cycles / state.lineFreq;
    const win = getDisplayWindow(buffer, windowSec);
    const cfgBase = {
      windowSec,
      tStart: win.tStart,
      tEnd: win.tEnd,
      cycles: state.cycles,
      freq: state.lineFreq,
      xMaxDeg: state.cycles * 360,
      yLeftMax: sc.vMax,
      yRightMax: sc.iMax,
      leftColor: COLORS.voltage,
      rightColor: COLORS.current,
      leftLabel: `V${ch} [V]`,
      rightLabel: `C${ch} [A]`,
      showRight: false,
      series: [{ key: "v", color: COLORS.voltage, axis: "left" }],
    };

    if (state.view === "separate") {
      voltageChart.draw(buffer, cfgBase);
      currentChart.draw(buffer, {
        ...cfgBase,
        yLeftMax: sc.iMax,
        leftColor: COLORS.current,
        leftLabel: `C${ch} [A]`,
        series: [{ key: "i", color: COLORS.current, axis: "left" }],
      });
    } else {
      combinedChart.draw(buffer, {
        ...cfgBase,
        showRight: true,
        series: [
          { key: "v", color: COLORS.voltage, axis: "left" },
          { key: "i", color: COLORS.current, axis: "right" },
        ],
      });
    }
  }

  let lastTick = performance.now();
  let lastFpsAt = performance.now();
  let fpsFrames = 0;

  function loop(now) {
    requestAnimationFrame(loop);
    if (now - lastTick < MIN_FRAME_MS) return;

    const dt = clamp((now - lastTick) / 1000, 0.001, 0.05);
    lastTick = now;

    if (!state.paused) {
      if (state.source === "demo") {
        const batch = demo.pump(dt, state.lineFreq);
        if (batch) ingestBatch(batch);
      }
    }

    drawCharts();

    if (!state.paused && now - state.lastStatsAt > 200) {
      state.lastStatsAt = now;
      updateStatsAndScales();
    }

    fpsFrames += 1;
    if (now - lastFpsAt >= 1000) {
      state.fps = (fpsFrames * 1000) / (now - lastFpsAt);
      fpsFrames = 0;
      lastFpsAt = now;
      updateStatus();
    }
  }

  // -------------------------------------------------------------------------
  // Eventos
  // -------------------------------------------------------------------------
  for (const tab of els.tabs) {
    tab.addEventListener("click", () => {
      state.channel = Number(tab.dataset.channel);
      for (const t of els.tabs) {
        t.classList.toggle("active", t === tab);
        t.setAttribute("aria-selected", t === tab ? "true" : "false");
      }
      loadScaleUI();
      updateTexts();
      drawCharts();
    });
  }

  for (const btn of els.viewToggle.querySelectorAll("button")) {
    btn.addEventListener("click", () => setView(btn.dataset.view));
  }

  els.cyclesSelect.addEventListener("change", () => {
    state.cycles = Number(els.cyclesSelect.value);
    updateTexts();
    updateStatsAndScales();
  });

  els.lineFreqSelect.addEventListener("change", () => {
    state.lineFreq = Number(els.lineFreqSelect.value);
    demo.reset();
    clearBuffers();
    updateTexts();
    updateStatsAndScales();
  });

  els.triggerSelect.addEventListener("change", () => {
    state.trigger = els.triggerSelect.value;
    updateTexts();
    updateStatsAndScales();
  });

  els.pauseBtn.addEventListener("click", () => {
    state.paused = !state.paused;
    els.pauseBtn.textContent = state.paused ? "Reanudar" : "Pausar";
    updateStatus();
  });

  els.clearBtn.addEventListener("click", () => {
    clearBuffers();
    updateTable();
    updateStatus();
  });

  els.autoV.addEventListener("change", () => {
    const sc = activeScale();
    sc.autoV = els.autoV.checked;
    loadScaleUI();
  });

  els.autoI.addEventListener("change", () => {
    const sc = activeScale();
    sc.autoI = els.autoI.checked;
    loadScaleUI();
  });

  els.vScaleRange.addEventListener("input", () => {
    const sc = activeScale();
    if (sc.autoV) return;
    sc.vMax = clamp(Number(els.vScaleRange.value), 1, 2000);
    els.vScaleInput.value = String(Math.round(sc.vMax * 10) / 10);
  });

  els.vScaleInput.addEventListener("input", () => {
    const sc = activeScale();
    if (sc.autoV) return;
    sc.vMax = clamp(Number(els.vScaleInput.value) || 1, 1, 2000);
    els.vScaleRange.value = String(clamp(sc.vMax, Number(els.vScaleRange.min), Number(els.vScaleRange.max)));
  });

  els.iScaleRange.addEventListener("input", () => {
    const sc = activeScale();
    if (sc.autoI) return;
    sc.iMax = clamp(Number(els.iScaleRange.value), 0.1, 500);
    els.iScaleInput.value = String(Math.round(sc.iMax * 100) / 100);
  });

  els.iScaleInput.addEventListener("input", () => {
    const sc = activeScale();
    if (sc.autoI) return;
    sc.iMax = clamp(Number(els.iScaleInput.value) || 0.1, 0.1, 500);
    els.iScaleRange.value = String(clamp(sc.iMax, Number(els.iScaleRange.min), Number(els.iScaleRange.max)));
  });

  els.sourceSelect.addEventListener("change", () => {
    const value = els.sourceSelect.value;
    if (value === "demo") {
      startDemo();
      return;
    }
    wsSource.close();
    demo.stop();
    state.source = value;
    state.paused = false;
    state.sourceError = false;
    state.uartStatus = "";
    state.fs = 0;
    clearBuffers();
    applySourceUI();
    updateTexts();
    updateStatus();
    els.sourceHint.textContent = value === "uart"
      ? "Configure el puerto/baudios y presione Conectar."
      : "Ingrese la URL del WebSocket y presione Conectar.";
  });

  els.connectBtn.addEventListener("click", () => {
    if (state.source === "demo") startDemo();
    else if (state.source === "uart") startUart();
    else startWebSocket();
  });

  els.wsUrl.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    if (state.source === "ws") startWebSocket();
    else if (state.source === "uart") startUart();
  });

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      lastTick = performance.now();
      clearBuffers();
    }
  });

  // -------------------------------------------------------------------------
  // Arranque
  // -------------------------------------------------------------------------
  const params = new URLSearchParams(window.location.search);
  if (params.get("ws")) els.wsUrl.value = params.get("ws");

  loadScaleUI();
  updateTexts();
  updateStatus();
  startDemo();

  if (params.get("source") === "uart") {
    els.sourceSelect.value = "uart";
    state.source = "uart";
    if (params.get("port")) els.uartPort.value = params.get("port");
    if (params.get("baud")) els.uartBaud.value = params.get("baud");
    if (params.get("crc")) els.uartCrc.checked = params.get("crc") !== "0";
    applySourceUI();
    setTimeout(() => startUart(), 400);
  } else if (params.get("source") === "ws") {
    els.sourceSelect.value = "ws";
    state.source = "ws";
    applySourceUI();
    setTimeout(() => startWebSocket(), 400);
  }

  requestAnimationFrame(loop);
})();
