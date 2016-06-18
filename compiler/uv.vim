" Vim compiler file
" Compiler:	pyUV
" Maintainer:	Trond Snekvik
" Last Change:	2016 June 12

let current_compiler = "uv"
let s:scriptDir = expand('<sfile>:p:h')

let &makeprg='C:\Python27\python ' . '"' . s:scriptDir . '\..\plugin\build.py"'

setlocal errorformat=
    \%W\"%f\"\\,\ line\ %l:\ %tarning:\ \ #%n-D:\ %m,
    \%E\"%f\"\\,\ line\ %l:\ %trror:\ \ #%n:\ %m,
    \%E\"%f\"\\,\ line\ %l:\ %trror:\ At\ end\ of\ source:\ \ #%n:\ %m,
    \%Z\ \ \ \ %p,
    \%trror:\ L%*[^:]:\ %m,
    \%DChanging\ directory\ to\ %f,
    \%C\ %.%#,
    \%-GBuilding\ %.%#,
    \%-GLinking\ %.%#,
    \%-GCompiling\ %.%#,
    \%-GGenerating\ %.%#,
    \%-G%.%#,

