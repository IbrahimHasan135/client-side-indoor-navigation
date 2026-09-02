const DEFAULT_ALPHA = 0.28;

export class RssiFilter {
  constructor(alpha = DEFAULT_ALPHA) {
    this.alpha = alpha;
    this.values = new Map();
    this.sampleCounts = new Map();
  }

  update(deviceId, rssi) {
    if (typeof rssi !== "number") {
      return null;
    }

    const previous = this.values.get(deviceId);
    const smoothed = previous === undefined
      ? rssi
      : this.alpha * rssi + (1 - this.alpha) * previous;

    this.values.set(deviceId, smoothed);
    this.sampleCounts.set(deviceId, (this.sampleCounts.get(deviceId) || 0) + 1);
    return Math.round(smoothed);
  }

  getSampleCount(deviceId) {
    return this.sampleCounts.get(deviceId) || 0;
  }

  clear() {
    this.values.clear();
    this.sampleCounts.clear();
  }
}
