#include <Arduino.h>
#include "LED_driver.h"
#include <Adafruit_NeoPixel.h>
#include "AT_app.h" // to get buoy_bind_state

#ifndef LED_BUILTIN
#define LED_BUILTIN 2
#endif

#define LED_PIN 25
#define NUM_LEDS 20 // Configured for 60-LED strip

Adafruit_NeoPixel pixels(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

uint8_t led_r_val = 0;
uint8_t led_g_val = 0;
uint8_t led_b_val = 255; // Default color: Blue when bound

TaskHandle_t LED_TaskHandle = NULL;

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
            pixels.clear(); // Ensure all 60 are off
            pixels.fill(pixels.Color(led_r_val, led_g_val, led_b_val), 0, 20); // Turn on only the first 20
            pixels.show();
        }
        else
        {
            pixels.clear();
            pixels.show();
        }
        
        // Onboard LED as Sleep/Wake indicator
        if (digitalRead(32) == HIGH) {
            digitalWrite(LED_BUILTIN, HIGH); // Awake
        } else {
            digitalWrite(LED_BUILTIN, LOW);  // Asleep
        }
        
        // Update at 10Hz to quickly reflect color changes while saving CPU
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

void LED_app_init(void)
{
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
