// Smallest design that follows all the rules: blinks the on-board LED and returns to the factory
// image when the board's reset button is held for 5 s.
module blink_top (
    input  wire Clock,     // 16 MHz board clock
    input  wire RESET_N,   // reset button, active low
    output wire LED
);

  reg [23:0] cnt = 24'd0;
  always @(posedge Clock) cnt <= cnt + 24'd1;
  assign LED = cnt[23];                                  // about 1 Hz

  factory_escape #(.CLK_HZ(16_000_000), .HOLD_MS(5000)) escape (
      .clk(Clock), .hold(~RESET_N)
  );

endmodule
