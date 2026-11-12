#!/usr/bin/env bash
# Encerra so a sessao cadcli do socket cadcli.
tmux -L cadcli kill-session -t cadcli 2>/dev/null || true
