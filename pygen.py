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
        sys.stdout.write(colorama.Fore.GREEN + output + colorama.Style.RESET_ALL)

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
        out += "\t\tIncludes:\n"
        for d in self.includedirs:
            out += "\t\t\t" + d + "\n"
        out += "\t\tOutput: " + os.path.join(self.cwd, self.outputdir, self.outputname + ".hex") + "\n"
        out += "\t\tOptions: "
        for o in self.compileroptions:
            out += o + " "
        out += "\n"
        out += "\t\tDefines:\n"
        for d in self.defines:
            out += "\t\t\t" + d + "\n"
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


if __name__ == "__main__":
    colorama.init()
    root = findroot(".")
    projects = findUVprojects(root)
    while True:
        for (i,p) in enumerate(projects):
            liststr = str(i + 1) + ": " + os.path.basename(p).split(".")[0]
            liststr += (40 - len(liststr)) * " "
            liststr += colorama.Fore.BLUE + "(" + os.path.relpath(p, root) + ")" + colorama.Style.RESET_ALL
            print liststr
        choice = -1
        while choice < 0 or choice > len(projects):
            sys.stdout.write("Select a valid project: ")
            choice = int(sys.stdin.readline())

        p = Project()
        p.parseUV(projects[choice - 1])
        for (i, target) in enumerate(p.targets):
            print str(i + 1) + ": " + target.name
        choice = -1
        while choice < 0 or choice > len(p.targets):
            sys.stdout.write("Select a valid target: ")
            choice = int(sys.stdin.readline())
        target = p.targets[choice - 1]
        print target.name
        prevchoice = -1
        cont = True
        while cont:
            print 80 * "="
            titlestr = "= " + p.name + " | " + target.name + " ="
            titlestr += (80 - len(titlestr)) * "="
            print titlestr
            print 80 * "="
            tasks = ["build", "clean", "print", "back", "quit"]
            for (i, task) in enumerate(tasks):
                print str(i + 1) + ": " + task
            choice = -1
            while choice < 0 or choice > len(tasks):
                print "What do you want to do?"
                instr = sys.stdin.readline()
                if not instr or len(instr) is 1:
                    choice = prevchoice
                else:
                    choice = int(instr)
            prevchoice = choice
            task = tasks[choice - 1]
            if task == "build":
                target.build(ToolchainARMCC("C:\\Keil_v5\\ARM\\ARMCC\\"))
            elif task == "clean":
                if not os.path.exists(os.path.join(target.cwd, target.outputdir)):
                    print "Clean failed: Outputdir already cleaned."
                else:
                    try:
                        for f in os.listdir(os.path.join(target.cwd, target.outputdir)):
                            if f.endswith(".o") or f.endswith(".elf"):
                                os.remove(os.path.join(target.cwd, target.outputdir, f))
                        print "Successfully cleaned target " + target.name
                    except OSError as e:
                        print "Clean failed:"
                        print e
            elif task == "print":
                print str(target)
            elif task == "back":
                print "Going back"
                cont = False
            elif task == "quit":
                exit()

