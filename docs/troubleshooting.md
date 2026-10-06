# Troubleshooting

Each entry is something that actually happened while setting this up.

## Loader (`flash.bat` / `restore_alorium.bat`)

| What you see | Cause and fix |
|---|---|
| `ERROR: Was not able to handshake. ... Received 0. Handshake #1 of 3` as the **first** thing | The board isn't running something that answers the loader. If your design is running, hold the escape button until the screen/LED freezes, then run the script again. |
| `Programmed CFM page 2111`, `Complete`, `Loading image 1 ...`, **then** the handshake error | Normal. Your design doesn't answer Alorium's version query. |
| Python traceback ending in `...3.0.0GetXLR8Version.ino.hex` not found | `--dir_path` needs a trailing slash. The scripts in this repo pass `"%TOOL%/"`. |
| `avrdude: ser_open(): can't open device "\\.\COM3": Access is denied` | Another program has the port open, usually the Arduino IDE's **Serial Monitor**. Close it (and any terminal programs). |
| Arduino IDE's Burn Bootloader says **Missing programmer** | The IDE wants a programmer selected and the Alorium package has none. Use `restore_alorium.bat` / `flash.bat` instead. |
| Script exits at once saying `xlr8reconfig not found` | Install the *Alorium XLR8 Family* boards package in the Arduino IDE. |

## Quartus

| What you see | Cause and fix |
|---|---|
| `Error (16031): Current Internal Configuration mode does not support memory initialization or ROM` | A ROM or RAM has an init file (`.mif`, `$readmemh`, `init_file`). Replace it with logic (a `case` table) or fill it at run time. |
| `Error (169130): Configuration mode specified as Remote but remote update block is not found` | The design needs an instance of `alt_dual_boot` (use `factory_escape`). |
| `INTERNAL_FLASH_UPDATE_MODE "DUAL IMAGE"` is illegal | The legal value is `"Dual Images"` (also `"Single Comp Image"`, `"Single Image with ERAM"`, `"Single Comp Image with ERAM"`). |
| `quartus_cpf`: "must have 2 page(s) of data" | Dual-image mode needs two pages; `make_rpd.py` does this for you. |
| `make_rpd.py` says `check : FAILED`, byte 12 is `3b` | The design was compiled in a single-image mode. Set `"Dual Images"`, recompile. |
| `Can't fit design in device` after adding things | The 10M16 has 61 M9K RAM blocks (the Game Boy design needed all of them); check the fitter report. |

## Arduino sketches on the board

* **Right after the escape hold, the board runs the factory image** (r3000, 64 MHz). It stays there
  until the next reset or power cycle, when it boots your design again.
* The IDE's **FPGA Image** menu for *Sno M2* lists 16 and 32 MHz only. For the factory image
  add a 64 MHz entry to `boards.txt` in
  `%LOCALAPPDATA%\Arduino15\packages\alorium\hardware\avr\<version>\` after the 32 MHz lines:
  ```
  snom2.menu.fpga.snom2_c64_oDefault_u16_x0F_svn3317=64MHz Standard (Float, NeoPixel, Servo, Quad) r3317
  snom2.menu.fpga.snom2_c64_oDefault_u16_x0F_svn3317.bootloader.rpdfile=snom2_c64_oDefault_u16__x0F_p0_q6_n15_s12_f1__svn3317.rpd
  snom2.menu.fpga.snom2_c64_oDefault_u16_x0F_svn3317.build.f_cpu=64000000L
  ```
  **Fully quit and restart the IDE** to see it. A `boards.local.txt` was not enough in our test.
  A Boards Manager update would overwrite the file. Use the entry only for compiling; use the
  restore script to change the image.
* Blink running too fast in the factory image means you compiled for 16 MHz. Choose the 64 MHz entry.
* In the factory image the display and SD data pins are the other way round from the newer
  r3317 image (MOSI on D12 and MISO on D11, versus D11 and D12). Bit-banged SD at 64 MHz needs extra
  delay on each clock edge, or the card never answers (`CMD0:FF`).
* `COM3` still appears with your own design loaded: that's the board's FTDI chip, which is powered
  whatever the FPGA runs.
