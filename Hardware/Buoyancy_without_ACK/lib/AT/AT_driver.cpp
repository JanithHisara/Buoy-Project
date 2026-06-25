#include "AT_driver.h"

static AT_CommandCategory get_category(const char *cmd)
{
    const char *start = strchr(cmd, '+');
    if (!start)
        return AT_CAT_UNKNOWN;
    start++;

    const char *end = strpbrk(start, "= ?");
    size_t len = end ? (size_t)(end - start) : strlen(start);

    for (size_t i = 0; i < sizeof(AT_CMD_CAT_LIST) / sizeof(AT_CMD_CAT_LIST[0]); i++)
    {
        if (strlen(AT_CMD_CAT_LIST[i].cmd) == len &&
            strncmp(start, AT_CMD_CAT_LIST[i].cmd, len) == 0)
        {
            return AT_CMD_CAT_LIST[i].category;
        }
    }
    return AT_CAT_UNKNOWN;
}

static AT_CommandType get_type(const char *cmd)
{
    size_t len = strlen(cmd);

    if (len > 0 && cmd[len - 1] == '?')
    {
        if (len > 1 && cmd[len - 2] == '=')
            return AT_CMD_TYPE_TEST;

        return AT_CMD_TYPE_READ;
    }

    if (strchr(cmd, '='))
    {
        return AT_CMD_TYPE_WRITE;
    }

    if (strncmp(cmd, "AT+", 3) == 0)
    {
        return AT_CMD_TYPE_EXECUTE;
    }

    return AT_CMD_TYPE_UNKNOWN;
}

static int get_parameters(const char *cmd, char params[MAX_WRITE_PARAMS][MAX_WRITE_PARAM_LEN])
{
    const char *equal_ptr = strchr(cmd, '=');

    if (equal_ptr == NULL)
    {
        return 0;
    }

    // Move after '='
    equal_ptr++;

    char temp[128];
    strncpy(temp, equal_ptr, sizeof(temp) - 1);
    temp[sizeof(temp) - 1] = '\0';

    int count = 0;

    char *token = strtok(temp, ",");

    while (token != NULL && count < MAX_WRITE_PARAMS)
    {
        strncpy(params[count], token, MAX_WRITE_PARAM_LEN - 1);
        params[count][MAX_WRITE_PARAM_LEN - 1] = '\0';

        count++;
        token = strtok(NULL, ",");
    }

    return count;
}

static bool get_authorization_data(const char *input,char *userID,size_t userSize,char *buoyancyID,size_t buoyancySize,const char **at_cmd_start)
{
    if (!input || input[0] != '<')
        return false;

    const char *endBracket = strchr(input, '>');
    if (!endBracket)
        return false;

    const char *comma = strchr(input, ',');
    if (!comma || comma > endBracket)
        return false;

    size_t userLen = comma - (input + 1);
    size_t buoyLen = endBracket - comma - 1;

    if (userLen >= userSize)
        userLen = userSize - 1;

    if (buoyLen >= buoyancySize)
        buoyLen = buoyancySize - 1;

    strncpy(userID, input + 1, userLen);
    userID[userLen] = '\0';

    strncpy(buoyancyID, comma + 1, buoyLen);
    buoyancyID[buoyLen] = '\0';

    const char *cmdStart = endBracket + 1;

    if (*cmdStart != ',')
        return false;

    cmdStart++; // skip ','

    while (*cmdStart == ' ')
        cmdStart++;

    *at_cmd_start = cmdStart;

    return true;
}

AT_CommandInfo parseATCommand(const char *input)
{
    AT_CommandInfo AT_info;

    memset(&AT_info, 0, sizeof(AT_info));

    AT_info.AT_type = AT_CMD_TYPE_UNKNOWN;
    AT_info.AT_category = AT_CAT_UNKNOWN;

    const char *cmd = NULL;

    if (!get_authorization_data(input,AT_info.UserID,sizeof(AT_info.UserID),AT_info.BuoyancyID,sizeof(AT_info.BuoyancyID),&cmd))
    {
        return AT_info;
    }

    if (strncmp(cmd, "AT", 2) != 0)
    {
        return AT_info;
    }

    if (strcmp(cmd, "AT") == 0)
    {
        AT_info.AT_type = AT_CMD_TYPE_BASIC;
        AT_info.AT_category = AT_CAT_BASIC_AT;
        return AT_info;
    }

    AT_info.AT_type = get_type(cmd);
    AT_info.AT_category = get_category(cmd);

    if (AT_info.AT_type == AT_CMD_TYPE_WRITE)
    {
        AT_info.param_count = get_parameters(cmd, AT_info.params);
    }

    return AT_info;
}