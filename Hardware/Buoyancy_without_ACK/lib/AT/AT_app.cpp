#include "AT_app.h"

TaskHandle_t AT_AppHandle;

#define LED_BUILTIN 2

void AT_app(void *pvParameters)
{
    pinMode(LED_BUILTIN, OUTPUT);

    char AT_RX_CMD_buf[128];
    char AT_TX_buf[128];
    AT_CommandInfo AT_cmdInfo;
    buoyancy_bind_state_t buoy_bind_state = NOT_BOUND;

    loadString(SAVED_TRX_ID_KEY, SAVED_TRANSCEIVER_ID, sizeof(SAVED_TRANSCEIVER_ID), "");

    if (strlen(SAVED_TRANSCEIVER_ID) == 12)
    {
        buoy_bind_state = BOUND;
        digitalWrite(LED_BUILTIN, HIGH);
        Serial.print("Loaded bound TRX ID: ");
        Serial.println(SAVED_TRANSCEIVER_ID);
    }
    else
    {
        digitalWrite(LED_BUILTIN, LOW);
    }

    while (1)
    {
        if (xQueueReceive(LoRa_to_AT_Queue, AT_RX_CMD_buf, portMAX_DELAY))
        {
            clean_buffer(AT_RX_CMD_buf);
            AT_cmdInfo = parseATCommand(AT_RX_CMD_buf);

            // Print Received Parameters
            {
                Serial.println("-------------------------");
                Serial.print("Received Command : ");
                Serial.println(AT_RX_CMD_buf);

                Serial.print("Buoyancy ID : ");
                Serial.println(AT_cmdInfo.BuoyancyID);

                Serial.print("TRX ID : ");
                Serial.println(AT_cmdInfo.UserID);

                Serial.print("Category : ");
                Serial.println(AT_cmdInfo.AT_category);

                Serial.print("Type : ");
                Serial.println(AT_cmdInfo.AT_type);

                Serial.print("Parameter Count : ");
                Serial.println(AT_cmdInfo.param_count);

                for (int i = 0; i < AT_cmdInfo.param_count; i++)
                {
                    Serial.print("Param[");
                    Serial.print(i);
                    Serial.print("] : ");
                    Serial.println(AT_cmdInfo.params[i]);
                }
                Serial.println("-------------------------");
            }
        }

        switch (buoy_bind_state)
        {
        case NOT_BOUND:
        {

            Serial.println("NOT BOUND");
            Serial.println("Contacting Me");

            switch ((AT_cmdInfo.AT_category))
            {
            case AT_CAT_SCAN:
            {
                handle_SCAN_AT_CMD(&AT_cmdInfo, NOT_BOUND);
                break;
            }
            case AT_CAT_BIND:
            {
                buoy_bind_state = handle_BIND_AT_CMD(&AT_cmdInfo, NOT_BOUND);
                break;
            }
            default:
                break;
            }
            break;
        }

        case BOUND:
        {
            Serial.println("BOUND");
            Serial.println("Contacting Me");
            if (strcmp(AT_cmdInfo.BuoyancyID, BUOYANCY_ID) == 0)
            {
                if (strcmp(AT_cmdInfo.UserID, SAVED_TRANSCEIVER_ID) == 0)
                {
                    Serial.println("Authentification done");
                    switch ((AT_cmdInfo.AT_category))
                    {
                    case AT_CAT_BIND:
                    {
                        buoy_bind_state = handle_BIND_AT_CMD(&AT_cmdInfo, BOUND);
                        break;
                    }
                    case AT_CAT_SCAN:
                    {
                        handle_SCAN_AT_CMD(&AT_cmdInfo, BOUND);
                        break;
                    }
                    case AT_CAT_CGPS:
                    {
                        handle_CGPS_AT_CMD(&AT_cmdInfo);
                        break;
                    }
                    case AT_CAT_CGPSINFO:
                    {
                        handle_CGPSINFO_AT_CMD(&AT_cmdInfo);
                        break;
                    }
                    case AT_CAT_BSOC:
                    {
                        handle_BSOC_AT_CMD(&AT_cmdInfo);
                        break;
                    }
                    case AT_CAT_LED:
                    {
                        handle_LED_AT_CMD(&AT_cmdInfo);
                        break;
                    }
                    default:
                    {
                        break;
                    }
                    }
                }
                else if (AT_cmdInfo.AT_category == AT_CAT_BIND && AT_cmdInfo.AT_type == AT_CMD_TYPE_WRITE && AT_cmdInfo.param_count == 1 && strcmp(AT_cmdInfo.params[0], "0") == 0)
                {
                    Serial.println("Authentification bypassed for Unbind command");
                    buoy_bind_state = handle_BIND_AT_CMD(&AT_cmdInfo, BOUND);
                }
                else
                {
                    Serial.print("Authentification failed. Expected TRX: ");
                    Serial.print(SAVED_TRANSCEIVER_ID);
                    Serial.print(", Got: ");
                    Serial.println(AT_cmdInfo.UserID);
                    
                    extern char AT_handler_TX_msg[256];
                    sprintf(AT_handler_TX_msg, "\r\n<%s,%s>\r\n+BIND:AUTH_FAILED\r\nERROR\r\n", AT_cmdInfo.UserID, AT_cmdInfo.BuoyancyID);
                    xQueueSend(AT_to_LoRa_Queue, AT_handler_TX_msg, 0);
                }
            }

            break;
        }

        default:
            break;
        }
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}