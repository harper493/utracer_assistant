#!/usr/bin/python
# -*- coding: utf-8 -*-
import csv
import re
import sys
import numpy as np
import scipy
import scipy.optimize
import math
from argparse import ArgumentParser
from copy import deepcopy
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.pyplot as plt
from scipy.interpolate import RectBivariateSpline


VVK_ESTIMATE = 0.5
CHILD_POWER = 1.5

def read_file(filename) :
    rowno = 1
    with open(filename, 'rb') as f :
        reader = csv.reader(f, delimiter=' ', skipinitialspace=True)
        result = []
        for row in reader :
            if rowno==1:
                anode_down = 'Va' in row
            else :
                if rowno == 2:
                    row = ' '.join(' '.join(row).split())
                    row = re.sub(r"V\w*\s*=\s*(\S*)\s*V", r"\1", row).split()
                    row = [0] + row
                row = [float(r) for r in row if r]
                row = [r if abs(r) > 0.001 else 0 for r in row]
                result.append(row)
            rowno += 1
    if not anode_down :
        print result
        print result[1:]
        print [ d[0] for d in result[1:]]
        r = [[ d[0] for d in result[1:]]]
        print r
        for i,v in enumerate(zip(*result[1:])[1:]) :
            r.append([result[0][i]] + list(v))
        result = r
    return result


def make_axes(data):
    y = [-d for d in data[0]]
    x = [d[0] for d in data[1:]]
    dd = [d[1:] for d in data[1:]]
    if y[0] > y[-1]:
        y = y[::-1]
        dd = [d[::-1] for d in dd]
    return (x, y, dd)


def make_interp(x, y, data):
    return RectBivariateSpline(x, y, np.array(data), kx=3 if len(x)>3 else 2)


def x_from_y(fn, bounds, y):
    xmin, xmax = bounds
    ymin, ymax = fn(xmin), fn(xmax)
    x, yn = xmin, fn(xmin)
    asc = ymin < ymax
    if not asc :
        ymin, ymax = ymax, ymin
    if y < ymin :
        return xmin if asc else xmax
    if y > ymax :
        return xmax if asc else xmin
    while not np.isclose(y, yn):
        if (yn > y) ^ (not asc):
            xmax = x
            x = (xmin + x) / 2
        else:
            xmin = x
            x = (x + xmax) / 2
        yn = fn(x)
    return x

def extrapolate_slope(x, y) :
    next_x = x[-1]*2 - x[-2]
    x_d2, x_d1 = x[-2] - x[-3], x[-1] - x[-2]
    y_d2, y_d1 = y[-2] - y[-3], y[-1] - y[-2]
    d2, d1 = y_d2 / x_d2, y_d1 / x_d1
    if math.fabs(d2) > 1 :
        d0 = d1*d1/d2
    else :
        d0 = d1*2
    result = (next_x - x[-1]) * d0 + y[-1]
    #print '@@@ x:', x[-3], x[-2], x[-1], x_d2, x_d1, 'y:', y[-3], y[-2], y[-1], y_d2, y_d1, 'd:', d2, d1, d0, result
    return result

def pderiv(fn, x, delta):
    y = fn(x)
    yd = fn(x + delta)
    result = (yd - y) / delta
    return result

def child(va, vg, perv, mu, pow=CHILD_POWER) :
    eff_va = va/mu+vg+VVK_ESTIMATE
    if isinstance(eff_va, float) :
        eff_va = max(eff_va, 0)
    else :
        eff_va.clip(0)
    result = perv * (eff_va**pow)
    print '///', va, vg, perv, mu, eff_va, result
    return result

def make_perv(ia, va, vg, mu) :
    return ia/child(va, vg, 1, mu)

def last_n(l, n) :
    return l[-1:-(n+1):-1][::-1]

class tube_map:
    MIN_DERIV_VA = 0.85       # lowest proportion of Eb to use when calculating derivatives
    MIN_DERIV_VG = 0.3       # highest (lowest) Vg to use for derivatives
    MIN_DERIV_IA = 0.05      # lowest Ia to use when calculating derivatives
    EB_RATIO = 0.95           # fraction of max Va to use for Eb
    DERIV_POINTS = 20        # number of points to calculate for derivatives
    DERIV_DELTA = 0.01       # delta multiplier for differential calculation
    EXTEND_DATA = 'slope'

    def __init__(self, filename):
        self.x, self.y, self.data = make_axes(read_file(filename))
        if True :
            print self.x
            print self.y
            for d in self.data :
                print '    ', d
        if tube_map.EXTEND_DATA=='scipy' :
            self.extend_data_scipy()
        elif tube_map.EXTEND_DATA=='calculate' :
            self.extend_data_calculate()
        elif tube_map.EXTEND_DATA=='slope' :
            self.extend_data_slope()
        self.interp = make_interp(self.x, self.y, self.data)

    def __call__(self, Va, Vg):
        result = float(self.interp.ev(Va, -Vg))
        if result < 1e-3 :
            result = 0
        return result

    def va_range(self):
        return (min(self.x), max(self.x))

    def va_min(self):
        return min(self.x)

    def va_max(self):
        return max(self.x)

    def vg_range(self) :
            return (self.vg_min(), self.vg_max())

    def va_span(self):
        return self.va_max() - self.va_min()

    def vg_min(self):
        return min(self.y)

    def vg_max(self):
        return -max(self.y)

    def vg_span(self):
        return self.vg_min() - self.vg_max()

    def ia_min(self):
        return min([min(d) for d in self.data])

    def ia_max(self):
        return max([max(d) for d in self.data])

    def ia_range(self):
        return (self.ia_min(), self.ia_max())

    def ia_span(self):
        return self.ia_max() - self.ia_min()

    def y_range(self):
        return (min(self.y), max(self.y))

    def Va_from_Ia(self, Vg, Ia):
        return x_from_y(lambda va: self(va, Vg), self.va_range(), Ia)

    def Vg_from_Ia(self, Va, Ia):
        return x_from_y(lambda vg: self(Va, vg), self.vg_range(), Ia)

    def get_one_derivative(self, Vg, Va, Ia, verbose=False):
        if Vg :
            va = self.Va_from_Ia(Vg, Ia)
        else :
            va = Va
            Vg = self.Vg_from_Ia(va, Ia)
        va_delta = min(max(va * 0.05, 1), self.va_span() * tube_map.DERIV_DELTA)
        vg_delta = min(max(Vg * 0.05, 0.05), self.vg_span() * tube_map.DERIV_DELTA)
        gm = pderiv(lambda vg: self(va, vg), Vg, vg_delta)
        invrp = pderiv(lambda va: self(va, Vg), va, va_delta)
        rp = 1 / invrp if invrp > 0 else 0
        dia = self(va, Vg + vg_delta)
        vad = self.Va_from_Ia(Vg, dia)
        dva = vad - va
        mu = dva / vg_delta
        if verbose :
            print '***', Vg, Ia, va, gm, rp, mu
        return (gm, rp, mu, va, Vg)

    def get_derivatives(self, Eb=0, Rl=0, Va=0, Vg=0, max_ia=0,
                            min_eb_ratio=None,
                            min_vg_ratio=None,
                            min_ia_ratio=None,
                            args={}) :
        min_eb_ratio = min_eb_ratio or tube_map.MIN_DERIV_VA
        min_vg_ratio = min_vg_ratio or tube_map.MIN_DERIV_VG
        min_vg = min(1, self.vg_span() * min_vg_ratio)
        min_ia_ratio = min_ia_ratio or tube_map.MIN_DERIV_IA
        min_eb = 0
        if Eb+Va+Vg==0 :               # nothing given, figure it out ourselves
            Eb = self.va_max() * tube_map.EB_RATIO
        if Eb and Rl==0 :
            min_eb = min(Eb, self.Va_from_Ia(min_vg, max_ia) * 1.1)
            Rl = round((Eb - min_eb) / max_ia, 2)
            args.Rl = Rl
        max_ia = max_ia or self(min_eb, -min_vg)
        min_ia = max_ia * min_ia_ratio
        if args.verbose :
            print '!!!', Eb, Rl, max_ia, min_ia, Vg, Va, min_eb,  min_vg
        x_range = np.linspace(min_ia, max_ia, tube_map.DERIV_POINTS)
        derivs = []
        for ia in x_range :
            if Eb :
                va = Eb - Rl * ia
                vg = self.Vg_from_Ia(va, ia)
            elif Va :
                va = Va
                vg = self.Vg_from_Ia(va, ia)
            elif Vg :
                va = self.Va_from_Ia(Vg, ia)
                vg = Vg
            derivs.append(self.get_one_derivative(vg, va, ia, verbose=args.verbose))
        zipped = zip(*derivs)
        gm = zipped[0]
        rp = zipped[1]
        mu = zipped[2]
        if args.smooth :
            gm = smooth(x_range, gm)
            rp = smooth(x_range, rp)
            mu = [ g * r for g,r in zip(gm, rp)]
        va = zipped[3]
        vg = [ -vg for vg in zipped[4]]
        return (x_range, gm, rp, mu, va, vg)

    def extend_data_slope(self) :
        extra_y = [ extrapolate_slope(self.x, ia) for ia in zip(*self.data) ]
        self.x.append(self.x[-1]*2 - self.x[-2])
        self.data.append(extra_y)
        print '***', extra_y
        extra_x = [ extrapolate_slope(self.y[::-1], ia[::-1]) for ia in self.data ]
        self.y = [self.y[0]*2 - self.y[1]] + self.y
        self.data = [ [extra] + ia for extra, ia in zip(extra_x, self.data) ]
        print '&&&', extra_x
        for d in self.data :
            print '    ', d

    def calculate_anode_extension(self, vg, next_va, va, ia):
        if vg!=0 :
            print '&&&', ia[-2], ia[-1], ia[-2]/ia[-1], ia
            ia_ratio = (ia[-2]/ia[-1])**(1/1.35)
            print '%%%', ia_ratio
            mu = (ia_ratio*va[-2] - va[-1]) / (vg*(1-ia_ratio))
            print '^^^', mu
            perv = make_perv(ia[-1], va[-1], vg, mu)
            result = child(next_va, vg, perv, mu)
        else :
            mu, perv, result = 1, 1, 1
        print '###', vg, next_va, ia[-1], mu, perv, result
        return result

    def calculate_grid_extension(self, va, next_vg, vg, ia):
        ia_ratio = (ia[-2]/ia[-1])**(0.666667)
        mu = va*(1-ia_ratio) / (g[-1] - g[-2])
        perv = make_perv(ia[-1], va, vg[-1], mu)
        return child(va, next_vg, perv, mu)

    def extend_data_calculate(self) :
        for vg in self.y :
            for ia in zip(*self.data) :
                next_va = self.x[-1]*2 - self.x[-2]
                print '***', vg, next_va, self.x, ia
                extra_y = self.calculate_anode_extension(-vg, next_va, self.x, ia)


    def extend_data_scipy(self) :
        # print self.x
        # print self.y
        # print self.data
        z = 3
        if z > 0:
            lastx = last_n(self.x, z)
            nextx = 2 * lastx[-1] - lastx[-2]
            extray = []
            for d in zip(self.y, *self.data):
                vg = d[0]
                lasty = last_n(d, z)
                # print '~~~', vg, lastx, lasty
                popt, pcov = scipy.optimize.curve_fit(lambda x, p, mu: child(x, -vg, p, mu), lastx, lasty)
                nexty = child(nextx, -vg, popt[0], popt[1])
                extray.append(nexty)
                # print '@@@', popt, nexty, [ child(x, -vg, popt[0], popt[1])/x for x in lastx]
            # print '** extra y:', extray
            next_vg = 2 * self.y[0] - self.y[1]
            last_va = last_n(self.y, z)
            extrax = []
            prevopt = None
            for va, d in zip(self.x + [nextx], self.data + [extray]):
                this_ia = d[:z][::-1]
                first_vg = self.y[:z][::-1]
                # print "$$$", va, next_vg, first_vg, this_ia
                if this_ia[-2] == 0:  # we only have a single data point
                    extrax.append(this_ia[-1] * 5)  # make something up!
                else:
                    popt, pcov = scipy.optimize.curve_fit(lambda x, p, mu: child(va, -x, p, mu), first_vg, this_ia)
                    perv, mu = popt
                    if mu != mu:  # if result is NaN
                        if prevopt:
                            nx = child(va, -next_vg * 0.95, prevopt[0], prevopt[1])
                        else:
                            nx = this_ia[-1] * 5
                    else:
                        nx = child(va, -next_vg * 0.95, perv, mu)
                        prevpopt = popt
                    # print "+++", popt, nx
                    extrax.append(nx)
            # print '** extra x:', extrax
            # print '^^^^^^^', self.x+[nextx]
            # print '^^^^^^^', [next_vg]+self.y
            self.datax = [[extra] + data for extra, data in zip(extrax, self.data + [extray])]
            self.x, self.y, self.data = self.x + [nextx], [next_vg] + self.y, self.datax


def smooth(x, y, iterations=1) :
    x = [xx for xx in x]
    y = [yy for yy in y]        # in case the inputs are iterators
    for n in xrange(iterations) :
        new_y = [y[0]]
        for i in xrange(1, len(x)-1) :
            xx, yy = x[:i]+x[i+1:], y[:i]+y[i+1:]
            interp = scipy.interpolate.interp1d(xx, yy, kind='cubic')
            new_y.append(float(interp(x[i])))
        y = new_y + [y[-1]]
    return y

def add_plot(host, x, y, label) :
    new_x = np.linspace(min(x), max(x), num=len(x) * 10, endpoint=True)
    interp = scipy.interpolate.interp1d(x, y, kind='cubic')
    p, = host.plot(new_x, interp(new_x), label=label)
    return p

def draw_multi_axis_graphs(x_values, y_values, y_labels=None, x_label=''):
    y_labels = y_labels or []
    if len(y_labels) < len(y_values):
        y_labels += [''] * (len(y_values) - len(y_labels))
    host = host_subplot(111, axes_class=AA.Axes)
    plt.subplots_adjust(right=0.75)
    offset = 0
    pars = []
    for l in y_labels[1:]:
        par = host.twinx()
        pars.append(par)
        new_fixed_axis = par.get_grid_helper().new_fixed_axis
        par.axis["right"] = new_fixed_axis(loc="right", axes=par,
                                               offset=(offset, 0))
        offset += 40
        par.axis["right"].toggle(all=True)
        par.set_ylabel(l)
    host.set_xlim(0, round(max(x_values), 2))
    ylim = round(max(y_values[0]), 2)
    host.set_ylim(0, ylim)
    host.set_xlabel(x_label)
    host.set_ylabel(y_labels[0])
    p = add_plot(host, x_values, y_values[0], y_labels[0])
    host.axis["left"].label.set_color(p.get_color())
    for par, l, y in zip(pars, y_labels[1:], y_values[1:]) :
        p = add_plot(par, x_values, y, l)
        par.set_ylim(0, round(max(y)))
        par.axis["right"].label.set_color(p.get_color())
    leg = host.legend(loc="best")
    leg.get_frame().set_alpha(0.3)
    return host

def draw_single_axis_graphs(x_values, y_values, y_label='', line_labels=None, x_label=''):
    y_max = round(max([ max(y) for y in y_values]), 2)
    if len(line_labels) < len(y_values):
        line_labels += [''] * (len(y_values) - len(line_labels))
    host = host_subplot(111, axes_class=AA.Axes)
    host.set_xlim(-2, round(max(x_values), 2))
    host.set_ylim(0, y_max)
    host.set_xlabel(x_label)
    host.set_ylabel(y_label)
    for l, y in zip(line_labels, y_values) :
        add_plot(host, x_values, y, l)
    leg = host.legend(loc="best")
    leg.get_frame().set_alpha(0.3)
    return host


#
# round - round a number to the specified number of digits
#

def round(value, digits=1, round_up=True):
    remainder = float(value)
    result = 0
    if value > 0:
        while digits > 0:
            try:
                log = math.log10(remainder)
            except ValueError:
                break
            if log >= 0:
                int_log = int(log)
            else:
                int_log = -int(1 - log)
            one_digit = float(10 ** int_log)
            bound = int(remainder / one_digit) * one_digit
            result += bound
            remainder -= bound
            digits -= 1
        if round_up and result<value :
            result += one_digit
    return result

def get_args() :
    parser = ArgumentParser(usage='[options] data-filename')
    parser.add_argument('-a', '--Va', type=float, default=0, help='Fixed anode voltage')
    parser.add_argument('-b', '--Eb', type=float, default=0, help='Fixed B+ voltage')
    parser.add_argument('-d', '--draw', action='store_true', default=False, help='Draw curves')
    parser.add_argument('-g', '--Vg', type=float, default=0, help='Fixed grid voltage')
    parser.add_argument('-G', '--grid', action='store_true', help='Draw grid curves')
    parser.add_argument('-i', '--max_i', type=float, default=0, help='Maximum anode current (ma)')
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
        if not args.grid and not args.plate and sum([ v!=0 for v in [args.Va, args.Eb, args.Vg]]) > 1 :
            raise Exception("Can only specify one of Eb, Va, Vg")
        if args.file is None :
            raise Exception("Must give a data file name")
    except Exception, exc :
        print str(exc)
        return None
    if not (args.draw or args.output or args.plate or args.grid) :
        args.draw = True
    if args.file.find('.') < 0 :
        args.file += '.txt'
    if not args.title :
        args.title = args.file[:args.file.find('.')].upper()
    return args

def make_title(host, args, extra) :
    host.title.set_position((0.5, 1.05))
    host.title.set_text(args.title + extra)
    host.title.set_size(14)
    host.title.set_weight("bold")

def make_range(def_value, value, intervals=6) :
    v = value or def_value
    interval = v / float(intervals)
    interval = round(interval, round_up=False)
    return [ interval * n for n in xrange(int(v/interval)+1) ]
    
    divisor = (10 ** int(math.log10(v)))
    top_digit = int(v / divisor)
    if top_digit >= 6 :
        result = [ float(i*divisor) for i in xrange(top_digit+1) ]
    elif top_digit > 1 :
        result = np.linspace(0, top_digit*divisor, top_digit*2+1)
    else :
        result = np.linspace(0, divisor, 6)
    return result


def do_derivs(tm, args) :
    derivs = tm.get_derivatives(Eb=args.Eb, Va=args.Va, Vg=args.Vg, Rl=args.Rl, max_ia=args.max_i, args=args)

    if args.output:
        sys.stdout.write(','.join(['Ia', 'Gm', 'Rp', 'mu', 'Va', 'Vg']) + '\n')
        for r in zip(*derivs):
            sys.stdout.write(','.join(["%.3f" % (n,) for n in r]) + '\n')

    if args.draw:
        labels = ["Gm (mA/V)", u"Rp (KΩ)", u"µ"]
        n_plots = 3
        if args.extra:
            labels += ["Va", "Vg"]
            n_plots = 5
        ia_range = np.linspace(0, args.max_i, 20)
        host = draw_multi_axis_graphs(ia_range, derivs[1:n_plots + 1], labels, "Ia (ma)")
        if args.Eb:
            note = u"Eb = %.0f V Rl=%.1f KΩ" % (args.Eb, args.Rl)
        elif args.Vg:
            note = "Vg = %.2f V" % (args.Vg,)
        else:
            note = "Va = %.0f V" % (args.Va,)
        make_title(host, args, u": Gm, Rp and µ")
        host.text(0.5, 0.9, note, transform=host.transAxes, fontsize=12, fontweight="bold")
        if args.verbose:
            for d in derivs:
                print d
        plt.show()

def do_plate_curves(tm, args) :
    curves = []
    labels = []
    va_range = np.linspace(0, round((args.Va if args.Va else tm.va_max()), 2), 20)
    vg_range = make_range(-tm.vg_max(), -args.Vg)
    for vg in vg_range :
        curves.append([tm(va, -vg) for va in va_range])
        labels.append("Vg = %.1f" % (-vg,))
    if args.verbose :
        for c, l in zip(curves, labels) :
            print "%10s %s" % (l, '  '.join([ "%.1f" % cc for cc in c]))
    host = draw_single_axis_graphs(va_range, curves, line_labels=labels, x_label="Va", y_label="Ia (mA)")
    make_title(host, args, u": Plate Curves")
    plt.show()

def do_grid_curves(tm, args) :
    curves = []
    labels = []
    va_range = make_range(tm.va_max(), args.Va)
    vg_range = np.linspace(-2, -(args.Vg if args.Vg else tm.vg_max()), 8)
    for va in va_range :
        curves.append([tm(va, -vg) for vg in vg_range])
        labels.append("Va = %.0f" % (va,))
    if args.verbose :
        for c, l in zip(curves, labels) :
            print "%10s %s" % (l, '  '.join([ "%.1f" % cc for cc in c]))
    host = draw_single_axis_graphs(vg_range, curves, line_labels=labels, x_label="Vg", y_label="Ia (mA)")
    make_title(host, args, u": Grid Curves")
    plt.show()


args = get_args()
if args is None :
    sys.exit(1)

tm = tube_map(args.file)

if args.output or args.draw :
    do_derivs(tm, args)
elif args.plate :
    do_plate_curves(tm, args)
elif args.grid :
    do_grid_curves(tm, args)

