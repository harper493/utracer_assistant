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
    -- v1,v2,v3,v4,... : explicit list of values
    -- v1,v2, : if the values end with a comma, it is an explicit list
    -- v1,v2,v3 : if this looks more like a list than a range (e.g. 10,20,30)
       it is treated as a list
    -- v1,+v2,v3 : forces v2 to be treated as an interval even if it doesn't
       look like one (e.g. 10,+20,30)

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
        self._values = None
        self.value_count = 6    # default interval count
        self.precise_intervals = False
        self.actual_interval = 0
        if isinstance(value, basestring) :
            self._parse()
        elif isinstance(value, list) or isinstance(value, tuple) :
            self._values = value
            self._start, self._end = min(value), max(value)
            self._interval = None
            self.value = str(value)
        elif isinstance(value, int) or isinstance(value, float) :
            if v3 is None :
                if v2 is None :
                    self._end = float(value)
                    self._start, self._interval = 0, None
                    self.value = str(value)
                else :
                    self._start, self._end = float(value), float(v2)
                    self._interval = None
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
        try :
            values = self.value.split(',')
            is_list = False
            if len(values[-1])==0:      # explicit list
                is_list = True
                nvalues = map(float, values[:-1])
            elif len(values) > 3 :
                is_list = True
                nvalues = map(float, values)
            else :
                nvalues = map(float, values)
                is_list = len(values)==3 \
                          and nvalues[1]>nvalues[0] \
                          and nvalues[0]+nvalues[1] > nvalues[2]/2 \
                          and not values[1][0]=='+'
            if is_list :
                self._values = nvalues
                self._start, self._end = min(nvalues), max(nvalues)
                self._interval = None
            elif len(nvalues)==1 :
                self._start, self._interval, self._end, self._values = 0, None, nvalues[0], None
            elif len(nvalues)==2 :
                self._start, self._interval, self._end, self._values = nvalues[0], None, nvalues[1], None
            else :
                self._start, self._interval, self._end, self._values = nvalues[0], nvalues[1], nvalues[2], None
        except ValueError :
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
        return self._start==0

    def must_be_unique(self) :
        """
        Raise ValueError if value is not a single value
        """
        if not self.is_unique() :
            raise ValueError("range '%s' must be just a single number" % (self.value,))
        return self()

    def start(self) :
        return 0.0 if self._start is None else self._start

    def span(self) :
        return math.fabs(self._end - self.start())

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
        basis = float(10 ** int(math.log10(self.span())))
        best = basis/10.0
        best_metric = metric(best)
        for x in [basis/5, basis/2, basis, basis*2, basis*5, basis*10] :
            this_metric = metric(x)
            if this_metric < best_metric :
                best, best_metric = x, this_metric
        return best

    def _make_values(self) :
        if self._values is None :
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

def t(v) :
    print v, range(v).values()

if __name__=="__main__" :
    t('10')
    t('0,10')
    t('5,10')
    t('0,2,10')
    t('0,2,11')
    t('10,20,30')
    t('1,2,3,4,5')
    t('1,2,20,')
    t('0,+10,21')
    f = range('5,6')
    for x in f:
        print x,
    print
    g = range('10,300')
    print g.values()
    g.set_value_count(12)
    print g.values()
    b = range('0,10')
    b.set_exact_values(9)
    print b.values()
    print b()

