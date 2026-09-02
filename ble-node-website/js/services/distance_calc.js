const DEFAULT_TX_POWER = -59;
const DEFAULT_PATH_LOSS = 2.2;

export function estimateDistanceMeters(rssi, txPower = DEFAULT_TX_POWER, pathLoss = DEFAULT_PATH_LOSS) {
  if (typeof rssi !== "number") {
    return null;
  }

  const distance = 10 ** ((txPower - rssi) / (10 * pathLoss));
  return Number(distance.toFixed(2));
}

export function classifyRssi(rssi) {
  if (typeof rssi !== "number") {
    return "unknown";
  }

  if (rssi >= -65) {
    return "strong";
  }

  if (rssi >= -80) {
    return "medium";
  }

  return "weak";
}
