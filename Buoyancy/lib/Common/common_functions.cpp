#include "common_functions.h"

void getChipID(char *buffer, size_t bufferSize)
{
    if (buffer == nullptr || bufferSize < 13)
    {
        return;
    }

    uint64_t efuseMac = ESP.getEfuseMac();

    snprintf(buffer, bufferSize, "%012llX", efuseMac);
}

void clean_buffer(char *buf)
{
    buf[strcspn(buf, "\r\n")] = '\0';
}
