#ifndef AT_cmd_HANDLER_H
#define AT_cmd_HANDLER_H

#include <Arduino.h>
#include "AT_cmd_list.h"
#include "Identification.h"
#include "common_functions.h"
#include "queues.h"
#include "semaphores.h"
#include "data_types.h"
#include "Memory_driver.h"

void handle_BASIC_AT_CMD(const AT_CommandInfo *cmd);
buoyancy_bind_state_t handle_BIND_AT_CMD(const AT_CommandInfo *cmd, buoyancy_bind_state_t current_state);
void handle_SCAN_AT_CMD(const AT_CommandInfo *cmd, buoyancy_bind_state_t current_state);
void handle_CGPS_AT_CMD(const AT_CommandInfo *cmd);
void handle_CGPSINFO_AT_CMD(const AT_CommandInfo *cmd);
void handle_LED_AT_CMD(const AT_CommandInfo *cmd);
void handle_BSOC_AT_CMD(const AT_CommandInfo *cmd);

#endif