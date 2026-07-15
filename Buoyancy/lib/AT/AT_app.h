#ifndef AT_APP_H
#define AT_APP_H

#include <Arduino.h>
#include "AT_driver.h"
#include "queues.h"

#include "common_functions.h"
#include "../AT/AT_cmd_handler/AT_cmd_handler.h"
#include "Identification.h"
#include "Memory_driver.h"

void AT_app(void *pvParameters);

extern TaskHandle_t AT_AppHandle;
extern buoyancy_bind_state_t buoy_bind_state;



#endif