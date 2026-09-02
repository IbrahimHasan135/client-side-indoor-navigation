package org.indoor.navigation;

public interface BleAdvertisementListener {
    void onAdvertisement(
        String address,
        String name,
        int rssi,
        int txPower,
        int[] manufacturerIds,
        byte[][] manufacturerPayloads
    );

    void onScanFailed(int errorCode);
}
