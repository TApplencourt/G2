#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
import re


class v_un(namedtuple('v_un', 'e err')):

    p = re.compile(ur'^0*\.0*(\d+)$')

    def __repr__(self):
        # Same formating and take the non zero value
        str_e = "{:>10.5f}".format(self.e)
        str_err = "{:>10.5f}".format(self.err).strip()

        m = re.search(self.p, str_err)

        return "{}({})".format(str_e, m.group(1))

    def __add__(self, x):
        try:
            return v_un(self.e + x.e, self.err + x.err)
        except AttributeError:
            return v_un(self.e + x, self.err)

    def __radd__(self, x):
        try:
            return v_un(self.e + x.e, self.err + x.err)
        except AttributeError:
            return v_un(self.e + x, self.err)

    def __sub__(self, x):
        try:
            return v_un(self.e - x.e, self.err - x.err)
        except AttributeError:
            return v_un(self.e - x, self.err)

    def __rsub__(self, x):
        try:
            return v_un(self.e - x.e, self.err - x.err)
        except AttributeError:
            return v_un(self.e - x, self.err)

    def __mul__(self, x):
        try:
            return v_un(self.e * x.e, self.err * x.err)
        except AttributeError:
            return v_un(self.e * x, self.err * x)

    def __neg__(self):
        return v_un(-self.e, self.err)

if __name__ == '__main__':
    roger = v_un(0.10,0.12)
    print -roger
    print roger + 2
    print 2.06 + roger
    print roger - 2
    print 2.06 - roger