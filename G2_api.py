#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Welcome to the G2 Api! Grab all the G2 data you're dreaming of.

Usage:
  G2_api.py (-h | --help)
  G2_api.py list_run [--order_by=column...]
                     [--ele=element_name...]
                     [--geo=geometry_name...]
                     [--basis=basis_name...]
                     [--method=method_name...]
                     [--all_children]
  G2_api.py get_energy [--order_by=column...]
                       [--run_id=id...]
                       [--ele=element_name...]
                       [--geo=geometry_name...]
                       [--basis=basis_name...]
                       [--method=method_name...]
                       [--without_pt2]
                       [--get_ae]
                       [--all_children]
  G2_api.py --version

Options:
  --help                 Here you go.
  --without_pt2          Show all the data without adding the PT2 when avalaible.
  --get_ae               Show the atomization energy (both theorical and experiment) when avalaible.
  --all_children         Find all the children of the ele.
  All the other          Filter the data or ordering it. See example.

/!\ If you use --get_ae and filter by ele don't forger to use --all_children !

Example of use:
  ./G2_api.py list_run --method cipsi
  ./G2_api.py get_energy --run_id 11 --order_by num_elec --without_pt2
  ./G2_api.py get_energy --basis cc-pvdz --ele AlCl --ele Li2 --get_ae --all_children
"""

version = "1.0.1"

import sys
import os
from collections import defaultdict

try:
    from misc.docopt import docopt
except:
    print "You need docopt. Git reset if not exist"
    sys.exit(1)

try:
    import sqlite3
except:
    print "Sorry, you need sqlite3"
    sys.exit(1)


try:
    from misc.pprint_table import pprint_table
except:
    print "You need pprint Git reset if not exist"


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
        return False


def cond_sql_or(table_name, l_value, l=[]):

    dmy = " OR ".join(['%s = "%s"' % (table_name, i) for i in l_value])
    if dmy:
        l.append("(%s)" % dmy)

    return l

if __name__ == '__main__':

    path = os.path.dirname(sys.argv[0]) + "/misc/g2.db"
    if not isSQLite3(path):
        print "'%s' is not a SQLite3 database file" % path
        print sys.exit(1)

    conn = sqlite3.connect(path)
    c = conn.cursor()

    arguments = docopt(__doc__, version='G2 Api ' + version)

    # ______ _ _ _
    # |  ___(_) | |
    # | |_   _| | |_ ___ _ __
    # |  _| | | | __/ _ \ '__|
    # | |   | | | ||  __/ |
    # \_|   |_|_|\__\___|_|

    #| ||_  _  __ _
    #|^|| |(/_ | (/_
    d = {"run_id": "--run_id",
         "geo": "--geo",
         "basis": "--basis",
         "method": "--method"}

    str_ = []
    for k, v in d.items():
        str_ = cond_sql_or(k, arguments[v], str_)

    ele = arguments["--ele"]

    if ele:

        if arguments["--all_children"]:
            # Find all this children of the element; this is the new conditions
            cond = " ".join(cond_sql_or("name", ele))
            c.execute("""SELECT name, formula
                           FROM id_tab
                          WHERE {where_cond}""".format(where_cond=cond))

            list_name_needed = ()
            for name, formula_raw in c.fetchall():
                list_name_needed += (name,)
                for atom, number in eval(formula_raw):
                    list_name_needed += (atom,)

            str_ = cond_sql_or("ele", list_name_needed, str_)
        else:
            str_ = cond_sql_or("ele", ele, str_)

    cmd_where = " AND ".join(str_)
    if not cmd_where:
        cmd_where = "(1)"

    # _     _     _
    #| |   (_)   | |
    #| |    _ ___| |_   _ __ _   _ _ __
    #| |   | / __| __| | '__| | | | '_ \
    #| |___| \__ \ |_  | |  | |_| | | | |
    #\_____/_|___/\__| |_|   \__,_|_| |_|
    if arguments["list_run"]:

        c.execute(
            """SELECT run_id,
                 method_name method,
                  basis_name basis,
                    geo_name geo,
                    comments,
                        name ele
                        FROM output_tab
                       WHERE {where_cond}
                    GROUP BY run_id""".format(where_cond=cmd_where))

        # ___
        #  |  _. |_  |  _
        #  | (_| |_) | (/_
        table = []
        header = ["Run_id", "Method", "Basis", "Geo", "Comments"]

        table.append(header)
        table.extend(c.fetchall())
    # _____
    #|  ___|
    #| |__ _ __   ___ _ __ __ _ _   _
    #|  __| '_ \ / _ \ '__/ _` | | | |
    #| |__| | | |  __/ | | (_| | |_| |
    #\____/_| |_|\___|_|  \__, |\__, |
    #                      __/ | __/ |
    #                     |___/ |___/
    elif arguments["get_energy"]:

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
                     WHERE {cmd_where}
                    """.format(cmd_where=cmd_where))

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
                d_energy[run_id][name] = float(c_energy)
                if not arguments["--without_pt2"]:
                    d_energy[run_id][name] += float(c_pt2)
        #
        #  /\ _|_  _  ._ _  o _   _. _|_ o  _  ._
        # /--\ |_ (_) | | | | /_ (_|  |_ | (_) | |
        if arguments["--get_ae"]:

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
                ae_exp[name] = energy + zpe

            ae_th = defaultdict(dict)
            for info in data_th:

                run_id = info[1]
                name = info[-4]
                formula_raw = info[0]

                ao_tmp = -d_energy[run_id][name]
                for name_at, number in eval(formula_raw):
                    ao_tmp += number * d_energy[run_id][name_at]
                ae_th[run_id][name] = ao_tmp
        # ___
        #  |  _. |_  |  _
        #  | (_| |_) | (/_
        table = []

        line = "#Run_id method basis geo comments ele energy".split()
        if arguments["""--get_ae"""]:
            line += "Ae_th Ae_exp Diff".split()

        table.append(line)

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
                else:
                    line += [""] * 2

            table.append(line)
        #  _
        # / \ ._ _|  _  ._   |_
        # \_/ | (_| (/_ |    |_) \/
        #                        /
        cmd_order = arguments["--order_by"]
        for arg in cmd_order:
            try:
                index = table[0].index(arg)
            except:
                from misc.docopt import parse_section
                for i in parse_section('usage:', __doc__):
                    print i
                sys.exit(1)
            else:
                table = sorted(table, key=lambda x: x[6], reverse=True)

    #______     _       _
    #| ___ \   (_)     | |
    #| |_/ / __ _ _ __ | |_
    #|  __/ '__| | '_ \| __|
    #| |  | |  | | | | | |_
    #\_|  |_|  |_|_| |_|\__|
    pprint_table(table)
    print "#GnuPlot cmd for energy : "
    print "# $gnuplot -e",
    print "\"set xtics rotate;",
    print "plot 'dat' u 7:xtic(6) w lp title 'energy';",
    print "pause -1 \""
