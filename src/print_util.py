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
    for arg in list_order:
        try:
            index = header_name.index(arg)
        except ValueError:
            print "For --order_by you need a column name"
            sys.exit(1)
        else:
            table_body = sorted(table_body,
                                key=lambda x: abs(x[index]),
                                reverse=True)
    return table_body


#  _
# |_) ._ o ._ _|_   ._ _   _.  _|
# |   |  | | | |_   | | | (_| (_|
#
def print_mad(run_info, d_mad, list_order):
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
    from src.terminaltables import AsciiTable

    table_body = [map(str, i) for i in table_body]
    table_data = [header_name] + [header_unit] + table_body

    table_big = AsciiTable(table_data)
    print table_big.table(row_separator=2)

