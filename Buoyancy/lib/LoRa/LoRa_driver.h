#ifndef LORA_DRIVER_H
#define LORA_DRIVER_H

#include "LoRa_hal.h"

#include <SPI.h>
#include <LoRa.h>

bool LoRa_init(uint32_t frequency);
bool LoRa_send(const char* data);
bool LoRa_receive(char* buffer, size_t bufferSize);

#endif