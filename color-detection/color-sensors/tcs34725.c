#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

#define I2C_PORT i2c0
#define SDA_PIN 4
#define SCL_PIN 5

#define TCS_ADDR 0x29
#define CMD_BIT 0x80

#define REG_ENABLE 0x00
#define REG_ATIME 0x01
#define REG_CONTROL 0x0F
#define REG_ID 0x12
#define REG_CDATAL 0x14

#define PON 0x01
#define AEN 0x02

static inline int tcs_write8(uint8_t reg, uint8_t val)
{
  uint8_t buf[2] = {(uint8_t)(CMD_BIT | reg), val};
  return i2c_write_blocking(I2C_PORT, TCS_ADDR, buf, 2, false);
}

static inline int tcs_read(uint8_t start_reg, uint8_t *buf, size_t n)
{
  uint8_t r = (uint8_t)(CMD_BIT | start_reg);

  int ok = i2c_write_blocking(I2C_PORT, TCS_ADDR, &r, 1, true);
  if (ok < 0)
    return ok;

  return i2c_read_blocking(I2C_PORT, TCS_ADDR, buf, n, false);
}

static bool tcs_init(void)
{
  uint8_t id = 0;
  if (tcs_read(REG_ID, &id, 1) < 0)
    return false;

  printf("TCS ID: 0x%02X\n", id);

  if (tcs_write8(REG_ENABLE, PON) < 0)
    return false;
  sleep_ms(3);

  if (tcs_write8(REG_ATIME, 0xEB) < 0)
    return false;
  if (tcs_write8(REG_CONTROL, 0x01) < 0)
    return false;

  if (tcs_write8(REG_ENABLE, PON | AEN) < 0)
    return false;

  return true;
}

int main(void)
{
  stdio_init_all();
  sleep_ms(1500);

  i2c_init(I2C_PORT, 100 * 1000);
  gpio_set_function(SDA_PIN, GPIO_FUNC_I2C);
  gpio_set_function(SCL_PIN, GPIO_FUNC_I2C);
  gpio_pull_up(SDA_PIN);
  gpio_pull_up(SCL_PIN);

  if (!tcs_init())
  {
    printf("init failed. check wiring/address.\n");
    while (true)
      sleep_ms(1000);
  }

  while (true)
  {
    uint8_t raw[8];

    if (tcs_read(REG_CDATAL, raw, 8) < 0)
    {
      printf("read fail\n");
      sleep_ms(250);
      continue;
    }

    uint16_t c = raw[0] | (raw[1] << 8);
    uint16_t r = raw[2] | (raw[3] << 8);
    uint16_t g = raw[4] | (raw[5] << 8);
    uint16_t b = raw[6] | (raw[7] << 8);

    printf("C:%u R:%u G:%u B:%u\n", c, r, g, b);

    sleep_ms(250);
  }
}