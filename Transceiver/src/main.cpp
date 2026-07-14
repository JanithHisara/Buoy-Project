#include <Arduino.h>

#include "common_functions.h"

#include "LoRa_app.h"
#include "Serial_app.h"

QueueHandle_t Serial_to_LoRa_Queue;
QueueHandle_t LoRa_to_Serial_Queue;

char TRX_ID[13];

void setup()
{
  // put your setup code here, to run once:
  Serial.begin(115200);

  Serial.println("===============TRANSCEIVER==================");
  getChipID(TRX_ID, sizeof(TRX_ID));
  Serial.print("TRX ID : ");
  Serial.println(TRX_ID);

  Serial_to_LoRa_Queue = xQueueCreate(5, sizeof(char[128]));
  LoRa_to_Serial_Queue = xQueueCreate(5, sizeof(char[128]));

  xTaskCreatePinnedToCore(Serial_app, "Serial_app", 4096, NULL, 1, &SerialAppHandle, 0);
  xTaskCreatePinnedToCore(LoRa_app, "LoRa_app", 4096, NULL, 1, &LoRaAppHandle, 1);
}

void loop()
{
  // put your main code here, to run repeatedly:
}
