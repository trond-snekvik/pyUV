"""
Generate various build files.
"""
import toolchain
from toolchain_armcc import *

import xml.etree.ElementTree as xml
from json import encoder, decoder
import os.path
import exceptions
import sys
import shutil
import colorama

LANG_EXT_C = ["c", "h"]
LANG_EXT_CPP = ["cpp", "hpp", "cc"]
LANG_EXT_ASM = ["s", "asm"]


class Region:
    TYPE_ROM = "rom"
    TYPE_RAM = "ram"

    def __init__(self, start, size, memtype, init=False):
        self.start = start
        self.size = size
        self.memtype = memtype
        self.init = init


class SourceFile:
    def __init__(self, path):
        self.name = os.path.basename(path)
        self.path = path

    def language(self):
        ext = self.name.lower().split(".")[-1]
        if ext in LANG_EXT_C:
            return "c"
        if ext in LANG_EXT_CPP:
            return "cpp"
        if ext in LANG_EXT_ASM:
            return "asm"

class SourceGroup:
    def __init__(self, name = ""):
        self.name = name
        self.files = []

class Target:
    def __init__(self, project, name = ""):
        self.name = name
        self.includedirs = []
        self.defines = []
        self.outputdir = None
        self.compileroptions = []
        self.linkeroptions = []
        self.groups = []
        self.outputname = name
        self.project = project
        self.romRegions = []
        self.ramRegions = []
        self.genhex = True
        self.miscopts = {}
        self.cwd = None

    def build(self, toolchain):
        (status, output) = toolchain.scatterGen(self)
        if not os.path.exists(self.outputdir):
            os.mkdir(self.outputdir)
        if not status:
            print("Failed.")
            print(output)
            return status
        else:
            with open(os.path.join(self.outputdir,
                    self.outputname + "." + toolchain.linkerfileext), "w") as f:
                f.write(output)

        for g in self.groups:
            for f in g.files:
                outfile = os.path.join(self.cwd, self.outputdir, f.name.split(".")[0] + ".o")
                if not os.path.exists(outfile) or \
                    os.path.getmtime(outfile) < os.path.getmtime(os.path.join(self.cwd, f.path)):
                    (status, output) = toolchain.compile(self, f)
                    if not status:
                        print(colorama.Fore.RED + output + colorama.Style.RESET_ALL)
                        return status
        (status, output) = toolchain.link(self)
        if status:
            sys.stdout.write(colorama.Fore.GREEN)
        else:
            sys.stdout.write(colorama.Fore.RED)
        sys.stdout.write(output + colorama.Style.RESET_ALL)

        if self.genhex:
            print("generating " + self.outputname + ".hex...")
            elf = os.path.join(self.outputdir, self.outputname + ".elf")
            (status, output) = toolchain.toHex(self, elf)
        return status

    def __str__(self):
        out = "Target " + self.name + ":\n"
        out += "\tROM Regions:\n"
        for (i, region) in enumerate(self.romRegions):
            out += "\t\tRegion " + str(i + 1)
            if region.init:
                out += " (Init)\n"
            else:
                out += "\n"
            out += "\t\t\tStart: 0x" + format(region.start, "x") + "\n"
            out += "\t\t\tSize:  0x" + format(region.size, "x") + "\n"
        out += "\tRAM Regions:\n"
        for (i, region) in enumerate(self.ramRegions):
            out += "\t\tRegion " + str(i + 1)
            if not region.init:
                out += " (NoInit)\n"
            else:
                out += "\n"
            out += "\t\t\tStart: 0x" + format(region.start, "x") + "\n"
            out += "\t\t\tSize:  0x" + format(region.size, "x") + "\n"
        out += "\tIncludes:\n"
        for d in self.includedirs:
            out += "\t\t" + d + "\n"
        out += "\tOutput: " + os.path.join(self.cwd, self.outputdir, self.outputname + ".hex") + "\n"
        out += "\tOptions: "
        for o in self.compileroptions:
            out += o + " "
        out += "\n"
        out += "\tDefines:\n"
        for d in self.defines:
            out += "\t\t" + d + "\n"
        out += "\n"
        for group in self.groups:
            out += "\tGroup " + str(group.name) + ":\n"
            for sourcefile in group.files:
                out += "\t\t" + sourcefile.name + "\n"
        return out

class Project:
    def __init__(self, name = ""):
        self.name = name
        self.targets = []
        self.origin = "" # uv, make, cmake
        self.uvfile = None
        self.makefile = None
        self.cmakelist = None
        self.toolchain = None

    def buildAll(self, toolchain):
        if len(self.targets) is 0:
            print "No targets."
            return False

        for target in self.targets:
            if not target.build(toolchain):
                return False
        return True

    def parseUV(self, filename):
        if not os.path.exists(filename):
            print "Can't find file " + filename
            return False

        tree = xml.parse(filename).getroot()
        self.name = os.path.basename(filename.split(".")[0])
        for xmltarget in tree.find("Targets"):
            target = Target(self, xmltarget.find("TargetName").text)
            xmltargetads = xmltarget.find("TargetOption").find("TargetArmAds")
            xmlcommon = xmltarget.find("TargetOption").find("TargetCommonOption")
            xmlmisc = xmltargetads.find("ArmAdsMisc")
            xmlmemories = xmlmisc.find("OnChipMemories")
            target.genhex = (xmlcommon.find("CreateHexFile").text == "1")

            if xmlmisc.find("Ir1Chk").text == "1":
                target.romRegions.append(Region(int(xmlmemories.find("OCR_RVCT4").find("StartAddress").text, 16),
                                                int(xmlmemories.find("OCR_RVCT4").find("Size").text, 16), Region.TYPE_ROM,
                                                int(xmlmisc.find("StupSel").text) == 8))
            if xmlmisc.find("Ir2Chk").text == "1":
                target.romRegions.append(Region(int(xmlmemories.find("OCR_RVCT5").find("StartAddress").text, 16),
                                                int(xmlmemories.find("OCR_RVCT5").find("Size").text, 16), Region.TYPE_ROM,
                                                int(xmlmisc.find("StupSel").text) == 16))

            if xmlmisc.find("Im1Chk").text == "1":
                target.ramRegions.append(Region(int(xmlmemories.find("OCR_RVCT9").find("StartAddress").text, 16),
                                                int(xmlmemories.find("OCR_RVCT9").find("Size").text, 16), Region.TYPE_RAM,
                                                not xmlmisc.find("NoZi4").text == "1"))
            if xmlmisc.find("Im2Chk").text == "1":
                target.ramRegions.append(Region(int(xmlmemories.find("OCR_RVCT10").find("StartAddress").text, 16),
                                                int(xmlmemories.find("OCR_RVCT10").find("Size").text, 16), Region.TYPE_RAM,
                                                not xmlmisc.find("NoZi5").text == "1"))

            for xmlgroup in xmltarget.find("Groups").findall("Group"):
                group = SourceGroup(xmlgroup.find("GroupName").text)
                for xmlfile in xmlgroup.find("Files").findall("File"):
                    group.files.append(SourceFile(str(os.path.join(os.path.dirname(filename), xmlfile.find("FilePath").text))))
                target.groups.append(group)
            self.targets.append(target)

            xmlcads = xmltargetads.find("Cads")
            xmlcadsvarious = xmlcads.find("VariousControls")
            misccontrol = xmlcadsvarious.find("MiscControls").text
            if misccontrol:
                target.compileroptions = misccontrol.split()
            target.compileroptions.append("-O" + str(int(xmlcads.find("Optim").text) - 1))
            warnlevel = int(xmlcads.find("wLevel").text)
            if warnlevel is 1:
                target.miscopts["warning"] = "none"
            if warnlevel is 2:
                target.miscopts["warning"] = "all"
            if xmlcads.find("uC99").text == "1":
                target.compileroptions.append("--c99")
            target.outputname = xmlcommon.find("OutputName").text

            target.includedirs = xmlcadsvarious.find("IncludePath").text.split(";")
            target.includedirs.sort()
            target.defines = xmlcadsvarious.find("Define").text.split()
            target.cwd = os.path.dirname(os.path.abspath(filename))
            if not target.cwd:
                target.cwd = os.path.dirname(os.path.join(os.curdir, filename))
            target.outputdir = os.path.join(target.cwd, xmlcommon.find("OutputDirectory").text)

    def __str__(self):
        out = "Project " + self.name + ":\n"
        for target in self.targets:
            for line in str(target).splitlines():
                out += "\t" + line + "\n"
        return out

def findroot(cwd):
    path = os.path.abspath(cwd)
    while not os.path.dirname(path) == path:
        if ".git" in os.listdir(path):
            return os.path.abspath(path)
        path = os.path.dirname(path)
    return None

def findUVprojects(root):
    if not root:
        return None
    projs = []
    def walkcb(projs, dirname, names):
        projs += [os.path.join(dirname, name) for name in names if name.endswith(".uvprojx")]

    #walkcb(projs, root, os.listdir(root)) # do the root first
    for d in os.listdir(root):
        d = os.path.join(root, d)
        if os.path.isdir(d) and os.path.basename(d) != ".git":
            os.path.walk(d, walkcb, projs)
    return projs



