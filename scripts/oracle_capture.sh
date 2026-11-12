#!/usr/bin/env bash
# Tela do oraculo: exatamente 24 linhas, sem espacos a direita.
set -euo pipefail
tmux -L cadcli capture-pane -p -t cadcli | sed 's/[[:space:]]*$//' | head -n 24 | awk '{print} END{for(i=NR;i<24;i++)print ""}'
