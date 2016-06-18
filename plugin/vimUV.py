import os
import sys
import vim
import session
import pygen

root = pygen.findroot(".")
s = session.Session(root)

def selproj():
    print("Finding projects from " + root + "...")
    projs = pygen.findUVprojects(root)
    bufsize = min(len(projs) + 1, 10)
    if len(projs) is 0:
        print("No UV projects found...")
        return
    #vim.command("echo \"" + str(len(projs)) + " found.\"")
    vim.command("call UV#Select(\"project\")\n")
    projs = [(os.path.basename(proj), proj) for proj in projs]
    maxnamelen = len(max(projs, key = lambda p: len(p[0]))[0])
    for p in projs:
        vim.current.buffer.append(p[0] + " " * (maxnamelen + 2 - len(p[0])) + "(" + os.path.relpath(p[1], root) + ")")
    vim.command("resize " + str(bufsize))
    #the first line is now empty
    vim.current.buffer[0] = None
    vim.command("setlocal nomodifiable")

def seltarget():
    if not "project" in s:
        print("No project selected...")
        return
    project = pygen.Project()
    project.parseUV(s["project"])
    if len(project.targets) is 0:
        print("No targets found...")
        return
    vim.command("call UV#Select(\"target\")")
    for t in project.targets:
        vim.current.buffer.append(t.name)
    vim.command("resize " + str(len(project.targets) + 1))
    #the first line is now empty
    vim.current.buffer[0] = None
    vim.command("setlocal nomodifiable")

def selected():
    option = vim.eval("g:UV#sel#opt")
    selected = vim.eval("g:UV#sel#sel")
    if option == "project":
        selected = pygen.findUVprojects(root)[int(selected)]
        s.pop("target")
    if option == "target":
        project = pygen.Project()
        project.parseUV(s["project"])
        selected = project.targets[int(selected)].name
    s[option] = selected

def getsession():
    if "project" in s:
        vim.command("let g:uvproject=\"" + os.path.basename(s["project"]).split(".")[0] + "\"")
    else:
        vim.command("let g:uvproject=\"?\"")
    if "target" in s:
        vim.command("let g:uvtarget=\"" + s["target"] + "\"")
    else:
        vim.command("let g:uvtarget=\"?\"")
