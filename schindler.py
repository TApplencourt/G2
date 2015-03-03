#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Welcome to the G2 Api! Grab all the G2 data you're dreaming of.

Usage:
  G2_result.py (-h | --help)
  G2_result.py list_run [--order_by=<column>...]
                        [--run_id=<id>...]
                        [(--ele=<element_name>... |
                          --like_toulouse |
                          --like_applencourt |
                          --like_run_id=<run_id>) [--all_children]]
                        [--method=<method_name>...]
                        [--basis=<basis_name>...]
                        [--geo=<geometry_name>...]
                        [--without_pt2]
"""

version = "3.8.1"

# -#-#-#-#-#-#-#-#- #
# D i s c l a m e r #
# -#-#-#-#-#-#-#-#- #
# Proof of concept : Procedural code with minimal function call can be clean

#
#  _____                           _         _____              __ _
# |_   _|                         | |    _  /  __ \            / _(_)
#   | | _ __ ___  _ __   ___  _ __| |_  (_) | /  \/ ___  _ __ | |_ _  __ _
#   | || '_ ` _ \| '_ \ / _ \| '__| __|     | |    / _ \| '_ \|  _| |/ _` |
#  _| || | | | | | |_) | (_) | |  | |_   _  | \__/\ (_) | | | | | | | (_| |
#  \___/_| |_| |_| .__/ \___/|_|   \__| ( )  \____/\___/|_| |_|_| |_|\__, |
#                | |                    |/                            __/ |
#                |_|                                                 |___/

import sys

#
# \  / _  ._ _ o  _  ._
#  \/ (/_ | _> | (_) | |
#
if sys.version_info[:2] != (2, 7):
    print "You need python 2.7."
    print "You can change the format (in src/objet.py) for 2.6"
    print "And pass the 2to3 utility for python 3"
    print "Send me a pull request after friend!"
    sys.exit(1)

#
# |  o |_  ._ _. ._
# |_ | |_) | (_| | \/
#                  /
try:
    from src.docopt import docopt
except:
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)

#  _
# /   _  | |  _   _ _|_ o  _  ._
# \_ (_) | | (/_ (_  |_ | (_) | |
#
from collections import defaultdict

# ___  ___      _
# |  \/  |     (_)
# | .  . | __ _ _ _ __
# | |\/| |/ _` | | '_ \
# | |  | | (_| | | | | |
# \_|  |_/\__,_|_|_| |_|
#
if __name__ == '__main__':

    arguments = docopt(__doc__, version='G2 Api ' + version)

    # ___
    #  |  ._  o _|_
    # _|_ | | |  |_
    #
    # Set somme option, get l_ele and the commande used by sql

    from src.Data_util import get_l_ele, ListEle, get_cmd

    # -#-#-#-#-#- #
    # O p t i o n #
    # -#-#-#-#-#- #

    print_children = False
    need_all = True
    get_children = True

    # -#-#-#-#- #
    # l _ e l e #
    # -#-#-#-#- #

    l_ele, _ = get_l_ele(arguments)

    # Usefull object contain all related stuff to l_ele
    a = ListEle(l_ele, get_children, print_children)

    # -#-#-#-#-#- #
    # F i l t e r #
    # -#-#-#-#-#- #

    cond_filter_ele, cmd_where = get_cmd(arguments, a, need_all)

    #  _
    # |_) ._ _   _  _   _  _ o ._   _
    # |   | (_) (_ (/_ _> _> | | | (_|
    #                               _|
    # We get and calcul all the info
    # aka : e_cal, run_info, f_info, mad, ...

    from src.Data_util import get_ecal_runinfo_finfo, get_zpe_aeexp
    from src.Data_util import get_enr, complete_e_nr
    from src.Data_util import get_ae_cal, get_ae_nr, get_ae_diff

    # -#-#-#- #
    # E c a l #
    # -#-#-#- #

    e_cal, run_info, f_info = get_ecal_runinfo_finfo(cmd_where, "var+pt2")

    if not a.l_ele:
        a.l_ele = [name for name in f_info]

    # -#-#- #
    # E n r #
    # -#-#- #

    zpe_exp, ae_exp = get_zpe_aeexp(cond_filter_ele)
    e_nr = get_enr(cond_filter_ele)
    complete_e_nr(e_nr, f_info, ae_exp, zpe_exp)

    # -#- #
    # A E #
    # -#- #

    ae_cal = get_ae_cal(f_info, e_cal)
    ae_nr = get_ae_nr(f_info, e_nr)
    ae_diff = get_ae_diff(ae_cal, ae_nr)

    # -#-#- #
    # M A D #
    # -#-#- #
    # mad = mean( abs( x_i - mean(x) ) )

    d_mad = defaultdict()
    for run_id, ae_diff_rd in ae_diff.iteritems():

        l_energy = [val for name, val in ae_diff_rd.iteritems()
                    if f_info[name].num_atoms > 1]

        try:
            mad = 627.510 * sum(map(abs, l_energy)) / len(l_energy)
        except ZeroDivisionError:
            pass
        else:
            d_mad[run_id] = mad

    #  _
    # |_) ._ o ._ _|_ o ._   _
    # |   |  | | | |_ | | | (_|
    #                        _|

    # -#-#-#- #
    # I n i t #
    # -#-#-#- #

    table_body = []

    # -#-#-#-#-#- #
    # H e a d e r #
    # -#-#-#-#-#- #
    DEFAULT_CHARACTER = ""

    header_name = "Run_id Method Basis Geo Comments mad".split()
    header_unit = [DEFAULT_CHARACTER] * 5 + ["kcal/mol"]

    # -#-#-#- #
    # B o d y #
    # -#-#-#- #

    for run_id, l in run_info.iteritems():
        mad = d_mad[run_id] if run_id in d_mad else 0.

        line = [run_id] + l + [mad]
        table_body.append(line)

    from src.Print_util import format_table
    table_body = format_table(header_name, table_body)

    # -#-#-#-#-#-#-#- #
    # B i g  Ta b l e #
    # -#-#-#-#-#-#-#- #
    from src.terminaltables import AsciiTable

    table_body = [map(str, i) for i in table_body]
    table_data = [header_name] + [header_unit] + table_body

    table_big = AsciiTable(table_data)
    print table_big.table(row_separator=2)
