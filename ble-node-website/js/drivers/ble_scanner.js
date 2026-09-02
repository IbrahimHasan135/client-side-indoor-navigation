export const BEACON_CONFIG = {
  deviceNamePrefix: "BLE-NAV-ESP32",
  companyIdentifier: 0x004c,
  uuidBytes: [
    0xfd, 0xa5, 0x06, 0x93, 0xa4, 0xe2, 0x4f, 0xb1,
    0xaf, 0xcf, 0xc6, 0xeb, 0x07, 0x64, 0x78, 0x25,
  ],
};

const IBEACON_PREFIX = [0x02, 0x15, ...BEACON_CONFIG.uuidBytes];
const DEBUG_SCAN_EVENTS = true;

export function isWebBluetoothSupported() {
  return Boolean(navigator.bluetooth);
}

export function supportsLeScan() {
  return Boolean(navigator.bluetooth?.requestLEScan);
}

export async function requestBeaconScan(onAdvertisement) {
  return requestBeaconScanWithDiagnostics(onAdvertisement);
}

export async function requestBeaconScanWithDiagnostics(onAdvertisement, onScanEvent = () => {}) {
  ensureBluetooth();
  if (!supportsLeScan()) {
    throw new Error("Browser ini belum expose navigator.bluetooth.requestLEScan(). Aktifkan Experimental Web Platform features di Chrome/Edge, lalu reload halaman.");
  }

  return requestPassiveAdvertisementScan(onAdvertisement, onScanEvent);
}

async function requestPassiveAdvertisementScan(onAdvertisement, onScanEvent) {
  onScanEvent({ type: "scan-state", state: "requesting", mode: "requestLEScan" });

  const listener = (event) => {
    const reading = normalizeAdvertisement(event);
    const summary = describeAdvertisingEvent(event);
    if (reading) {
      logScanEvent("accepted", event, { reading });
      onScanEvent({ type: "accepted", reading, summary });
      onAdvertisement(reading);
      return;
    }

    const reason = getRejectReason(event);
    logScanEvent("rejected", event, { reason });
    onScanEvent({ type: "rejected", event, reason, summary });
  };

  navigator.bluetooth.addEventListener("advertisementreceived", listener);

  let scan;
  let mode = "requestLEScan-accept-all";
  try {
    console.info("[BLE scan] Requesting accept-all advertisement scan.");
    scan = await startAcceptAllScan();
  } catch (error) {
    try {
      mode = "requestLEScan-esp-filtered";
      console.warn("[BLE scan] Accept-all scan failed, retrying ESP32/iBeacon filtered scan.", error);
      scan = await startFilteredScan();
    } catch (fallbackError) {
      navigator.bluetooth.removeEventListener("advertisementreceived", listener);
      console.warn("Accept-all BLE scan failed before filtered fallback failed.", error);
      onScanEvent({
        type: "scan-state",
        state: "failed",
        mode,
        error: fallbackError?.message || String(fallbackError),
      });
      throw fallbackError;
    }
  }

  onScanEvent({
    type: "scan-state",
    state: "started",
    mode,
    scan: {
      active: Boolean(scan.active),
      acceptAllAdvertisements: Boolean(scan.acceptAllAdvertisements),
      keepRepeatedDevices: Boolean(scan.keepRepeatedDevices),
      filters: scan.filters || [],
    },
  });

  console.info("[BLE scan] Started.", {
    mode,
    active: scan.active,
    acceptAllAdvertisements: scan.acceptAllAdvertisements,
    keepRepeatedDevices: scan.keepRepeatedDevices,
    filters: scan.filters,
  });

  return {
    mode,
    stop() {
      navigator.bluetooth.removeEventListener("advertisementreceived", listener);
      scan.stop();
    },
  };
}

function startFilteredScan() {
  return navigator.bluetooth.requestLEScan({
    filters: [
      {
        manufacturerData: [
          {
            companyIdentifier: BEACON_CONFIG.companyIdentifier,
            dataPrefix: new Uint8Array(IBEACON_PREFIX),
          },
        ],
      },
      {
        namePrefix: BEACON_CONFIG.deviceNamePrefix,
      },
    ],
    keepRepeatedDevices: true,
  });
}

function startAcceptAllScan() {
  return navigator.bluetooth.requestLEScan({
    acceptAllAdvertisements: true,
    keepRepeatedDevices: true,
  });
}

function normalizeAdvertisement(event) {
  const manufacturer = getManufacturerData(event.manufacturerData, BEACON_CONFIG.companyIdentifier);
  const parsedIBeacon = manufacturer ? parseIBeaconPayload(manufacturer) : null;
  const name = event.device?.name || event.name || BEACON_CONFIG.deviceNamePrefix;

  if (!isExpectedBeacon(event, parsedIBeacon)) {
    return null;
  }

  return {
    id: parsedIBeacon?.anchorId || event.device?.id || name || "unknown-device",
    browserDeviceId: event.device?.id || "-",
    name,
    rssi: typeof event.rssi === "number" ? event.rssi : null,
    txPower: parsedIBeacon?.txPower ?? (typeof event.txPower === "number" ? event.txPower : null),
    major: parsedIBeacon?.major ?? null,
    minor: parsedIBeacon?.minor ?? null,
    anchorId: parsedIBeacon?.anchorId ?? null,
    source: parsedIBeacon ? "ibeacon" : "name",
    lastSeen: Date.now(),
  };
}

function parseIBeaconPayload(dataView) {
  const bytes = new Uint8Array(dataView.buffer, dataView.byteOffset, dataView.byteLength);
  const prefixOffset = findByteSequence(bytes, IBEACON_PREFIX);

  if (prefixOffset < 0 || bytes.length < prefixOffset + 23) {
    return null;
  }

  const majorOffset = prefixOffset + 18;
  const minorOffset = prefixOffset + 20;
  const txPowerOffset = prefixOffset + 22;
  const major = (bytes[majorOffset] << 8) | bytes[majorOffset + 1];
  const minor = (bytes[minorOffset] << 8) | bytes[minorOffset + 1];
  const txPower = bytes[txPowerOffset] > 127 ? bytes[txPowerOffset] - 256 : bytes[txPowerOffset];

  return { major, minor, txPower, anchorId: `${major}:${minor}` };
}

function findByteSequence(bytes, sequence) {
  for (let offset = 0; offset <= bytes.length - sequence.length; offset += 1) {
    const matched = sequence.every((value, index) => bytes[offset + index] === value);
    if (matched) {
      return offset;
    }
  }

  return -1;
}

function isExpectedBeacon(event, parsedIBeacon) {
  if (parsedIBeacon) {
    return true;
  }

  const name = event.device?.name || event.name || "";
  return name.startsWith(BEACON_CONFIG.deviceNamePrefix);
}

function getManufacturerData(manufacturerData, companyIdentifier) {
  if (!manufacturerData) {
    return null;
  }

  const directMatch = manufacturerData.get?.(companyIdentifier);
  if (directMatch) {
    return directMatch;
  }

  if (typeof manufacturerData.forEach !== "function") {
    return null;
  }

  let matched = null;
  manufacturerData.forEach((value, key) => {
    if (Number(key) === companyIdentifier) {
      matched = value;
    }
  });
  return matched;
}

function getRejectReason(event) {
  if (event.manufacturerData?.size > 0) {
    return `manufacturer:${[...event.manufacturerData.keys()].map(formatCompanyId).join(",")}`;
  }

  const name = event.device?.name || event.name;
  if (name) {
    return `name:${name}`;
  }

  return "no-name-no-manufacturer-data";
}

function logScanEvent(status, event, extra = {}) {
  if (!DEBUG_SCAN_EVENTS) {
    return;
  }

  const detail = {
    status,
    ...describeAdvertisingEvent(event),
    ...extra,
  };

  console.debug(`[BLE scan] Advertisement ${status}`, detail);
}

function describeAdvertisingEvent(event) {
  return {
    deviceId: event.device?.id || null,
    deviceName: event.device?.name || null,
    eventName: event.name || null,
    rssi: typeof event.rssi === "number" ? event.rssi : null,
    txPower: typeof event.txPower === "number" ? event.txPower : null,
    uuids: Array.isArray(event.uuids) ? event.uuids : [],
    manufacturerData: dataMapToObject(event.manufacturerData, formatCompanyId),
    serviceData: dataMapToObject(event.serviceData),
  };
}

function dataMapToObject(dataMap, keyFormatter = (key) => key) {
  if (!dataMap || typeof dataMap.forEach !== "function") {
    return {};
  }

  const output = {};
  dataMap.forEach((value, key) => {
    output[keyFormatter(key)] = dataViewToHex(value);
  });
  return output;
}

function dataViewToHex(dataView) {
  return [...new Uint8Array(dataView.buffer, dataView.byteOffset, dataView.byteLength)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join(" ");
}

function hexToDataView(hexString) {
  const bytes = hexString
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((byte) => Number.parseInt(byte, 16));

  return new DataView(new Uint8Array(bytes).buffer);
}

function formatCompanyId(companyId) {
  return `0x${Number(companyId).toString(16).padStart(4, "0")}`;
}

function ensureBluetooth() {
  if (!isWebBluetoothSupported()) {
    throw new Error("Browser ini belum mendukung Web Bluetooth.");
  }
}
