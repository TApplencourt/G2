#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Welcome to the G2 Api! Grab all the G2 data you're dreaming of.

Usage:
  G2_input.py (-h | --help)
  G2_input.py list_geometries         [--ele=element_name...]
  G2_input.py list_elements      --geo=geometry_name...
  G2_input.py get_xyz            --geo=geometry_name...
                                 --ele=element_name...
                                      [(--save [--path=path])]
  G2_input.py get_g09            --geo=geometry_name...
                                 --ele=element_name...
                                      [(--save [--path=path])]
  G2_input.py get_multiplicity   --ele=element_name
"""

version = "1.0.3"

import sys

try:
    from misc.docopt import docopt
    from misc.SQL_util import *

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

    if arguments["get_g09"]:
        # Creates a Gaussian09 input file

        l_geo = arguments["--geo"]
        l_ele = arguments["--ele"]

        to_print = []
        for ele in l_ele:
            for geo in l_geo:
                try:
                    xyz = get_g09(geo, ele)
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
                path = "/tmp/" + path + ".com"

            with open(path, 'w') as f:
                f.write(str_ + "\n")
            print path
        else:
            print str_

    if arguments["get_xyz"]:
        l_geo = arguments["--geo"]
        l_ele = arguments["--ele"]

        to_print = []
        for ele in l_ele:
            for geo in l_geo:
                try:
                    xyz = get_xyz(geo, ele)
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
                path = "/tmp/" + path + ".xyz"

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
