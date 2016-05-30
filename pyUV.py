import pygen
import subprocess
import os
import sys
import colorama
from toolchain_armcc import *
import hashlib
import binascii
import json

gFilter = ""
tempstore = ""
gProject = ""
gTarget = ""

def store(dictionary):
    j = None
    if os.path.exists(tempstore):
        with open(tempstore, "r") as f:
            j = json.load(f)
    if j:
        j.update(dictionary)
        with open(tempstore, "w") as f:
            json.dump(j, f)
    else:
        with open(tempstore, "w") as f:
            f.write(json.JSONEncoder().encode(dictionary))

def task_build(target):
    target.build(ToolchainARMCC("C:\\Keil_v5\\ARM\\ARMCC\\"))

def task_clean(target):
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

def task_print(target):
    print str(target)

def task_flash(target):
    hexfile = os.path.join(target.cwd, target.outputdir, target.outputname + ".hex")
    if os.path.exists(hexfile):
        args = ["C:\\Users\\trsn\\bin\\prog.bat", hexfile]
        if gFilter != "":
            args += ["-s", gFilter]
        subprocess.call(args)
    else:
        print("ERROR: Invalid hex file " + hexfile)

def task_set_device(_):
    sys.stdout.write("Set device filter: ")
    gFilter = sys.stdin.readline().splitlines()[0]
    if len(gFilter) is 0:
        gFilter = ""
        print("Device filter disabled.")
    else:
        print("Filter is " + gFilter)
    store({"filter": gFilter})

if __name__ == "__main__":
    colorama.init()
    root = pygen.findroot(".")
    h = hashlib.new("SHA1")
    h.update(root)
    tempstore = os.path.join(os.environ["TEMP"], binascii.hexlify(h.digest())[:16] + ".json")
    # load settings
    if os.path.exists(tempstore):
        with open(tempstore, "r") as f:
            options = json.load(f)
            print "Session loaded:"
            for key in options.keys():
                if len(key) > 0 and len(options[key]) > 0:
                    print key + ": " + options[key]
            if "project" in options.keys():
                gProject = options["project"]
            if "target" in options.keys():
                gTarget = options["target"]
            if "filter" in options.keys():
                gFilter = options["filter"]


    projects = pygen.findUVprojects(root)
    while True:
        maxlen = 0
        p = pygen.Project()

        if gProject == "":
            for proj in projects:
                baselen = len(os.path.basename(proj).split(".")[0])
                if baselen > maxlen:
                    maxlen = baselen
            for (i,proj) in enumerate(projects):
                liststr = str(i + 1) + ": " + os.path.basename(proj).split(".")[0]
                liststr += (maxlen + 5 - len(liststr)) * " "
                liststr += colorama.Fore.CYAN + "(" + os.path.relpath(proj, root) + ")" + colorama.Style.RESET_ALL
                print liststr
            choice = -1
            while choice < 0 or choice > len(projects):
                sys.stdout.write("Select a valid project: ")
                try:
                    choice = int(sys.stdin.readline())
                except ValueError:
                    choice = -1
            gProject = projects[choice - 1]
            store({"project": gProject})

        p.parseUV(gProject)

        if gTarget == "" or not gTarget in [t.name for t in p.targets]:
            for (i, target) in enumerate(p.targets):
                print str(i + 1) + ": " + target.name
            choice = -1
            while choice < 0 or choice > len(p.targets):
                sys.stdout.write("Select a valid target: ")
                try:
                    choice = int(sys.stdin.readline())
                except ValueError:
                    choice = -1
            target = p.targets[choice - 1]
            gTarget = target.name
            store({"target": gTarget})
            print target.name
        else:
            for t in p.targets:
                if gTarget == t.name:
                    target = t
                    break
        prevchoice = -1
        cont = True
        while cont:
            print colorama.Fore.CYAN + 80 * "="
            titlestr = "= " + p.name + " | " + target.name + " ="
            titlestr += (80 - len(titlestr)) * "="
            print titlestr
            print 80 * "=" + colorama.Style.RESET_ALL
            tasks = ["build", "clean", "print", "set device filter", "flash", "back", "quit"]
            functions = {"build": task_build, "clean": task_clean, "print": task_print, "flash": task_flash, "set device filter": task_set_device}
            for (i, task) in enumerate(tasks):
                print str(i + 1) + ": " + task
            choice = -1
            while choice < 0 or choice > len(tasks):
                sys.stdout.write("What's next? ")
                instr = sys.stdin.readline()
                if not instr or len(instr) is 1:
                    choice = prevchoice
                else:
                    try:
                        choice = int(instr)
                    except ValueError:
                        choice = -1
            prevchoice = choice
            task = tasks[choice - 1]
            if task in functions.keys():
                functions[task](target)
            elif task == "back":
                print "Going back"
                cont = False
                gProject = ""
                gTarget = ""
            elif task == "quit":
                exit()

