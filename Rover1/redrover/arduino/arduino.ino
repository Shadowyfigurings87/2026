#include <Arduino.h>
#include <ArduinoJson.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// ------------- BLE setup -------------
BLEScan* bleScanner;
const int BLE_SCAN_DURATION_SEC = 1;

// ------------- Helper: internal sensors -------------

// NOTE: ESP32 internal temperature sensor is not accurate, but we can still expose it.
// Some cores expose temperatureRead() or this custom function; adjust if needed.
float readInternalTemperatureC() {
  // On many ESP32 boards, there is no calibrated temp sensor accessible by default.
  // If your core supports temperatureRead(), you can use that instead.
  // For now, we just return NAN as a placeholder.
  // return temperatureRead();  // uncomment if supported by your core
  return NAN;
}

// Built-in hall effect sensor
int readHallRaw() {
  // hallRead() is available on classic ESP32 cores
  return hallRead();
}

// ------------- Setup -------------

void setup() {
  Serial.begin(115200);
  delay(1000);

  // BLE init
  BLEDevice::init("");
  bleScanner = BLEDevice::getScan();
  bleScanner->setActiveScan(true); // better results, more power use
}

// ------------- Main loop -------------

void loop() {
  StaticJsonDocument<2048> doc;

  // ---------- BLE scan ----------
  JsonObject ble = doc.createNestedObject("ble");
  JsonArray bleDevices = ble.createNestedArray("devices");

  BLEScanResults results = bleScanner->start(BLE_SCAN_DURATION_SEC, false);
  int count = results.getCount();

  for (int i = 0; i < count; i++) {
    BLEAdvertisedDevice d = results.getDevice(i);
    JsonObject dev = bleDevices.createNestedObject();
    dev["mac"] = d.getAddress().toString().c_str();
    dev["rssi"] = d.getRSSI();

    // Optional: basic info if available
    if (d.haveName()) {
      dev["name"] = d.getName().c_str();
    }
    if (d.haveServiceUUID()) {
      dev["service_uuid"] = d.getServiceUUID().toString().c_str();
    }
  }

  ble["count"] = count;
  ble["status"] = "ok";
  bleScanner->clearResults();

  // ---------- Bluetooth Classic (placeholder) ----------
  // The Arduino BLE libraries don't provide true Classic inquiry scanning
  // without additional stacks. We keep the JSON slot for future expansion.
  JsonObject btClassic = doc.createNestedObject("bt_classic");
  btClassic["status"] = "not_implemented";

  // ---------- Internal temperature ----------
  JsonObject internalTemp = doc.createNestedObject("internal_temp");
  float tempC = readInternalTemperatureC();
  if (isnan(tempC)) {
    internalTemp["status"] = "unavailable";
  } else {
    internalTemp["celsius"] = tempC;
    internalTemp["status"] = "ok";
  }

  // ---------- Hall sensor ----------
  JsonObject hall = doc.createNestedObject("hall");
  hall["raw"] = readHallRaw();
  hall["status"] = "ok";

  // ---------- System stats ----------
  JsonObject sys = doc.createNestedObject("system");
  sys["free_heap"] = ESP.getFreeHeap();
  sys["uptime_ms"] = millis();

  // ---------- Overall status ----------
  doc["status"] = "ok";
  doc["ts_ms"] = millis();

  // ---------- Serialize once per loop ----------
  serializeJson(doc, Serial);
  Serial.println();

  // Adjust loop rate
  delay(1000);
}
