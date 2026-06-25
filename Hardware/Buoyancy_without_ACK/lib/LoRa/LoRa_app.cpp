#include "LoRa_app.h"
#include "Identification.h"
#include "Memory_driver.h"

TaskHandle_t LoRaAppHandle;

void LoRa_app(void *pvParameters)
{
    static char LoRa_RX_buf[128];
    static char LoRa_TX_buf[256];

    if (!LoRa_init(433E6))
    {
        Serial.println("Failed to initialize LoRa");
        vTaskDelete(NULL);
    }

    Serial.println("LoRa initialized successfully");

    // Send boot notification over LoRa
    char boot_msg[128];
    char saved_trx[13];
    loadString(SAVED_TRX_ID_KEY, saved_trx, sizeof(saved_trx), "");
    if (strlen(saved_trx) == 12)
    {
        snprintf(boot_msg, sizeof(boot_msg), "\r\n<%s,%s>\r\nDEVICE_LOCATED\r\n", saved_trx, BUOYANCY_ID);
    }
    else
    {
        snprintf(boot_msg, sizeof(boot_msg), "\r\n<ALL,%s>\r\nDEVICE_LOCATED\r\n", BUOYANCY_ID);
    }
    LoRa_send(boot_msg);
    Serial.print("Sent Boot Message over LoRa: ");
    Serial.println(boot_msg);

    while (1)
    {
        if (xQueueReceive(AT_to_LoRa_Queue, LoRa_TX_buf, 0))
        {
            LoRa_send(LoRa_TX_buf);
        }

        if (LoRa_receive(LoRa_RX_buf, sizeof(LoRa_RX_buf)))
        {
            Serial.print("LoRa RX MSG : ");
            Serial.println(LoRa_RX_buf);
            xQueueSend(LoRa_to_AT_Queue, LoRa_RX_buf, 0);
        }

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}