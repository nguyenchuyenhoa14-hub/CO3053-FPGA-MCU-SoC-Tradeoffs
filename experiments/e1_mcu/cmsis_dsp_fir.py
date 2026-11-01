# Bien dich 3 ham FIR Q15 cua CMSIS-DSP (goi framework-cmsis-dsp cua PlatformIO) vao firmware.
import os

Import("env")

dsp = env.PioPlatform().get_package_dir("framework-cmsis-dsp")
assert dsp and os.path.isdir(dsp), "Thieu goi framework-cmsis-dsp"

env.Append(CPPPATH=[os.path.join(dsp, "Include"), os.path.join(dsp, "PrivateInclude")])
env.BuildSources(
    os.path.join("$BUILD_DIR", "cmsis_dsp"),
    os.path.join(dsp, "Source", "FilteringFunctions"),
    src_filter=["-<*>", "+<arm_fir_q15.c>", "+<arm_fir_fast_q15.c>", "+<arm_fir_init_q15.c>"],
)
