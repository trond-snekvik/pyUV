import pygen
import subprocess
import os
import sys
import colorama
from toolchain_armcc import *
import hashlib
import binascii
import json
import session
import nrfmultiprog

root = ""

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

def task_build(target, session):
    target.build(ToolchainARMCC("C:\\Keil_v5\\ARM\\ARMCC\\"))

def task_clean(target, session):
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

def task_print(target, session):
    print str(target)

def task_flash(target, session):
    hexfile = os.path.join(target.cwd, target.outputdir, target.outputname + ".hex")
    if os.path.exists(hexfile):
        devfilter = None
        if "filter" in session:
            devfilter = session["filter"]
        out = nrfmultiprog.program(hexfile, devfilter)
    else:
        print("ERROR: Invalid hex file " + hexfile)

def task_set_device(_, session):
    sys.stdout.write("Set device filter: ")
    session["filter"] = sys.stdin.readline().splitlines()[0]
    if len(gFilter) is 0:
        session.pop("filter")
        print("Device filter disabled.")
    else:
        print("Filter is " + session["filter"])

def task_not_available(_,__):
    print("Not available.")

def task_edit_defines(target, session):
    pass

def task_edit_sourcefiles(target, session):
    global root
    groups = {}
    for group in target.groups:
        groups[group.name] = group
    while True:
        groupoptions = groups.keys()
        groupoptions.append("CANCEL")
        choice = select(groupoptions, "Select a source group: ")
        if choice is len(groups):
            break
        group = groups.items()[choice][1]
        print("GROUP " + group.name)

        while True:
            tasks = ["add", "remove", "print", "back"]
            task = tasks[select(tasks, "Action: ")]
            if task == "add":
                sys.stdout.write("Path (relative to root): ")
                path = os.path.normpath(os.path.join(root, sys.stdin.readline().splitlines()[0]))
                if not os.path.exists(path):
                    print(colorama.Fore.RED + "Invalid path " + path + colorama.Style.RESET_ALL)
                else:
                    group.files.append(pygen.SourceFile(path))
                    print("File " + path + " added.")
            elif task == "remove":
                files = {}
                for f in group.files:
                    files[f.name] = f
                f = files.items()[select(files.keys(), "Select a file: ")][1]
                group.files.remove(f)
                print("Removed " + f.name)
            elif task == "print":
                print("Group \"" + group.name + "\"")
                for f in group.files:
                    print("\t" + os.path.relpath(f.path, root))
            else:
                target.saveGroup(group)
                break



def task_edit(target, session):
    tasks = {"includes": task_not_available,
        "defines": task_not_available,
        "source files": task_edit_sourcefiles,
        "regions": task_not_available}
    tasks.items()[select(tasks.keys(), "Edit what? ")][1](target, session)



def select(optlist, query="", default = -1):
    for (i, option) in enumerate(optlist):
        if i == default:
            liststr = ">"
        else:
            liststr = " "
        liststr += str(i + 1) + ": " + option
        print liststr
    choice = -1
    while choice < 0 or choice > len(optlist):
        sys.stdout.write(query)
        try:
            choicestr = sys.stdin.readline()
            if len(choicestr.splitlines()[0]) == 0 and default >= 0:
                return default
            choice = int(choicestr)
        except ValueError:
            choice = -1
    print("")
    return choice - 1


if __name__ == "__main__":
    global root
    colorama.init()
    root = pygen.findroot(".")
    session = session.Session(root)
    # load settings
    if len(session.options) > 0:
        print "Session loaded:"
        for option in session:
            print option + ": " + session[option]

    if not "project" in session:
        projects = pygen.findUVprojects(root)
    while True:
        maxlen = 0
        p = pygen.Project()

        if not "project" in session:
            for proj in projects:
                baselen = len(os.path.basename(proj).split(".")[0])
                if baselen > maxlen:
                    maxlen = baselen
            projlist = []
            for proj in projects:
                liststr = os.path.basename(proj).split(".")[0]
                liststr += (maxlen + 5 - len(liststr)) * " "
                liststr += colorama.Fore.CYAN + "(" + os.path.relpath(proj, root) + ")" + colorama.Style.RESET_ALL
                projlist.append(liststr)
            session["project"] = projects[select(projlist, "Select a valid project: ")]
            session.pop("target")

        p.parseUV(session["project"])

        if not "target" in session or not session["target"] in [t.name for t in p.targets]:
            target = p.targets[select([target.name for target in p.targets], "Select a valid target: ")]
            session["target"] = target.name
            print target.name
        else:
            for t in p.targets:
                if session["target"] == t.name:
                    target = t
                    break
        cont = True
        prevchoice = -1
        while cont:
            print colorama.Fore.CYAN + 80 * "="
            titlestr = "= " + p.name + " | " + target.name + " ="
            titlestr += (80 - len(titlestr)) * "="
            print titlestr
            print 80 * "=" + colorama.Style.RESET_ALL

            tasks = ["build", "clean", "print", "set device filter", "flash", "edit", "back", "quit"]
            functions = {"build": task_build, "clean": task_clean, "print": task_print, "flash": task_flash, "set device filter": task_set_device, "edit": task_edit}
            prevchoice = select(tasks, "What's next? ", prevchoice)
            task = tasks[prevchoice]
            if task in functions.keys():
                functions[task](target, session)
            elif task == "back":
                print "Going back"
                print colorama.Fore.CYAN + 80 * "=" + colorama.Style.RESET_ALL
                cont = False
                session.pop("project")
                session.pop("target")
            elif task == "quit":
                exit()

