`timescale 1ns/1ps
module tb;
reg clk=0, reset_n=0, write_en=0;
reg [7:0] data=0;
wire [7:0] q;
integer pattern,i,checks=0;
`ifdef SCAN
reg scan_en=0,si=0;
wire so;
register8 dut(.clk(clk),.reset_n(reset_n),.write_en(write_en),.data(data),.q(q),
              .scan_enable(scan_en),.scan_in(si));
`include "chain.vh"
assign so=q[SCAN_TAIL_BIT];
`else
register8 dut(.clk(clk),.reset_n(reset_n),.write_en(write_en),.data(data),.q(q));
`endif
task tick;
begin
    clk=0; #5; clk=1; #5; clk=0; #5;
end
endtask
task check_q;
input [7:0] expected;
begin
    checks=checks+1;
    if(q !== expected) $fatal(1,"Q_MISMATCH pattern=%0d got=%h expected=%h",pattern,q,expected);
end
endtask
initial begin
    tick; check_q(0); reset_n=1;
    for(pattern=0;pattern<256;pattern=pattern+1) begin
        data=pattern; write_en=1; tick; check_q(pattern);
        write_en=0; data=~pattern; tick; check_q(pattern);
`ifdef SCAN
        // Shift out the functionally captured byte, checking before each edge.
        scan_en=1; si=0; #1;
        for(i=0;i<8;i=i+1) begin
            checks=checks+1;
            if(so !== scan_bit(pattern,i)) $fatal(1,"SCAN_MISMATCH pattern=%0d index=%0d got=%b expected=%b",pattern,i,so,scan_bit(pattern,i));
            tick;
        end
        check_q(0);
        // Inject the target byte in the chain order reconstructed from gates.
        for(i=0;i<8;i=i+1) begin si=scan_bit(pattern,i); tick; end
        check_q(pattern);
        // Return to functional mode and capture the complement.
        scan_en=0; write_en=1; data=~pattern; tick; check_q(~pattern);
        write_en=0;
`endif
    end
    reset_n=0; tick; check_q(0);
`ifdef SCAN
    $display("DFT_SCAN_CAPTURE_PASS patterns=256 checks=%0d",checks);
`else
    $display("DFT_BASELINE_PASS patterns=256 checks=%0d",checks);
`endif
    $finish;
end
initial begin #200000; $fatal(1,"TEST_TIMEOUT"); end
endmodule
