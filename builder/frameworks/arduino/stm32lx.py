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

https://github.com/Redferne/Arduino_Core_STM32
"""

import sys
from os.path import isfile, isdir, join

from SCons.Script import DefaultEnvironment
from platformio.project import helpers as util

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

FRAMEWORK_DIR = platform.get_package_dir("framework-arduinocorestm32")
#CMSIS_DIR = join(platform.get_package_dir(
#    "framework-arduinoststm32"), "CMSIS", "CMSIS")
CMSIS_DIR = platform.get_package_dir("framework-cmsis")
assert isdir(FRAMEWORK_DIR)
assert isdir(CMSIS_DIR)


#variant = board.id.upper()
mcu = env.BoardConfig().get("build.mcu", "")
board_name = env.subst("$BOARD")
mcu_type = mcu[:-2]
variant = board.get("build.variant")
series = mcu_type[:7].upper() + "xx"
variant_dir = join(FRAMEWORK_DIR, "variants", variant)


def process_standard_library_configuration(cpp_defines):
    if "PIO_FRAMEWORK_ARDUINO_STANDARD_LIB" in cpp_defines:
        env['LINKFLAGS'].remove("--specs=nano.specs")
    if "PIO_FRAMEWORK_ARDUINO_NANOLIB_FLOAT_PRINTF" in cpp_defines:
        env.Append(LINKFLAGS=["-u_printf_float"])
    if "PIO_FRAMEWORK_ARDUINO_NANOLIB_FLOAT_SCANF" in cpp_defines:
        env.Append(LINKFLAGS=["-u_scanf_float"])


def process_usart_configuration(cpp_defines):
    if "PIO_FRAMEWORK_ARDUINO_SERIAL_DISABLED" in cpp_defines:
        env['CPPDEFINES'].remove("HAL_UART_MODULE_ENABLED")

    elif "PIO_FRAMEWORK_ARDUINO_SERIAL_WITHOUT_GENERIC" in cpp_defines:
        env.Append(CPPDEFINES=["HWSERIAL_NONE"])


def process_usb_speed_configuration(cpp_defines):
    if "PIO_FRAMEWORK_ARDUINO_USB_HIGHSPEED" in cpp_defines:
        env.Append(CPPDEFINES=["USE_USB_HS"])

    elif "PIO_FRAMEWORK_ARDUINO_USB_HIGHSPEED_FULLMODE" in cpp_defines:
        env.Append(CPPDEFINES=["USE_USB_HS", "USE_USB_HS_IN_FS"])


def process_usb_configuration(cpp_defines):
    if "PIO_FRAMEWORK_ARDUINO_ENABLE_CDC" in cpp_defines:
        env.Append(CPPDEFINES=["USBD_USE_CDC"])

    elif "PIO_FRAMEWORK_ARDUINO_ENABLE_CDC_WITHOUT_SERIAL" in cpp_defines:
        env.Append(CPPDEFINES=["USBD_USE_CDC", "DISABLE_GENERIC_SERIALUSB"])

    elif "PIO_FRAMEWORK_ARDUINO_ENABLE_HID" in cpp_defines:
        env.Append(CPPDEFINES=["USBD_USE_HID_COMPOSITE"])

upload_protocol = env.subst("$UPLOAD_PROTOCOL")
vector_offset = 0x0
if upload_protocol == "dfu":
    vector_offset = 0xc000
    ldscript = "ldscript_dfu.ld"
else:
    ldscript = "ldscript.ld"

if any(mcu in board.get("build.cpu") for mcu in ("cortex-m4", "cortex-m7")):
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
        "-ffunction-sections",
        "-fdata-sections",
        "-nostdlib",
        "--param",
        "max-inline-insns-single=500",
    ],

    CXXFLAGS=[
        "-std=gnu++14",
        "-fno-threadsafe-statics",
        "-fno-rtti",
        "-fno-exceptions"
    ],

    CCFLAGS=[
        "-Os",  # optimize for size
        "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
        "-mthumb",
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections",
        "-Wall",
        "-MMD",
        "-nostdlib",
        "--param", "max-inline-insns-single=500"
    ],

    CPPDEFINES=[
        (series),
        ("ARDUINO", 10808),
        "ARDUINO_ARCH_STM32",
        "ARDUINO_%s" % variant.upper(),
        ("BOARD_NAME", variant),
        ("DEBUG_LEVEL", "DEBUG_NONE"),
        ("VECT_TAB_OFFSET", vector_offset),
        ("BOARD_%s" % variant),
        ("MCU_%s" % mcu_type.upper()),
        ("F_CPU", "$BOARD_F_CPU"),
#        ("SERIAL_USB") # this is so that usb serial is connected when the board boots, use USB_MSC for having USB Mass Storage (MSC) instead
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "cores", "arduino", "avr"),
        join(FRAMEWORK_DIR, "cores", "arduino", "stm32"),
        join(FRAMEWORK_DIR, "cores", "arduino", "stm32", "LL"),
        join(FRAMEWORK_DIR, "cores", "arduino", "stm32", "usb"),
        join(FRAMEWORK_DIR, "cores", "arduino", "stm32", "usb", "hid"),
        join(FRAMEWORK_DIR, "cores", "arduino", "stm32", "usb", "cdc"),
        join(FRAMEWORK_DIR, "system", "Drivers",
             series + "_HAL_Driver", "Inc"),
        join(FRAMEWORK_DIR, "system", "Drivers",
             series + "_HAL_Driver", "Src"),
        join(FRAMEWORK_DIR, "system", series),
#        join(FRAMEWORK_DIR, variant_dir, "usb"),
        join(FRAMEWORK_DIR, "system", "Middlewares", "ST",
             "STM32_USB_Device_Library", "Core", "Inc"),
        join(FRAMEWORK_DIR, "system", "Middlewares", "ST",
             "STM32_USB_Device_Library", "Core", "Src"),
        join(CMSIS_DIR, "CMSIS", "Core", "Include"),
        join(FRAMEWORK_DIR, "system", "Middlewares", "ST", "STM32_USB_Device_Library", "Class", "CDC", "Inc"),
        join(FRAMEWORK_DIR, "system", "Middlewares", "ST", "STM32_USB_Device_Library", "Class", "CDC", "Src"),
        join(FRAMEWORK_DIR, "system", "Drivers", "CMSIS", "Device", "ST", series, "Include"),
        join(FRAMEWORK_DIR, "system", "Drivers", "CMSIS", "Device", "ST", series, "Source", "Templates", "gcc" ),
        join(FRAMEWORK_DIR, "cores", "arduino"),
        variant_dir
   ],

    LINKFLAGS=[
        "-Os",
        "-mthumb",
        "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
        "-specs=nano.specs",
        "-Wl,--gc-sections,--relax",
        "-Wl,--check-sections",
#        "-Wl,--entry=Reset_Handler",
        "-Wl,--unresolved-symbols=report-all",
        "-Wl,--warn-common",
        "-Wl,--warn-section-align",
        "-nostartfiles",
        "-nostdlib",
        "-specs=nosys.specs"
    ],

    LIBS=["c"],

    LIBPATH=[variant_dir]

)

env.ProcessFlags(board.get("build.framework_extra_flags.arduino", ""))

#
# Linker requires preprocessing with correct RAM|ROM sizes
#

# remap ldscript
env.Replace(LDSCRIPT_PATH=ldscript)

if not isfile(join(variant_dir, "ldscript.ld")):
    print("Warning! Cannot find linker script for the current target!\n")


#linker_script = env.Command(
#    join("$BUILD_DIR", "preproc.ld"),
#    join(variant_dir, "ldscript.ld"),
#    env.VerboseAction(
#        '{} -E -P $_CPPDEFFLAGS $_CPPINCFLAGS {} {} $SOURCE -o $TARGET'.format(
#            env.subst("$GDB").replace("-gdb", "-cpp"),
#            "-DLD_MAX_SIZE=%d" % board.get("upload.maximum_size"),
#            "-DLD_MAX_DATA_SIZE=%d" % board.get("upload.maximum_ram_size")),
#        "Generating LD script $TARGET"))

#env.Depends("$BUILD_DIR/$PROGNAME$PROGSUFFIX", linker_script)
#env.Replace(LDSCRIPT_PATH=linker_script)

# remove unused linker flags
for item in ("-nostartfiles", "-nostdlib"):
    if item in env['LINKFLAGS']:
        env['LINKFLAGS'].remove(item)

# remove unused libraries
for item in ("stdc++", "nosys"):
    if item in env['LIBS']:
        env['LIBS'].remove(item)

#
# Process configuration flags
#

cpp_defines = env.Flatten(env.get("CPPDEFINES", []))

process_standard_library_configuration(cpp_defines)
process_usb_configuration(cpp_defines)
process_usb_speed_configuration(cpp_defines)
process_usart_configuration(cpp_defines)

# copy CCFLAGS to ASFLAGS (-x assembler-with-cpp mode)
env.Append(ASFLAGS=env.get("CCFLAGS", [])[:])

env.Append(
    LIBSOURCE_DIRS=[
        join(FRAMEWORK_DIR, "libraries", "__cores__", "arduino"),
        join(FRAMEWORK_DIR, "libraries")
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
    env.BuildSources(
        join("$BUILD_DIR", "FrameworkArduinoVariant"),
        variant_dir
    )

env.BuildSources(
    join("$BUILD_DIR", "FrameworkArduino"),
    join(FRAMEWORK_DIR, "cores", "arduino"))

env.Prepend(LIBS=libs)
