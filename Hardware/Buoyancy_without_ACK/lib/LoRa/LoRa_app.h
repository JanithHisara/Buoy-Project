#ifndef LORA_APP_H
#define LORA_APP_H

#include <Arduino.h>

#include "LoRa_driver.h"
#include "queues.h"

extern TaskHandle_t LoRaAppHandle;

void LoRa_app(void *pvParameters);

#endif