#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

#include "pico/stdlib.h"
#include "hardware/gpio.h"

#define PIN_S0 2
#define PIN_S1 3
#define PIN_S2 4
#define PIN_S3 5
#define PIN_OUT 6

static volatile uint32_t g_pulse_count = 0;

static void out_irq_callback(uint gpio, uint32_t events)
{
  (void)gpio;
  (void)events;
  g_pulse_count++;
}

static inline void tcs_set_scaling_20_percent(void)
{
  gpio_put(PIN_S0, 1);
  gpio_put(PIN_S1, 0);
}

typedef enum
{
  FILTER_RED,
  FILTER_GREEN,
  FILTER_BLUE,
  FILTER_CLEAR
} tcs_filter_t;

static inline void tcs_set_filter(tcs_filter_t f)
{
  switch (f)
  {
  case FILTER_RED:
    gpio_put(PIN_S2, 0);
    gpio_put(PIN_S3, 0);
    break;
  case FILTER_BLUE:
    gpio_put(PIN_S2, 0);
    gpio_put(PIN_S3, 1);
    break;
  case FILTER_CLEAR:
    gpio_put(PIN_S2, 1);
    gpio_put(PIN_S3, 0);
    break;
  case FILTER_GREEN:
    gpio_put(PIN_S2, 1);
    gpio_put(PIN_S3, 1);
    break;
  }
}

static float tcs_measure_freq_hz(uint32_t window_ms)
{
  g_pulse_count = 0;
  sleep_ms(window_ms);
  float seconds = (float)window_ms / 1000.0f;
  return (seconds > 0.0f) ? ((float)g_pulse_count / seconds) : 0.0f;
}

static inline float clamp01(float x)
{
  if (x < 0.0f)
    return 0.0f;
  if (x > 1.0f)
    return 1.0f;
  return x;
}

static inline float max3(float a, float b, float c)
{
  float m = a;
  if (b > m)
    m = b;
  if (c > m)
    m = c;
  return m;
}

static inline float min3(float a, float b, float c)
{
  float m = a;
  if (b < m)
    m = b;
  if (c < m)
    m = c;
  return m;
}

static const char *classify_color(float clear_hz, float r_hz, float g_hz, float b_hz)
{
  if (clear_hz < 50.0f)
    return "BLACK";

  float r = r_hz / clear_hz;
  float g = g_hz / clear_hz;
  float b = b_hz / clear_hz;

  r = clamp01(r);
  g = clamp01(g);
  b = clamp01(b);

  float mx = max3(r, g, b);
  float mn = min3(r, g, b);
  float sat = mx - mn;
  float avg = (r + g + b) / 3.0f;

  if (sat < 0.10f)
  {
    if (clear_hz < 120.0f)
      return "BLACK";
    if (clear_hz > 900.0f && avg > 0.30f)
      return "WHITE";
    return "GRAY";
  }

  if (clear_hz < 700.0f && r > 0.28f && g > 0.16f && b < 0.12f && r > g && (r - b) > 0.18f)
  {
    return "BROWN";
  }

  if (r > 0.32f && r > g + 0.10f && r > b + 0.10f)
  {
    if (g > 0.22f && b < 0.14f)
      return "ORANGE";
    return "RED";
  }

  if (g > 0.30f && g > r + 0.08f && g > b + 0.08f)
    return "GREEN";
  if (b > 0.26f && b > r + 0.08f && b > g + 0.08f)
    return "BLUE";

  if (r > 0.26f && g > 0.24f && b < 0.14f)
    return "YELLOW";
  if (r > 0.22f && b > 0.22f && g < 0.18f)
    return "PURPLE";

  return "UNKNOWN";
}

int main(void)
{
  stdio_init_all();
  sleep_ms(2000);

  gpio_init(PIN_S0);
  gpio_set_dir(PIN_S0, GPIO_OUT);
  gpio_init(PIN_S1);
  gpio_set_dir(PIN_S1, GPIO_OUT);
  gpio_init(PIN_S2);
  gpio_set_dir(PIN_S2, GPIO_OUT);
  gpio_init(PIN_S3);
  gpio_set_dir(PIN_S3, GPIO_OUT);

  gpio_init(PIN_OUT);
  gpio_set_dir(PIN_OUT, GPIO_IN);

  tcs_set_scaling_20_percent();

  gpio_set_irq_enabled_with_callback(PIN_OUT, GPIO_IRQ_EDGE_RISE, true, &out_irq_callback);

  const uint32_t settle_ms = 30;
  const uint32_t window_ms = 100;

  printf("TCS3200 started. Measuring...\n");

  while (true)
  {
    tcs_set_filter(FILTER_CLEAR);
    sleep_ms(settle_ms);
    float c = tcs_measure_freq_hz(window_ms);

    tcs_set_filter(FILTER_RED);
    sleep_ms(settle_ms);
    float r = tcs_measure_freq_hz(window_ms);

    tcs_set_filter(FILTER_GREEN);
    sleep_ms(settle_ms);
    float g = tcs_measure_freq_hz(window_ms);

    tcs_set_filter(FILTER_BLUE);
    sleep_ms(settle_ms);
    float b = tcs_measure_freq_hz(window_ms);

    const char *name = classify_color(c, r, g, b);

    float rn = (c > 0.0f) ? (r / c) : 0.0f;
    float gn = (c > 0.0f) ? (g / c) : 0.0f;
    float bn = (c > 0.0f) ? (b / c) : 0.0f;

    printf("%-7s | C:%.0fHz R:%.0fHz G:%.0fHz B:%.0fHz | rn:%.2f gn:%.2f bn:%.2f\n",
           name, c, r, g, b, rn, gn, bn);

    sleep_ms(200);
  }
}