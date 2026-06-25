#include "AT_cmd_handler.h"

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
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+SCAN:%s\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID, cmd->BuoyancyID);
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
    else
    {
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
                if (!gps_power_Status)
                {
                    saveBool(SAVED_GPS_POWER_STATUS_KEY, true);

                    snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+CGPS:1\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);

                    xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                }
                else
                {
                    Serial.println("GPS already ON");

                    snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+CGPS:ALREADY GPS ON\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);

                    xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                }
            }
            else if (strcmp(cmd->params[0], "0") == 0)
            {
                if (gps_power_Status)
                {
                    saveBool(SAVED_GPS_POWER_STATUS_KEY, false);

                    snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+CGPS:0\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);

                    xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                }
                else
                {
                    Serial.println("GPS already OFF");

                    snprintf(AT_handler_TX_msg, sizeof(AT_handler_TX_msg), "\r\n<%s,%s>\r\n+CGPS:ALREADY GPS OFF\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);

                    xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                }
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
        sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+CGPS:\r\nOK\r\n", cmd->UserID, cmd->BuoyancyID);
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
        gps_power_Status = loadBool(SAVED_GPS_POWER_STATUS_KEY, false);
        if (gps_power_Status)
        {
            xSemaphoreGive(GPS_data_request_Semaphore);
            if (xQueueReceive(GPS_to_AT_Queue, &gpsData, 5000))
            {
                snprintf(
                    AT_handler_TX_msg,
                    sizeof(AT_handler_TX_msg),
                    "\r\n<%s,%s>\r\n+CGPSINFO:%.6f,%.6f,%02u/%02u/%04u,%02u:%02u:%02u,%.2f,%.2f,%.2f,%lu,%.1f\r\nOK\r\n",
                    cmd->UserID,
                    cmd->BuoyancyID,
                    gpsData.latitude,
                    gpsData.longitude,
                    gpsData.day,
                    gpsData.month,
                    gpsData.year,
                    gpsData.hour,
                    gpsData.minute,
                    gpsData.second,
                    gpsData.altitude_m,
                    gpsData.speed_kmph,
                    gpsData.course_deg,
                    (unsigned long)gpsData.satellites_num,
                    gpsData.hdop);
                xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
            }
        }
        else
        {
            sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+CGPSINFO:GPS TURNED OFF\r\nERROR\r\n", cmd->UserID, cmd->BuoyancyID);
            xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
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

void handle_LED_AT_CMD(const AT_CommandInfo *cmd)
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
