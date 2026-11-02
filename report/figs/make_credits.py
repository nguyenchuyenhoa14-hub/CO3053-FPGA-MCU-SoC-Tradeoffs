#!/usr/bin/env python3
"""Sinh figs/credits.tex (macro ghi cong anh) tu figs/img/credits.json."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
cr = json.load(open(os.path.join(HERE, "img", "credits.json")))
NAMES = {  # khoa anh -> ten macro (chi chu cai)
    "mcu_stm32f103": "Mcu", "soc_rpi4": "Rpi", "fpga_artix7": "Artix", "fpga_cell": "Cell",
    "app_ecu": "Ecu", "app_router": "Router", "app_phone_soc": "Phone", "app_ultrasound": "Ultra",
    "hybrid_zynq": "Zynq",
}


def tex(s):
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")):
        s = s.replace(a, b)
    return s


lines = ["% TU DONG SINH boi figs/make_credits.py tu figs/img/credits.json - KHONG SUA TAY"]
rows = []
lets = []
for key, c in cr.items():
    n = NAMES[key]
    short = f"Ảnh: {tex(c['author'])} / Wikimedia Commons, {tex(c['license'])}"
    lines.append(f"\\newcommand{{\\credit{n}}}{{{short}}}")
    lines.append(f"\\newcommand{{\\creditShort{n}}}{{{tex(c['author'])}, {tex(c['license'])}}}")
    lets.append(f"\\let\\credit{n}\\creditShort{n}")
    rows.append(f"\\item {tex(c['title'])} — {tex(c['author'])}, {tex(c['license'])}. "
                f"\\url{{{c['page']}}}")
lines.append("% Slide: dung dang ngan (tac gia, giay phep); ban day du nam o \\creditList\n"
             "\\newcommand{\\useShortCredits}{" + "".join(lets) + "}")
lines.append("\\newcommand{\\creditList}{%\n" + "\n".join(rows) + "}")
open(os.path.join(HERE, "credits.tex"), "w").write("\n".join(lines) + "\n")
print("-> figs/credits.tex")
