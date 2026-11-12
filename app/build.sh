#!/bin/sh
# -Wno-builtin-macro-redefined: o cobc da distro passa -D_FORTIFY_SOURCE=2 e o gcc ja define 3 (aviso inofensivo do toolchain)
cd "$(dirname "$0")/.." && mkdir -p bin && \
COB_CFLAGS="$(cobc --info | sed -n 's/^COB_CFLAGS *: //p') -Wno-builtin-macro-redefined" cobc -x -free -o bin/cadcli app/cadcli.cbl
