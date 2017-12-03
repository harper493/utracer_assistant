__all__ = [ 'round', 'cmpfn', 'flatten_reduce',
            'flatten_min', 'flatten_min', 'x_from_y', 'pderiv', 'scale_list', 'camel_to_title',
            'make_plural', 'make_singular', 'is_irregular_plural', 'make_indef_article',
            'construct', 'add_default_arg', 'check_unused_args', 'contains_any', 'translate' ]

import math
import re
import os
import sys
import warnings
import numpy as np

#
# round - round a number to the specified number of digits
#

def round(value, digits=1, round_up=True) :
    sign = value < 0
    if sign :
        value, round_up = -value, not round_up
    remainder = value
    result = 0
    if value > 0 :
        while digits>0 :
            try :
                log = math.log10(remainder)
            except ValueError :
                break
            if log >= 0 :
                int_log = int(log)
            else :
                int_log = -int(1-log)
            one_digit = float(10**int_log)
            bound = int(remainder / one_digit) * one_digit
            result += bound
            remainder -= bound
            digits -= 1
        if round_up :
            result += one_digit
    if sign :
        result = -result
    return result
        
#
# cmpfn - given any two comparable objects, return a cmp-like comparison result for them
#

def cmpfn(a,b) :
    if a < b :
        return -1
    elif a > b :
        return 1
    else :
        return 0

#
# flatten_reduce - apply reduce to a flattened list
#
def flatten_reduce(fn, _list) :
    return reduce(fn, [ flatten_reduce(fn, l) \
                        if isinstance(l, list) or isinstance(l, tuple) else l \
                        for l in _list])
#
# flattened versions of max and min
#
def flatten_min(_list) :
    return flatten_reduce(min, _list)

def flatten_max(_list) :
    return flatten_reduce(max, _list)

def x_from_y(fn, bounds, y):
    '''
    Given a function (interpolation or actual function) and a y value, find the corresponding x value.
    Assumes the function is monotonic.
    '''
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

def pderiv(fn, x, delta):
    '''
    Given a function, an x value, and dx, return dy/dx
   '''
    y = fn(x)
    yd = fn(x + delta)
    result = (yd - y) / delta
    return result

#
# scale_list - scale a list (or anything that behaves like one)
#

def scale_list(l, scale) :
    for i in len(l) :
        l[i] *= scale

#
# camel_to_title - insert spaces before upper case letters
#
def camel_to_title(text) :
    result = ''
    prev_upper = True
    for c in text :
        if c.isupper() :
            if not prev_upper :
                prev_upper = True
                result += ' '
        else :
            prev_upper = False
        result += c
    return result

#
# translate - does what the str.translate function does, but works
# conveniently for unicode. The sceond argument is a list
# of 2-tuples to be translated. If backwards is True, the
# translation works in the opposite direction.
#

def translate(source, xlate, backwards=False) :
    result = source[:0]  # copy type of source
    for ch in source :
        for x in xlate:
            with warnings.catch_warnings() :
                if ch == x[1 if backwards else 0] :
                    warnings.simplefilter("ignore")
                    ch = x[0 if backwards else 1]
        result += ch
    return result

#
# contains_any - return true if the first collection contains anything in the
# second collection 
#
def contains_any(container, choices) :
    for ch in choices:
        if ch in container :
            return True
    return False

#
# make_plural - given a word, return its plural
#

_plural_transforms = [(r'(.*(?:s|z|ch|sh|x))$', r'\1es'),
                     (r'(.*)quy$', r'\1quies'),
                     (r'(.*[^aeiou])y$', r'\1ies'),
                     (r'(.*[aeiloru])f$', r'\1ves'),
                     (r'(.*i)fe$', r'\1ves'),
                     (r'(.*)man$', r'\1men'),
                     ]

_plural_irregulars = { 
    'ox':'oxen',
    'vax' : 'vaxen',
    'roof' : 'roofs',
    'turf' : 'turfs',
    'sheep' : 'sheep',
    'salmon' : 'salmon',
    'trout' : 'trout',
    'child' : 'children',
    'person' : 'people',
    'louse' : 'lice',
    'foot' : 'feet',
    'mouse' : 'mice',
    'goose' : 'geese',
    'tooth' : 'teeth',
    'aircraft' : 'aircraft',
    'hovercraft' : 'hovercraft',
    'potato' : 'potatoes',
    'tomato' : 'tomatoes',
    'phenomenon' : 'phenomena',
    'index' : 'indices',
    'matrix' : 'matrices',
    'vertex' : 'vertices',
    'crisis' : 'crises',
    'axis' : 'axes',
    'crisis' : 'crises',
    'samurai' : 'samurai',
    'radius' : 'radii',
    'fungus' : 'fungi',
    'millennium' : 'millennia',
    }

_plural_cache = {}

def make_plural(singular, quantity=2) :
    if quantity==1 :
        return singular
    try :
        return _plural_cache[singular]
    except KeyError : pass
    if singular=='!@!' :
        return _plural_cache
    try :
        plural = _plural_irregulars[singular]
    except KeyError :
        for t in _plural_transforms :
            plural = re.sub(t[0], t[1], singular)
            if plural!=singular :
                break
        else :
            plural = singular + 's'
    _plural_cache[singular] = plural
    return plural
#
# make_singular - opposite of the above
#
# For the time being this does the bare minimum needed for the CLI
#

_singular_irregulars = { p:s for s,p in _plural_irregulars.iteritems() }

_singular_transforms = [(r'(.*)ies$', r'\1y'),
                        #(r'(.*[aeiloru])ves$', r'\1f'),
                        #(r'(.*i)fe$', r'\1ves'),
                        (r'(.*)men$', r'\1man'),
                        (r'(.*)s$', r'\1'),
                       ] 

_singular_cache = {}

def is_irregular_plural(plural) :
    return make_singular(plural) + 's' != plural

def make_singular(plural) :
    try :
        return _singular_cache[plural]
    except KeyError : pass
    if plural=='!@!' :
        return _singular_cache
    try :
        singular = _singular_irregulars[plural]
    except KeyError :
        for t in _singular_transforms :
            singular = re.sub(t[0], t[1], plural)
            if singular!=plural :
                break
        else :
            singular = plural
    _singular_cache[plural] = singular
    return singular

#
# make_indef_article - return 'a' or 'an' as apropriate
# for the given string
#

_indef_vowel_irregulars = re.compile('|'.join([
    'ewe',
    'ewer',
    'u[^aeiou][aeiou]\w*',
])+'$')

_indef_vowel_irregulars_2 = re.compile('|'.join([
    'uni[cfltv][aeiou]\w*',
    'unio\w*',
])+'$')

_indef_vowel_regulars = re.compile('|'.join([
    'un\w*', 
]))

_indef_consonant_irregulars = re.compile('|'.join([
    'hour\w*',
    'honor\w*',
    'honour\w*',
    'honest\w*',
])+'$')

def make_indef_article(noun) :
    result = 'a'
    if noun[0] in 'aeiou' :
        result = 'an'
        m1 = _indef_vowel_irregulars.match(noun)
        if m1 :
            result = 'a'
            m2 = _indef_vowel_regulars.match(noun)
            if m2 :
                result = 'an'
                m3 = _indef_vowel_irregulars_2.match(noun)
                if m3 :
                    result = 'a'
    elif _indef_consonant_irregulars.match(noun) :
        result = 'an'
    return result

# 
# construct - generic help for delegated constructors
#
# arg table is either a list of argument names, or a dict of args names and
# the associated handler function or None, or the default value
#
# args which are handled are removed from the dict.
#

def construct(obj, arg_table, kwargs) :
    if not isinstance(arg_table, dict)  :
        arg_table = { a : None for a in arg_table }
    for k,a in arg_table.iteritems() :
        if k in kwargs :
            if callable(a) :
                v = (a)(obj, kwargs[k])
            else :
                v = kwargs[k]
            del kwargs[k]
        else :
            if callable(a) :
                v = (a)(obj, None)
            else :
                v = a
        setattr(obj, k, v)

def add_default_arg(args, name, value) :
    if name not in args :
        args[name] = value

def check_unused_args(kwargs) :
    if kwargs :
        raise NameError, "unexpected args: " + ", ".join(kwargs.keys())
            
    
