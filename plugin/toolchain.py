"""
Toolchain prototype
"""

import subprocess
import os.path
import exceptions
import sys
import colorama

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

    def compile(self, target, sourcefiles, verbose=False):
        """
        Compile a single source file.
        Returns a tuple of (Success (True/False), output)
        """
        retval = True
        output = ""

        # force argument to become a list
        if sourcefiles.__class__ != list:
            sourcefiles = [sourcefiles]

        for sourcefile in sourcefiles:
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
            args.append(os.path.relpath(sourcefile.path, target.cwd))

            if verbose:
                verbosestring = ""
                for a in args:
                    verbosestring += a + " "
                output = verbosestring
            else:
                output = "Compiling " + sourcefile.name + "...\n"

            #try:
            popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=target.cwd)
            (out,err) = popen.communicate()
            if popen.returncode != 0:
                retval = False
            if len(err) > 0:
                output += err
            elif len(out) > 0:
                output += out
        #except Exception as e:
        #    print args
        #    return (False, e)
        return (retval, output)

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
            args.append(os.path.join(os.path.relpath(target.outputdir, target.cwd), target.outputname + ".map"))
        if self.options["linker"]:
            args.append(self.options["linker"])
            args.append(os.path.join(os.path.relpath(target.outputdir, target.cwd), target.outputname + "." + self.linkerfileext))
        args += target.linkeroptions
        args.append("-o")
        args.append(os.path.join(os.path.relpath(target.outputdir, target.cwd), target.outputname + ".elf"))

        if verbose:
            verbosestring = ""
            for a in args:
                verbosestring += a + " "
            sys.stdout.write(verbosestring + "\n")
        else:
            sys.stdout.write("Linking target " + target.name + "...\n")

        popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=target.cwd)
        (out,err) = popen.communicate()

        if popen.returncode != 0:
            return (False, err)

        return (True, err)

    def genDepList(self, target, sourcefile):
        """
        Generate a list of paths upon which the given file depends on.
        returns a list of absolute paths.
        """
        raise NotImplementedError("Generic toolchain class does not implement genDepList(). Please specify a toolchain.")

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

