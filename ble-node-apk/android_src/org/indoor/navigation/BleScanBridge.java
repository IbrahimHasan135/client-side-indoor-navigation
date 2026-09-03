package org.indoor.navigation;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothManager;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanRecord;
import android.bluetooth.le.ScanResult;
import android.content.Context;
import android.util.Log;
import android.util.SparseArray;

import java.util.List;

public class BleScanBridge {
    private static final String TAG = "BleScanBridge";
    public static final int ERROR_BLUETOOTH_NOT_SUPPORTED = -100;
    public static final int ERROR_BLUETOOTH_DISABLED = -101;
    public static final int ERROR_SCANNER_UNAVAILABLE = -102;

    private final Context context;
    private final BleAdvertisementListener listener;
    private BluetoothLeScanner scanner;
    private ScanCallback callback;
    private boolean scanning;

    public BleScanBridge(Context context, BleAdvertisementListener listener) {
        this.context = context;
        this.listener = listener;
    }

    public boolean isBluetoothEnabled() {
        BluetoothAdapter adapter = getBluetoothAdapter();
        return adapter != null && adapter.isEnabled();
    }

    public void start() {
        if (scanning) {
            return;
        }

        BluetoothAdapter adapter = getBluetoothAdapter();
        if (adapter == null) {
            listener.onScanFailed(ERROR_BLUETOOTH_NOT_SUPPORTED);
            return;
        }

        if (!adapter.isEnabled()) {
            listener.onScanFailed(ERROR_BLUETOOTH_DISABLED);
            return;
        }

        scanner = adapter.getBluetoothLeScanner();
        if (scanner == null) {
            listener.onScanFailed(ERROR_SCANNER_UNAVAILABLE);
            return;
        }

        callback = createCallback();
        scanner.startScan(callback);
        scanning = true;
    }

    public void stop() {
        if (scanner != null && callback != null && scanning) {
            try {
                scanner.stopScan(callback);
            } catch (RuntimeException exception) {
                Log.w(TAG, "stopScan ignored runtime exception", exception);
            }
        }

        scanning = false;
        callback = null;
    }

    private ScanCallback createCallback() {
        return new ScanCallback() {
            @Override
            public void onScanResult(int callbackType, ScanResult result) {
                emitResult(result);
            }

            @Override
            public void onBatchScanResults(List<ScanResult> results) {
                for (ScanResult result : results) {
                    emitResult(result);
                }
            }

            @Override
            public void onScanFailed(int errorCode) {
                listener.onScanFailed(errorCode);
            }
        };
    }

    private void emitResult(ScanResult result) {
        if (result == null || result.getDevice() == null) {
            return;
        }

        ScanRecord record = result.getScanRecord();
        String address = result.getDevice().getAddress();
        String name = "";
        int txPower = Integer.MIN_VALUE;
        int[] manufacturerIds = new int[0];
        byte[][] manufacturerPayloads = new byte[0][];

        if (record != null) {
            name = record.getDeviceName();
            txPower = record.getTxPowerLevel();

            SparseArray<byte[]> manufacturerData = record.getManufacturerSpecificData();
            if (manufacturerData != null) {
                manufacturerIds = new int[manufacturerData.size()];
                manufacturerPayloads = new byte[manufacturerData.size()][];
                for (int index = 0; index < manufacturerData.size(); index++) {
                    manufacturerIds[index] = manufacturerData.keyAt(index);
                    byte[] payload = manufacturerData.valueAt(index);
                    manufacturerPayloads[index] = payload != null ? payload : new byte[0];
                }
            }
        }

        if (name == null) {
            name = result.getDevice().getName();
        }
        if (name == null) {
            name = "";
        }
        if (address == null) {
            address = "";
        }

        try {
            listener.onAdvertisement(
                address,
                name,
                result.getRssi(),
                txPower,
                manufacturerIds,
                manufacturerPayloads
            );
        } catch (RuntimeException exception) {
            Log.e(TAG, "Python BLE advertisement callback failed", exception);
        }
    }

    private BluetoothAdapter getBluetoothAdapter() {
        BluetoothManager manager = (BluetoothManager) context.getSystemService(Context.BLUETOOTH_SERVICE);
        if (manager == null) {
            return null;
        }

        return manager.getAdapter();
    }
}
