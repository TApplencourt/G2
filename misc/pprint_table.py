#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prints out a table, padded to make it pretty.

call pprint_table with an output (e.g. sys.stdout, cStringIO, file)
and table as a list of lists. Make sure table is "rectangular" -- each
row has the same number of columns.
"""

import sys


def format_num(num):
    """Format a number according to given places."""

    if isinstance(num, float):
        return "{:>12.6f}".format(num)
    else:
        return str(num)


def get_max_width(table, index):
    """Get the maximum width of the given column index
    """

    return max([len(format_num(row[index])) for row in table])


def pprint_table(table, out=sys.stdout):
    """Prints out a table of data, padded for alignment

    @param out: Output stream ("file-like object")
    @param table: The table to print. A list of lists. Each row must have the same
    number of columns.
    """

    col_paddings = [get_max_width(table, i) for i in range(len(table[0]))]

    #Handle the header
    for r, p in zip(table[0], col_paddings):
        col = format_num(r).center(p) + " " * 2
        print >> out, col,
    print >> out

    for row in table[1:]:
        for r, p in zip(row, col_paddings):
            col = format_num(r).ljust(p + 2)
            print >> out, col,
        print >> out

if __name__ == "__main__":
    table = [["", "taste sfsdfsd sdfsdf", "land speed", "life"],
             ["spam", 300.101, 4, 100300000000000000],
             ["eggs", 105.2, 13, 42],
             ["lumberjacks", 13.00, 105, 10]]

    import sys
    out = sys.stdout
    pprint_table(out, table)
