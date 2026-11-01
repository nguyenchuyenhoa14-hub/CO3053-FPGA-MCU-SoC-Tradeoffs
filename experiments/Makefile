# ============================================================================
# Makefile cho bo thi nghiem E0-E5. Chay "make" hoac "make help" de xem danh sach.
#
# Doi cong/may bang bien, vi du:
#   make mcu MCU_PORT=/dev/ttyUSB0
#   make fpga FPGA_PORT=/dev/ttyUSB2
#   make pi PI=pi@192.168.1.50
# ============================================================================

# ---- Cong cu (doi neu cai o cho khac) ----
PIO      ?= $(shell command -v pio 2>/dev/null || echo $(HOME)/Desktop/TEEP/.venv-pio/bin/pio)
# python co pyserial (venv PlatformIO) / python co matplotlib
PYSERIAL ?= $(shell dirname $(PIO))/python3
PYPLOT   ?= /usr/bin/python3
VIVADO   ?= vivado

# ---- Cong serial / may Pi ----
MCU_PORT  ?= /dev/ttyUSB0
FPGA_PORT ?= /dev/ttyUSB1
PI        ?= pi@raspberrypi.local
PI_DIR    ?= ~/co3053-experiments
LOOPS     ?= 100000

.DEFAULT_GOAL := help
.PHONY: help golden sim sim-vcd wave \
        mcu-build mcu-flash mcu-capture mcu \
        fpga-build fpga-flash fpga-capture fpga \
        pi-sync pi-bench pi-cyclictest pi-fetch pi \
        collect ports clean

help:
	@echo "E0/E2 (chay tren may nay):"
	@echo "  make golden          sinh he so + vector + golden (E0)"
	@echo "  make sim             mo phong RTL FIR, tu so golden (E2a)"
	@echo "  make wave            mo phong + mo GTKWave"
	@echo "STM32F103 (ST-Link + USB-UART o $(MCU_PORT)):"
	@echo "  make mcu-build       build firmware"
	@echo "  make mcu-flash       build + nap qua ST-Link"
	@echo "  make mcu-capture     doc ket qua serial -> results/e1_mcu.json"
	@echo "  make mcu             = flash + capture"
	@echo "Arty A7-100T (USB-JTAG, UART o $(FPGA_PORT)):"
	@echo "  make fpga-build      Vivado synth/impl/bitstream + bao cao (5-10 phut)"
	@echo "  make fpga-flash      nap bitstream qua JTAG"
	@echo "  make fpga-capture    doc dong tu kiem -> results/e2_fpga_board.json"
	@echo "  make fpga            = build + flash + capture"
	@echo "Raspberry Pi 4 qua SSH ($(PI)):"
	@echo "  make pi-sync         copy code sang Pi ($(PI_DIR))"
	@echo "  make pi-bench        chay benchmark FIR tren Pi"
	@echo "  make pi-cyclictest   chay cyclictest (sudo tren Pi), LOOPS=$(LOOPS)"
	@echo "  make pi-fetch        keo results/ tu Pi ve"
	@echo "  make pi              = sync + bench + cyclictest + fetch"
	@echo "Khac:"
	@echo "  make collect         bang kiem chung cheo + chart (E5)"
	@echo "  make ports           liet ke cong serial dang cam"
	@echo "  make clean           xoa thu muc build"

# ---------------------------------------------------------------- E0
golden:
	python3 e0_golden/gen_vectors.py

# ---------------------------------------------------------------- E2 mo phong
sim: golden
	./e2_fpga/run_sim.sh

sim-vcd: golden
	./e2_fpga/run_sim.sh vcd

wave: sim-vcd
	gtkwave e2_fpga/build/fir16.vcd &

# ---------------------------------------------------------------- E1 STM32
mcu-build: golden
	cd e1_mcu && $(PIO) run

mcu-flash: golden
	cd e1_mcu && $(PIO) run -t upload

mcu-capture:
	@echo ">> Nhan RESET tren Blue Pill sau khi script bat dau cho"
	$(PYSERIAL) tools/capture_serial.py mcu $(MCU_PORT)

mcu: mcu-flash mcu-capture

# ---------------------------------------------------------------- E2 Arty
fpga-build: golden
	mkdir -p e2_fpga/build/vivado
	cd e2_fpga && $(VIVADO) -mode batch -nojournal -log build/vivado/vivado.log -source vivado/build.tcl

fpga-flash:
	@test -f e2_fpga/build/vivado/top_arty.bit || { echo "Chua co bitstream, chay: make fpga-build"; exit 1; }
	cd e2_fpga && $(VIVADO) -mode batch -nojournal -nolog -source vivado/program.tcl

fpga-capture:
	@echo ">> Nhan BTN0 tren Arty neu chua thay ket qua"
	$(PYSERIAL) tools/capture_serial.py fpga $(FPGA_PORT)

fpga: fpga-build fpga-flash fpga-capture

# ---------------------------------------------------------------- E3 Pi 4
PI_SRC := common e3_soc results/templates

pi-sync: golden
	ssh $(PI) 'mkdir -p $(PI_DIR)/results'
	rsync -a --exclude build $(PI_SRC:%=./%) $(PI):$(PI_DIR)/ --relative

pi-bench: pi-sync
	ssh $(PI) 'cd $(PI_DIR)/e3_soc && ./run_bench.sh'

pi-cyclictest: pi-sync
	ssh -t $(PI) 'cd $(PI_DIR)/e3_soc && sudo LOOPS=$(LOOPS) ./run_cyclictest.sh'

pi-fetch:
	rsync -a $(PI):$(PI_DIR)/results/ results/ --exclude templates

pi: pi-bench pi-cyclictest pi-fetch

# ---------------------------------------------------------------- E5
collect:
	$(PYPLOT) e5_crosscheck/collect.py

ports:
	@ls -l /dev/serial/by-id/ 2>/dev/null || ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "Khong thay cong serial nao"

clean:
	rm -rf e2_fpga/build e3_soc/build e1_mcu/.pio
