#include "LoRa_app.h"

TaskHandle_t LoRaAppHandle;

void LoRa_app(void *pvParameters)
{
    static char LoRa_RX_buf[256];
    static char LoRa_TX_buf[256];

    if (!LoRa_init(433E6))
    {
        Serial.println("Failed to initialize LoRa");
        vTaskDelete(NULL);
    }

    Serial.println("LoRa initialized successfully");

    while (1)
    {
        if (xQueueReceive(Serial_to_LoRa_Queue, LoRa_TX_buf, 0))
        {
            LoRa_send(LoRa_TX_buf);
        }

        if (LoRa_receive(LoRa_RX_buf, sizeof(LoRa_RX_buf)))
        {
            xQueueSend(LoRa_to_Serial_Queue, LoRa_RX_buf, 0);
        }

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}