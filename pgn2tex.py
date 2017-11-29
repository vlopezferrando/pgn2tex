#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import sys

import chess.pgn

nags = dict(zip(range(1, 7), ['!', '?', '!!', '??', '!?', '?!']))

tex = """
\\documentclass[10pt,DIV=20,twocolumn]{scrreprt}
\\usepackage{chessboard,xskak}
\\usepackage{latexsym}
\\usepackage[utf8]{inputenc}
\\usepackage{graphicx}
\\usepackage{xcolor}
\\usepackage[margin=0.5in]{geometry}

%%\\setlength{\\parskip}{1em}
%%\\setlength{\\leftskip}{2em}
%%\\setlength{\\parindent}{-2em}
\\setlength{\\parindent}{0cm}

\\definecolor{var0}{HTML}{1B6031}
\\definecolor{var1}{HTML}{601b28}
\\definecolor{var2}{HTML}{541b60}

\\definecolor{var3}{HTML}{0d0d4b}
\\definecolor{var4}{HTML}{4b2c0d}
\\definecolor{var5}{HTML}{0d4b4b}

\\begin{document}
\\newgame
GAME
\\end{document}
"""

NUM_COLOR = 0


def diagram(node, scale=None, position='center'):
    if not scale:
        if node.is_main_line():
            scale = 0.95
        else:
            scale = 0.8
    # Black point of view: \chessboard[inverse]
    # markmoves={a1-c3, b7-c6}
    # pgfstyle=circle, markfields=g1
    return '\\begin{%s}\\scalebox{%f}{\\chessboard[setfen=%s,vmarginwidth=.3em]}\\vspace{1ex}\\end{%s}\n' % (
                position, scale, node.board().fen(), position)


def format_line(line, level):
    if len(line) == 0:
        return ''
    ret = '\\par\n\\%s{%s }' % (
        'mainline' if line[0].is_main_line() else 'variation',
        line[0].parent.board().variation_san([n.move for n in line])
        if line[0].parent else '')
    # Posat els nags
    if len(line[0].nags):
        n = ''.join([nags[n] for n in line[0].nags])
        if '...' in ret:
            ret = re.sub(' ', n + ' ', ret, 1)
        else:
            ret = re.sub(r'^((.*? .*?){1}) ', r'\1%s ' % n, ret)
    if hasattr(line[-1], 'has_diagram'):
        ret += '\\textit{(D)}'
    if line[-1].comment:
        ret += ' %s\n' % line[-1].comment
    ret = '\\begin{addmargin}[%dem]{0cm}%s\\end{addmargin}' % (2*level, ret)
    return ret


def format_nodes(nodes, level):
    ret = ''
    line = []
    for node in nodes:
        line.append(node)
        if node.comment:
            ret += format_line(line, level)
            line = []
    ret += format_line(line, level)
    return ret


def parse(node, level):
    if node.is_end():
        return ''

    # Fer la llista de nodes que no tenen variants
    nodes = []
    while len(node.variations) == 1 and not node.is_end():
        nodes.append(node)
        node = node.variations[0]
    nodes.append(node)
    if node.variations:
        nodes.append(node.variations[0])

    # Escriure el contingut d'aquesta llista
    # Escriure per separat l'últim si després ve un diagrama amb variants
    # Posar un diagrama si hi haurà variants
    if node.variations:
        nodes[-1].has_diagram = True
        ret = format_nodes(nodes[:-1], level) + \
            format_nodes([nodes[-1]], level) + \
            diagram(node.variations[0])
    else:
        ret = format_nodes(nodes, level)
        ret += diagram(node, scale=0.5, position='flushright')

    # Escriure cada variant
    for i, var in enumerate(node.variations[1:]):
        if True:  # node.is_main_line():
            global NUM_COLOR
            ret += '{\\color{var%d}' % (NUM_COLOR % 6)
            NUM_COLOR += 1
        ret += parse(var, level+1)
        if True:  # node.is_main_line():
            ret += '}'

    # Escriure la continuació de la línia original
    if node.variations and node.variations[0].variations:
        ret += parse(node.variations[0].variations[0], level)
    return ret


if __name__ == "__main__":
    pgn_fname = sys.argv[1]
    pgn = open(sys.argv[1])
    out = re.sub(r'pgn$', 'tex', pgn_fname)

    games_tex = ''
    while True:
        NUM_COLOR = 0
        game = chess.pgn.read_game(pgn)
        if not game:
            break
        games_tex += '\\chapter*{%s}\n\\newgame\n' % game.headers['Event']
        games_tex += parse(game, level=0)

    with open(out, 'w') as fout:
        print(tex.replace('GAME', games_tex), file=fout)

# Options
# number-variations
# use-colors
# indent-variations
# flip-board
# arrow-last-move
# diagrams-end-variation
# diagram-variations-root
