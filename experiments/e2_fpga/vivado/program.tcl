# Nap bitstream vao Digilent Arty Z7-20 (xc7z020clg400-1) qua USB-JTAG
# va tu dong doc ket qua tu kiem qua JTAG USER4 (BSCANE2) -> results/e2_fpga_board.json
#   vivado -mode batch -source vivado/program.tcl
set here [file normalize [file dirname [info script]]]
set root [file normalize "$here/.."]
set bit  [file normalize "$root/build/vivado/top_arty.bit"]
set out_json [file normalize "$root/../results/e2_fpga_board.json"]

open_hw_manager
connect_hw_server
open_hw_target
set dev [lindex [get_hw_devices xc7z020*] 0]
if {$dev eq ""} {
    set dev [lindex [get_hw_devices xc7*] 0]
}
current_hw_device $dev
set_property PROGRAM.FILE $bit $dev
program_hw_devices $dev
puts "Da nap $bit vao $dev (Arty Z7-20 @ 125 MHz, LUT-only)"

# Cho 50 ms de POR (255 chu ky) + 1024 mau FIR (1031 chu ky = 8.25 us) chay xong
after 50

# Thu doc ket qua truc tiep qua JTAG USER4 (BSCANE2)
if {[catch {
    close_hw_target
    open_hw_target -jtag_mode on
    set got 0
    foreach {ir_len ir_hex dr_len} {10 23f 97  10 3e3 97  6 23 96} {
        run_state_hw_jtag RESET
        run_state_hw_jtag IDLE
        scan_ir_hw_jtag $ir_len -tdi $ir_hex
        set raw_hex [scan_dr_hw_jtag $dr_len -tdi 0]
        set v [expr {"0x$raw_hex"}]
        for {set shift 0} {$shift <= 1} {incr shift} {
            set w [expr {$v >> $shift}]
            set hdr  [expr {($w >> 80) & 0xFFFF}]
            set magic [expr {($hdr >> 2) & 0x3FFF}]
            set pass_b [expr {($hdr >> 1) & 1}]
            set done_b [expr {$hdr & 1}]
            if {$magic == 0x2A55 && $done_b == 1} {
                set fbad [expr {($w >> 64) & 0xFFFF}]
                set lat  [expr {($w >> 48) & 0xFFFF}]
                set err  [expr {($w >> 32) & 0xFFFF}]
                set cyc  [expr {$w & 0xFFFFFFFF}]
                set n    1024
                set status [expr {$pass_b ? "PASS" : "FAIL"}]
                set line [format "FIR16 %s N=%04X ERR=%04X LAT=%04X CYC=%08X FBAD=%04X" $status $n $err $lat $cyc $fbad]
                puts "JTAG Readout: $line"
                set spc  [format %.4f [expr {double($n) / double($cyc - $lat)}]]
                set msps [format %.2f [expr {double($n) / double($cyc - $lat) * 125.0}]]
                set lns  [format %.1f [expr {double($lat) * 8.0}]]
                set fbad_json [expr {$fbad == 0xFFFF ? "null" : $fbad}]
                set pass_json [expr {$pass_b ? "true" : "false"}]
                set fd [open $out_json w]
                puts $fd "{"
                puts $fd " \"label\": \"do\","
                puts $fd " \"experiment\": \"E2_fpga_on_board\","
                puts $fd " \"board\": \"Digilent Arty Z7-20\","
                puts $fd " \"part\": \"xc7z020clg400-1\","
                puts $fd " \"clock_mhz\": 125.0,"
                puts $fd " \"dsp_mode\": \"none (LUT-only)\","
                puts $fd " \"pass\": $pass_json,"
                puts $fd " \"num_samples\": $n,"
                puts $fd " \"mismatches\": $err,"
                puts $fd " \"first_bad\": $fbad_json,"
                puts $fd " \"latency_cycles\": $lat,"
                puts $fd " \"cycles_first_in_to_last_out\": $cyc,"
                puts $fd " \"samples_per_cycle\": $spc,"
                puts $fd " \"throughput_msps\": $msps,"
                puts $fd " \"latency_ns\": $lns,"
                puts $fd " \"raw\": \"$line\""
                puts $fd "}"
                close $fd
                puts "-> $out_json"
                set got 1
                break
            }
        }
        if {$got} { break }
    }
    catch { close_hw_target }
} err]} {
    catch { close_hw_target }
    puts "(Ghi chu: Khong doc qua JTAG raw mode: $err. Co the doc qua UART Pmod JA\[0\] chan Y18 bang capture_serial.py)"
}

close_hw_manager
