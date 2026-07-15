#include <Arduino.h>
#include "LED_driver.h"
#include <Adafruit_NeoPixel.h>
#include "AT_app.h" // to get buoy_bind_state
#include <Preferences.h>

#ifndef LED_BUILTIN
#define LED_BUILTIN 2
#endif

#define LED_PIN 25
#define NUM_LEDS 20 // Configured for 60-LED strip

Adafruit_NeoPixel pixels(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

uint8_t led_r_val = 0;
uint8_t led_g_val = 0;
uint8_t led_b_val = 255; // Default color: Blue when bound
uint8_t led_is_on = 1;

TaskHandle_t LED_TaskHandle = NULL;
uint16_t led_off_time = 0;

void vLEDBlinkTask(void *pvParameters)
{
    pixels.begin();
    pixels.clear();
    pixels.show();
    
    pinMode(LED_BUILTIN, OUTPUT);

    while (1)
    {
        if (buoy_bind_state == BOUND)
        {
            if (led_is_on == 0 || (led_r_val == 0 && led_g_val == 0 && led_b_val == 0))
            {
                // LED completely off
                pixels.clear();
                pixels.show();
                vTaskDelay(pdMS_TO_TICKS(100));
            }
            else if (led_off_time > 0)
            {
                // Blink logic: 1 second ON, led_off_time OFF
                pixels.clear();
                pixels.fill(pixels.Color(led_r_val, led_g_val, led_b_val), 0, 20);
                pixels.show();
                
                // Sleep indicator during ON phase
                digitalWrite(LED_BUILTIN, digitalRead(32) == HIGH ? HIGH : LOW);
                
                vTaskDelay(pdMS_TO_TICKS(1000)); // Always on for 1s
                
                pixels.clear();
                pixels.show();
                
                // Sleep indicator during OFF phase
                digitalWrite(LED_BUILTIN, digitalRead(32) == HIGH ? HIGH : LOW);
                
                vTaskDelay(pdMS_TO_TICKS(led_off_time)); // User defined OFF time
            }
            else
            {
                // Solid ON
                pixels.clear();
                pixels.fill(pixels.Color(led_r_val, led_g_val, led_b_val), 0, 20);
                pixels.show();
                vTaskDelay(pdMS_TO_TICKS(100));
            }
        }
        else
        {
            pixels.clear();
            pixels.show();
            vTaskDelay(pdMS_TO_TICKS(100));
        }
        
        // Onboard LED as Sleep/Wake indicator if not blinking
        if (led_off_time == 0 || led_is_on == 0 || (led_r_val == 0 && led_g_val == 0 && led_b_val == 0) || buoy_bind_state != BOUND) {
            if (digitalRead(32) == HIGH) {
                digitalWrite(LED_BUILTIN, HIGH); // Awake
            } else {
                digitalWrite(LED_BUILTIN, LOW);  // Asleep
            }
        }
    }
}

void LED_app_init(void)
{
    Preferences prefs;
    prefs.begin("led_cfg", true); // true = read-only mode
    led_r_val = prefs.getUChar("r", 0);
    led_g_val = prefs.getUChar("g", 0);
    led_b_val = prefs.getUChar("b", 255);
    led_off_time = prefs.getUShort("off_time", 0);
    led_is_on = prefs.getUChar("is_on", 1);
    prefs.end();

    xTaskCreatePinnedToCore(
        vLEDBlinkTask,
        "LED_Task",
        2048,
        NULL,
        1,
        &LED_TaskHandle,
        1
    );
}
