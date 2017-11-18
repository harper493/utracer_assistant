import re
import math

class range(object) :
    """
    A range object takes bounds and an interval, and can produce either
    the exact values implied, or an iterator to the values.

    The supplied string can be one of:

    -- end : start is implicitly 0, the interval is determined as below
    -- start,end : interval determined implicitly
    -- start,interval,end : everything is explicit

    If no interval is given, a range object will come up with with
    best choice of interval. By default, it tries to generate 6
    intervals (i.e. 7 values). This can be overridden by calling
    set_value_count(n). That will choose the best number of
    intervals (closest to n) that allows the intervals to be
    multiples of 2, 5 or 10.

    set_exact_values imposes the number of intervals, regardless
    of how odd the resulting values may look.

    For example:

    '10' => 0, 2, 4, 6, 8, 10
    '0,10' => (the same)
    '5,10' => 5, 6, 7, 8, 9, 10
    '0,1,10' => 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    """

    def __init__(self, value, v2=None, v3=None) :
        self.value = value
        self._start, self._interval, self._end = None, None, None
        self.value_count = 6    # default interval count
        self.precise_intervals = False
        self.actual_interval = 0
        if isinstance(value, basestring) :
            self._parse()
        elif isinstance(value, int) or isinstance(value, float) :
            if v3 is None :
                if v2 is None :
                    self._end = float(value)
                    self.value = str(value)
                else :
                    self._start, self._end = float(value), float(v2)
                    self.value = '%f,%f' % (value, v2)
            else :
                self._start, self._interval, self._end = \
                    float(value), float(v2), float(v3)
                self.value = '%f,%f,%f' % (value, v2, v3)
        elif isinstance(value, range) :
            self.value, self._start, self._interval, self._end, self.value_count, self.precise_intervals, self.actual_interval = \
                value.value, value._start, value._interval, value._end, value.value_count, value.precise_intervals, value.actual_interval
        else :
            raise ValueError("'%s' (%s) is not an acceptable type for a range" %
                             (value, type(value)))

    def _parse(self):
        rx = r'^([+-]?\d*\.?\d+)(?:,([+-]?\d*\.?\d+)(?:,([+-]?\d*\d+))?)?$'
        m = re.match(rx, self.value)
        try :
            if m :
                if m.group(2) :
                    if m.group(3) :
                        self._start, self._interval, self._end = \
                            float(m.group(1)), float(m.group(2)), float(m.group(3))
                    else :
                        self._start, self._end = float(m.group(1)), float(m.group(2))
                else :
                    self._end = float(m.group(1))
        except str :
            raise Exception("incorrect range expression '%s'" % (self.value,))

    def __call__(self) :
        return self._end

    def __nonzero__(self):
        return self._end != 0

    def is_unique(self) :
        """
        Return True iff the range contains only a final value, meaning
        that it can be used as a single value.
        """
        return self._start is None

    def must_be_unique(self) :
        """
        Raise ValueError if value is not a single value
        """
        if not self.is_unique() :
            raise ValueError("range '%s' must be just a single number" % (self.value,))

    def start(self) :
        return 0.0 if self._start is None else self._start

    def span(self) :
        return self._end - self.start()

    def set_exact_values(self, n) :
        self.value_count, self.precise_intervals = n, True

    def set_value_count(self, n) :
        self.value_count, self.precise_intervals = n, False

    def _make_interval(self) :
        if self._interval is None :
            if self.precise_intervals :
                self.actual_interval = self.span() / self.value_count
            else :
                self.actual_interval = \
                    self._round_interval()
        else :
            self.actual_interval = self._interval

    def _round_interval(self):
        """
        Find the best interval to use, considering the
        requested number and the span of the values. We look for
        a number whose most significant digit is 1, 2 or 5, which
        gives the closest match to the requested number of intervals.
        """
        def metric(x) :
            return math.fabs(math.log((self.span() / x) / self.value_count))
        int1 = self.span() / self.value_count
        basis = float(10 ** int(math.log10(self.span())))
        mantissa = self.span() / basis
        best = basis/10.0
        best_metric = metric(best)
        for x in [basis/5, basis/2, basis, basis*2, basis*5, basis*10] :
            this_metric = metric(x)
            if this_metric < best_metric :
                best, best_metric = x, this_metric
        return best

    def _make_values(self) :
        self._make_interval()
        actual_intervals = self.span() / self.actual_interval
        n = int(actual_intervals)
        if actual_intervals > n :
            n += 1
        self._values = [ self.start() + i * self.actual_interval for i in xrange(n+1)]

    def values(self) :
        self._make_values()
        return self._values

    def __iter__(self) :
        self._make_values()
        for v in self._values :
            yield v

    def __str__(self) :
        return self.value

# Test code - executed if the file is run stand-alone

if __name__=="__main__" :
    a = range('10')
    print a.values()
    b = range('0,10')
    print b.values()
    c = range('5,10')
    print c.values()
    d = range('0,2,10')
    print d.values()
    e = range('0,2,11')
    print e.values()
    f = range('5,6')
    for x in f:
        print x,
    print
    g = range('10,300')
    print g.values()
    g.set_intervals(12)
    print g.values()
    b.set_exact_intervals(9)
    print b.values()
    print b()

