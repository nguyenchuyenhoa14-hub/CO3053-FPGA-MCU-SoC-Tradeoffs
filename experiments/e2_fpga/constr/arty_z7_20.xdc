## Digilent Arty Z7-20 (xc7z020clg400-1), chan theo Arty-Z7-20-Master.xdc
## Clock PL 125 MHz (8.000 ns)
set_property -dict { PACKAGE_PIN H16  IOSTANDARD LVCMOS33 } [get_ports CLK125MHZ]
create_clock -add -name sys_clk_pin -period 8.000 -waveform {0 4} [get_ports CLK125MHZ]

## Nut nhan PL (active-high: nhan = 1, nha = 0)
set_property -dict { PACKAGE_PIN D19  IOSTANDARD LVCMOS33 } [get_ports btn0]
set_property -dict { PACKAGE_PIN D20  IOSTANDARD LVCMOS33 } [get_ports btn1_rst]

## 4 LED don tren board (LD0..LD3)
set_property -dict { PACKAGE_PIN R14  IOSTANDARD LVCMOS33 } [get_ports {led[0]}]
set_property -dict { PACKAGE_PIN P14  IOSTANDARD LVCMOS33 } [get_ports {led[1]}]
set_property -dict { PACKAGE_PIN N16  IOSTANDARD LVCMOS33 } [get_ports {led[2]}]
set_property -dict { PACKAGE_PIN M14  IOSTANDARD LVCMOS33 } [get_ports {led[3]}]

## UART TX tu PL ra ngoai (Pmod JA chan 1 = JA[0], 115200 8N1)
set_property -dict { PACKAGE_PIN Y18  IOSTANDARD LVCMOS33 } [get_ports uart_rxd_out]

## Tin hieu cham / bat dong bo: khong rang buoc thoi gian
set_false_path -from [get_ports {btn1_rst btn0}]
set_false_path -to   [get_ports {led[*] uart_rxd_out}]
