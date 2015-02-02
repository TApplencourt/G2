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

    def __mul__(self, x):
        try:
            return v_un(self.e * x.e, self.err * x.err)
        except AttributeError:
            return v_un(self.e * x, self.err * x)

    def __sub__(self, x):
        try:
            return v_un(self.e - x.e, self.err - x.err)
        except AttributeError:
            return v_un(self.e - x, self.err)

    def __div__(self, x):
        try:
            return v_un(self.e / x.e, self.err / x.err)
        except AttributeError:
            return v_un(self.e / x, self.err / x)
