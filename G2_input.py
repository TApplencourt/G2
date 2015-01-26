#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Welcome to the G2 Api! Grab all the G2 data you're dreaming of.

Usage:
  G2_input.py (-h | --help)
  G2_input.py list_geometries         [--ele=<element_name>...]
  G2_input.py list_elements      --geo=<geometry_name>...
  G2_input.py get_xyz            --geo=<geometry_name>...
                                 --ele=<element_name>...
                                      [(--save [--path=<path>])]
  G2_input.py get_g09            --geo=<geometry_name>...
                                 --ele=<element_name>...
                                      [(--save [--path=<path>])]
  G2_input.py get_multiplicity   --ele=<element_name>

Example of use:
  ./G2_input.py list_geometries
  ./G2_input.py list_elements --geo Experiment
  ./G2_input.py get_xyz --geo Experiment --ele NaCl --ele H3CCl
"""

version = "1.0.4"

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

    if arguments["list_elements"]:

        str_ = cond_sql_or("geo_tab.name", arguments["--geo"])
        str_ = "AND".join(str_)

        l = [x for x in list_ele(str_) if "-" not in x and "+" not in x]

        print ", ".join(l)

    if arguments["get_g09"] or arguments["get_xyz"]:

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

    if arguments["get_multiplicity"]:
        ele = arguments["--ele"][0]
        try:
            m = dict_raw()[ele]["multiplicity"]
        except KeyError:
            pass
        else:
            print m
