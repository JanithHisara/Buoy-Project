#ifndef SERIAL_APP_H
#define SERIAL_APP_H

#include <Arduino.h>

#include "queues.h"

extern TaskHandle_t SerialAppHandle;

void Serial_app(void *pvParameters);

#endif // SERIAL_APP_H