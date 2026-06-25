#include "Serial_app.h"

TaskHandle_t SerialAppHandle;

void Serial_app(void *pvParameters)
{
  static char serial_TX_Buf[128];
  static char serial_RX_Buf[128];

  while (1)
  {
    if (Serial.available())
    {
      size_t len = Serial.readBytesUntil('\n', serial_TX_Buf, sizeof(serial_TX_Buf) - 1);
      serial_TX_Buf[len] = '\0'; // Null-terminate the string
      xQueueSend(Serial_to_LoRa_Queue, serial_TX_Buf, 0);
      Serial.print("Reveived via Serial : ");
      Serial.println(serial_TX_Buf);
    }

    if (xQueueReceive(LoRa_to_Serial_Queue, serial_RX_Buf, 0) == pdTRUE)
    {
      Serial.print("Received via LoRa: ");
      Serial.println(serial_RX_Buf);
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}