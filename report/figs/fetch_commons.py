#!/usr/bin/env python3
"""Tai lai anh tu Wikimedia Commons (kem tac gia, giay phep) vao figs/img/.
    /usr/bin/python3 figs/fetch_commons.py figs/img
"""
import json, os, re, sys, time, urllib.parse, urllib.request
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "CO3053-student-report/1.0 (educational)"}
OUT = sys.argv[1]
FILES = {
    "mcu_stm32f103": "Core Learning Board module Arduino STM32 F103 C8T6.jpg",
    "soc_rpi4": "Raspberry Pi 4 Model B - Top.jpg",
    "fpga_artix7": "Xilinx Artix7 XC7A100T FGG484 on PCB.jpg",
    "fpga_cell": "FPGA cell example.png",
    "app_ecu": "ECU and wire bundles.JPG",
    "app_router": "Intel FWIXP422BB on mainboard of UMTS Router Surf@home II, o2-8338.jpg",
    "app_phone_soc": "HTC Desire - main board - Qualcomm QSD8250-2.jpg",
    "app_ultrasound": "Sonoscape Ultrasound Machine.jpg",
    "hybrid_zynq": "Xilinx ZynqUltrascale XCZU4CG on PCB.jpg",
}
def api(params):
    for i in range(5):
        time.sleep(3)
        try:
            url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(20 * (i + 1))
def clean(s): return re.sub(r"\s+", " ", re.sub("<[^>]+>", "", s or "")).strip()
credits = {}
for key, title in FILES.items():
    r = api({"action": "query", "titles": "File:" + title, "prop": "imageinfo",
             "iiprop": "url|extmetadata|mime", "iiurlwidth": 1200})
    page = next(iter(r["query"]["pages"].values()))
    ii = page["imageinfo"][0]; m = ii["extmetadata"]
    ext = ".png" if ii["mime"] == "image/png" else ".jpg"
    dst = os.path.join(OUT, key + ext)
    for i in range(5):
        try:
            data = urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers=UA), timeout=60).read(); break
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(20 * (i + 1))
    open(dst, "wb").write(data)
    credits[key] = {"file": os.path.basename(dst), "title": title,
                    "author": clean(m.get("Artist", {}).get("value")),
                    "license": m.get("LicenseShortName", {}).get("value"),
                    "license_url": m.get("LicenseUrl", {}).get("value", ""),
                    "page": ii["descriptionurl"],
                    "description": clean(m.get("ImageDescription", {}).get("value"))[:200]}
    print(key, len(data), credits[key]["license"], "|", credits[key]["author"])
json.dump(credits, open(os.path.join(OUT, "credits.json"), "w"), indent=1, ensure_ascii=False)
