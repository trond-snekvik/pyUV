"""
Toolchain prototype
"""

import subprocess
import os.path
import exceptions
import sys

class Toolchain:
    def __init__(self, name):
        self.name = name
        self.includedirs = []
        self.cflags = []
        self.asmflags = []
        self.linkflags = []
        self.objcopyflags = []
        self.linkerfileext = ""
        self.options = {}
        self.CC = None
        self.AS = None
        self.AR = None
        self.LD = None
        self.NM = None
        self.OBJCOPY = None
        self.SIZE = None

    def compile(self, target, sourcefile, verbose=False):
        """
        Compile a single source file.
        Returns a tuple of (Success (True/False), output)
        """
        output = ""
        language = sourcefile.language()
        if language is "c":
            args = [self.CC] + self.cflags
            args += target.compileroptions
            for d in target.defines:
                args.append("-D" + d)
        elif language is "asm":
            args = [self.AS] + self.asmflags
        else:
            return (False, "Unsupported language " + language)

        for i in self.includedirs:
            args.append("-I"+i)

        for i in target.includedirs:
            args.append("-I"+i)
        args.append("-o")
        args.append(os.path.join(target.outputdir, sourcefile.name.split(".")[0] + ".o"))
        args.append(sourcefile.path)

        if verbose:
            verbosestring = ""
            for a in args:
                verbosestring += a + " "
            sys.stdout.write(verbosestring + "\n")
        else:
            sys.stdout.write("compiling " + sourcefile.name + "...\n")

        out = ""
        #try:
        popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=target.cwd)
        (out,err) = popen.communicate()
        if popen.returncode != 0:
            return (False, err)
        #except Exception as e:
        #    print args
        #    return (False, e)
        return (True, out)

    def link(self, target, verbose = False):
        """
        Link the given target.
        Returns a tuple (Status (True/False), output)
        """
        objects = []
        for group in target.groups:
            for sourcefile in group.files:
                obj = os.path.join(target.outputdir, sourcefile.name.split(".")[0] + ".o")
                if not os.path.exists(obj):
                    return (False, "Unable to locate " + obj + ". Fix builderrors and recompile.")
                objects.append(obj)
        args = [self.LD] + self.linkflags + objects
        if self.options["map"]:
            args.append(self.options["map"])
            args.append(os.path.join(target.outputdir, target.outputname + ".map"))
        if self.options["linker"]:
            args.append(self.options["linker"])
            args.append(os.path.join(target.outputdir, target.outputname + "." + self.linkerfileext))
        args.append("-o")
        args.append(os.path.join(target.outputdir, target.outputname + ".elf"))

        if verbose:
            verbosestring = ""
            for a in args:
                verbosestring += a + " "
            sys.stdout.write(verbosestring + "\n")
        else:
            sys.stdout.write("linking target " + target.name + "...\n")

        popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=target.cwd)
        (out,err) = popen.communicate()

        if popen.returncode != 0:
            return (False, err)

        return (True, err)

    def toHex(self, target, elf):
        """
        Generate hex-file from elf.
        returns (Success (True/False), output)
        """
        raise NotImplementedError("Generic toolchain class does not implement toHex(). Please specify a toolchain.")

    def scatterGen(self, target):
        """
        Generate content text for a scatterfile for the given target.
        returns (Success (True/False), scatterfile text)
        """
        raise NotImplementedError("Generic toolchain class does not implement scatterGen(). Please specify a toolchain.")

