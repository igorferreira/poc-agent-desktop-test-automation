#!/bin/sh
cd "$(dirname "$0")/.." && mkdir -p data && cp app/seed/clientes.dat data/clientes.dat
