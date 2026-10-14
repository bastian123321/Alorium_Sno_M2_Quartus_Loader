// factory_escape: hold `hold` high for HOLD_MS milliseconds and the FPGA reloads its FACTORY image
// (image 0). Alorium's factory image contains the soft AVR + serial bootloader that the
// xlr8reconfig loader talks to, so this is how a design hands the board back to the loader.
//
// EVERY design you load into the application slot must contain this (or an equivalent), otherwise
// the only way back to the loader is a USB-Blaster.
//
// Needs Intel's alt_dual_boot.v in the project (scripts/copy_dual_boot.py copies it from your
// Quartus install) and  INTERNAL_FLASH_UPDATE_MODE "Dual Images"  in the .qsf.
module factory_escape #(
    parameter CLK_HZ  = 16_000_000,   // frequency of clk
    parameter HOLD_MS = 5000          // how long `hold` must stay high (max 8191)
) (
    input wire clk,
    input wire hold                   // active high; wire a button (or a button combination) here
);

  localparam CLKS_PER_MS = CLK_HZ / 1000;

  reg  [31:0] ms_div = 32'd0;
  wire        ms_tick = (ms_div == CLKS_PER_MS - 1);
  always @(posedge clk) ms_div <= ms_tick ? 32'd0 : ms_div + 32'd1;

  reg  [12:0] held = 13'd0;
  reg  [2:0]  st   = 3'd0;
  reg         wr   = 1'b0;
  reg         rc   = 1'b0;
  wire        busy;

  always @(posedge clk) begin
    if (hold) begin
      if (ms_tick && held != 13'h1FFF) held <= held + 13'd1;
    end else
      held <= 13'd0;

    case (st)
      3'd0: if (held >= HOLD_MS) begin wr <= 1'b1; st <= 3'd1; end   // select image 0, override pins
      3'd1: if (busy)  begin wr <= 1'b0; st <= 3'd2; end
      3'd2: if (!busy) begin rc <= 1'b1; st <= 3'd3; end             // trigger the reconfiguration
      3'd3: rc <= 1'b0;
      default: ;
    endcase
  end

  alt_dual_boot dual_boot (
      .clk(clk), .nreset(1'b1), .rconfig(rc), .rst_timer(1'b0),
      .read_watchdog(1'b0), .msm_cs(), .watchdog_en(), .watchdog_timer(),
      .read_app_reconfig1(1'b0), .app_reconfig_source1(), .app_msm_cs1(),
      .read_app_reconfig2(1'b0), .app_reconfig_source2(), .app_msm_cs2(),
      .read_inreg(1'b0), .rd_boot_sel_overwrite(), .rd_boot_sel(),
      .write_inreg(wr), .boot_sel(1'b0), .boot_sel_overwrite(1'b1), .busy(busy)
  );

endmodule
