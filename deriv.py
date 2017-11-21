#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import numpy as np
from argparse import ArgumentParser
from tube_map import tube_map
from utracer_data import utracer_data
from graphing import single_axis_graph, multi_axis_graph
from range import range
import os

def get_args() :
    parser = ArgumentParser(usage='[options] data-filename')
    parser.add_argument('-a', '--Va', type=range, default=None, help='Anode voltage')
    parser.add_argument('-b', '--Eb', type=float, default=0, help='Fixed B+ voltage')
    parser.add_argument('-d', '--draw', action='store_true', default=False, help='Draw curves')
    parser.add_argument('-g', '--Vg', type=range, default=None, help='Grid voltage')
    parser.add_argument('-G', '--grid', action='store_true', help='Draw grid curves')
    parser.add_argument('-i', '--Ia', type=range, default=None, help='Anode current (mA)')
    parser.add_argument('-o', '--output', action='store_true', help='Send raw numeric data to stdout')
    parser.add_argument('-l', '--Rl', type=float, default=0, help=u'Load resistor (KΩ)')
    parser.add_argument('-P', '--plate', action='store_true', help='Draw plate curves')
    parser.add_argument('-s', '--smooth', action='store_true', help='Smooth raw calculations')
    parser.add_argument('-t', '--title', type=unicode, default='', help='Figure title')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show calculations')
    parser.add_argument('-x', '--extra', action='store_true', help='Plot Vg and Va')
    parser.add_argument('file', nargs='?', default=None)
    args = parser.parse_args()
    try :
        if args.Rl and not args.Eb :
            raise Exception("Must give a B+ voltage if a load resistance is specified")
        if not args.grid and not args.plate and False :
            raise Exception("Can only specify one of Eb, Va, Vg")
        if args.file is None :
            raise Exception("Must give a data file name")
    except Exception, exc :
        print str(exc)
        return None
    if not (args.draw or args.output or args.plate or args.grid) :
        args.draw = True
    if not args.title :
        args.title = os.path.basename(args.file).split('.')[0].upper()
    return args

def make_range(def_value, value, intervals=6) :
    v = value or def_value
    interval = v / float(intervals)
    interval = round(interval, round_up=False)
    return [ interval * n for n in xrange(int(v/interval)+1) ]

def do_derivs(tm, args) :
    if args.Eb:
        note = u"Eb = %.0f V Rl=%.1f KΩ" % (args.Eb, args.Rl)
    elif args.Vg:
        args.Vg = args.Vg.must_be_unique()
        note = "Vg = %.2f V" % (args.Vg,)
    else:
        args.Va = args.Va.must_be_unique()
        note = "Va = %.0f V" % (args.Va,)
    derivs = tm.get_derivatives(Eb=args.Eb, Va=args.Va, Vg=args.Vg, Rl=args.Rl, Ia=args.Ia, args=args)

    if args.output:
        sys.stdout.write(','.join(['Ia', 'Gm', 'Rp', 'mu', 'Va', 'Vg']) + '\n')
        for r in zip(*derivs):
            sys.stdout.write(','.join(["%.3f" % (n,) for n in r]) + '\n')

    if args.draw:
        labels = ["Gm (mA/V)", u"Rp (KΩ)", u"µ"]
        if args.extra:
            labels += ["Va", "Vg"]
        ia_range = np.linspace(0, args.Ia(), 20)
        graph = multi_axis_graph(x_values=derivs[0], y_values=derivs[1:len(labels) + 1], labels=labels, x_label="Ia (ma)", title=args.title,
                                subtitle=u"Gm, Rp and µ", note=note)
        if args.verbose:
            for d in derivs:
                print d
        graph.show()

def do_plate_curves(tm, args) :
    curves = []
    labels = []
    for vg in args.Vg :
        curves.append([tm(va, -vg) for va in args.Va])
        labels.append("Vg = %.1f" % (-vg,))
    if args.verbose :
        for c, l in zip(curves, labels) :
            print "%10s %s" % (l, '  '.join([ "%.1f" % cc for cc in c]))
    graph = single_axis_graph(x_values=args.Va, y_values=curves, labels=labels, x_label="Va", y_label="Ia (mA)",
                              title=args.title, subtitle=u"Plate Curves")
    graph.show()

def do_grid_curves(tm, args) :
    curves = []
    labels = []
    for va in args.Va :
        curves.append([tm(va, -vg) for vg in args.Vg])
        labels.append("Va = %.0f" % (va,))
    if args.verbose :
        for c, l in zip(curves, labels) :
            print "%10s %s" % (l, '  '.join([ "%.1f" % cc for cc in c]))
    graph = single_axis_graph(x_values=args.Vg, y_values=curves, labels=labels, x_label="Vg", y_label="Ia (mA)",
                             title=args.title, subtitle=u": Grid Curves")
    graph.show()


args = get_args()
if args is None :
    sys.exit(1)

utd = utracer_data(args.file)
tm = tube_map(utd)

if args.Ia is None :
    args.Ia = range(tm.ia_min(), tm.ia_max())

if args.output or args.draw :
    do_derivs(tm, args)
elif args.plate :
    if args.Vg is None:
        args.Vg = tm.vg_values()
    if args.Va is None:
        args.Va = tm.va_values()
    do_plate_curves(tm, args)
elif args.grid :
    if args.Vg is None:
        args.Vg = tm.vg_values()
    if args.Va is None:
        args.Va = tm.va_values()
    do_grid_curves(tm, args)

