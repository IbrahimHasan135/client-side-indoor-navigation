import { BeaconMonitor } from "../services/beacon_monitor.js?v=webapi-poc-20260902";

const monitor = new BeaconMonitor();

export function initUiController() {
  const els = getElements();

  renderSupportState(els);
  renderSnapshot(els, { devices: [], position: null, isScanning: false });

  els.startButton.addEventListener("click", async () => {
    await handleStart(els);
  });

  els.stopButton.addEventListener("click", async () => {
    await monitor.stop();
    setStatus(els, "Dihentikan", "");
    els.startButton.disabled = false;
    els.stopButton.disabled = true;
    renderSnapshot(els, monitor.getSnapshot());
  });
}

async function handleStart(els) {
  els.startButton.disabled = true;
  els.stopButton.disabled = false;
  setStatus(els, "Meminta akses", "");
  els.supportText.textContent = "Saat dialog Chrome muncul, klik Allow. Tidak perlu memilih satu device; ini izin scan advertisement BLE experimental.";

  try {
    const mode = await monitor.start((snapshot) => {
      renderSnapshot(els, snapshot);
      setStatus(els, snapshot.devices.length > 0 ? "RSSI Masuk" : "Scanning", "is-ready");
    });

    if (monitor.getSnapshot().isScanning) {
      setStatus(els, "Scanning", "is-ready");
      els.supportText.textContent = `Web Bluetooth scan aktif (${mode}). RSSI raw dan EMA diperbarui dari semua anchor ESP32-C6 yang terdengar.`;
    }
  } catch (error) {
    els.startButton.disabled = false;
    els.stopButton.disabled = true;
    setStatus(els, "Gagal", "is-error");
    els.supportText.textContent = error?.message || "Akses Bluetooth ditolak atau tidak tersedia.";
  }
}

function renderSupportState(els) {
  els.supportText.textContent = "Klik mulai untuk menjalankan navigator.bluetooth.requestLEScan(). Chrome tetap akan meminta izin scan; setelah Allow, RSSI masuk lewat event advertisementreceived.";
}

function renderSnapshot(els, snapshot) {
  renderSummary(els, snapshot.devices);
  renderPosition(els, snapshot.position);
  renderDiagnostics(els, snapshot.stats);
  renderDevices(els, snapshot.devices);
}

function renderSummary(els, devices) {
  const nearest = devices[0];
  els.deviceCount.textContent = String(devices.length);
  els.nearestDevice.textContent = nearest ? formatBeaconId(nearest) : "-";
  els.nearestRssi.textContent = formatRssi(nearest?.smoothedRssi ?? nearest?.rssi);
  els.nearestDistance.textContent = nearest?.distanceMeters === null || nearest === undefined
    ? "-"
    : `${nearest.distanceMeters} m`;
}

function renderDevices(els, devices) {
  els.deviceList.innerHTML = "";

  if (devices.length === 0) {
    els.emptyState.hidden = false;
    renderSummary(els, devices);
    return;
  }

  els.emptyState.hidden = true;

  const fragment = document.createDocumentFragment();
  for (const device of devices) {
    const card = document.createElement("article");
    card.className = "device-card";
    if (device.isStale) {
      card.classList.add("is-stale");
    }

    const identity = document.createElement("div");
    const name = document.createElement("div");
    name.className = "device-name";
    name.textContent = formatBeaconId(device);

    const id = document.createElement("div");
    id.className = "device-id";
    id.textContent = `${device.name} | ${device.browserDeviceId}`;

    identity.append(name, id);

    card.append(
      identity,
      makeMetric("Raw RSSI", formatRssi(device.rssi), `rssi-${device.signal}`),
      makeMetric("EMA RSSI", formatRssi(device.smoothedRssi), `rssi-${device.signal}`),
      makeMetric("Jarak", device.distanceMeters === null ? "-" : `${device.distanceMeters} m`),
      makeMetric("Sampel", String(device.sampleCount || 0)),
      makeMetric("Terakhir", formatAge(device.ageMs)),
    );

    fragment.append(card);
  }

  els.deviceList.append(fragment);
}

function renderPosition(els, position) {
  if (!position) {
    els.positionX.textContent = "-";
    els.positionY.textContent = "-";
    els.positionQuality.textContent = "Belum ada anchor yang bisa dipakai untuk menghitung posisi.";
    return;
  }

  els.positionX.textContent = `${position.x} m`;
  els.positionY.textContent = `${position.y} m`;
  els.positionQuality.textContent = position.anchorCount >= 3
    ? `Menggunakan ${position.anchorCount} anchor.`
    : `Menggunakan ${position.anchorCount} anchor. Tambah anchor untuk posisi yang lebih stabil.`;
}

function renderDiagnostics(els, stats = {}) {
  els.rawEventCount.textContent = String(stats.rawEvents || 0);
  els.acceptedEventCount.textContent = String(stats.acceptedEvents || 0);
  els.rejectedEventCount.textContent = String(stats.rejectedEvents || 0);
  els.noRssiEventCount.textContent = String(stats.noRssiEvents || 0);
  els.lastEventAge.textContent = formatAge(stats.lastEventAgeMs);
  renderRawEvents(els, stats.recentEvents || []);

  if (!stats.rawEvents) {
    if (stats.scanState === "requesting") {
      els.scanDebugText.textContent = "Menunggu izin Chrome. Klik Allow di dialog scan Bluetooth.";
      return;
    }

    if (stats.scanState === "started") {
      els.scanDebugText.textContent = `requestLEScan sudah start (${stats.scanMode}), tapi browser belum mengirim event advertisementreceived. Kalau tetap 0 setelah 10 detik, kendalanya ada di implementasi Chrome/platform/izin Bluetooth OS, bukan di filter ESP.`;
      return;
    }

    if (stats.scanState === "failed") {
      els.scanDebugText.textContent = `requestLEScan gagal: ${stats.scanError || "-"}.`;
      return;
    }

    els.scanDebugText.textContent = "Belum ada paket BLE yang diterima browser.";
    return;
  }

  if (!stats.acceptedEvents) {
    els.scanDebugText.textContent = `Paket BLE masuk, tapi belum cocok dengan iBeacon ESP32-C6. Terakhir ditolak: ${stats.lastRejectReason || "-"}.`;
    return;
  }

  els.scanDebugText.textContent = `Paket ESP32-C6 diterima. Scan mode: ${stats.mode || "requestLEScan"}.`;
}

function renderRawEvents(els, events) {
  els.rawEventList.innerHTML = "";
  if (events.length === 0) {
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const event of events) {
    const row = document.createElement("div");
    row.className = `raw-event-row raw-event-${event.status}`;
    row.append(
      makeRawCell(event.status),
      makeRawCell(formatRssi(event.rssi)),
      makeRawCell(event.deviceName),
      makeRawCell(event.deviceId),
      makeRawCell(event.manufacturerKeys),
      makeRawCell(event.reason),
    );
    fragment.append(row);
  }
  els.rawEventList.append(fragment);
}

function makeRawCell(value) {
  const cell = document.createElement("div");
  cell.textContent = value || "-";
  return cell;
}

function makeMetric(label, value, valueClass = "") {
  const wrapper = document.createElement("div");
  const labelEl = document.createElement("div");
  const valueEl = document.createElement("div");

  labelEl.className = "metric-label";
  labelEl.textContent = label;
  valueEl.className = `metric-value ${valueClass}`.trim();
  valueEl.textContent = value;

  wrapper.append(labelEl, valueEl);
  return wrapper;
}

function formatRssi(rssi) {
  return typeof rssi === "number" ? `${rssi} dBm` : "-";
}

function formatBeaconId(device) {
  if (device.major === null || device.minor === null) {
    return device.id;
  }

  return `Anchor ${device.major}:${device.minor}`;
}

function formatAge(ageMs) {
  if (typeof ageMs !== "number") {
    return "-";
  }

  if (ageMs < 1000) {
    return "baru";
  }

  return `${(ageMs / 1000).toFixed(1)} s`;
}

function setStatus(els, text, className) {
  els.status.textContent = text;
  els.status.className = `status-pill ${className}`.trim();
}

function getElements() {
  return {
    startButton: document.querySelector("#startScan"),
    stopButton: document.querySelector("#stopScan"),
    status: document.querySelector("#status"),
    supportText: document.querySelector("#supportText"),
    deviceCount: document.querySelector("#deviceCount"),
    nearestDevice: document.querySelector("#nearestDevice"),
    nearestRssi: document.querySelector("#nearestRssi"),
    nearestDistance: document.querySelector("#nearestDistance"),
    positionX: document.querySelector("#positionX"),
    positionY: document.querySelector("#positionY"),
    positionQuality: document.querySelector("#positionQuality"),
    rawEventCount: document.querySelector("#rawEventCount"),
    acceptedEventCount: document.querySelector("#acceptedEventCount"),
    rejectedEventCount: document.querySelector("#rejectedEventCount"),
    noRssiEventCount: document.querySelector("#noRssiEventCount"),
    lastEventAge: document.querySelector("#lastEventAge"),
    scanDebugText: document.querySelector("#scanDebugText"),
    rawEventList: document.querySelector("#rawEventList"),
    deviceList: document.querySelector("#deviceList"),
    emptyState: document.querySelector("#emptyState"),
  };
}
