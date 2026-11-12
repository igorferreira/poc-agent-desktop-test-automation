#!/usr/bin/env bash
# Sobe a tela falsa na sessao tmux cadcli (socket -L cadcli). Recria se ja existir.
set -euo pipefail
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmux -L cadcli kill-session -t cadcli 2>/dev/null || true
tmux -L cadcli -f /dev/null new-session -d -s cadcli -x 80 -y 24 "python3 '$dir/fake_screen.py'"
tmux -L cadcli set -g status off
