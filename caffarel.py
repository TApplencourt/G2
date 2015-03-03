#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
<< Je veux des nombres !!! >>

Usage:
  caffarel.py get_energy [--run_id=<id>...]
                         [(--ele=<element_name>... |
                           --like_toulouse |
                           --like_applencourt |
                           --like_run_id=<run_id>) [--all_children]]
                         [--method=<method_name>...]
                         [--basis=<basis_name>...]
                         [--geo=<geometry_name>...]
                         [--zpe]
                         [--no_relativist]
                         [--ae]
                         [--without_pt2]
                         [--order_by=<column>...]
                         [--gnuplot]
                         [--plotly=<column>...]
"""

version = "0.0.1"

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
    from src.docopt import docopt, DocoptExit
except:
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)


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

    from src.data_util import get_l_ele, ListEle, get_cmd

    # -#-#-#-#-#- #
    # O p t i o n #
    # -#-#-#-#-#- #

    print_children = True if arguments["--all_children"] else False
    need_all = False
    # -#-#-#-#- #
    # l _ e l e #
    # -#-#-#-#- #

    l_ele, get_children = get_l_ele(arguments)

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

    from src.data_util import get_ecal_runinfo_finfo
    from src.data_util import get_zpe_aeexp
    from src.data_util import get_enr, complete_e_nr, get_ediff
    from src.data_util import get_ae_cal, get_ae_nr, get_ae_diff
    from src.data_util import convert, get_header_unit, get_values

    # -#-#-#- #
    # E c a l #
    # -#-#-#- #

    energy_opt = "var" if arguments["--without_pt2"] else "var+pt2"

    e_cal, run_info, f_info = get_ecal_runinfo_finfo(cmd_where, energy_opt)

    if not a.l_ele:
        a.l_ele = [name for name in f_info]

    # -#-#- #
    # Z P E #
    # -#-#- #
    if arguments["--zpe"] or arguments["--ae"]:
        zpe_exp, ae_exp = get_zpe_aeexp(cond_filter_ele)
        convert("zpe_exp", zpe_exp)

    # -#-#-#-#-#-#-#-#-#-#-#-#- #
    # N o _ r e l a t i v i s t #
    # -#-#-#-#-#-#-#-#-#-#-#-#- #
    if arguments["--no_relativist"] or arguments["--ae"]:
        e_nr = get_enr(cond_filter_ele)
        complete_e_nr(e_nr, f_info, ae_exp, zpe_exp)

        e_diff, e_diff_rel = get_ediff(e_cal, e_nr)

        convert("e_cal", e_cal, opt=1)
        convert("e_diff", e_diff, opt=1)

    # -#- #
    # A E #
    # -#- #
    if arguments["--ae"]:
        ae_cal = get_ae_cal(f_info, e_cal)
        ae_nr = get_ae_nr(f_info, e_nr)
        ae_diff = get_ae_diff(ae_cal, ae_nr)

        convert("ae_cal", ae_cal, opt=1)
        convert("ae_nr", ae_nr)
        convert("ae_diff", ae_diff, opt=1)

    #  _
    # |_) ._ o ._ _|_
    # |   |  | | | |_
    #
    table_body = []

    # -#-#-#-#-#- #
    # H e a d e r #
    # -#-#-#-#-#- #

    header_name = "run_id method basis geo comments ele e_cal".split()

    if arguments["--zpe"]:
        header_name += "zpe_exp".split()

    if arguments["--no_relativist"]:
        header_name += "e_nr e_diff e_diff_rel".split()

    if arguments["--ae"]:
        header_name += "ae_cal ae_nr ae_diff".split()

    header_unit = get_header_unit(header_name)

    # -#-#-#- #
    # B o d y #
    # -#-#-#- #

    for run_id in run_info:

        line_basis = [run_id] + run_info[run_id][:4]

        for ele in a.to_print(e_cal[run_id]):

            line = list(line_basis) + [ele]
            line += get_values(ele, [e_cal[run_id]])

            if arguments["--zpe"]:
                line += get_values(ele, [zpe_exp])

            if arguments["--no_relativist"]:
                line += get_values(ele, [e_nr,
                                         e_diff[run_id],
                                         e_diff_rel[run_id]])

            if arguments["--ae"]:
                line += get_values(ele, [ae_cal[run_id],
                                         ae_nr,
                                         ae_diff[run_id]])
            table_body.append(line)

    # -#-#-#-#-#- #
    # F o r m a t #
    # -#-#-#-#-#- #

    from src.print_util import order_by, format_table

    table_body = order_by(arguments["--order_by"], header_name, table_body)
    table_body = format_table(header_name, table_body)

    #               ___
    #  /\   _  _ o o |  _. |_  |  _
    # /--\ _> (_ | | | (_| |_) | (/_
    #

    if not arguments["--gnuplot"]:
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

        from src.Requirement_util import config

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

    #  __
    # /__ ._      ._  |  _ _|_
    # \_| | | |_| |_) | (_) |_
    #             |
    elif arguments["--gnuplot"]:

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

        print "#" + header_name[0] + " " + " ".join(header_name[5:])
        table_data_small = [[line[0]] + line[5:] for line in table_body]

        for line in table_data_small:
            l = tuple(map(str, line[:2]))
            for i in line[2:]:
                l += _value(i)

            print " ".join(l)

        print "#GnuPlot cmd"
        print ""
        print "for energy: "
        print "#$gnuplot -e",
        print "\"set datafile missing '-';",
        print "set xtics rotate;",
        print "plot 'dat' u 3:xtic(2) w lp title 'energy';",
        print "pause -1\""
        print ""
        print "for ae_diff: "
        print "#$gnuplot -e",
        print "\"set datafile missing '-';",
        print "set xtics rotate;",
        print "plot 'dat' u 9:xtic(2) w lp title 'ae_diff';",
        print "pause -1\""
