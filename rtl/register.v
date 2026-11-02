module register8 (
    input wire clk,
    input wire reset_n,
    input wire write_en,
    input wire [7:0] data,
    output reg [7:0] q
);
    always @(posedge clk)
        if (!reset_n) q <= 8'b0;
        else if (write_en) q <= data;
endmodule
