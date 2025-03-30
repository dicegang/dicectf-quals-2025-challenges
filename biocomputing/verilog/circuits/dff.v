module dff(
  clk,
  rst,
  out,
  out2
);

input wire clk;
input wire rst;
output reg [7:0] out;
output reg [7:0] out2;
always @(posedge clk) begin
  if (rst) begin
    out <= 1;
    out2 <= 1;
  end else begin
    out <= out2;
    out2 <= out + out2;
  end
end

endmodule
