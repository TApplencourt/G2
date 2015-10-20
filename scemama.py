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
  scemama.py get_target_pt2_max --hf_id=<run_id>
                                --fci_id=<run_id>
                                [--like_toulouse |
                                 --like_applencourt |
                                 --ele=<element_name>...]
                                [--quality_factor=<qf>]
  scemama.py get_this_ae  --run_atom=<run_id>
                          (--ae_ref=<ae_value>... | --ae_nr)
                          [--like_toulouse |
                           --like_applencourt |
                           --ele=<element_name>...]
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

        l_ele = get_l_ele(arguments)

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

        hf_id = int(arguments["--hf_id"])
        fci_id = int(arguments["--fci_id"])

        # -#-#-#-#-#-#-#-#-#-#-#- #
        # D _ t a r g e t _ p t 2 #
        # -#-#-#-#-#-#-#-#-#-#-#- #

        from collections import defaultdict
        d_target_pt2 = defaultdict(lambda: 0.)

        for ele in e_cal[hf_id].viewkeys() & e_cal[fci_id].viewkeys():
            for name_atome, number in f_info[ele].formula:
                dump = (e_cal[fci_id][name_atome] - e_cal[hf_id][name_atome])
                d_target_pt2[ele] += dump * number

        # -#-#-#-#-#-#-#-#-#-#-#-#-#- #
        # Q u a l i t y _ f a c t o r #
        # -#-#-#-#-#-#-#-#-#-#-#-#-#- #

        if arguments["--quality_factor"]:
            if not 0. <= float(arguments["--quality_factor"]) <= 1.:
                print "0. < quality factor < 1. "
                sys.exit(1)
            else:
                quality_factor = float(arguments["--quality_factor"])
        else:
            quality_factor = 0.

        #  _
        # |_) ._ o ._ _|_
        # |   |  | | | |_
        #
        print "quality_factor :", quality_factor
        for ele, target_pt2 in d_target_pt2.iteritems():
            EPT2 = target_pt2 * (1 - quality_factor)
            EFCI = e_cal[fci_id][ele]
            print ele, EPT2, EFCI-EPT2

    elif arguments["get_this_ae"]:

        # ___
        #  |  ._  o _|_
        # _|_ | | |  |_
        #
        # Set somme option, get l_ele and the commande used by sql

        from src.data_util import ListEle, get_cmd, get_l_ele
        from src.data_util import get_ecal_runinfo_finfo

        # -#-#-#-#-#-#-#- #
        # F u n c t i o n #
        # -#-#-#-#-#-#-#- #

        l_ele = get_l_ele(arguments)

        def get_atome_energy():

            need_all = True
            print_children = False
            get_children = True

            # -#-#-#-#- #
            # l _ e l e #
            # -#-#-#-#- #

            arguments["--run_id"] = [arguments["--run_atom"]]

            # Usefull object contain all related stuff to l_ele
            a = ListEle(l_ele, get_children, print_children)

            # Only get the children
            a.l_ele = a.l_ele_children
            a.l_ele_to_get = a.l_ele_children

            # -#-#-#-#-#- #
            # F i l t e r #
            # -#-#-#-#-#- #

            _, cmd_where = get_cmd(arguments, a, need_all)

            # -#-#-#-#-#-#-#-#-#- #
            # P r o c e s s i n g #
            # -#-#-#-#-#-#-#-#-#- #
            e_cal_atom, _, _ = get_ecal_runinfo_finfo(cmd_where, "var")

            # -#-#-#-#-#- #
            # R e t u r n #
            # -#-#-#-#-#- #
            return e_cal_atom[int(arguments["--run_atom"])]

        def get_ae():
            """Returnb dict [mol] = ae"""

            # User give the ae
            if arguments["--ae_ref"]:

                # -#-#-#-#-#-#-#-#-#- #
                # P r o c e s s i n g #
                # -#-#-#-#-#-#-#-#-#- #

                ae_nr = dict()
                for mol, ae in zip(l_ele, arguments["--ae_ref"]):
                    ae_nr[mol] = float(ae)

            # User wana use the nr ae
            elif arguments["--ae_nr"]:
                need_all = True
                print_children = True
                get_children = True

                # -#-#-#-#- #
                # l _ e l e #
                # -#-#-#-#- #

                a = ListEle(l_ele, get_children, print_children)
                cond_filter_ele, cmd_where = get_cmd(arguments, a, need_all)

                # -#-#-#-#-#-#-#-#-#- #
                # P r o c e s s i n g #
                # -#-#-#-#-#-#-#-#-#- #

                from src.data_util import get_enr, get_ae_nr

                _, _, f_info = get_ecal_runinfo_finfo(cmd_where, "var")
                e_nr = get_enr(cond_filter_ele)
                ae_nr = get_ae_nr(f_info, e_nr)

            # -#-#-#-#-#- #
            # R e t u r n #
            # -#-#-#-#-#- #

            return ae_nr

        #  _
        # |_) ._ _   _  _   _  _ o ._   _
        # |   | (_) (_ (/_ _> _> | | | (_|
        #                               _|
        e_cal_atom = get_atome_energy()
        ae = get_ae()

        from src.SQL_util import dict_raw
        dict_ = dict_raw()

        for mol in l_ele:

            e_ref = ae[mol]

            for atome, number in dict_[mol]["formula"]:
                e_ref += e_cal_atom[atome] * number

            print mol, e_ref
