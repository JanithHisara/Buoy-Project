#include "GPS_app.h"

TaskHandle_t GPSAppHandle;

void GPS_app(void *pvParameters)
{
    GPS_init();

    while (true)
    {
        GPS_Data gps_data = GPS_getData();

        if (xSemaphoreTake(GPS_data_request_Semaphore, 0) == pdTRUE)
        {
            // Send GPS data to LoRa queue
            xQueueSend(GPS_to_AT_Queue, &gps_data, 0);
        }

        GPS_loop();
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}
