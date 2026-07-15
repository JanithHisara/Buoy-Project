#include <Arduino.h>

#include "common_functions.h"

#include "LoRa_app.h"
#include "AT_app.h"
#include "GPS_app.h"
#include "LED_driver.h"

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

void HourlySaveTimerCallback(TimerHandle_t xTimer)
{
  if (GPS_Background_Lock_Semaphore != NULL)
  {
    xSemaphoreGive(GPS_Background_Lock_Semaphore);
  }
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

  // Create 1-hour timer (3600000 ms)
  HourlySaveTimer = xTimerCreate("HourlySaveTimer", pdMS_TO_TICKS(3600000), pdTRUE, (void *)0, HourlySaveTimerCallback);
  if (HourlySaveTimer != NULL)
  {
    xTimerStart(HourlySaveTimer, 0);
  }

  xTaskCreatePinnedToCore(LoRa_app, "LoRa_app", 4096, NULL, 1, &LoRaAppHandle, 1);
  xTaskCreatePinnedToCore(AT_app, "AT_app", 4096, NULL, 1, &LoRaAppHandle, 1);
  xTaskCreatePinnedToCore(GPS_app, "GPS_app", 4096, NULL, 1, &GPSAppHandle, 1);
  LED_app_init();
}

void loop()
{
  // put your main code here, to run repeatedly:
}
