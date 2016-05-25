import pygen
import os
import sys
import colorama
from toolchain_armcc import *

if __name__ == "__main__":
    colorama.init()
    root = pygen.findroot(".")
    projects = pygen.findUVprojects(root)
    while True:
        maxlen = 0
        for p in projects:
            baselen = len(os.path.basename(p).split(".")[0])
            if baselen > maxlen:
                maxlen = baselen
        for (i,p) in enumerate(projects):
            liststr = str(i + 1) + ": " + os.path.basename(p).split(".")[0]
            liststr += (maxlen + 5 - len(liststr)) * " "
            liststr += colorama.Fore.CYAN + "(" + os.path.relpath(p, root) + ")" + colorama.Style.RESET_ALL
            print liststr
        choice = -1
        while choice < 0 or choice > len(projects):
            sys.stdout.write("Select a valid project: ")
            choice = int(sys.stdin.readline())

        p = pygen.Project()
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

