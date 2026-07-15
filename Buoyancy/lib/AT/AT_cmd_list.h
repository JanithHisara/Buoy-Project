#ifndef AT_CMD_LIST_H
#define AT_CMD_LIST_H

#define MAX_WRITE_PARAMS 10
#define MAX_WRITE_PARAM_LEN 8

typedef enum{
    BOUND=0,
    NOT_BOUND
}buoyancy_bind_state_t;

typedef enum
{
    AT_CMD_TYPE_UNKNOWN = 0,
    AT_CMD_TYPE_BASIC,
    AT_CMD_TYPE_TEST,
    AT_CMD_TYPE_WRITE,
    AT_CMD_TYPE_READ,
    AT_CMD_TYPE_EXECUTE

} AT_CommandType;

typedef enum
{
    AT_CAT_UNKNOWN = 0,
    AT_CAT_BASIC_AT,
    AT_CAT_SCAN,
    AT_CAT_BIND,
    AT_CAT_BSOC,
    AT_CAT_CGPS,
    AT_CAT_CGPSINFO,
    AT_CAT_LED

} AT_CommandCategory;

typedef struct
{
    AT_CommandType AT_type;
    AT_CommandCategory AT_category;
    int param_count;
    char params[MAX_WRITE_PARAMS][MAX_WRITE_PARAM_LEN];
    char UserID[32];
    char BuoyancyID[32];
} AT_CommandInfo;

typedef struct
{
    const char *cmd;
    AT_CommandCategory category;
} AT_CommandMap;

static const AT_CommandMap AT_CMD_CAT_LIST[] = {
    {"AT", AT_CAT_BASIC_AT},
    {"SCAN", AT_CAT_SCAN},
    {"BIND", AT_CAT_BIND},
    {"BSOC", AT_CAT_BSOC},
    {"CGPS", AT_CAT_CGPS},
    {"CGPSINFO", AT_CAT_CGPSINFO},
    {"LED", AT_CAT_LED}
};

#endif