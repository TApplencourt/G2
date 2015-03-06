#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  _
# /   _  | |  _   _ _|_ o  _  ._
# \_ (_) | | (/_ (_  |_ | (_) | |
#
from collections import defaultdict

from src.Requirement_util import config

import sys

# Format dict
format_dict = defaultdict()
for name, value in config.items("Format_dict"):
    format_dict[name] = config.get("Format_mesure", value)


DEFAULT_CHARACTER = ""

from src.terminaltables import AsciiTable


#  _
# |_ _  ._ ._ _   _. _|_
# | (_) |  | | | (_|  |_
#
def format_table(header_name, table_body):
    """
    Take and retable table_body.
    Format the table
    """
    for line in table_body:
        for i, name in enumerate(header_name):
            if name in format_dict:
                if line[i]:
                    line[i] = format_dict[name].format(line[i])
                else:
                    line[i] = DEFAULT_CHARACTER

    return table_body


#  _
# / \ ._ _|  _  ._   |_
# \_/ | (_| (/_ |    |_) \/
#                        /
def order_by(list_order, header_name, table_body):
    """
    Take and return table_body.
    Order table body by the list_order
    Example: list_order = ["mad"]
    """

    def tryabs(value):
        try:
            return abs(value)
        except TypeError:
            return value

    for arg in list_order:
        try:
            index = header_name.index(arg)
        except ValueError:
            print "For --order_by you need a column name"
            sys.exit(1)
        else:
            table_body = sorted(table_body,
                                key=lambda x: tryabs(x[index]),
                                reverse=True)
    return table_body


#  _
# |_) ._ o ._ _|_   ._ _   _.  _|
# |   |  | | | |_   | | | (_| (_|
#
def create_print_mad(run_info, d_mad, list_order):
    """
    Create the table then print the mad
    """
    # -#-#-#- #
    # I n i t #
    # -#-#-#- #

    table_body = []

    # -#-#-#-#-#- #
    # H e a d e r #
    # -#-#-#-#-#- #

    header_name = "Run_id Method Basis Geo Comments mad".split()
    header_unit = [DEFAULT_CHARACTER] * 5 + ["kcal/mol"]

    # -#-#-#- #
    # B o d y #
    # -#-#-#- #

    for run_id, l in run_info.iteritems():
        mad = d_mad[run_id] if run_id in d_mad else 0.

        line = [run_id] + l + [mad]
        table_body.append(line)

    # -#-#-#-#-#- #
    # F o r m a t #
    # -#-#-#-#-#- #

    table_body = order_by(list_order, header_name, table_body)
    table_body = format_table(header_name, table_body)

    # -#-#-#-#-#-#-#- #
    # B i g  Ta b l e #
    # -#-#-#-#-#-#-#- #

    table_body = [map(str, i) for i in table_body]
    table_data = [header_name] + [header_unit] + table_body

    table_big = AsciiTable(table_data)
    print table_big.table(row_separator=2)


def print_table_energy(run_info, table_body, header_name, header_unit):
    """
    Print the famous energy table.
    If is to big, split it !
    """
    # -#-#-#-#-#-#-#- #
    # B i g  Ta b l e #
    # -#-#-#-#-#-#-#- #
    from src.terminaltables import AsciiTable

    table_body = [map(str, i) for i in table_body]
    table_data = [header_name] + [header_unit] + table_body

    table_big = AsciiTable(table_data)

    # -#-#-#-#-#- #
    # F i l t e r #
    # -#-#-#-#-#- #

    # Table_big.ok Check if the table will fit in the terminal

    mode = config.get("Size", "mode")
    if all([mode == "Auto",
            not table_big.ok]) or mode == "Small":

            # Split into two table
            # table_run_id  (run _id -> method,basis, comment)
            # table_data_small (run_id -> energy, etc)
        table_run_id = ["Run_id Method Basis Geo Comments".split()]

        for run_id, l in run_info.iteritems():
            line = [run_id] + l
            table_run_id.append(line)

        t = AsciiTable([map(str, i) for i in table_run_id])
        print t.table()

        table_data_small = [[l[0]] + l[5:] for l in table_data]
        t = AsciiTable(table_data_small)
        print t.table(row_separator=2)

    else:
        print table_big.table(row_separator=2)


def print_table_gnuplot(table_body, header_name):
    def _value(var):

        default_character = "-"
        if not var:
            return default_character, default_character
        try:
            return str(var.e), str(var.err)
        except AttributeError:
            return str(var), "0."
        except:
            raise

    print "#" + header_name[0] + " " + header_name[5],
    print " err ".join(header_name[6:])
    table_data_small = [[line[0]] + line[5:] for line in table_body]

    for line in table_data_small:
        l = tuple(map(str, line[:2]))
        for i in line[2:]:
            l += _value(i)

        print " ".join(l)

    print "#GnuPlot cmd"
    print ""
    print "#for energy: "
    print "#$gnuplot -e",
    print "\"set datafile missing '-';",
    print "set xtics rotate;",
    print "plot 'dat' u 3:xtic(2) w lp title 'energy';",
    print "pause -1\""
    print ""
