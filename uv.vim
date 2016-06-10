fu! UV#Selected()
    echo g:UV#sel#opt . ': ' . getline(".")
    let g:UV#sel#sel = line(".") - 1
python << EOPY
import vim
import session
import pygen

root = pygen.findroot(".")
s = session.Session(root)
option = vim.eval("g:UV#sel#opt")
selected = vim.eval("g:UV#sel#sel")
if option == "project":
    selected = pygen.findUVprojects(root)[int(selected)]
if option == "target":
    project = pygen.Project()
    project.parseUV(s["project"])
    selected = project.targets[int(selected)].name
s[option] = selected
EOPY

    hi! link CursorLine NONE
    hi! link Cursor NONE
    q!
    if g:UV#task == "build"
        call UV#Build()
    endif

:endfunction

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
fu! UV#Select(opt)
    new
    let g:UV#sel#opt = a:opt
    setlocal hidden
    setlocal cursorline
    setlocal colorcolumn=999
    hi! link CursorLine Visual
    hi! link Cursor Visual
    nnoremap <buffer> <silent> <CR> :call UV#Selected()<CR>
    nnoremap <buffer> <silent> <Esc> :q!<CR>
    au BufLeave <buffer> :q!


:endfunction

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
fu! UV#Forget()
python << EOPY
import session
import pygen

root = pygen.findroot(".")
s = session.Session(root)
s.delete()
EOPY
:endfunction

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
fu! UV#Build()
    let g:UV#task = "build"
python << EOPY
import session
from toolchain_armcc import *
import pygen
import vim
import os

def build():
    root = pygen.findroot(".")
    s = session.Session(root)
    if "project" in s:
        project = pygen.Project()
        project.parseUV(s["project"])
        if "target" in s:
            for t in project.targets:
                if t.name == s["target"]:
                    target = t
                    break
            target.build(ToolchainARMCC("C:\\Keil_v5\\ARM\\ARMCC"))
        else:
            if len(project.targets) is 0:
                print("No targets found...")
                return
            vim.command("call UV#Select(\"target\")")
            for t in project.targets:
                vim.current.buffer.append(t.name)
            vim.command("resize " + str(len(project.targets) + 1))

            #the first line is now empty
            vim.current.buffer[0] = None

    else:
        projs = pygen.findUVprojects(root)
        bufsize = min(len(projs) + 1, 10)
        if len(projs) is 0:
            print("No UV projects found...")
            return
        vim.command("call UV#Select(\"project\")")
        projs = [(os.path.basename(proj), proj) for proj in projs]
        maxnamelen = len(max(projs, key = lambda p: len(p[0]))[0])
        for p in projs:
            vim.current.buffer.append(p[0] + " " * (maxnamelen + 2 - len(p[0])) + "(" + os.path.relpath(p[1], root) + ")")
        vim.command("resize " + str(bufsize))

        #the first line is now empty
        vim.current.buffer[0] = None

build()

EOPY

:endfunction

