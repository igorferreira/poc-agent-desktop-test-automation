#!/usr/bin/env python3
"""Tela falsa 80x24 para as sondagens P2-P8. Sai com Ctrl+Q; F3 so e registrado."""
import curses
import os

TEXTO = [
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789",
    "O RAPIDO RAPOSA MARROM PULA SOBRE O CAO PREGUICOSO.",
    "CODIGO 000123  NOME: MARIA DA SILVA  CPF: 11111111111",
    "CIDADE: RIO DE JANEIRO  UF: RJ  CEP 20000-000",
    "VALOR: R$ 1.234,56  DESCONTO: 10%  TOTAL: 1.111,10",
    "DATA: 12/11/2026  HORA: 08:30:45  LOTE #7 (A/B)",
    "0O0O 1IL1 5S5S 8B8B 2Z2Z  OCR: 0123456789 OIL",
    "PONTUACAO: . , ; : ! ? - _ + = * / \\ | < > ( ) [ ] { }",
    "ASPAS: ' \" `  E COMERCIAL & ARROBA @ CIFRAO $ TIL ~ ^",
    "SAO PAULO / SP - AV. PAULISTA, 1000 - BELA VISTA",
    "JOAO PEREIRA  22222222222  SAO PAULO  SP",
    "LINHA 11: THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
    "LINHA 12: 1234567890 0987654321 1357924680 2468013579",
    "LINHA 13: AAAA BBBB CCCC DDDD EEEE FFFF GGGG HHHH",
    "LINHA 14: IIII JJJJ KKKK LLLL MMMM NNNN OOOO PPPP",
    "LINHA 15: QQQQ RRRR SSSS TTTT UUUU VVVV WWWW XXXX",
    "LINHA 16: YYYY ZZZZ 0000 1111 2222 3333 4444 5555",
    "FIM DO TEXTO FIXO DE SONDAGEM.",
]
NOMES = {
    9: "TAB", 10: "ENTER", 13: "ENTER", 27: "ESC", 32: "SPACE",
    curses.KEY_ENTER: "ENTER", curses.KEY_BACKSPACE: "BACKSPACE", 127: "BACKSPACE", 8: "BACKSPACE",
    curses.KEY_UP: "UP", curses.KEY_DOWN: "DOWN", curses.KEY_LEFT: "LEFT", curses.KEY_RIGHT: "RIGHT",
}
for n in range(1, 13):
    NOMES[curses.KEY_F0 + n] = f"F{n}"


def desenha(scr, buf, teclas, ultima):
    scr.erase()
    scr.addstr(0, 1, "CADCLI")
    scr.addstr(0, 30, "TELA FALSA DE SONDAGEM")
    scr.addstr(0, 77, "T00")
    for i, t in enumerate(TEXTO):
        scr.addstr(2 + i, 0, t[:80])
    scr.addstr(20, 0, ("ENTRADA: " + buf)[-79:])
    scr.addstr(21, 0, "TECLAS: " + " ".join(teclas)[-71:].lstrip())
    scr.addstr(22, 0, " F3=SAIR")
    scr.addstr(23, 0, ("ULTIMA: " + ultima)[:79])
    scr.refresh()


def main(scr):
    curses.raw()  # Ctrl+Q/Ctrl+S chegam como teclas, sem controle de fluxo
    scr.keypad(True)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    scr.bkgd(" ", curses.color_pair(1))
    buf, teclas, ultima = "", [], ""
    while True:
        desenha(scr, buf, teclas, ultima)
        k = scr.getch()
        if k == 17:  # Ctrl+Q
            return
        if k in NOMES:
            nome = NOMES[k]
            if nome == "BACKSPACE":
                buf = buf[:-1]
            elif nome == "SPACE":
                buf += " "
            if nome != "SPACE":
                teclas = (teclas + [nome])[-30:]
        elif 33 <= k <= 126:
            buf += chr(k)
            nome = chr(k)
        else:
            continue
        ultima = nome
        buf = buf[-70:]


if __name__ == "__main__":
    os.environ.setdefault("ESCDELAY", "25")
    curses.wrapper(main)
