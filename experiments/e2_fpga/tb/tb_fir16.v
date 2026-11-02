// ============================================================================
// E2 - Testbench tu kiem tra FIR16 voi golden model E0.
//   Luot 1: bom 1024 mau lien tuc (in_valid = 1 moi chu ky) -> do do tre, thong luong
//   Luot 2: cung vector, chen khoang trong ngau nhien vao in_valid -> kiem tra dieu khien
// So sanh TUNG mau, in PASS/FAIL va ghi ket qua JSON.
// ============================================================================
`timescale 1ns / 1ps

module tb_fir16;
    localparam integer NS   = 1024;
    localparam real    TCLK = 8.0;    // 125 MHz (8 ns) tren Arty Z7-20; RTL sim khong co tre cong

    reg clk = 0, rst = 1, in_valid = 0;
    reg signed [15:0] in_data = 0;
    wire out_valid;
    wire signed [15:0] out_data;

    fir16 dut (.clk(clk), .rst(rst), .in_valid(in_valid), .in_data(in_data),
               .out_valid(out_valid), .out_data(out_data));

    always #(TCLK/2) clk = ~clk;

    reg [15:0] vin  [0:NS-1];
    reg [15:0] gold [0:NS-1];

    integer pass_no, n_out, n_bad, first_bad, cycle, t_first_in, t_first_out, t_last_out;
    integer errs_total, seed, i, fd;
    integer lat [1:2], cyc [1:2], bad [1:2];

    initial begin
        $readmemh("vectors_in.hex", vin);
        $readmemh("golden_out.hex", gold);
        if (^vin[NS-1] === 1'bx || ^gold[NS-1] === 1'bx) begin
            $display("LOI: khong doc duoc file hex (chay tu thu muc chua vectors_in.hex)");
            $finish;
        end
        if ($test$plusargs("vcd")) begin
            $dumpfile("fir16.vcd");
            $dumpvars(0, tb_fir16);
        end
        seed = 3053;
        errs_total = 0;
        for (pass_no = 1; pass_no <= 2; pass_no = pass_no + 1) begin
            run_pass(pass_no == 2);
            lat[pass_no] = t_first_out - t_first_in;
            cyc[pass_no] = t_last_out - t_first_in + 1;
            bad[pass_no] = n_bad;
            errs_total = errs_total + n_bad;
            $display("Luot %0d (%s): %0d/%0d mau ra, sai %0d, do tre %0d chu ky, %0d chu ky tu mau vao dau den mau ra cuoi",
                     pass_no, pass_no == 1 ? "lien tuc" : "co khoang trong", n_out, NS, n_bad,
                     lat[pass_no], cyc[pass_no]);
        end

        $display("==> %s", errs_total == 0 ? "PASS: khop golden 100%" : "FAIL");
        $display("    Thong luong luot 1: %0d mau / %0d chu ky = %0.4f mau/chu ky",
                 NS, cyc[1] - lat[1], NS * 1.0 / (cyc[1] - lat[1]));

        fd = $fopen("e2_fpga_sim.json", "w");
        $fwrite(fd, "{\n  \"label\": \"mo phong\",\n  \"experiment\": \"E2_fpga_rtl_sim\",\n");
        $fwrite(fd, "  \"simulator\": \"icarus verilog\",\n  \"num_samples\": %0d,\n", NS);
        $fwrite(fd, "  \"pass\": %s,\n", errs_total == 0 ? "true" : "false");
        $fwrite(fd, "  \"continuous\": {\"mismatches\": %0d, \"latency_cycles\": %0d, \"cycles_first_in_to_last_out\": %0d},\n",
                bad[1], lat[1], cyc[1]);
        $fwrite(fd, "  \"with_gaps\":  {\"mismatches\": %0d, \"latency_cycles\": %0d, \"cycles_first_in_to_last_out\": %0d},\n",
                bad[2], lat[2], cyc[2]);
        $fwrite(fd, "  \"samples_per_cycle\": %0.4f\n}\n", NS * 1.0 / (cyc[1] - lat[1]));
        $fclose(fd);
        $finish;
    end

    // Dem chu ky va kiem tra ngo ra
    always @(posedge clk) begin
        cycle <= cycle + 1;
        if (!rst && out_valid) begin
            if (n_out == 0) t_first_out = cycle;
            t_last_out = cycle;
            if (out_data !== $signed(gold[n_out])) begin
                if (n_bad < 5)
                    $display("  SAI mau %0d: ra %0d, mong doi %0d", n_out, out_data, $signed(gold[n_out]));
                n_bad = n_bad + 1;
            end
            n_out = n_out + 1;
        end
    end

    task run_pass(input gaps);
        integer k;
        begin
            // Reset de duong tre ve 0, giong golden
            @(negedge clk); rst = 1; in_valid = 0;
            repeat (3) @(negedge clk);
            rst = 0;
            cycle = 0; n_out = 0; n_bad = 0;
            k = 0;
            while (k < NS) begin
                @(negedge clk);
                if (gaps && ($random(seed) & 3) == 0) begin
                    in_valid = 0;
                    in_data  = 16'h7fff;   // rac: khong duoc lot vao ket qua
                end else begin
                    if (k == 0) t_first_in = cycle;
                    in_valid = 1;
                    in_data  = vin[k];
                    k = k + 1;
                end
            end
            @(negedge clk); in_valid = 0; in_data = 0;
            wait (n_out == NS);
            repeat (2) @(negedge clk);
        end
    endtask
endmodule
