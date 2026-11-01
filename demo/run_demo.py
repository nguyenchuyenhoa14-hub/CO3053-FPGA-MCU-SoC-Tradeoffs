"""
===============================================================================
DEMO BENCHMARK RUNNER (CO3053 EMBEDDED SYSTEMS - TOPIC 09)
Mo phong doi sanh dinh luong: MCU vs. FPGA vs. Heterogeneous SoC
===============================================================================
"""

import os
import sys
import subprocess
import shutil

# Dam bao tuong thich ma hoa tren moi console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(DEMO_DIR, "outputs")
CHARTS_DIR = os.path.join(OUTPUTS_DIR, "charts")

os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def step1_mcu_benchmark():
    print_header("[BUOC 1/4] BIEN DICH VA CHAY BENCHMARK FIR TREN MCU (C)")
    c_source = os.path.join(DEMO_DIR, "mcu_firmware", "fir_mcu.c")
    c_exe = os.path.join(DEMO_DIR, "mcu_firmware", "fir_mcu.exe")

    # Bien dich GCC
    compile_cmd = ["gcc", "-O3", "-Wall", c_source, "-o", c_exe]
    print(f"Executing: {' '.join(compile_cmd)}")
    res = subprocess.run(compile_cmd, capture_output=True, text=True, errors='replace')
    if res.returncode != 0:
        print(f"[LOI BIEN DICH GCC]:\n{res.stderr}")
        return False
    print("-> Bien dich fir_mcu.c thanh cong!")

    # Chay fir_mcu.exe
    res_run = subprocess.run([c_exe], capture_output=True, text=True, cwd=os.path.join(DEMO_DIR, "mcu_firmware"), errors='replace')
    print(res_run.stdout)
    if res_run.returncode != 0:
        print(f"[LOI THUC THI]:\n{res_run.stderr}")
        return False
    
    json_src = os.path.join(DEMO_DIR, "mcu_firmware", "mcu_benchmark.json")
    if os.path.exists(json_src):
        shutil.copy(json_src, os.path.join(OUTPUTS_DIR, "mcu_benchmark.json"))

    return True

def step2_fpga_simulation():
    print_header("[BUOC 2/4] TONG HOP VA MO PHONG PHAN CUNG FPGA (IVERILOG + VVP)")
    rtl_v = os.path.join(DEMO_DIR, "fpga_rtl", "fir_filter_16tap.v")
    tb_v = os.path.join(DEMO_DIR, "fpga_rtl", "tb_fir_filter.v")
    sim_vvp = os.path.join(DEMO_DIR, "fpga_rtl", "sim.vvp")

    # Bien dich bang iverilog
    compile_cmd = ["iverilog", "-o", sim_vvp, rtl_v, tb_v]
    print(f"Executing: {' '.join(compile_cmd)}")
    res = subprocess.run(compile_cmd, capture_output=True, text=True, errors='replace')
    if res.returncode != 0:
        print(f"[LOI TONG HOP IVERILOG]:\n{res.stderr}")
        return False
    print("-> Tong hop Verilog RTL thanh cong!")

    # Chay mo phong bang vvp
    res_run = subprocess.run(["vvp", "sim.vvp"], capture_output=True, text=True, cwd=os.path.join(DEMO_DIR, "fpga_rtl"), errors='replace')
    print(res_run.stdout)
    if res_run.returncode != 0:
        print(f"[LOI MO PHONG VVP]:\n{res_run.stderr}")
        return False

    vcd_src = os.path.join(DEMO_DIR, "fpga_rtl", "fir_simulation.vcd")
    if os.path.exists(vcd_src):
        vcd_dst = os.path.join(OUTPUTS_DIR, "fir_simulation.vcd")
        shutil.copy(vcd_src, vcd_dst)
        print(f"-> Da xuat file dang song GTKWave: {vcd_dst}")

    return True

def step3_soc_simulation():
    print_header("[BUOC 3/4] MO PHONG TANG TOC HETEROGENEOUS SOC (ZYNQ AXI DMA)")
    soc_script = os.path.join(DEMO_DIR, "soc_emulation", "soc_axi_dma_sim.py")
    res = subprocess.run([sys.executable, soc_script], capture_output=True, text=True, cwd=os.path.join(DEMO_DIR, "soc_emulation"), errors='replace')
    print(res.stdout)
    if res.returncode != 0:
        print(f"[LOI MO PHONG SOC]:\n{res.stderr}")
        return False

    json_src = os.path.join(DEMO_DIR, "soc_emulation", "soc_benchmark.json")
    if os.path.exists(json_src):
        shutil.copy(json_src, os.path.join(OUTPUTS_DIR, "soc_benchmark.json"))

    return True

def step4_plot_charts():
    print_header("[BUOC 4/4] XUAT 4 BIEU DO DOI SANH KHOA HOC CHUAN IEEE (300 DPI)")
    plot_script = os.path.join(DEMO_DIR, "visualization", "plot_benchmark_results.py")
    res = subprocess.run([sys.executable, plot_script], capture_output=True, text=True, errors='replace')
    print(res.stdout)
    if res.returncode != 0:
        print(f"[LOI XUAT DO THI]:\n{res.stderr}")
        return False
    return True

def main():
    print("\n" + "=" * 70)
    print("  KHOI DONG HE THONG DEMO BENCHMARK: MCU vs. FPGA vs. SOC (CO3053)")
    print("=======================================================================")

    ok1 = step1_mcu_benchmark()
    if not ok1:
        print("Dung do loi tai Buoc 1.")
        return

    ok2 = step2_fpga_simulation()
    if not ok2:
        print("Dung do loi tai Buoc 2.")
        return

    ok3 = step3_soc_simulation()
    if not ok3:
        print("Dung do loi tai Buoc 3.")
        return

    ok4 = step4_plot_charts()
    if not ok4:
        print("Dung do loi tai Buoc 4.")
        return

    print_header("TONG KET: QUY TRINH DEMO DA HOAN TAT THANH CONG!")
    print(f"Tat ca san pham da san sang trong thu muc:\n -> {OUTPUTS_DIR}")
    print("\nCac tep tin san sang phuc vu trinh chieu va bao cao:")
    print(f" 1. Dang song mo phong: {os.path.join(OUTPUTS_DIR, 'fir_simulation.vcd')}")
    print(f" 2. Bieu do Thong luong: {os.path.join(CHARTS_DIR, 'chart1_throughput_comparison.png')}")
    print(f" 3. Bieu do Do tre & Jitter: {os.path.join(CHARTS_DIR, 'chart2_latency_and_jitter.png')}")
    print(f" 4. Bieu do Hieu qua nang luong: {os.path.join(CHARTS_DIR, 'chart3_energy_efficiency.png')}")
    print(f" 5. Bieu do Diem hoa von: {os.path.join(CHARTS_DIR, 'chart4_breakeven_cost_analysis.png')}")

if __name__ == "__main__":
    main()
