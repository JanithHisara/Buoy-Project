#include "GPS_app.h"

TaskHandle_t GPSAppHandle;

void GPS_app(void *pvParameters)
{
    GPS_init();
    
    bool is_background_searching = false;
    uint32_t search_start_time = 0;

    while (true)
    {
        GPS_Data gps_data = GPS_getData();

        if (xSemaphoreTake(GPS_data_request_Semaphore, 0) == pdTRUE)
        {
            // Send GPS data to LoRa queue (legacy request if needed)
            xQueueSend(GPS_to_AT_Queue, &gps_data, 0);
        }
        
        if (xSemaphoreTake(GPS_Background_Lock_Semaphore, 0) == pdTRUE)
        {
            if (!is_background_searching) {
                is_background_searching = true;
                search_start_time = millis();
                // Forcefully turn on GPS for the search
                pinMode(32, OUTPUT);
                digitalWrite(32, HIGH);
                Serial.println("ESP32 WAKEUP - GPS ON");
                Serial.println("Started Background GPS Search...");
            }
        }
        
        if (is_background_searching)
        {
            if (gps_data.latitude != 0.0 && gps_data.longitude != 0.0 && gps_data.location_age_ms < 2000) {
                // Got a FRESH lock! Save it.
                GPS_History_Data history;
                loadGPSHistory(&history, sizeof(history));
                
                // Shift history down
                if (history.count < 5) history.count++;
                for (int i = history.count - 1; i > 0; i--) {
                    history.records[i] = history.records[i-1];
                }
                history.records[0] = gps_data;
                saveGPSHistory(&history, sizeof(history));
                
                Serial.println("Background GPS Lock Achieved and Saved!");
                is_background_searching = false;
                
                // Always turn off GPS after search finishes
                digitalWrite(32, LOW);
                Serial.println("ESP32 SLEEP - GPS OFF (Lora Listening)");
            }
            else if (millis() - search_start_time > 900000) { // 15 minutes timeout
                Serial.println("Background GPS Search Timeout.");
                is_background_searching = false;
                
                digitalWrite(32, LOW);
                Serial.println("ESP32 SLEEP - GPS OFF (Lora Listening)");
            }
        }

        GPS_loop();
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}
