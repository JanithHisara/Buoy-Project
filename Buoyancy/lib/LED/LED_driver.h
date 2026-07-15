#ifndef LED_DRIVER_H
#define LED_DRIVER_H

#include <Arduino.h>

void LED_app_init(void);

extern uint8_t led_r_val;
extern uint8_t led_g_val;
extern uint8_t led_b_val;

#endif
