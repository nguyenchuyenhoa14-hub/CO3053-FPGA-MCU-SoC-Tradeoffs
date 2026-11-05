#!/usr/bin/env python3
"""Gom so lieu tho cua run_qemu.sh (results/e3_sim_raw/) thanh results/e3_soc_sim.json."""
import json
import os
import sys

res = sys.argv[1]
raw = os.path.join(res, "e3_sim_raw")
tool = open(os.path.join(raw, "toolchain.txt")).read().split("\n")
out = {
    "label": "mo phong",
    "experiment": "E3_soc_qemu",
    "simulator": tool[1].strip() + " user-mode, -cpu cortex-a72",
    "target": "ARMv8-A, -mcpu=cortex-a72, static, " + tool[0].strip(),
    "note": "QEMU khong mo phong thoi gian cua Cortex-A72: chi dung tinh dung va so lenh/mau. "
            "Thong luong trong collect.py la uoc luong tu so lenh/mau va gia dinh IPC.",
    "builds": [],
}
for opt in ("O2", "O3"):
    bench = json.load(open(os.path.join(raw, f"bench_{opt}.json")))
    b = {"opt": opt, "build_flags": bench.get("build_flags", ""), "variants": []}
    for v in bench["variants"]:
        vid = 0 if v["variant"] == "shift_loop" else 1
        n1 = int(open(os.path.join(raw, f"n_{opt}_{vid}_1.txt")).read())
        n2 = int(open(os.path.join(raw, f"n_{opt}_{vid}_2.txt")).read())
        b["variants"].append({
            "variant": v["variant"], "correct": v["correct"], "mismatches": v["mismatches"],
            "first_bad": v["first_bad"], "insn_per_sample": round((n2 - n1) / 1024.0, 2),
            "insn_total_k1": n1, "insn_total_k2": n2,
        })
    out["builds"].append(b)
path = os.path.join(res, "e3_soc_sim.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
for b in out["builds"]:
    for v in b["variants"]:
        print(f"  {b['opt']} {v['variant']:18s} correct={v['correct']}  {v['insn_per_sample']:7.2f} lenh/mau")
print("->", os.path.relpath(path, os.path.dirname(res)))
