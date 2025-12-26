#include <Arduino.h>
#include <ArduinoJson.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include "esp_bt_main.h"
#include "esp_bt_device.h"
#include "esp_gap_bt_api.h"

// ---------------- BLE Setup ----------------
BLEScan* bleScanner;
const int BLE_SCAN_DURATION_SEC = 1;

// ---------------- Bluetooth Classic Globals ----------------
bool btInquiryDone = false;
StaticJsonDocument<2048> btClassicDoc;

// Extract RSSI from Classic GAP structure
int extractRSSI(esp_bt_gap_cb_param_t *param) {
  for (int i = 0; i < param->disc_res.num_prop; i++) {
    if (param->disc_res.prop[i].type == ESP_BT_GAP_DEV_PROP_RSSI) {
      return *(int8_t*)param->disc_res.prop[i].val;
    }
  }
  return 0;
}

// Bluetooth Classic GAP callback
void bt_inquiry_callback(esp_bt_gap_cb_event_t event, esp_bt_gap_cb_param_t *param) {
  if (event == ESP_BT_GAP_DISC_RES_EVT) {
    JsonArray arr = btClassicDoc["devices"].as<JsonArray>();
    JsonObject dev = arr.createNestedObject();

    char bda_str[18];
    sprintf(bda_str, "%02x:%02x:%02x:%02x:%02x:%02x",
            param->disc_res.bda[0], param->disc_res.bda[1], param->disc_res.bda[2],
            param->disc_res.bda[3], param->disc_res.bda[4], param->disc_res.bda[5]);
    dev["mac"] = bda_str;
    dev["rssi"] = extractRSSI(param);
  }

  if (event == ESP_BT_GAP_DISC_STATE_CHANGED_EVT) {
    if (param->disc_st_chg.state == ESP_BT_GAP_DISCOVERY_STOPPED) {
      btInquiryDone = true;
    }
  }
}

// ---------------- Setup ----------------
void setup() {
  Serial.begin(115200);
  delay(1000);

  // ----- BLE -----
  BLEDevice::init("");
  bleScanner = BLEDevice::getScan();
  bleScanner->setActiveScan(true);

  // ----- Bluetooth Classic -----
  btClassicDoc.clear();
  btClassicDoc["devices"] = btClassicDoc.createNestedArray("devices");

  esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
  esp_bt_controller_init(&bt_cfg);
  esp_bt_controller_enable(ESP_BT_MODE_BTDM); // Dual mode
  esp_bluedroid_init();
  esp_bluedroid_enable();
  esp_bt_gap_register_callback(bt_inquiry_callback);
}

// ---------------- Main Loop ----------------
void loop() {
  StaticJsonDocument<4096> doc;

  // ---------- BLE Scan ----------
  JsonObject ble = doc.createNestedObject("ble");
  JsonArray bleDevices = ble.createNestedArray("devices");

  BLEScanResults results = bleScanner->start(BLE_SCAN_DURATION_SEC, false);
  int count = results.getCount();

  for (int i = 0; i < count; i++) {
    BLEAdvertisedDevice d = results.getDevice(i);
    JsonObject dev = bleDevices.createNestedObject();
    dev["mac"] = d.getAddress().toString().c_str();
    dev["rssi"] = d.getRSSI();

    if (d.haveName()) {
      dev["name"] = d.getName().c_str();
    }
    if (d.haveServiceUUID()) {
      dev["service_uuid"] = d.getServiceUUID().toString().c_str();
    }
    if (d.haveManufacturerData()) {
      std::string mfg = d.getManufacturerData();
      char hex[2 * mfg.length() + 1];
      for (size_t j = 0; j < mfg.length(); j++) {
        sprintf(&hex[j * 2], "%02X", (uint8_t)mfg[j]);
      }
      hex[2 * mfg.length()] = '\0';
      dev["mfg_data"] = hex;
    }
  }

  ble["count"] = count;
  ble["status"] = "ok";
  bleScanner->clearResults();

  // ---------- Bluetooth Classic Inquiry ----------
  btClassicDoc["devices"].clear();
  btInquiryDone = false;
  esp_bt_gap_start_discovery(ESP_BT_INQ_MODE_GENERAL_INQUIRY, 3, 0);

  unsigned long t0 = millis();
  while (!btInquiryDone && millis() - t0 < 3500) {
    delay(10);
  }

  doc["bt_classic"] = btClassicDoc;

  // ---------- System Stats ----------
  JsonObject sys = doc.createNestedObject("system");
  sys["free_heap"] = ESP.getFreeHeap();
  sys["uptime_ms"] = millis();

  // ---------- Final ----------
  doc["status"] = "ok";
  doc["ts_ms"] = millis();

  serializeJson(doc, Serial);
  Serial.println();

  delay(1000);
}

