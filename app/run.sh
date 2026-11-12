#!/bin/sh
# Sem exec: grava o codigo de saida em bin/cadcli.exit para o oraculo distinguir saida normal (0) de queda.
cd "$(dirname "$0")/.." && rm -f bin/cadcli.exit && { COB_SCREEN_EXCEPTIONS=Y COB_SCREEN_ESC=Y ./bin/cadcli; echo $? > bin/cadcli.exit; }
