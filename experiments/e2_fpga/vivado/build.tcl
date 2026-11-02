# ============================================================================
# E2b - Vivado non-project flow cho Digilent Arty Z7-20 (xc7z020clg400-1)
#       CHE DO THUAN LOGIC (LUT-ONLY, KHONG DUNG DSP48E1: -max_dsp 0)
#   cd experiments/e2_fpga && vivado -mode batch -source vivado/build.tcl
#
# Chay 2 phan:
#  (A) fir16 doc lap, out-of-context, rang buoc clock 2.5 ns (400 MHz) de tim Fmax
#      cua rieng bo loc -> tai nguyen + WNS -> Fmax uoc tinh.
#  (B) top_arty day du @125 MHz (chan H16) -> bitstream de nap board + bao cao cong suat.
# Ket qua: build/vivado/*.rpt va ../results/e2_fpga_impl.json  (nhan "uoc luong cong cu")
# ============================================================================
set part   xc7z020clg400-1
set here   [file normalize [file dirname [info script]]]
set root   [file normalize "$here/.."]
set outdir "$root/build/vivado"
file mkdir $outdir
# $readmemh tim file hex theo thu muc hien hanh
file copy -force "$root/mem/vectors_in.hex" "$root/mem/golden_out.hex" $outdir
cd $outdir

proc count_cells {filter} { return [llength [get_cells -hier -quiet -filter $filter]] }
proc wns {} {
    set p [get_timing_paths -max_paths 1 -nworst 1 -setup]
    return [get_property SLACK $p]
}
proc power_of {rpt key} {
    if {[regexp "$key\[^|\]*\\|\\s*(\[0-9.\]+)" $rpt -> v]} { return $v }
    return "null"
}

# ---------------- (A) fir16 out-of-context (LUT-only, max_dsp 0) ----------------
set ooc_period 2.5
create_project -in_memory -part $part
read_verilog [list "$root/rtl/fir16.v"]
synth_design -top fir16 -part $part -mode out_of_context -include_dirs "$root/rtl" -max_dsp 0
create_clock -name clk -period $ooc_period [get_ports clk]
opt_design
place_design
route_design
report_utilization     -file fir16_ooc_util.rpt
report_timing_summary  -file fir16_ooc_timing.rpt
set a_wns  [wns]
set a_fmax [format %.1f [expr {1000.0 / ($ooc_period - $a_wns)}]]
set a_dsp  [count_cells {REF_NAME =~ DSP48E1}]
set a_lut  [count_cells {PRIMITIVE_GROUP == LUT}]
set a_ff   [count_cells {PRIMITIVE_GROUP == FLOP_LATCH}]
puts "fir16 OOC (LUT-only, xc7z020): DSP=$a_dsp/220 LUT=$a_lut/53200 FF=$a_ff/106400 WNS=$a_wns ns @ $ooc_period ns -> Fmax ~ $a_fmax MHz"
close_project

# ---------------- (B) top_arty @125 MHz (LUT-only, max_dsp 0) ----------------
create_project -in_memory -part $part
read_verilog [list "$root/rtl/fir16.v" "$root/rtl/uart_tx.v" "$root/rtl/top_arty.v"]
read_xdc "$root/constr/arty_z7_20.xdc"
synth_design -top top_arty -part $part -include_dirs "$root/rtl" -max_dsp 0
opt_design -directive Explore
place_design -directive Explore
phys_opt_design -directive Explore
route_design -directive Explore
report_utilization -hierarchical -file top_util_hier.rpt
report_utilization     -file top_util.rpt
report_timing_summary  -file top_timing.rpt
# Cong suat: uoc luong vector-less, toggle mac dinh cua Vivado (khong phai do)
report_power           -file top_power.rpt
set prpt      [report_power -return_string]
set b_wns     [wns]
set b_total   [power_of $prpt "Total On-Chip Power"]
set b_dyn     [power_of $prpt "Dynamic \\(W\\)"]
set b_static  [power_of $prpt "Device Static"]
set b_fir_dsp [llength [get_cells -hier -quiet -filter {REF_NAME =~ DSP48E1 && NAME =~ u_fir/*}]]
set b_bram    [count_cells {REF_NAME =~ RAMB*}]
write_bitstream -force top_arty.bit
puts "top_arty (Arty Z7-20 @125 MHz, LUT-only): WNS=$b_wns ns @ 8.0 ns, P_total=$b_total W (dyn $b_dyn, static $b_static), FIR DSP=$b_fir_dsp, BRAM=$b_bram"

# ---------------- JSON ----------------
set fd [open "$root/../results/e2_fpga_impl.json" w]
puts $fd "{"
puts $fd "  \"label\": \"uoc luong cong cu\","
puts $fd "  \"experiment\": \"E2_fpga_vivado\","
puts $fd "  \"board\": \"Digilent Arty Z7-20\","
puts $fd "  \"tool\": \"[version -short]\","
puts $fd "  \"part\": \"$part\","
puts $fd "  \"clock_mhz\": 125.0,"
puts $fd "  \"dsp_mode\": \"none (LUT-only)\","
puts $fd "  \"fir16_ooc\": {\"target_period_ns\": $ooc_period, \"wns_ns\": $a_wns, \"fmax_mhz_est\": $a_fmax,"
puts $fd "                \"dsp48e1\": $a_dsp, \"lut\": $a_lut, \"ff\": $a_ff, \"dsp_available\": 220, \"lut_available\": 53200, \"ff_available\": 106400},"
puts $fd "  \"top_125mhz\": {\"clock_mhz\": 125.0, \"period_ns\": 8.0, \"wns_ns\": $b_wns, \"fir_dsp48e1\": $b_fir_dsp, \"bram_tiles\": $b_bram,"
puts $fd "                 \"power_total_w\": $b_total, \"power_dynamic_w\": $b_dyn, \"power_static_w\": $b_static,"
puts $fd "                 \"power_note\": \"Vivado report_power vector-less @125 MHz (LUT-only), toggle mac dinh; gom ca UART/BRAM/IO\"},"
puts $fd "  \"top_100mhz\": {\"clock_mhz\": 125.0, \"period_ns\": 8.0, \"wns_ns\": $b_wns, \"fir_dsp48e1\": $b_fir_dsp, \"bram_tiles\": $b_bram,"
puts $fd "                 \"power_total_w\": $b_total, \"power_dynamic_w\": $b_dyn, \"power_static_w\": $b_static,"
puts $fd "                 \"power_note\": \"Alias tuong thich nguoc cho top_125mhz tren Arty Z7-20\"}"
puts $fd "}"
close $fd
puts "-> results/e2_fpga_impl.json, bitstream: $outdir/top_arty.bit"
