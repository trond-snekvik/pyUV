" Vim compiler file
" Compiler:	pyUV
" Maintainer:	Trond Snekvik
" Last Change:	2016 June 12

let current_compiler = "uv"
let s:scriptDir = expand('<sfile>:p:h')
echom s:scriptDir

let &l:makeprg='python ' . s:scriptDir . '\..\plugin\build.py'

setlocal errorformat=
    \%W\"%f\"\\,\ line\ %l:\ %tarning:\ \ #%n-D:\ %m,
    \%E\"%f\"\\,\ line\ %l:\ %trror:\ \ #%n:\ %m,
    \%-DChanging\ directory\ to\ %f,
    \%Z\ \ \ \ %p,
    \%C\ %.%#,
    \%-G%.%#
