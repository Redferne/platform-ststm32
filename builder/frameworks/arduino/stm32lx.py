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
from platformio import util

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

FRAMEWORK_DIR = platform.get_package_dir("framework-arduinocorestm32")
CMSIS_DIR = platform.get_package_dir("framework-cmsis")
#MBED_DIR = platform.get_package_dir("framework-mbed")

#FRAMEWORK_VERSION = platform.get_package_version("framework-arduinocorestm32")
assert isdir(FRAMEWORK_DIR)
assert isdir(CMSIS_DIR)
#assert isdir(MBED_DIR)

# remap board configuration values
mcu_type = board.get("build.mcu")[:-2]
variant = board.id.upper()
series = mcu_type[:7].upper() + "xx"

upload_protocol = env.subst("$UPLOAD_PROTOCOL")

vector_offset = 0x0

if upload_protocol == "dfu":
    vector_offset = 0xc000
    ldscript = "ldscript_dfu.ld"
else:
    ldscript = "ldscript.ld"

# mcus with a supprot for float point
mcu_with_fp = [
    "f429", "l496", "f302", "f303re",
    "f401", "f411", "f446", "l476",
#    "f401", "f411", "f446",
    "l432", "f407", "f746", "l475"
]

if any(item in mcu_type for item in mcu_with_fp):
    env.Append(
        CCFLAGS=[
            "-mfpu=fpv4-sp-d16",
            "-mfloat-abi=hard"
        ],

        LINKFLAGS=[
            "-mfpu=fpv4-sp-d16",
            "-mfloat-abi=hard"
        ]
    )

avd = util.get_project_optional_dir("arduino_variants_dir")
variant_dir = join(FRAMEWORK_DIR, "variants", variant)

if avd and isdir(join(avd, variant)):
    variant_dir = join(avd, variant)

env.Append(
    ASFLAGS=["-x", "assembler-with-cpp"],

    CFLAGS=[
        "-MMD",
        "-std=gnu11",
#        "-Dprintf=iprintf"
        "-ffunction-sections",
        "-fdata-sections",
        "-nostdlib",
        "--param",
        "max-inline-insns-single=500",
    ],

    CCFLAGS=[
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
        "-fno-threadsafe-statics",
        "-fno-rtti",
        "-fno-exceptions"
    ],

    CPPDEFINES=[
        ("ARDUINO_%s" % variant.upper()),
        ("DEBUG_LEVEL", "DEBUG_NONE"),
        ("ARDUINO_ARCH_STM32"),
        ("BOARD_NAME", variant),
        (series),
        ("VECT_TAB_OFFSET", vector_offset),
        ("BOARD_%s" % variant),
        ("ARDUINO", 10805),
        ("MCU_%s" % mcu_type.upper()),
        ("F_CPU", "$BOARD_F_CPU"),
        ("SERIAL_USB") # this is so that usb serial is connected when the board boots, use USB_MSC for having USB Mass Storage (MSC) instead
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "cores", "arduino"),
        join(FRAMEWORK_DIR, "cores", "arduino", "avr"),
        join(FRAMEWORK_DIR, "cores", "arduino", "stm32"),
        join(FRAMEWORK_DIR, "system", "Drivers", series + "_HAL_Driver", "Inc"),
        join(FRAMEWORK_DIR, "system", "Drivers", series + "_HAL_Driver", "Src"),
        join(FRAMEWORK_DIR, "system", "Drivers", "CMSIS", "Device", "ST", series, "Include"),
        join(FRAMEWORK_DIR, "system", series),
        join(FRAMEWORK_DIR, variant_dir, "usb"),
        join(FRAMEWORK_DIR, "system", "Middlewares", "ST", "STM32_USB_Device_Library", "Core", "Inc"),
        join(FRAMEWORK_DIR, "system", "Middlewares", "ST", "STM32_USB_Device_Library", "Core", "Src"),
        join(FRAMEWORK_DIR, "system", "Middlewares", "ST", "STM32_USB_Device_Library", "Class", "CDC", "Inc"),
        join(FRAMEWORK_DIR, "system", "Middlewares", "ST", "STM32_USB_Device_Library", "Class", "CDC", "Src"),
        join(FRAMEWORK_DIR, "system", "Drivers", "CMSIS", "Device", "ST", series, "Source", "Templates", "gcc" ),
        join(CMSIS_DIR, "CMSIS", "Core", "Include"),
        variant_dir
#        join(MBED_DIR, "features", "unsupported", "dsp", "cmsis_dsp")
   ],

    LINKFLAGS=[
        "-Os",
        "-Wl,--gc-sections,--relax",
        "-Wl,--check-sections",
#        "-Wl,--entry=Reset_Handler",
        "-Wl,--unresolved-symbols=report-all",
        "-Wl,--warn-common",
        "-Wl,--warn-section-align",
        "-mthumb",
        "-nostartfiles",
        "-nostdlib",
        "-specs=nano.specs",
        "-specs=nosys.specs",
        "-mcpu=%s" % env.BoardConfig().get("build.cpu")
    ],

    LIBPATH=[variant_dir],

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
        join(FRAMEWORK_DIR, "libraries", "__cores__", "arduino"),
        join(FRAMEWORK_DIR, "libraries"),
    ]
)

#
# Target: Build Core Library
#

libs = []

if isdir(variant_dir):
    env.Append(
        CPPPATH=[variant_dir]
    )
    libs.append(env.BuildLibrary(
        join("$BUILD_DIR", "FrameworkArduinoVariant"),
        variant_dir
    ))

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "FrameworkArduino"),
    join(FRAMEWORK_DIR, "cores", "arduino")
))

#libs.append(env.BuildLibrary(
#    join("$BUILD_DIR", "CMSIS_Dsp"),
#    join(MBED_DIR, "features", "unsupported", "dsp", "cmsis_dsp")
#))

env.Prepend(LIBS=libs)
