# Load your own Quartus design into an Alorium Sno M2 over USB (no USB-Blaster)

The Alorium Sno M2 (MAX 10 `10M16SAU169C8G`) normally runs Alorium's Arduino-compatible AVR core,
and you load a custom FPGA design with a USB-Blaster. This repo shows how to build a Quartus design
that Alorium's own serial loader (`xlr8reconfig`, the tool behind the Arduino IDE's *Burn
Bootloader*) will write into the board's flash over the normal USB cable, and how to get back to
the loader afterwards, so the blaster is only needed for recovery.

> **Status.** Everything below was worked out on one setup and proven there with a large design
> (a Game Boy core with display and SD loader): Sno M2 on the SparkFun MicroMod Input & Display
> carrier, Windows 11, Quartus Prime Lite 25.1, Arduino IDE 2.3.10, Alorium XLR8 boards package
> 2.3.2. The small example in `example/` compiles and passes the file checks here, but has not been
> run on hardware by the author yet. Other boards (Sno, Sno Edge, XLR8) are untested; see
> [Limitations](#limitations-and-things-not-verified).
> This is not affiliated with or endorsed by Alorium Technology or Intel. No Alorium or Intel files
> are included.

## How it works in one minute

* The MAX 10 keeps **two images** in its internal flash. **Image 0 (factory)** is Alorium's design with
  the soft AVR and its serial bootloader. **Image 1 (application)** is the slot Alorium's *Burn
  Bootloader* writes, and it's the one that boots at power-up.
* `xlr8reconfig` talks to the soft AVR through the board's FTDI USB-serial chip, and it rewrites
  **only image 1**: 2,112 pages of 128 bytes = **270,336 bytes**, verified page by page, then it
  tells the chip to reload.
* So your design must (1) be compiled in a flash mode and format that fits that slot, and (2)
  contain a way to **hand the board back to image 0**, because your design has no soft AVR and
  can't answer the loader. This repo provides that as a small Verilog module (`factory_escape`):
  hold a button for 1.5 s and the FPGA reloads the factory image.

Details: [docs/how-it-works.md](docs/how-it-works.md).

## What you need

* Sno M2 board, on USB power.
* **Arduino IDE** with the *Alorium XLR8 Family* boards package installed (it provides
  `xlr8reconfig.exe` and Alorium's own images). Boards Manager URL:
  `https://raw.githubusercontent.com/AloriumTechnology/Arduino_Boards/master/package_aloriumtech_index.json`
* **Quartus Prime Lite** with MAX 10 device support.
* **Python 3** (for `make_rpd.py`).
* A **USB-Blaster** is still useful for first experiments and as a last-resort recovery.

## One-time setup

1. Clone this repo.
2. Copy Intel's dual-boot wrapper from your Quartus install (it's Intel IP, so it's not stored
   here):
   ```
   python scripts/copy_dual_boot.py
   ```
   (If it can't find Quartus, pass your install root, e.g. `C:\altera_lite\25.1std`.)
3. **Back up Alorium's images** so you can always restore them: copy
   `%LOCALAPPDATA%\Arduino15\packages\alorium\hardware\avr\<version>\fpga_images` somewhere safe.

## Rules for a design the loader can use

1. **Device** `10M16SAU169C8G`.
2. **Flash mode: "Dual Images".** In the `.qsf`:
   ```
   set_global_assignment -name INTERNAL_FLASH_UPDATE_MODE "Dual Images"
   set_global_assignment -name USE_CONFIGURATION_DEVICE OFF
   ```
   (In the GUI: Assignments → Device → Device and Pin Options → Configuration → Configuration
   mode: *Dual Compressed Images*.) A design built in another mode produces a different file
   header and is not what the loader expects.
3. **No memory initialisation files.** Dual-image mode rejects any ROM or RAM with initial contents
   (Quartus error 16031: "does not support memory initialization or ROM"). Put constant tables in
   Verilog (`case` statements, functions) or fill RAMs at run time. The cost is logic cells instead
   of block RAM.
4. **Include the escape hatch.** Add `verilog/factory_escape.v` and `third_party/alt_dual_boot.v` to
   the project and connect `hold` to a button:
   ```verilog
   factory_escape #(.CLK_HZ(16_000_000), .HOLD_MS(1500)) escape (.clk(Clock), .hold(~RESET_N));
   ```
   Dual-image mode also *requires* a remote-update block in the design (Quartus error 169130
   otherwise), which `alt_dual_boot` provides. **Every design you load must contain this.** If a
   design doesn't, the loader can no longer reach the board and only the USB-Blaster can recover it.
5. **Pins and clock.** The board clock is 16 MHz on ball `H6`. See [docs/pins.md](docs/pins.md).
6. **Size.** The compiled, compressed design must fit in 270,336 bytes (the slot).
   `make_rpd.py` prints how full it is: a trivial blink design already takes about 94 KB, and the
   Game Boy design (45% of the logic) takes 148 KB. Quartus/`quartus_cpf` fails or the check
   reports a wrong size if it doesn't fit.

## Build and load

1. **Compile** in Quartus (or `quartus_sh --flow compile <project>`). Check for 0 errors and
   positive timing slack.
2. **Make the loader file:**
   ```
   python scripts/make_rpd.py path\to\output_files\design.sof -o design.rpd
   ```
   It must end with `check : OK` (size 270,336 bytes and the expected header).
3. **Get the board to answer the loader.** If the board is running Alorium's image, it already
   does. If it is running your design, hold the escape button for 1.5 s: the display/LED stops, and
   the board is now in the factory image. Close the Arduino Serial Monitor (it holds the COM port).
4. **Flash:**
   ```
   scripts\flash.bat COM3 design.rpd
   ```
   You should see `Programmed CFM page 2111` and `Complete`, then `Loading image 1 and resetting
   xlr8`. An `ERROR: Was not able to handshake` right after that is normal: the loader tries to read
   Alorium's version report from your design, which isn't Alorium's.
5. Your design now runs, **and stays in flash across power cycles**.

## Going back to Alorium's Arduino image

Hold the escape button, then:
```
scripts\restore_alorium.bat COM3          (16 MHz r3317, the default)
scripts\restore_alorium.bat COM3 32       (32 MHz r3317)
scripts\restore_alorium.bat COM3 64       (64 MHz r3317)
scripts\restore_alorium.bat COM3 r3195    (older 16 MHz image)
```
It prints the version report at the end. Afterwards pick the matching **FPGA Image** entry in the
Arduino IDE.

While in the **factory image** (right after the escape hold, until the next reset or power cycle)
you can also upload ordinary Arduino sketches. It is an older design (r3000) with a 64 MHz clock and
none of the extra blocks (floating point, NeoPixel, Servo, Quad), so see
[docs/troubleshooting.md](docs/troubleshooting.md) for the 64 MHz menu entry and pin differences.

## Try the example

`example/` is the smallest design that follows every rule: it blinks the on-board LED (ball `K10`)
and returns to the factory image when you hold the board's reset button (`RESET_N`, ball `B9`)
for 1.5 s.

```
python scripts/copy_dual_boot.py
cd example
quartus_sh --flow compile blink
cd ..
python scripts/make_rpd.py example/output_files/blink.sof -o example/blink.rpd
scripts\flash.bat COM3 example\blink.rpd
```

## Limitations and things not verified

* Proven only on a **Sno M2 (10M16)**. The loader's source suggests other flash sizes (1,120 pages
  for MAX 10 M08, 5,376 for M50, so a different file size and addresses), so the `270336` check and
  the header in `make_rpd.py` are M16-specific. Untested.
* **Windows only** as written. The loader also exists for macOS and Linux; the scripts have not
  been ported.
* The factory image's contents are inferred from its behaviour (it answers the loader and runs
  Arduino sketches). Nothing here modifies it.
* Behaviour was observed, not documented by Alorium: the layout of the flash slots, which image
  boots at power-up (image 1 did), and that image 0 is the factory image reached by the dual-boot
  block with `boot_sel = 0`.
* `example/` and `factory_escape` at **16 MHz**: the module itself was proven at 64 MHz in the
  Game Boy design; the 16 MHz parameters are a straightforward use of it but not yet hardware
  tested.

## Recovery

The loader only erases and writes image 1; image 0 is never touched. If a design misbehaves and
the escape doesn't work, load a known-good `.sof` with a USB-Blaster (volatile), use its escape
hold, then restore from the loader. Keep a known-good `.sof` and `.rpd` of your last working build.

## Licence

MIT (see `LICENSE`) for the scripts, Verilog and docs in this repo. `alt_dual_boot.v` is Intel IP and is
copied from your own Quartus install by `scripts/copy_dual_boot.py`; Alorium's tool and images stay in
your Arduino package.
