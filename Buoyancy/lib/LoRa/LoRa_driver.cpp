#include "LoRa_driver.h"

bool LoRa_init(uint32_t frequency)
{
    LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
    if (!LoRa.begin(frequency))
    {
        return false;
    }
    return true;
}

bool LoRa_send(const char* data)
{
    LoRa.beginPacket();
    LoRa.print(data);
    return (LoRa.endPacket() == 1);
}

bool LoRa_receive(char* buffer, size_t bufferSize)
{
    int packetSize = LoRa.parsePacket();
    if (packetSize)
    {
        size_t i = 0;
        while (LoRa.available() && i < bufferSize - 1)
        {
            buffer[i++] = (char)LoRa.read();
        }
        buffer[i] = '\0';
        return true;
    }
    return false;
}
