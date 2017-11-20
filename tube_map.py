import scipy
import scipy.interpolate
import numpy as np
from utility import *
import math
from copy import copy

class tube_map:
    MIN_DERIV_VA = 0.85       # lowest proportion of Eb to use when calculating derivatives
    MIN_DERIV_VG = 0.3       # highest (lowest) Vg to use for derivatives
    MIN_DERIV_IA = 0.05      # lowest Ia to use when calculating derivatives
    EB_RATIO = 0.95           # fraction of max Va to use for Eb
    DERIV_POINTS = 20        # number of points to calculate for derivatives
    DERIV_DELTA = 0.01       # delta multiplier for differential calculation

    def __init__(self, udata):
        self.va, self.vg, self.data = udata.get()
        self.original_va, self.original_vg = copy(self.va), copy(self.vg)
        self.udata = udata
        if True :
            print self.va
            print self.vg
            for d in self.data :
                print '    ', d
        self.extend_data_slope()
        degree = 3 if len(self.va) > 3 else 2
        self.interp = scipy.interpolate.RectBivariateSpline(self.va, self.vg, np.array(self.data), kx=degree)

    def __call__(self, Va, Vg):
        result = float(self.interp.ev(Va, -Vg))
        if result < 1e-3 :
            result = 0
        return result

    def va_range(self):
        return (min(self.va), max(self.va))

    def va_min(self):
        return min(self.va)

    def va_max(self):
        return max(self.va)

    def va_values(self):
        return self.original_va

    def vg_range(self) :
            return (self.vg_min(), self.vg_max())

    def va_span(self):
        return self.va_max() - self.va_min()

    def vg_min(self):
        return min(self.vg)

    def vg_max(self):
        return -max(self.vg)

    def vg_span(self):
        return self.vg_min() - self.vg_max()

    def vg_values(self):
        return self.original_vg

    def ia_min(self):
        return min([min(d) for d in self.data])

    def ia_max(self):
        return max([max(d) for d in self.data])

    def ia_range(self):
        return (self.ia_min(), self.ia_max())

    def ia_span(self):
        return self.ia_max() - self.ia_min()

    def y_range(self):
        return (min(self.vg), max(self.vg))

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

    def get_derivatives(self, Eb=0, Rl=0, Va=0, Vg=0, Ia=0,
                        min_eb_ratio=None,
                        min_vg_ratio=None,
                        min_ia_ratio=None,
                        args={}) :
        min_eb_ratio = min_eb_ratio or tube_map.MIN_DERIV_VA
        min_vg_ratio = min_vg_ratio or tube_map.MIN_DERIV_VG
        min_vg = min(1, self.vg_span() * min_vg_ratio)
        min_ia_ratio = min_ia_ratio or tube_map.MIN_DERIV_IA
        min_eb = 0
        if not (Eb or Va or Vg) :
            Eb = self.va_max() * tube_map.EB_RATIO
        if Eb and Rl==0 :
            min_eb = min(Eb, self.Va_from_Ia(min_vg, Ia) * 1.1)
            Rl = round((Eb - min_eb) / Ia(), 2)
            args.Rl = Rl
        max_ia = Ia() or self(min_eb, -min_vg)
        min_ia = Ia() * min_ia_ratio
        if args.verbose :
            print '!!!', Eb, Rl, Ia, min_ia, Vg, Va, min_eb,  min_vg
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
        va = zipped[3]
        vg = [ -vg for vg in zipped[4]]
        return (x_range, gm, rp, mu, va, vg)

    def extrapolate_slope(self, x, ia):
        '''
        Given an X axis (Vg or Va) and the corresponding values of Ia,
        extrapolate by one further data point.
        '''
        next_x = x[-1] * 2 - x[-2]
        x_d2, x_d1 = x[-2] - x[-3], x[-1] - x[-2]
        y_d2, y_d1 = ia[-2] - ia[-3], ia[-1] - ia[-2]
        d2, d1 = y_d2 / x_d2, y_d1 / x_d1
        if math.fabs(d2) > 1:
            d0 = d1 * math.sqrt(d1 / d2)
        else:
            d0 = d1 * math.sqrt(2)
        result = (next_x - x[-1]) * d0 + ia[-1]
        return result

    def extend_data_slope(self) :
        '''
        To get good interpolation at the extremities of the data, we have to provide a reasonable guess
        for the "next" points beyond the data we have been given. We do this in both dimensions
        (for plate voltage and grid voltage), using the extrapolate_slope function.
        (Several extrapolation techniques were tried, this one gave the most consistent
        results though it isn't perfect - but then extrapolations aren't, by definition).
        '''
        extra_y = [self.extrapolate_slope(self.va, ia) for ia in zip(*self.data)]
        self.va.append(self.va[-1] * 2 - self.va[-2])
        self.data.append(extra_y)
        extra_x = [self.extrapolate_slope(self.vg[::-1], ia[::-1]) for ia in self.data]
        self.vg = [self.vg[0] * 2 - self.vg[1]] + self.vg
        self.data = [ [extra] + ia for extra, ia in zip(extra_x, self.data) ]

