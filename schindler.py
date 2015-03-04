#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Get all the List you whant.

Usage:
  schindler.py (-h | --help)
  schindler.py list_run [--run_id=<id>...]
                        [(--ele=<element_name>... |
                          --like_toulouse |
                          --like_applencourt |
                          --like_run_id=<run_id>) [--all_children]]
                        [--method=<method_name>...]
                        [--basis=<basis_name>...]
                        [--geo=<geometry_name>...]
                        [--without_pt2]
                        [--order_by=<column>...]
  schindler.py list_element [--run_id=<id>...]
                            [--geo=<geometry_name>...]
                            [--basis=<basis_name>...]
                            [--method=<method_name>...]
                            [--missing (--ele=<element_name>... |
                                        --like_toulouse |
                                        --like_applencourt |
                                        --like_run_id=<run_id>) [--all_children]]
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

    # Docopt Fix
    if arguments["--missing"] or arguments["--all_children"]:

        if not any(arguments[k] for k in ["--like_toulouse",
                                          "--like_applencourt",
                                          "--like_run_id",
                                          "--ele"]):
            raise DocoptExit
            sys.exit(1)

    # ___
    #  |  ._  o _|_
    # _|_ | | |  |_
    #
    # Set somme option, get l_ele and the commande used by sql

    from src.data_util import get_l_ele, ListEle, get_cmd

    # -#-#-#-#-#- #
    # O p t i o n #
    # -#-#-#-#-#- #

    print_children = False
    need_all = False if arguments["list_element"] else True

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

    from src.data_util import get_ecal_runinfo_finfo, get_mad

    # -#-#-#- #
    # E c a l #
    # -#-#-#- #

    energy_opt = "var" if arguments["--without_pt2"] else "var+pt2"

    e_cal, run_info, f_info = get_ecal_runinfo_finfo(cmd_where, energy_opt)

    if not a.l_ele:
        a.l_ele = [name for name in f_info]

    if arguments["list_run"]:
        d_mad = get_mad(f_info, e_cal, cond_filter_ele)

    #  _
    # |_) ._ o ._ _|_ o ._   _
    # |   |  | | | |_ | | | (_|
    #                        _|
    if arguments["list_run"]:
        from src.print_util import create_print_mad
        create_print_mad(run_info, d_mad, arguments["--order_by"])

    elif arguments["list_element"]:
        for run_id in run_info:

            if arguments["--missing"]:
                line = [e for e in a.l_ele_to_get if e not in e_cal[run_id]]
            else:
                line = [e for e in e_cal[run_id]]

            if line:
                print run_id
                print " ".join(run_info[run_id])
                print " ".join(line)
                print "====="
