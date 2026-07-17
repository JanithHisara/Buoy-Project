#include <Arduino.h>

#include "common_functions.h"

#include "LoRa_app.h"
#include "AT_app.h"
#include "GPS_app.h"
#include "LED_driver.h"

#include <WiFi.h>
#include <WebServer.h>
#include <Update.h>
#include <ESPmDNS.h>

QueueHandle_t AT_to_LoRa_Queue;
QueueHandle_t LoRa_to_AT_Queue;

QueueHandle_t AT_to_GPS_Queue;
QueueHandle_t GPS_to_AT_Queue;

SemaphoreHandle_t GPS_data_request_Semaphore;
SemaphoreHandle_t GPS_Background_Lock_Semaphore;

TimerHandle_t HourlySaveTimer;

char BUOYANCY_ID[13];
char SAVED_TRANSCEIVER_ID[13] = {0};

const char *SAVED_TRX_ID_KEY = "TRXID_KEY";
const char *SAVED_GPS_POWER_STATUS_KEY = "GPS_PWR";

WebServer server(80);

void HourlySaveTimerCallback(TimerHandle_t xTimer)
{
  if (GPS_Background_Lock_Semaphore != NULL)
  {
    xSemaphoreGive(GPS_Background_Lock_Semaphore);
  }
}

// OTA Setup
void setupOTA() {
  server.on("/", HTTP_GET, []() {
    server.sendHeader("Connection", "close");
    server.send(200, "text/html", "<h2>OceanNav Buoy OTA Update</h2>");
  });
  
  server.on("/update", HTTP_POST, []() {
    Serial.println("Update endpoint hit! Upload callback finished.");
    Serial.printf("Update has error: %d\n", Update.hasError());
    server.sendHeader("Connection", "close");
    server.send(200, "text/plain", (Update.hasError()) ? "FAIL" : "OK");
    ESP.restart();
  }, []() {
    HTTPUpload& upload = server.upload();
    if (upload.status == UPLOAD_FILE_START) {
      Serial.printf("Update: %s\n", upload.filename.c_str());
      if (!Update.begin(UPDATE_SIZE_UNKNOWN)) { // start with max available size
        Update.printError(Serial);
      }
    } else if (upload.status == UPLOAD_FILE_WRITE) {
      if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
        Update.printError(Serial);
      }
    } else if (upload.status == UPLOAD_FILE_END) {
      if (Update.end(true)) { // true to set the size to the current progress
        Serial.printf("Update Success: %u\nRebooting...\n", upload.totalSize);
      } else {
        Update.printError(Serial);
      }
    }
  });
  server.begin();
}

void setup()
{
  // put your setup code here, to run once:
  Serial.begin(115200);

  Serial.println("===============BUOYANCY==================");
  getChipID(BUOYANCY_ID, sizeof(BUOYANCY_ID));
  Serial.print("BUOYANCY ID : ");
  Serial.println(BUOYANCY_ID);

  AT_to_LoRa_Queue = xQueueCreate(5, sizeof(char[256]));
  LoRa_to_AT_Queue = xQueueCreate(5, sizeof(char[128]));

  AT_to_GPS_Queue = xQueueCreate(5, sizeof(char[128]));
  GPS_to_AT_Queue = xQueueCreate(5, sizeof(char[256]));

  GPS_data_request_Semaphore = xSemaphoreCreateBinary();
  GPS_Background_Lock_Semaphore = xSemaphoreCreateBinary();

  // Load WiFi Credentials
  char ssid[65] = {0};
  char pwd[65] = {0};
  loadString("WIFI_SSID", ssid, sizeof(ssid), "");
  loadString("WIFI_PASS", pwd, sizeof(pwd), "");

  if (strlen(ssid) > 0) {
      Serial.printf("Connecting to WiFi: %s\n", ssid);
      WiFi.mode(WIFI_STA);
      WiFi.begin(ssid, pwd);
      
      // Wait for WiFi, but don't block forever
      int retries = 0;
      while (WiFi.status() != WL_CONNECTED && retries < 20) {
          delay(500);
          Serial.print(".");
          retries++;
      }
      
      if (WiFi.status() == WL_CONNECTED) {
          Serial.println("\nWiFi Connected!");
          Serial.print("IP Address: ");
          Serial.println(WiFi.localIP());
          
          char mdns_name[32];
          sprintf(mdns_name, "oceanbuoy-%s", BUOYANCY_ID);
          if (MDNS.begin(mdns_name)) {
              Serial.printf("mDNS responder started: %s.local\n", mdns_name);
          }
          
          setupOTA();
          
          // Send IP and Version back over LoRa queue if bound
          if (strlen(SAVED_TRANSCEIVER_ID) == 12) {
              char ip_msg[256];
              sprintf(ip_msg, "\r\n<%s,%s>\r\n+IP:%s\r\nOK\r\n", SAVED_TRANSCEIVER_ID, BUOYANCY_ID, WiFi.localIP().toString().c_str());
              xQueueSend(AT_to_LoRa_Queue, ip_msg, 0);
              
              char ver_msg[256];
              // Currently hardcoded Buoy version, you can change this when bumping
              sprintf(ver_msg, "\r\n<%s,%s>\r\n+VER:1.0.0\r\nOK\r\n", SAVED_TRANSCEIVER_ID, BUOYANCY_ID);
              xQueueSend(AT_to_LoRa_Queue, ver_msg, 0);
          }
      } else {
          Serial.println("\nWiFi Failed to connect.");
      }
  }

  // Create 1-hour timer (3600000 ms)
  HourlySaveTimer = xTimerCreate("HourlySaveTimer", pdMS_TO_TICKS(3600000), pdTRUE, (void *)0, HourlySaveTimerCallback);
  if (HourlySaveTimer != NULL)
  {
    xTimerStart(HourlySaveTimer, 0);
  }

  // Trigger an immediate GPS search on startup so we don't have to wait 1 hour for the first location
  if (GPS_Background_Lock_Semaphore != NULL)
  {
    xSemaphoreGive(GPS_Background_Lock_Semaphore);
  }

  xTaskCreatePinnedToCore(LoRa_app, "LoRa_app", 4096, NULL, 1, &LoRaAppHandle, 1);
  xTaskCreatePinnedToCore(AT_app, "AT_app", 4096, NULL, 1, &LoRaAppHandle, 1);
  xTaskCreatePinnedToCore(GPS_app, "GPS_app", 4096, NULL, 1, &GPSAppHandle, 1);
  LED_app_init();
}

void loop()
{
  if (WiFi.status() == WL_CONNECTED) {
      server.handleClient();
  }
  delay(10);
}
