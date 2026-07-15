#include "AT_cmd_handler.h"
#include <Preferences.h>

/*void handle_CMD_template(const AT_CommandInfo *cmd)
{
    switch (cmd->AT_type)
    {
    case AT_CMD_TYPE_TEST:
    {
        break;
    }
    case AT_CMD_TYPE_READ:
    {
        break;
    }
    case AT_CMD_TYPE_WRITE:
    {
        break;
    }
    case AT_CMD_TYPE_EXECUTE:
    {
        break;
    }
    case AT_CMD_TYPE_UNKNOWN:
    {
        break;
    }
    default:
    {
        break;
    }
    }
}
*/

char AT_handler_TX_msg[256];

static GPS_Data gpsData;
static bool gps_power_Status;

void handle_BASIC_AT_CMD(const AT_CommandInfo *cmd)
{

    switch (cmd->AT_type)
    {
    case AT_CMD_TYPE_TEST:
    {
        break;
    }
    case AT_CMD_TYPE_READ:
    {
        break;
    }
    case AT_CMD_TYPE_WRITE:
    {
        break;
    }
    case AT_CMD_TYPE_EXECUTE:
    {
        break;
    }
    case AT_CMD_TYPE_UNKNOWN:
    {
        break;
    }
    default:
    {
        break;
    }
    }
}

buoyancy_bind_state_t handle_BIND_AT_CMD(const AT_CommandInfo *cmd, buoyancy_bind_state_t current_state)
{

    if (current_state == NOT_BOUND)
    {
        switch (cmd->AT_type)
        {
        case AT_CMD_TYPE_TEST:
        {
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:(0,1)\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            break;
        }
        case AT_CMD_TYPE_READ:
        {
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:0\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            break;
        }
        case AT_CMD_TYPE_WRITE:
        {
            if (strcmp(cmd->BuoyancyID, BUOYANCY_ID) == 0)
            {

                if (cmd->param_count == 1)
                {
                    if (strcmp(cmd->params[0], "1") == 0)
                    {
                        TURNON_LED();
                        // save received TRX ID
                        saveString(SAVED_TRX_ID_KEY, cmd->UserID);
                        loadString(SAVED_TRX_ID_KEY, SAVED_TRANSCEIVER_ID, sizeof(SAVED_TRANSCEIVER_ID), "");
                        sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:1,%s,%s\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID, cmd->UserID, cmd->BuoyancyID);
                        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                        return BOUND;
                    }
                    else if (strcmp(cmd->params[0], "0") == 0)
                    {
                        sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:ALREADY NOT BINDED\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
                        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                    }

                    else
                    {
                        Serial.println("Wrong Parameter Entered");
                        sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:WRONG PARAMETER\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
                        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                    }
                }
                else
                {
                    Serial.println("Wrong Parameter Count");
                    sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:WRONG PARAMETER COUNT\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
                    xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                }
            }
            break;
        }
        case AT_CMD_TYPE_EXECUTE:
        {
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:%s\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID, SAVED_TRANSCEIVER_ID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            break;
        }
        case AT_CMD_TYPE_UNKNOWN:
        {
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:%s\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            break;
        }
        default:
        {
            break;
        }
        }
    }
    else if (current_state == BOUND)
    {
        switch (cmd->AT_type)
        {
        case AT_CMD_TYPE_TEST:
        {
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:(0,1)\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            break;
        }
        case AT_CMD_TYPE_READ:
        {
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:1\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            break;
        }
        case AT_CMD_TYPE_WRITE:
        {

            if (cmd->param_count == 1)
            {
                if (strcmp(cmd->params[0], "0") == 0)
                {
                    TURNOFF_LED();
                    // save received TRX ID
                    SAVED_TRANSCEIVER_ID[0] = '\0'; // clear form ram
                    saveString(SAVED_TRX_ID_KEY, "");
                    sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:0,%s,%s\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID, cmd->UserID, cmd->BuoyancyID);
                    xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                    return NOT_BOUND;
                }
                else if (strcmp(cmd->params[0], "1") == 0)
                {
                    sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:ALREADY BINDED\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
                    xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                }
                else
                {
                    sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:WRONG PARAMETER\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
                    xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                }
            }
            else
            {
                sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:WRONG PARAMETER COUNT\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
                xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                Serial.println("Wrong Parameter Count");
            }

            break;
        }
        case AT_CMD_TYPE_EXECUTE:
        {
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:%s\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID, SAVED_TRANSCEIVER_ID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            break;
        }
        case AT_CMD_TYPE_UNKNOWN:
        {
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:%s\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            break;
        }
        default:
        {
            break;
        }
        }
    }
    else
    {
        Serial.println("unsupported State");
    }
    return current_state;
}

void handle_SCAN_AT_CMD(const AT_CommandInfo *cmd, buoyancy_bind_state_t current_state)
{
    if (current_state == NOT_BOUND)
    {
        if (strcmp(cmd->BuoyancyID, "ALL") == 0 || strcmp(cmd->BuoyancyID, BUOYANCY_ID) == 0)
        {
            if (cmd->AT_type == AT_CMD_TYPE_EXECUTE)
            {
                sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+SCAN:%s\r\nOK\r\n", cmd->UserID, BUOYANCY_ID, BUOYANCY_ID);
                xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            }
        }
    }
    else if (current_state == BOUND)
    {
        // Binded buoys explicitly ignore "ALL" scans and only respond when targeted by their specific ID
        if (strcmp(cmd->BuoyancyID, BUOYANCY_ID) == 0)
        {
            switch (cmd->AT_type)
            {
            case AT_CMD_TYPE_TEST:
            {
                sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+SCAN:\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
                xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                break;
            }
            case AT_CMD_TYPE_READ:
            {
                sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+SCAN:\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
                xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                break;
            }
            case AT_CMD_TYPE_WRITE:
            {
                sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+SCAN:\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
                xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                break;
            }
            case AT_CMD_TYPE_EXECUTE:
            {
                sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+SCAN:%s\r\nOK\r\n", cmd->UserID, BUOYANCY_ID, BUOYANCY_ID);
                xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                break;
            }
            case AT_CMD_TYPE_UNKNOWN:
            {
                break;
            }
            default:
            {
                break;
            }
            }
        }
    }
}

void handle_SETWIFI_AT_CMD(const AT_CommandInfo *cmd)
{
    if (cmd->AT_type == AT_CMD_TYPE_WRITE)
    {
        if (cmd->param_count >= 2)
        {
            saveString("WIFI_SSID", cmd->params[0]);
            saveString("WIFI_PASS", cmd->params[1]);
            
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+SETWIFI:OK\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            
            // Wait a moment for LoRa to send, then restart to apply WiFi settings
            delay(1000);
            ESP.restart();
        }
        else
        {
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+SETWIFI:ERROR\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        }
    }
}

void handle_CGPS_AT_CMD(const AT_CommandInfo *cmd)
{
    switch (cmd->AT_type)
    {
    case AT_CMD_TYPE_TEST:
    {
        sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+CGPS:(0,1)\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        break;
    }
    case AT_CMD_TYPE_READ:
    {
        gps_power_Status = loadBool(SAVED_GPS_POWER_STATUS_KEY, false);
        sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+CGPS:%d\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID, gps_power_Status);
        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        break;
    }
    case AT_CMD_TYPE_WRITE:
    {
        gps_power_Status = loadBool(SAVED_GPS_POWER_STATUS_KEY, false);

        if (cmd->param_count == 1)
        {
            if (strcmp(cmd->params[0], "1") == 0)
            {
                // Trigger background search instead of permanent ON
                if (GPS_Background_Lock_Semaphore != NULL) {
                    xSemaphoreGive(GPS_Background_Lock_Semaphore);
                }

                snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+CGPS:1\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
                xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            }
            else if (strcmp(cmd->params[0], "0") == 0)
            {
                saveBool(SAVED_GPS_POWER_STATUS_KEY, false);
                gps_power_Status = false; // Update local state
                
                pinMode(32, OUTPUT);
                digitalWrite(32, LOW); // Force GPS OFF

                snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+CGPS:0\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
                xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            }
            else
            {
                snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+CGPS:INVALID PARAMETER\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
                xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            }
        }
        else
        {
            snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+CGPS:INVALID PARAMETER COUNT\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        }
        break;
    }
    case AT_CMD_TYPE_EXECUTE:
    {
        // Trigger background search instead of permanent ON
        if (GPS_Background_Lock_Semaphore != NULL) {
            xSemaphoreGive(GPS_Background_Lock_Semaphore);
        }

        sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+CGPS:1\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        break;
    }
    case AT_CMD_TYPE_UNKNOWN:
    {
        break;
    }
    default:
    {
        break;
    }
    }
}

void handle_CGPSINFO_AT_CMD(const AT_CommandInfo *cmd)
{
    switch (cmd->AT_type)
    {
    case AT_CMD_TYPE_TEST:
    {
        sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+CGPSINFO:\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        break;
    }
    case AT_CMD_TYPE_READ:
    {
        sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+CGPSINFO:\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        break;
    }
    case AT_CMD_TYPE_WRITE:
    {
        sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+CGPSINFO:\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        break;
    }
    case AT_CMD_TYPE_EXECUTE:
    {
        // Immediately send history to Master from NVS
        GPS_History_Data history;
        loadGPSHistory(&history, sizeof(history));
        
        if (history.count == 0) {
            // No history yet, send null values
            snprintf(
                AT_handler_TX_msg,
                sizeof(AT_handler_TX_msg),
                "\r\n<%s,%s>\r\n+CGPSINFO:,,,,,,,,\r\nOK\r\n",
                cmd->UserID,
                cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, &AT_handler_TX_msg, 0);
        } else {
            // Send each historical point
            for (int i = 0; i < history.count; i++) {
                GPS_Data *gpsData = &history.records[i];
                snprintf(
                    AT_handler_TX_msg,
                    sizeof(AT_handler_TX_msg),
                    "\r\n<%s,%s>\r\n+CGPSINFO:%.6f,%.6f,%02u/%02u/%04u,%02u:%02u:%02u,%.2f,%.2f,%.2f,%lu,%.1f,CACHED\r\n",
                    cmd->UserID,
                    cmd->BuoyancyID,
                    gpsData->latitude,
                    gpsData->longitude,
                    gpsData->day,
                    gpsData->month,
                    gpsData->year,
                    gpsData->hour,
                    gpsData->minute,
                    gpsData->second,
                    gpsData->altitude_m,
                    gpsData->speed_kmph,
                    gpsData->course_deg,
                    (unsigned long)gpsData->satellites_num,
                    gpsData->hdop);
                xQueueSend(AT_to_LoRa_Queue, &AT_handler_TX_msg, 0);
                vTaskDelay(pdMS_TO_TICKS(150)); // Tiny delay so LoRa doesn't choke on back-to-back packets
            }
            
            // Send OK at the end
            snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "OK\r\n");
            xQueueSend(AT_to_LoRa_Queue, &AT_handler_TX_msg, 0);
        }

        // Trigger background live location search
        extern SemaphoreHandle_t GPS_Background_Lock_Semaphore;
        if (GPS_Background_Lock_Semaphore != NULL) {
            xSemaphoreGive(GPS_Background_Lock_Semaphore);
        }
        break;
    }
    case AT_CMD_TYPE_UNKNOWN:
    {
        break;
    }
    default:
    {
        break;
    }
    }
}

// We no longer need led_state as it's handled automatically by the Task
static char led_r_str[8] = "0", led_g_str[8] = "0", led_b_str[8] = "255";

void handle_LED_AT_CMD(const AT_CommandInfo *cmd)
{
    switch (cmd->AT_type)
    {
    case AT_CMD_TYPE_TEST:
    {
        snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+LED:(R,G,B)\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        break;
    }
    case AT_CMD_TYPE_READ:
    {
        snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+LED:1,%s,%s,%s\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID, led_r_str, led_g_str, led_b_str);
        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        break;
    }
    case AT_CMD_TYPE_WRITE:
    {
        if (cmd->param_count >= 3 && cmd->param_count <= 5) // AT+LED=R,G,B[,OffTime[,State]]
        {
            strncpy(led_r_str, cmd->params[0], sizeof(led_r_str)-1);
            strncpy(led_g_str, cmd->params[1], sizeof(led_g_str)-1);
            strncpy(led_b_str, cmd->params[2], sizeof(led_b_str)-1);
            
            extern uint8_t led_r_val;
            extern uint8_t led_g_val;
            extern uint8_t led_b_val;
            extern uint16_t led_off_time;
            extern uint8_t led_is_on;

            led_r_val = atoi(led_r_str);
            led_g_val = atoi(led_g_str);
            led_b_val = atoi(led_b_str);
            
            if (cmd->param_count >= 4) {
                led_off_time = atoi(cmd->params[3]);
            } else {
                led_off_time = 0; // Default to solid on
            }
            
            if (cmd->param_count == 5) {
                led_is_on = atoi(cmd->params[4]);
            } else {
                led_is_on = 1; // Default to ON
            }

            // Save to NVS
            Preferences prefs;
            prefs.begin("led_cfg", false);
            prefs.putUChar("r", led_r_val);
            prefs.putUChar("g", led_g_val);
            prefs.putUChar("b", led_b_val);
            prefs.putUShort("off_time", led_off_time);
            prefs.putUChar("is_on", led_is_on);
            prefs.end();

            snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+LED:1,%s,%s,%s,%d,%d\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID, led_r_str, led_g_str, led_b_str, led_off_time, led_is_on);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        }
        else if (cmd->param_count == 1 && atoi(cmd->params[0]) == 0)
        {
            // Fallback for AT+LED=0 (off)
            extern uint8_t led_is_on;
            led_is_on = 0;
            
            Preferences prefs;
            prefs.begin("led_cfg", false);
            prefs.putUChar("is_on", led_is_on);
            prefs.end();
            
            snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+LED:0\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        }
        else
        {
            snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+LED:\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        }
        break;
    }
    case AT_CMD_TYPE_EXECUTE:
    {
        snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+LED:\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        break;
    }
    case AT_CMD_TYPE_UNKNOWN:
    {
        snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+LED:\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
        xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
        break;
    }
    default:
    {
        break;
    }
    }
}

void handle_BSOC_AT_CMD(const AT_CommandInfo *cmd)
{
    switch (cmd->AT_type)
    {
    case AT_CMD_TYPE_TEST:
    {
        break;
    }
    case AT_CMD_TYPE_READ:
    {
        break;
    }
    case AT_CMD_TYPE_WRITE:
    {
        break;
    }
    case AT_CMD_TYPE_EXECUTE:
    {
        break;
    }
    case AT_CMD_TYPE_UNKNOWN:
    {
        break;
    }
    default:
    {
        break;
    }
    }
}
