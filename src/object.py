#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
import re


class v_un(namedtuple('v_un', 'e err')):

    p = re.compile(ur'^0*\.(0*(\d{1,2}))')

    def __repr__(self):
        # Same formating and take the non zero value
        err = '%f' % float(self.err)

        m = re.search(self.p, str(err))

        try:
            len_format = len(m.group(1))
            good_digit = m.group(2)
        except AttributeError:
            len_format = len(str(int(self.e)))

            format_string = "{:>%dd}" % (len_format + 2)
            str_e = format_string.format(int(self.e))

            return "{}({})".format(str_e, int(self.err))
        else:
            format_string = "{:>%d.%df}" % (len_format + 5, len_format)
            str_e = format_string.format(self.e)
            return "{}({})".format(str_e, good_digit)

    # Add Left right
    def __add__(self, x):
        try:
            return v_un(self.e + x.e, self.err + x.err)
        except AttributeError:
            return v_un(self.e + x, self.err)

    def __radd__(self, x):
        return self.__add__(x)

    # Minis Left right
    def __sub__(self, x):
        try:
            return v_un(self.e - x.e, self.err - x.err)
        except AttributeError:
            return v_un(self.e - x, self.err)

    def __rsub__(self, x):
        try:
            return v_un(-self.e + x.e, self.err + x.err)
        except AttributeError:
            return v_un(-self.e + x, self.err)

    # Multiplication
    def __mul__(self, x):
        try:
            return v_un(self.e * x.e, self.err * x.err)
        except AttributeError:
            return v_un(self.e * x, self.err * x)

    def __rmul__(self, x):
        return self.__mul__(x)

    # Division
    def __div__(self, x):
        try:
            return v_un(self.e / x, self.err / x)
        except AttributeError:
            raise AttributeError

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

if __name__ == '__main__':
    roger = v_un(1005, 0.2264545454)
    dudule = v_un(1, 0.00001)
    print -roger
    print roger + 2
    print 2.06 + roger
    print roger - 2
    print dudule - roger
