# How the loader works

Everything here was worked out by reading the files Alorium ships in its Arduino package, running
Quartus' converter, and testing on a Sno M2. Where something is an inference rather than an
observation, it says so.

## The two images and the flash map

A MAX 10 loads its configuration from internal flash into SRAM at power-up. With
"Dual Compressed Images" the flash holds two images. Quartus' memory map for a two-page
programming file on the 10M16 shows:

| Area | Byte range | Size |
|---|---|---|
| ICB (settings) | 0x000000 to 0x000FFF | 4 KB |
| UFM (user flash) | 0x001000 to 0x008FFF | 32 KB |
| CFM1 (application image, with CFM2) | 0x009000 to 0x04AFFF | 0x42000 = 270,336 bytes |
| CFM0 (factory image) | 0x04B000 to 0x08CFFF | 0x42000 = 270,336 bytes |

Alorium's loader calls image 1 `{cfm2,cfm1}` (the application image) and image 0 `cfm0` (the factory
image). At power-up the chip boots image 1. **Inference:** the factory image (Alorium's r3000, 64 MHz,
no extra blocks) is the fallback.

## What `xlr8reconfig` does

From the strings and structure of the tool:

1. Resets the soft AVR with the serial port's DTR/RTS lines and does an Optiboot-style handshake
   (`0x30 0x20` answered by `0x14 0x10`).
2. Loads a small AVR program (its "reconfiguration code") into the soft AVR's program memory through
   the bootloader. It describes this code as containing "the handshaking required to program the
   CFM".
3. Using that code, enters a programming mode, reads a signature, erases the image-1 area, then
   writes the file page by page (2,112 pages of 128 bytes) and reads each page back to verify. It
   adjusts the bit and byte order within each 4-byte word while reading the file.
4. Sends "load image 1" (`--load_image 1`): the chip reloads from image 1.
5. Runs a version query against whatever is now running. Only an Alorium image answers it, so a
   custom design makes this last step fail with "Was not able to handshake". That's expected.

`--load_image 0` asks for the factory image instead.

The image must be loaded while an image with the soft AVR (Alorium's or the factory one) is
running, because that's what executes the programming code. That's why your own design needs a way
back to image 0.

## The `.rpd` format

* The file is exactly the size of one slot (270,336 bytes on a 10M16). The compressed design is at
  the start and the rest is `0xFF` padding.
* It starts with a fixed header. For this device: `50 ff 47 ff 4d ff 49 d2 43 ff 42 fb ff 1c 6f 00`.
  The loader's file reader checks the start of the data ("Unexpected header ... Expected P").
  Alorium's own images and ours produced by this repo have the same first 16 bytes. A design
  compiled in single-image mode has `3b` instead of `fb` at byte 12, which is how `make_rpd.py` spots
  the wrong mode.
* Quartus' converter writes several files from a dual-image `.pof`; the loader wants
  `*_cfm1_auto.rpd`. With both pages pointing to the same `.sof`, `cfm0` and `cfm1` are identical
  here. The converter insists on two pages in dual-image mode ("must have 2 page(s) of data").
* Alorium's recipe also gives the converter a bootloader hex for the UFM. The `cfm1` output does not
  change without it (checked byte for byte), and the loader never writes the UFM, so this repo omits it.

## Why the design needs these changes

* **"Dual Images" flash mode** produces the compressed single-slot bitstream format Alorium's loader
  expects. It *requires* a remote-update block in the design (error 169130: "Configuration mode
  specified as Remote but remote update block is not found in design").
* **No memory initialisation:** in this mode Quartus rejects a ROM or RAM with initial contents
  (error 16031). Constant tables go in logic.
* **`alt_dual_boot`** is Intel's wrapper around the `fiftyfivenm_rublock` primitive. Writing its
  boot-select register (`boot_sel = 0`, `boot_sel_overwrite = 1`) and then pulsing `rconfig` makes
  the chip reload image 0. `factory_escape.v` does exactly this after a button has been held.

## Related facts that matter when writing sketches

* The board's FTDI chip is a plain USB-to-UART bridge connected to the soft AVR's serial port. It
  is not a JTAG programmer. Its COM port appears whenever the board has USB power, whatever the FPGA
  is running.
* Different Alorium images wire the same Arduino pin names to different FPGA balls (observed with
  the SPI data pins D11 and D12). Designs that use FPGA balls directly are not affected.
