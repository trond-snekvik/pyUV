fu! UV#Selected()
endf
fu! UV#Select(opt)
endf
"import vimUV, need to do some trickery to add the directory to path first.
let g:uvpydir= fnamemodify(resolve(expand('<sfile>:p')), ':h')
python << EOPY
import sys
import vim
import os

plugindir = os.path.abspath(vim.eval('g:uvpydir'))
if not plugindir in sys.path:
    sys.path.append(plugindir)
# now safe to import our module
import vimUV
import session
EOPY

fu! UV#Selected()
    let g:UV#sel#sel = line(".") - 1

    py vimUV.selected()

    q!
    if g:UV#sel#opt == "project"
        py vimUV.seltarget()
    else
        call UVupdateAirline()
    endif
endf

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
fu! UV#Select(opt)
    new
    let g:UV#sel#opt = a:opt
    setlocal hidden
    setlocal buftype=nofile
    "setlocal bufhidden=hide
    setlocal noswapfile
    setlocal nobuflisted
    setlocal cursorline
    setlocal colorcolumn=999
    setlocal nowrap
    nnoremap <buffer> <silent> <CR> :call UV#Selected()<CR>
    nnoremap <buffer> <silent> <Esc> :q!<CR>
    au BufLeave <buffer> :q! | :call UVupdateAirline()

endf

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
fu! UV#SelProj() " Select a project and target to use
    py vimUV.selproj()
endf

fu! UV#SelTarget() " Select a target within current project
    py vimUV.seltarget()
endf

let g:uv_focus_gained = 1
fu! UVupdateAirline()
    py vimUV.getsession()
    if (exists('g:uvproject') && exists('g:uvtarget'))
        let g:airline_section_b = airline#section#create_left([g:uvproject, g:uvtarget])
        AirlineRefresh
    :endif
endfunction

fu! UVsetdevicefilter(filter)
    py vimUV.s["filter"]= vim.eval("a:filter")
endfunction

fu! UVfocusGained()
    if g:uv_focus_gained
        call UVupdateAirline()
        let g:uv_focus_gained=0
    endif
endf

au FocusGained *.c,*.h :call UVfocusGained()
au FocusLost *.c,*.h :let g:uv_focus_gained=1

com -nargs=1 UVfilter :call UVsetdevicefilter(<args>)
