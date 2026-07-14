#include <Arduino.h>

#include "common_functions.h"

#include "LoRa_app.h"
#include "AT_app.h"
#include "GPS_app.h"

QueueHandle_t AT_to_LoRa_Queue;
QueueHandle_t LoRa_to_AT_Queue;

QueueHandle_t AT_to_GPS_Queue;
QueueHandle_t GPS_to_AT_Queue;

SemaphoreHandle_t GPS_data_request_Semaphore;

TaskHandle_t AT_AppHandle; // Restore definition for AT_app task handle

char BUOYANCY_ID[13];
char SAVED_TRANSCEIVER_ID[13] = {0};

const char *SAVED_TRX_ID_KEY = "TRXID_KEY";
const char *SAVED_GPS_POWER_STATUS_KEY = "GPS_PWR";

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
  GPS_to_AT_Queue = xQueueCreate(5, sizeof(GPS_Data)); // Change back to struct size to avoid overflow

  GPS_data_request_Semaphore = xSemaphoreCreateBinary();

  xTaskCreatePinnedToCore(LoRa_app, "LoRa_app", 4096, NULL, 1, &LoRaAppHandle, 1);
  xTaskCreatePinnedToCore(AT_app, "AT_app", 4096, NULL, 1, &AT_AppHandle, 1); // Use AT_AppHandle
  xTaskCreatePinnedToCore(GPS_app, "GPS_app", 4096, NULL, 1, &GPSAppHandle, 1);
}

void loop()
{
  // put your main code here, to run repeatedly:
}
