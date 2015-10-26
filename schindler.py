#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Get all the List you whant.

Usage:
  schindler.py (-h | --help)
  schindler.py list_run [--run_id=<id>... | ([--method=<method_name>...]
                                             [--basis=<basis_name>...]
                                             [--geo=<geometry_name>...]
                                             [--comments=<comments>...])]
                        [(--ele=<element_name>...
                          | --like_toulouse
                          | --like_applencourt
                          | --like_run_id=<run_id>) [--all_children]]
                        [--without_pt2]
                        [--order_by=<column>...]
  schindler.py list_element [--run_id=<id>... | ([--method=<method_name>...]
                                                 [--basis=<basis_name>...]
                                                 [--geo=<geometry_name>...]
                                                 [--comments=<comments>...])]
                            [--missing (--ele=<element_name>...
                                        | --like_toulouse
                                        | --like_applencourt
                                        | --like_run_id=<run_id>) [--all_children]]
  schindler.py histogram --run_id=<id>... [--like_run_id=<run_id>]

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

    from src.data_util import get_l_ele
    from src.data_util import ListEle, get_cmd

    # -#-#-#-#-#- #
    # O p t i o n #
    # -#-#-#-#-#- #

    print_children = False
    need_all = True  # False if arguments["list_element"] else True

    # -#-#-#-#- #
    # l _ e l e #
    # -#-#-#-#- #

    l_ele = get_l_ele(arguments)

    if arguments["--all_children"]:
        get_children = True
    elif arguments["--like_run_id"]:
        get_children = False
    else:
        get_children = True

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
    #                                  
    # |_| o  _ _|_  _   _  ._ _. ._ _  
    # | | | _>  |_ (_) (_| | (_| | | | 
    #                   _|             
    elif arguments["histogram"]:

        from src.data_util import get_enr, complete_e_nr, get_ediff, get_zpe_aeexp
        from src.data_util import get_ae_cal, get_ae_nr, get_ae_diff
        from math import *

        ae_cal = get_ae_cal(f_info, e_cal)


        e_nr = get_enr(cond_filter_ele)
        zpe_exp, ae_exp = get_zpe_aeexp(cond_filter_ele)
        complete_e_nr(e_nr, f_info, ae_exp, zpe_exp)

        ae_nr = get_ae_nr(f_info, e_nr)
        ae_diff = get_ae_diff(ae_cal, ae_nr)

        sq_2pi_inv = .5/sqrt(2.*pi)
        def g(x,x0,sigma):
          return exp(-(x-x0)**2/(sigma*sigma))*sq_2pi_inv

        
        for run_id, ae_diff in ae_diff.items():
          print "run:%d"%run_id
          rmin =  1000.
          rmax = -1000.
          for ele, e in ae_diff.iteritems():
            try:
              x0 = e.e
            except:
              x0 = e
            rmin = min(x0, rmin)
            rmax = max(x0, rmax)

          print rmin, rmax
          dx = (rmax-rmin)/100.
          x = (rmax-rmin)*0.5 - 2.5*(rmax-rmin)
          for i in xrange(300):
            s = 0.
            for ele, e in ae_diff.iteritems():
              try:
                x0 = e.e
                sigma = max(0.001,e.err)
              except:
                x0 = e
                sigma = 0.001
              s += g(x,x0,sigma)
            print x*627.51, s
            x += dx
          print '\n'
          print "#Gnuplot cmd: plot for [IDX=0:1] 'visu' i IDX u 1:2 w lines title columnhead(1)"

