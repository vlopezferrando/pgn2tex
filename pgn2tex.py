#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
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
\\setlength{\\columnsep}{1cm}

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

\\newcommand\\N[1]{%%
  \\noindent
  \\makebox[0pt][r]{\\makebox[1cm][l]{\\textbf{#1}}}%%
  \\hspace*{\\parindent}\\ignorespaces}

\\begin{document}
\\newgame
GAME
\\end{document}
"""

NUM_COLOR = 0


def diagram(node, args, scale=None, position='center'):
    if not scale:
        if node.is_main_line():
            scale = 0.95
        else:
            scale = 0.8
    # markmoves={a1-c3, b7-c6}
    # pgfstyle=circle, markfields=g1
    # Mark last move if chosen
    move = ',pgfstyle=straightmove,markmoves={%s-%s}' % (
        chess.SQUARE_NAMES[node.move.from_square],
        chess.SQUARE_NAMES[node.move.to_square]) if args.arrow_last_move else ''

    # Get moves
    p = re.compile(r'\[%cal ([\w,]*)\]')
    m = p.search(node.comment)
    colors = {'G': 'green', 'R': 'red'}
    if m:
        arrows = m.group(1).split(',')
        move += ',pgfstyle=straightmove'
        for arrow in arrows:
            move += ',color=' + colors[arrow[0]]
            move += ',markmoves={%s-%s}' % (arrow[1:3], arrow[3:5])

    # Mark squares
    p = re.compile(r'\[%csl ([\w,]*)\]')
    m = p.search(node.comment)
    colors = {'G': 'green', 'R': 'red'}
    if m:
        squares = m.group(1).split(',')
        move += ',pgfstyle=circle'
        for square in squares:
            move += ',color=' + colors[square[0]]
            move += ',markfields=' + square[1:]

    # Flip board if chosen
    flip = ',inverse' if args.flip else ''

    # Add if position is right
    if position == 'flushright':
        move += ',color=lightgray!60,colorbackboard'

    return '\\begin{%s}\\scalebox{%f}{\\chessboard[setfen=%s,vmarginwidth=.3em%s%s]}\\vspace{1ex}\\end{%s}\n' % (
                position, scale, node.board().fen(), flip, move, position)


def format_line(line, level, args):
    if len(line) == 0:
        return ''

    # Remove first move if it is empty
    if line[0].move is None:
        line = line[1:]
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
    if line[-1].comment:
        ret += ' %s\n' % re.sub(r'\[%c.*\]', '', line[-1].comment)

    if args.indent_variations:
        ret = '\\begin{addmargin}[%dem]{0cm}%s\\end{addmargin}' % (2*level, ret)
    return ret


def format_nodes(nodes, level, args):
    ret = ''
    line = []
    for node in nodes:
        line.append(node)
        if node.comment:
            ret += format_line(line, level, args)
            line = []

    ret += format_line(line, level, args)
    return ret


def parse(node, level, args):
    if node.is_end():
        return ''

    # Fer la llista de nodes que no tenen variants
    nodes = []
    # TODO: encara hi ha algunes fletxes que no em dibuixa
    while len(node.variations) == 1 and not node.is_end() and '%%cal' not in node.comment and '%%csl' not in node.comment:
        nodes.append(node)
        node = node.variations[0]
    nodes.append(node)

    # Escriure el contingut d'aquesta llista
    # Escriure per separat l'últim si després ve un diagrama amb variants
    # Posar un diagrama si hi haurà variants

    ret = ''

    # If not in the root, add diagram
    if nodes[0].parent is not None:
        ret += diagram(nodes[0], args, scale=0.5)

    ret += format_nodes(nodes, level, args)

    if node.is_end():
        ret += diagram(node, args, scale=0.5, position='flushright')
    else:
        # For each variation
        for i, var in enumerate(node.variations[1:] + [node.variations[0]]):
            # Parse variation
            variant = parse(var, level+1, args)

            # Add variation number if chosen
            if args.number_variations:
                variant = '\\N{%d.%d} %s' % (level, i+1, variant)

            # Set color if chosen and not in main line
            if args.color and i != len(node.variations)-1:
                global NUM_COLOR
                variant = '{\\color{var%d}%s}' % (NUM_COLOR % 6, variant)
                NUM_COLOR += 1

            # Add variation to tex
            ret += variant

    return ret


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pgn", help="PGN file with games and variants")
    parser.add_argument("--number-variations", action='store_true')
    parser.add_argument("--indent-variations", action='store_true')
    parser.add_argument("--arrow-last-move", action='store_true')
    parser.add_argument("--diagrams-start-variation", action='store_true')
    parser.add_argument("--diagrams-end-variation", action='store_true')
    parser.add_argument("--color", help="use different colors for each variation", action='store_true')
    parser.add_argument("--flip", help="print boards from black's perspective", action='store_true')
    args = parser.parse_args()

    # Open PGN
    pgn = open(args.pgn)

    games_tex = ''
    while True:
        NUM_COLOR = 0
        game = chess.pgn.read_game(pgn)
        if not game:
            break
        games_tex += '\\chapter*{%s}\n\\newgame\n' % game.headers['Event']
        games_tex += parse(game, 0, args)

    # Tex output file
    tex_fname = re.sub(r'pgn$', 'tex', args.pgn)
    with open(tex_fname, 'w') as fout:
        print(tex.replace('GAME', games_tex), file=fout)
