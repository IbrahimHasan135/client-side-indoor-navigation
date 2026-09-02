import { requestBeaconScanWithDiagnostics } from "../drivers/ble_scanner.js?v=webapi-poc-20260902";
import { estimateDistanceMeters, classifyRssi } from "./distance_calc.js?v=webapi-poc-20260902";
import { estimateUserPosition } from "./navigation.js?v=webapi-poc-20260902";
import { RssiFilter } from "./rssi_filter.js?v=webapi-poc-20260902";

const UI_UPDATE_INTERVAL_MS = 250;
const STALE_AFTER_MS = 2500;

export class BeaconMonitor {
  constructor() {
    this.devices = new Map();
    this.filter = new RssiFilter();
    this.scanSession = null;
    this.updateTimer = null;
    this.stats = this.createStats();
  }

  async start(onUpdate) {
    await this.stop();
    this.devices.clear();
    this.filter.clear();
    this.stats = this.createStats();

    this.scanSession = await requestBeaconScanWithDiagnostics((reading) => {
      const smoothedRssi = this.filter.update(reading.id, reading.rssi);
      const displayRssi = smoothedRssi ?? reading.rssi;
      const device = {
        ...reading,
        smoothedRssi,
        distanceMeters: estimateDistanceMeters(displayRssi, reading.txPower ?? undefined),
        signal: classifyRssi(displayRssi),
        sampleCount: this.filter.getSampleCount(reading.id),
      };

      this.devices.set(reading.id, device);
    }, (scanEvent) => {
      this.updateStats(scanEvent);
      onUpdate(this.getSnapshot());
    });

    this.updateTimer = window.setInterval(() => {
      onUpdate(this.getSnapshot());
    }, UI_UPDATE_INTERVAL_MS);

    const mode = this.scanSession.mode;
    onUpdate(this.getSnapshot());

    return mode;
  }

  async stop() {
    if (this.updateTimer) {
      window.clearInterval(this.updateTimer);
      this.updateTimer = null;
    }

    if (this.scanSession) {
      this.scanSession.stop();
      this.scanSession = null;
    }
  }

  getSnapshot() {
    this.refreshStatsAge();
    const devices = this.getDevices();
    const mode = this.scanSession?.mode || "idle";
    return {
      devices,
      position: estimateUserPosition(devices),
      mode,
      isScanning: Boolean(this.scanSession),
      stats: { ...this.stats, mode },
    };
  }

  getDevices() {
    const now = Date.now();
    return [...this.devices.values()].sort((a, b) => {
      const aRssi = a.smoothedRssi ?? a.rssi ?? -999;
      const bRssi = b.smoothedRssi ?? b.rssi ?? -999;
      return bRssi - aRssi;
    }).map((device) => ({
      ...device,
      ageMs: now - device.lastSeen,
      isStale: now - device.lastSeen > STALE_AFTER_MS,
    }));
  }

  createStats() {
    return {
      rawEvents: 0,
      acceptedEvents: 0,
      rejectedEvents: 0,
      noRssiEvents: 0,
      scanState: "idle",
      scanMode: "idle",
      scanActive: false,
      scanStartedAt: null,
      scanError: null,
      lastRejectReason: "-",
      lastEventAgeMs: null,
      lastAcceptedAgeMs: null,
      recentEvents: [],
    };
  }

  updateStats(scanEvent) {
    const now = Date.now();
    if (scanEvent.type === "scan-state") {
      this.stats.scanState = scanEvent.state;
      this.stats.scanMode = scanEvent.mode || this.stats.scanMode;
      this.stats.scanActive = Boolean(scanEvent.scan?.active);
      this.stats.scanError = scanEvent.error || null;
      if (scanEvent.state === "started") {
        this.stats.scanStartedAt = now;
      }
      return;
    }

    this.stats.rawEvents += 1;
    this.stats.lastEventAt = now;
    this.stats.lastEventAgeMs = 0;

    const rssi = scanEvent.reading?.rssi ?? scanEvent.event?.rssi;
    if (typeof rssi !== "number") {
      this.stats.noRssiEvents += 1;
    }

    this.stats.recentEvents = [
      {
        status: scanEvent.type,
        reason: scanEvent.reason || "-",
        rssi: typeof rssi === "number" ? rssi : null,
        deviceId: scanEvent.summary?.deviceId || "-",
        deviceName: scanEvent.summary?.deviceName || scanEvent.summary?.eventName || "-",
        manufacturerKeys: Object.keys(scanEvent.summary?.manufacturerData || {}).join(", ") || "-",
      },
      ...this.stats.recentEvents,
    ].slice(0, 10);

    if (scanEvent.type === "accepted") {
      this.stats.acceptedEvents += 1;
      this.stats.lastAcceptedAt = now;
      this.stats.lastAcceptedAgeMs = 0;
      return;
    }

    this.stats.rejectedEvents += 1;
    this.stats.lastRejectReason = scanEvent.reason || "-";
  }

  refreshStatsAge() {
    const now = Date.now();
    this.stats.lastEventAgeMs = this.stats.lastEventAt ? now - this.stats.lastEventAt : null;
    this.stats.lastAcceptedAgeMs = this.stats.lastAcceptedAt ? now - this.stats.lastAcceptedAt : null;
  }
}
