// Kiem tra top_arty (Arty Z7-20 @ 125 MHz) truoc khi nap board:
// giai ma UART, chay 2 lan (tu chay sau POR/reset + nhan BTN0).
`timescale 1ns / 1ps

module tb_top_arty;
    localparam integer CPB = 8;   // UART nhanh cho mo phong
    reg clk = 0, btn1_rst = 1, btn0 = 0;
    wire [3:0] led;
    wire tx;

    top_arty #(.CLKS_PER_BIT(CPB)) dut (
        .CLK125MHZ(clk), .btn1_rst(btn1_rst), .btn0(btn0),
        .led(led), .uart_rxd_out(tx)
    );
    always #4 clk = ~clk;   // 125 MHz (chu ky 8 ns)

    reg [8*80-1:0] line;
    integer nch, nlines, b;
    reg [7:0] c;

    // Bo thu UART: lay mau giua moi bit (moi chu ky clk = 8 ns)
    initial begin
        nch = 0; nlines = 0; line = 0;
        forever begin
            @(negedge tx);
            #(CPB * 8 / 2);
            for (b = 0; b < 8; b = b + 1) begin
                #(CPB * 8);
                c[b] = tx;
            end
            #(CPB * 8);
            if (c == 8'h0A) begin
                nlines = nlines + 1;
                $display("UART dong %0d: %0s", nlines, line);
                line = 0;
            end else if (c != 8'h0D) begin
                line = {line[8*79-1:0], c};
            end
        end
    end

    initial begin
        repeat (5) @(posedge clk);
        btn1_rst = 0;   // nha nut reset (POR se tu dem xong 255 chu ky va chay)
        wait (nlines == 1);
        $display("LED = %b (LD3..LD0)", led);
        #80 btn0 = 1; #80 btn0 = 0;
        wait (nlines == 2);
        $finish;
    end

    initial begin
        #5_000_000;
        $display("TIMEOUT");
        $finish;
    end
endmodule
