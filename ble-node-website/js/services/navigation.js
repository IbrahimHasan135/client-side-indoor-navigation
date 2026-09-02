export const ANCHOR_POSITIONS = {
  "1:1": { x: 0, y: 0, label: "Anchor 1" },
  "1:2": { x: 6, y: 0, label: "Anchor 2" },
  "1:3": { x: 0, y: 6, label: "Anchor 3" },
  "1:4": { x: 6, y: 6, label: "Anchor 4" },
};

export function estimateUserPosition(devices) {
  const anchors = devices
    .filter((device) => device.anchorId && ANCHOR_POSITIONS[device.anchorId])
    .filter((device) => typeof device.distanceMeters === "number" && device.distanceMeters > 0);

  if (anchors.length === 0) {
    return null;
  }

  let weightTotal = 0;
  let xTotal = 0;
  let yTotal = 0;

  for (const device of anchors) {
    const position = ANCHOR_POSITIONS[device.anchorId];
    const weight = 1 / Math.max(device.distanceMeters ** 2, 0.01);
    weightTotal += weight;
    xTotal += position.x * weight;
    yTotal += position.y * weight;
  }

  return {
    x: Number((xTotal / weightTotal).toFixed(2)),
    y: Number((yTotal / weightTotal).toFixed(2)),
    anchorCount: anchors.length,
  };
}
