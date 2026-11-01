# Nap bitstream vao Arty A7 qua USB-JTAG (SRAM, mat khi tat nguon)
#   vivado -mode batch -source vivado/program.tcl
set bit [file normalize "[file dirname [info script]]/../build/vivado/top_arty.bit"]
open_hw_manager
connect_hw_server
open_hw_target
set dev [lindex [get_hw_devices xc7a100t*] 0]
current_hw_device $dev
set_property PROGRAM.FILE $bit $dev
program_hw_devices $dev
puts "Da nap $bit"
close_hw_manager
