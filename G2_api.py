#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Welcom to the G2 Api! Grab all G2 data you're dreaming for.

Usage:
  G2_api.py (-h | --help)
  G2_api.py list_run [--order_by=column...]
                     [--ele=element_name...]
                     [--geo=geometry_name...]
                     [--basis=basis_name...]
                     [--method=method_name...]
  G2_api.py get_energy [--without_pt2]
                       [--get_ae]
                       [--order_by=column...]
                       [--run_id=id...]
                       [--ele=element_name...]
                       [--geo=geometry_name...]
                       [--basis=basis_name...]
                       [--method=method_name...]
  G2_api.py --version

Options:
  --help                 Here you go.
  --without_pt2          Show all the data without adding the PT2 when avalaible.
  --get_ae               Show the atomization energy (both theorical and experiment) when avalaible.
  All the other          Filter the data or ordering it. See example.


Example of use:
  ./G2_api.py list_run g2.db
  ./G2_api.py get_energy --run_id 11 --order_by num_elec --without_pt2
  ./G2_api.py get_energy --basis cc-pvdz --ele AlCl --ele Li2 --get_ae
"""

version = "1.0.0"

import sys

try:
    from docopt import docopt
except:
    print "You need docopt"
    sys.exit(1)

try:
    import sqlite3
except:
    print "Sorry, you need sqlite3"
    sys.exit(1)

import os


def isSQLite3(filename):
    from os.path import isfile, getsize

    if not isfile(filename):
        return False
    if getsize(filename) < 100:  # SQLite database file header is 100 bytes
        return False

    with open(filename, 'rb') as fd:
        header = fd.read(100)

    if header[:16] == 'SQLite format 3\x00':
        return True
    else:
        print "'%s' is not a SQLite3 database file" % filename
        print sys.exit(1)


def cond_sql_or(table_name, l_value):
    dmy = " OR ".join(['%s = "%s"' % (table_name, i) for i in l_value])
    if dmy:
        return "(%s)" % dmy
    else:
        return "1"

if __name__ == '__main__':

    path = os.path.dirname(sys.argv[0]) + "/misc/g2.db"
    isSQLite3(path)

    conn = sqlite3.connect(path)
    c = conn.cursor()

    arguments = docopt(__doc__, version='G2 Api ' + version)

    # ______ _ _ _
    # |  ___(_) | |
    # | |_   _| | |_ ___ _ __
    # |  _| | | | __/ _ \ '__|
    # | |   | | | ||  __/ |
    # \_|   |_|_|\__\___|_|
    #

    #| ||_  _  __ _
    #|^|| |(/_ | (/_
    d = {"run_id": "--run_id",
         "geo_name": "--geo",
         "basis_name": "--basis",
         "meth_name": "--method"}

    str_ = []
    for k, v in d.items():
        l_v = arguments[v]
        cond = cond_sql_or(k, l_v)
        str_.append(cond)

    ele = arguments["--ele"]
    if ele:
        # Find all this children of the element; this is the new conditions
        cond = cond_sql_or("name", ele)
        c.execute("""SELECT name, formula
                       FROM id_tab
                      WHERE {where_cond}""".format(where_cond=cond))

        list_name_needed = ()
        for name, formula_raw in c.fetchall():
            list_name_needed += (name,)
            for atom, number in eval(formula_raw):
                list_name_needed += (atom,)

        cond = cond_sql_or("ele", list_name_needed)
        str_.append(cond)

    cmd_where = " AND ".join(str_)

    # _
    #/ \ __ _| _  __   |_  \/
    #\_/ | (_|(/_ |    |_) /
    cmd_by = ",".join(arguments["--order_by"])
    if not cmd_by:
        cmd_by = "run_id"

    # _     _     _
    #| |   (_)   | |
    #| |    _ ___| |_   _ __ _   _ _ __
    #| |   | / __| __| | '__| | | | '_ \
    #| |___| \__ \ |_  | |  | |_| | | | |
    #\_____/_|___/\__| |_|   \__,_|_| |_|
    #
    if arguments["list_run"]:

        c.execute(
            """SELECT run_id,
                 method_name method,
                  basis_name basis,
                    geo_name geo,
                    comments
                        FROM output_tab
                       WHERE {where_cond}
                    GROUP BY run_id
                    ORDER BY {order_by}""".format(where_cond=cmd_where, order_by=cmd_by))

        header = ["Run_id", "Method", "Basis", "Geo", "Comments"]
        print ' '.join('{:<22}'.format(i) for i in header)

        for line in c.fetchall():
            print ' '.join('{:<22}'.format(i) for i in line)
        print ""

    # _____
    #|  ___|
    #| |__ _ __   ___ _ __ __ _ _   _
    #|  __| '_ \ / _ \ '__/ _` | | | |
    #| |__| | | |  __/ | | (_| | |_| |
    #\____/_| |_|\___|_|  \__, |\__, |
    #                      __/ | __/ |
    #                     |___/ |___/
    elif arguments["get_energy"]:

        from collections import defaultdict

        c.execute("""SELECT formula,
                             run_id,
                        method_name method,
                         basis_name basis,
                           geo_name geo,
                           comments,
                    output_tab.name ele,
                           s_energy,
                           c_energy,
                              c_pt2
                      FROM output_tab
                INNER JOIN id_tab
                        ON output_tab.name = id_tab.name
                     WHERE {where_cond}
                  ORDER BY {order_by}
                    """.format(where_cond=cmd_where, order_by=cmd_by))

        data_th = c.fetchall()

        d_energy = defaultdict(dict)

        # Because formula is wrong for Anion and Cation
        data_th[:] = [x for x in data_th if not ("+" in x[0] or "-" in x[0])]

        for info in data_th:

            run_id = info[1]
            name = info[-4]
            s_energy = info[-3]
            c_energy = info[-2]
            c_pt2 = info[-1]

            if s_energy:
                d_energy[run_id][name] = float(s_energy)
            if c_energy:
                if arguments["--without_pt2"]:
                    d_energy[run_id][name] = float(c_energy)
                else:
                    d_energy[run_id][name] = float(c_energy) + float(c_pt2)

        #  ___   _____
        # / _ \ |  ___|
        #/ /_\ \| |__
        #|  _  ||  __|
        #| | | || |___
        #\_| |_/\____/
        #
        if arguments["--get_ae"]:
            # __    _
            #|_    |_) _  __ o __  _ __ _|_ _  |
            #|__>< |  (/_ |  | |||(/_| | |_(_| |
            ae_exp = defaultdict()

            c.execute("""SELECT name,zpe,kcal
                         FROM id_tab
                         NATURAL JOIN zpe_tab
                         NATURAL JOIN atomization_tab
                         WHERE
                             basis_id=1
                         AND method_id=1""")

            for name, zpe, kcal in c.fetchall():
                zpe = zpe * 4.55633e-06
                energy = kcal * 0.00159362
                ae_exp[name] = energy - zpe

            #___
            # | |_  _  _  __ o  _  _  |
            # | | |(/_(_) |  | (_ (_| |
            ae_th = defaultdict(dict)
            for info in data_th:

                run_id = info[1]
                name = info[-4]
                formula_raw = info[0]

                ao_tmp = -d_energy[run_id][name]
                for name_at, number in eval(formula_raw):
                    ao_tmp += number * d_energy[run_id][name_at]
                ae_th[run_id][name] = ao_tmp

        #______     _       _
        #| ___ \   (_)     | |
        #| |_/ / __ _ _ __ | |_
        #|  __/ '__| | '_ \| __|
        #| |  | |  | | | | | |_
        #\_|  |_|  |_|_| |_|\__|
        #

        line = "#Run_id method basis geo comments name energy".split()
        if arguments["""--get_ae"""]:
            line += "Ae_th Ae_exp Diff".split()

        print ' '.join('{:<22}'.format(i) for i in line)

        for info in data_th:

            name = info[-4]
            run_id = info[1]

            line = list(info[1:7]) + [d_energy[run_id][name]]

            if arguments["--get_ae"]:
                ae_th_tmp = ae_th[run_id][name]
                line += [ae_th_tmp]

                if name in ae_exp:
                    ae_exp_tmp = ae_exp[name]
                    line += [ae_exp_tmp, ae_exp_tmp - ae_th_tmp]

            print ' '.join('{:<22}'.format(i) for i in line)
