#!/usr/bin/env bash
# E2a - Mo phong RTL FIR16 bang Icarus Verilog, tu so sanh voi golden.
#   ./run_sim.sh        -> results/e2_fpga_sim.json
#   ./run_sim.sh vcd    -> them build/fir16.vcd de mo bang GTKWave
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build ../results
cp mem/*.hex build/
iverilog -g2005 -Wall -I rtl -o build/sim.vvp rtl/fir16.v tb/tb_fir16.v
cd build
vvp -n sim.vvp ${1:++vcd}
cp e2_fpga_sim.json ../../results/
echo "-> results/e2_fpga_sim.json"
