#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Welcome to the G2 Api! Grab all the G2 data you're dreaming of.

Usage:
  scemama.py (-h | --help)
  scemama.py list_geometries  [--ele=<element_name>...]
  scemama.py list_elements     --geo=<geometry_name>...
  scemama.py get_multiplicity  --ele=<element_name>
  scemama.py get_xyz    --geo=<geometry_name>...
                        --ele=<element_name>...
                            [(--save [--path=<path>])]
  scemama.py get_g09    --geo=<geometry_name>...
                        --ele=<element_name>...
                              [(--save [--path=<path>])]
  scemama.py get_target_pt2_max --hf_id=<id>
                                --fci_id=<id>
                                (--like_toulouse |
                                 --like_applencourt |
                                 --ele=<element_name>...)
                                [--quality_factor=<qf> |
                                 --born_min=<bmin> |
                                 --born_max=<bmax>]
Example of use:
  ./scemama.py list_geometries
  ./scemama.py list_elements --geo Experiment
  ./scemama.py get_xyz --geo Experiment --ele NaCl --ele H3CCl
"""

version = "0.0.1"

import sys

try:
    from src.docopt import docopt
    from src.SQL_util import cond_sql_or, list_geo, list_ele, dict_raw
    from src.SQL_util import get_xyz, get_g09
except:
    print "File in misc is corupted. Git reset may cure the disease."
    sys.exit(1)

if __name__ == '__main__':

    arguments = docopt(__doc__, version='G2 Api ' + version)

    if arguments["list_geometries"]:

        if arguments["--ele"]:
            str_ = cond_sql_or("id_tab.name", arguments["--ele"])
            str_ = "AND".join(str_)
        else:
            str_ = '(1)'

        print ", ".join(list_geo(str_))

    elif arguments["list_elements"]:

        str_ = cond_sql_or("geo_tab.name", arguments["--geo"])
        str_ = "AND".join(str_)

        l = [x for x in list_ele(str_) if "-" not in x and "+" not in x]

        print ", ".join(l)

    elif arguments["get_g09"] or arguments["get_xyz"]:

        from collections import namedtuple

        get_general = namedtuple('get_general', ['get', 'ext'])

        if arguments['get_g09']:
            g = get_general(get=get_g09, ext='.com')
        elif arguments['get_xyz']:
            g = get_general(get=get_xyz, ext='.xyz')

        l_geo = arguments["--geo"]
        l_ele = arguments["--ele"]

        to_print = []
        for ele in l_ele:
            for geo in l_geo:
                try:
                    xyz = g.get(geo, ele)
                except KeyError:
                    pass
                else:
                    to_print.append(xyz)

        str_ = "\n\n".join(to_print)
        if arguments["--save"]:

            if arguments["--path"]:
                path = arguments["--path"]
            else:
                path = "_".join([".".join(l_geo), ".".join(l_ele)])
                path = "/tmp/" + path + g.ext
            with open(path, 'w') as f:
                f.write(str_ + "\n")
            print path
        else:
            print str_

    elif arguments["get_multiplicity"]:
        ele = arguments["--ele"][0]
        try:
            m = dict_raw()[ele]["multiplicity"]
        except KeyError:
            pass
        else:
            print m

    elif arguments["get_target_pt2_max"]:

        # ___
        #  |  ._  o _|_
        # _|_ | | |  |_
        #
        # Set somme option, get l_ele and the commande used by sql

        from src.data_util import get_l_ele, ListEle, get_cmd

        # -#-#-#-#-#- #
        # O p t i o n #
        # -#-#-#-#-#- #

        need_all = True
        print_children = True
        get_children = True
        # -#-#-#-#- #
        # l _ e l e #
        # -#-#-#-#- #

        arguments["--run_id"] = [arguments["--hf_id"], arguments["--fci_id"]]

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

        from src.data_util import get_ecal_runinfo_finfo

        # -#-#-#- #
        # E c a l #
        # -#-#-#- #

        energy_opt = "var+pt2"

        e_cal, run_info, f_info = get_ecal_runinfo_finfo(cmd_where, energy_opt)

        if not a.l_ele:
            a.l_ele = [name for name in f_info]

        hf_id = int(arguments["--hf_id"])
        fci_id = int(arguments["--fci_id"])

        d_target_pt2 = dict()

        for ele in a.l_ele_to_get:
            d_target_pt2[ele] = 0.
            for name_atome, number in f_info[ele].formula:
                if number == 1:
                    d_target_pt2[ele] += e_cal[fci_id][ele] - e_cal[hf_id][ele]

            for name_atome, number in f_info[ele].formula:
                if number > 1:
                    d_target_pt2[ele] += d_target_pt2[name_atome] * number

        if arguments["--quality_factor"]:
            if not 0. <= float(arguments["--quality_factor"]) <= 1.:
                print "0. < quality factor < 1. "
                sys.exit(1)
            else:
                quality_factor = 1 - float(arguments["--quality_factor"])
        elif arguments["--born_min"]:
            if not float(arguments["--born_min"]) < 0.:
                print "You need a negative pt2"
                sys.exit()
            else:
                quality_factor = float(
                    arguments["--born_min"]) / max(d_target_pt2.values())
        elif arguments["--born_max"]:
            if not float(arguments["--born_max"]) < 0.:
                print "You need a negative pt2"
                sys.exit()
            else:
                quality_factor = float(
                    arguments["--born_max"]) / min(d_target_pt2.values())
        else:
            quality_factor = 0.

        print quality_factor
        for ele, target_pt2 in d_target_pt2.iteritems():
            print ele, target_pt2 * (quality_factor)
