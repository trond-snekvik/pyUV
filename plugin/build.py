import pygen
import session
import toolchain
import toolchain_armcc
import nrfmultiprog
import sys
import os

arguments = [("--project", 1), ("--target", 1)]

def consumearg(arg):
    if not arg in sys.argv:
        return None
    index = sys.argv.index(arg)
    sys.argv.pop(index)
    return sys.argv.pop(index)


if __name__ == "__main__":
    session = session.Session(pygen.findroot())
    sys.argv.pop(0)

    if "--project" in sys.argv:
        projectpath = consumearg("--project")
    elif "project" in session:
        projectpath = session["project"]
    else:
        sys.stderr.write("Error: Please specify a project path!\n");
        exit(1)

    if not os.path.exists(projectpath):
        sys.stderr.write("Error: Project " + projectpath + " not found.\n")
        exit(1)

    project = pygen.Project()
    project.parseUV(projectpath)

    if "--target" in sys.argv:
        targetstr = consumearg("--target")
        target = [t for t in project.targets if t.name == targetstr][0]
    elif "target" in session and len(session["target"]) > 0:
        target = [t for t in project.targets if t.name == session["target"]][0]
    else:
        sys.stderr.write("Error: Please specify a target!\n");
        exit(1)

    clean = False
    if "--clean" in sys.argv:
        clean = True
        sys.argv.pop(sys.argv.index("--clean"))
    if "-c" in sys.argv:
        clean = True
        sys.argv.pop(sys.argv.index("-c"))

    flash = False
    if "--flash" in sys.argv:
        flash = True
        sys.argv.pop(sys.argv.index("--flash"))
    if "-f" in sys.argv:
        flash = True
        sys.argv.pop(sys.argv.index("-f"))


    arm_dir = "C:\\Keil_v5\\ARM"
    latest_arm = [d for d in os.listdir(arm_dir) if "ARMCC" in d][-1]
    toolchain = toolchain_armcc.ToolchainARMCC(os.path.join(arm_dir, latest_arm))
    print("Changing directory to " + os.path.relpath(target.cwd))
    if len(sys.argv) == 0:
        print "Building all..."
        if clean:
            target.clean()
        success = target.build(toolchain)
        if success and flash:
            nrfmultiprog.program(os.path.join(target.cwd, target.outputdir, target.outputname + ".hex"), session["filter"])
    else:
        print(sys.argv)
        files = [f for f in target.allFiles() if f.name in sys.argv]
        print "Building " + str(files)
        print toolchain.compile(target, files)
