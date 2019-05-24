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

import sys
from os.path import join, isfile

from SCons.Script import DefaultEnvironment, SConscript

env = DefaultEnvironment()
mcu = env.BoardConfig().get("build.mcu")
core = env.BoardConfig().get("build.core", "")

#if 'variant' in build:
#    core_variant_dir = join(env.PioPlatform().get_package_dir(
#        "framework-arduinocorestm32"), "variants")

#    if build['variant'] in listdir(core_variant_dir):
#        env.SConscript("arduino/stm32duino.py")

if core == "maple":
    build_script = join(
        env.PioPlatform().get_package_dir("framework-arduinoststm32-maple"),
        "tools", "platformio-build-%s.py" % mcu[0:7])
    if isfile(build_script):
        SConscript(build_script)
    else:
        sys.stderr.write(
            "Error: %s family is not supported by maple core\n" % mcu[0:7])
        env.Exit(1)

# Testing...
elif "stm32l4" in mcu:
    env.SConscript("arduino/stm32lx.py")
else:
    env.SConscript("arduino/stm32duino.py")
#    SConscript(
#        join(env.PioPlatform().get_package_dir(
#            "framework-arduinocorestm32"),
#            "tools", "platformio-build.py"))
