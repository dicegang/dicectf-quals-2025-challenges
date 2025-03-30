module basic(
  inp,
  inp2,
  res
);

input wire inp;
input wire inp2;
output wire res;

assign res = !(inp & inp2);

endmodule
