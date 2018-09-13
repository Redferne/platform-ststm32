# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Arduino

Arduino Wiring-based Framework allows writing cross-platform software to
control devices attached to a wide range of Arduino boards to create all
kinds of creative coding, interactive objects, spaces or physical experiences.

http://www.stm32duino.com
"""

from os.path import isdir, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

FRAMEWORK_DIR = platform.get_package_dir("framework-arduinocorestm32")
CMSIS_DIR = platform.get_package_dir("framework-cmsis")

#FRAMEWORK_VERSION = platform.get_package_version("framework-arduinocorestm32")
assert isdir(FRAMEWORK_DIR)
assert isdir(CMSIS_DIR)

#print env.Dump()
#print "******************** BUILD VARIANT: " + env.BoardConfig().get("build.variant")

# remap board configuration values
# Nucleo_64.menu.pnum.NUCLEO_L476RG.build.mcu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard
mcu_type = board.get("build.mcu")[:-2]
if "stm32f103c8" in mcu_type:
    ldscript = "ldscript.ld"
    variant = "BLUEPILL_F103C8"

upload_protocol = env.subst("$UPLOAD_PROTOCOL")

# -mcpu=cortex-m3 -mthumb -mno-thumb-interwork -mfpu=vfp -msoft-float -mfix-cortex-m3-ldrd

env.Append(
    ASFLAGS=["-x", "assembler-with-cpp"],

    CFLAGS=[
        "-MMD",
        "-std=gnu11",
        "-ffunction-sections",
        "-fdata-sections",
        "-nostdlib",
        "--param",
        "max-inline-insns-single=500",
#        "-std=gnu11"
    ],

    CCFLAGS=[
#        "-MMD",
#        "--param",
#        "max-inline-insns-single=500"
        "-MMD",
        "--param",
        "max-inline-insns-single=500",
        "-Os",  # optimize for size
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections",
        "-Wall",
        "-mthumb",
        "-nostdlib",
        "-mcpu=%s" % env.BoardConfig().get("build.cpu")
    ],

    CXXFLAGS=[
        "-std=gnu++14",
        "-fno-rtti",
        "-fno-exceptions"
#        "-std=gnu++14"
    ],

    CPPDEFINES=[
        ("DEBUG_LEVEL", "DEBUG_NONE"),
        ("BOARD_%s" % variant),
        ("ARDUINO", 10805),
        ("ARDUINO_%s" % variant.upper()),
        ("ARDUINO_ARCH_STM32"),
        ("STM32F103xx"),
        ("STM32F1xx"),
        ("MCU_%s" % mcu_type.upper()),
        ("F_CPU", "$BOARD_F_CPU"),
        ("SERIAL_USB") # this is so that usb serial is connected when the board boots, use USB_MSC for having USB Mass Storage (MSC) instead
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "cores", "arduino"),
        join(FRAMEWORK_DIR, "cores", "arduino", "avr"),
        join(FRAMEWORK_DIR, "cores", "arduino", "stm32"),
        join(FRAMEWORK_DIR, "system", "Drivers", "STM32F1xx_HAL_Driver", "Inc"),
        join(FRAMEWORK_DIR, "system", "Drivers", "STM32F1xx_HAL_Driver", "Src"),
        join(FRAMEWORK_DIR, "system", "Drivers", "CMSIS", "Device", "ST", "STM32F1xx", "Include"),
        join(FRAMEWORK_DIR, "system", "STM32F1xx"),
        join(FRAMEWORK_DIR, "variants", "BLUEPILL_F103C8"),
        join(FRAMEWORK_DIR, "system", "Middlewares", "ST", "STM32_USB_Device_Library", "Core", "Inc"),
        join(FRAMEWORK_DIR, "system", "Middlewares", "ST", "STM32_USB_Device_Library", "Core", "Src"),
        join(FRAMEWORK_DIR, "system", "Drivers", "CMSIS", "Device", "ST", "STM32F1xx", "Source", "Templates", "gcc" ),
        join(CMSIS_DIR, "cores", "stm32"),
    ],

    LINKFLAGS=[
        "-Os",
        "-Wl,--gc-sections,--relax",
        "-mthumb",
        "-nostartfiles",
        "-nostdlib",
        "-specs=nosys.specs",
        "-mcpu=%s" % env.BoardConfig().get("build.cpu")
    ],

    LIBPATH=[join(FRAMEWORK_DIR, "variants", variant)],

    LIBS=["c"]
)

# copy CCFLAGS to ASFLAGS (-x assembler-with-cpp mode)
env.Append(ASFLAGS=env.get("CCFLAGS", [])[:])

# remap ldscript
env.Replace(LDSCRIPT_PATH=ldscript)

# remove unused linker flags
for item in ("-nostartfiles", "-nostdlib"):
    if item in env['LINKFLAGS']:
        env['LINKFLAGS'].remove(item)

# remove unused libraries
for item in ("stdc++", "nosys"):
    if item in env['LIBS']:
        env['LIBS'].remove(item)

#
# Lookup for specific core's libraries
#

env.Append(
    LIBSOURCE_DIRS=[
#        join(FRAMEWORK_DIR, "libraries", "__cores__", "maple"),
        join(FRAMEWORK_DIR, "libraries"),
    ]
)

#
# Target: Build Core Library
#

libs = []

if "build.variant" in board:
    libs.append(env.BuildLibrary(
        join("$BUILD_DIR", "FrameworkArduinoVariant"),
        join(FRAMEWORK_DIR, "variants", variant)
    ))

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "FrameworkArduino"),
    join(FRAMEWORK_DIR, "cores", "arduino"),
))

#libs.append(env.BuildLibrary(
#    join("$BUILD_DIR", "CMSIS_Dsp"),
#    join(MBED_DIR, "features", "unsupported", "dsp", "cmsis_dsp")
#))

env.Prepend(LIBS=libs)
