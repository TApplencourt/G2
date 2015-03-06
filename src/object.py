#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
import re
from math import sqrt, pow

# Need to add variance to the tuple
# Check with R


class v_un(namedtuple('v_un', 'e err')):

    p = re.compile(ur'^(0*)\.(0*(\d{1,2}))')

    def __str__(self):
        # Hypothese : Will display in flat form.
        #             not scientifique one

        # Same formating and take the non zero value
        err = '%f' % float(self.err)

        if not self.err:
            return '%f' % self.e

        if self.err >= 1.:
            return "{0}+/-{1}".format(self.e, float(self.err))

        else:
            m = re.search(self.p, str(err))

            left = len(m.group(1))

            len_format = len(m.group(2))
            good_digit = m.group(3)

            format_string = "{:>%d.%df}" % (len_format + left, len_format)
            str_e = format_string.format(self.e)
            return "{0}({1})".format(str_e, good_digit)

    # Add Left right
    def __add__(self, x):
        try:
            return v_un(self.e + x.e, sqrt(pow(self.err, 2) + pow(x.err, 2)))
        except AttributeError:
            return v_un(self.e + x, self.err)

    def __radd__(self, x):
        return self.__add__(x)

    # Minis Left right
    def __sub__(self, x):
        try:
            return v_un(self.e - x.e, sqrt(pow(self.err, 2) + pow(x.err, 2)))
        except AttributeError:
            return v_un(self.e - x, self.err)

    def __rsub__(self, x):
        try:
            return v_un(-self.e + x.e, sqrt(pow(self.err, 2) + pow(x.err, 2)))
        except AttributeError:
            return v_un(-self.e + x, self.err)

    # Multiplication
    def __mul__(self, x):
        return v_un(self.e * x, self.err * x)

    def __rmul__(self, x):
        return self.__mul__(x)

    # Division
    def __div__(self, x):
        return v_un(self.e / x, self.err / sqrt(abs(x)))

    # -v_un
    def __neg__(self):
        return v_un(-self.e, self.err)

    # abs
    def __abs__(self):
        return v_un(abs(self.e), self.err)

    # __lt__
    def __lt__(self, x):
        try:
            return self.e < x.e
        except AttributeError:
            return self.e < x

    def __gt__(self, x):
        try:
            return self.e > x.e
        except AttributeError:
            return self.e > x

    def __format__(self, format_spec):

        format_e = self.e.__format__(format_spec)
        format_err = self.err.__format__(format_spec)

        if not self.err:
            return format_e

        if ">" in format_spec:
            format_err = format_err.lstrip()
        elif "<" in format_spec:
            format_e = format_e.rstrip()

        if float(format_err) >= 1.:
            return "{0}+/-{1}".format(format_e, format_err)
        else:
            p2 = re.compile(ur'^0*\.0*(\d*)')
            m = re.search(p2, format_err.strip())
            good_digit = m.group(1)

            if good_digit:
                return "{0}({1})".format(format_e, good_digit)
            else:
                return format_e

if __name__ == '__main__':

    print "Operation"
    print "========="
    a = v_un(1.400, 0.6)
    print "a =", a
    print "a+a =", a + a
    print "a-a =", a - a
    print "a*a =", a * a
    print "a*2 =", a * 2

    print ""
    print "Display"
    print "======="

    list_ = [v_un(1.5, 1.300), v_un(1, 10),
             v_un(0.1, 0.1), v_un(0.1, 10), v_un(1, 0.00100),
             v_un(8.8819036, 3.0581249),
             v_un(-100.42304, 0o0036)]

    print "Value", "err", "display"
    for i in list_:
        print i.e, i.err, i

    print "Format"
    for i in list_:
        print ";", "{:>9.4f}".format(i), ";"
