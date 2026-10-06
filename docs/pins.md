# FPGA balls used

Verified on a Sno M2 (`10M16SAU169C8G`) on the SparkFun MicroMod Input & Display carrier. For
anything else, use Alorium's Sno M2 pin map (`AloriumTech_SnoM2_PinMap.pdf`) and check each ball.

| Signal | Ball | Notes |
|---|---|---|
| 16 MHz board clock | `H6` | `3.3-V LVTTL` |
| Reset button | `B9` | `3.3 V Schmitt Trigger`; works as a plain input |
| On-board LED | `K10` | |
| Carrier display CS / DC / RST / BL | `M12` / `N7` / `E8` / `L3` | backlight is active low |
| Carrier SPI SCK / MOSI (SPI_SDO) / MISO (SPI_SDI) | `A2` / `A7` / `A8` | |
| Carrier SD card CS | `A4` | |
| Carrier I2C SDA / SCL | `M11` / `M10` | the carrier's button controller is at address 0x71 |

Alorium's own Quartus settings for the Sno M2 (in their open-source XLR8Core repository) have
Arduino pins D11 and D12 swapped relative to the pin-map PDF, and different Alorium images wire the
two differently. If you work with FPGA balls directly, this doesn't matter.

Useful settings in the project `.qsf`:

```
set_global_assignment -name DEVICE 10M16SAU169C8G
set_global_assignment -name STRATIX_DEVICE_IO_STANDARD "3.3-V LVTTL"
set_global_assignment -name VCCA_USER_VOLTAGE 3.3V
set_global_assignment -name RESERVE_ALL_UNUSED_PINS "AS INPUT TRI-STATED"
set_global_assignment -name CRC_ERROR_OPEN_DRAIN OFF
set_global_assignment -name ENABLE_OCT_DONE OFF
```
