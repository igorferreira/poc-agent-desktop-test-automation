#!/bin/sh
cd "$(dirname "$0")/.." && COB_SCREEN_EXCEPTIONS=Y COB_SCREEN_ESC=Y exec ./bin/cadcli
