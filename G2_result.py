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
  G2_api.py get_energy [--order_by=column]
                       [--run_id=id...]
                       [--ele=element_name...]
                       [--geo=geometry_name...]
                       [--basis=basis_name...]
                       [--method=method_name...]
                       [--without_pt2]
                       [--estimated_exact]
                       [--get_ae]
                       [--all_children]
  G2_api.py --version

Options:
  --help                 Here you go.
  --without_pt2          Show all the data without adding the PT2 when avalaible.
  --get_ae               Show the atomization energy (both theorical and experiment) when avalaible.
  --all_children         Find all the children of the ele.
  All the other          Filter the data or ordering it. See example.

Example of use:
  ./G2_api.py list_run --method cipsi
  ./G2_api.py get_energy --run_id 11 --order_by energy --without_pt2
  ./G2_api.py get_energy --basis cc-pvdz --ele AlCl --ele Li2 --get_ae --order_by diff
"""

version = "1.0.2"

import sys
import os
from collections import defaultdict

try:
    from misc.docopt import docopt
    from misc.pprint_table import pprint_table
    from misc.SQL_util import isSQLite3, cond_sql_or
except:
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)

try:
    import sqlite3
except:
    print "Sorry, you need sqlite3"
    sys.exit(1)


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

    # \    / |_   _  ._ _
    #  \/\/  | | (/_ | (/_
    #
    d = {"run_id": "--run_id",
         "geo": "--geo",
         "basis": "--basis",
         "method": "--method"}

    str_ = []
    for k, v in d.items():
        str_ += cond_sql_or(k, arguments[v])

    ele = arguments["--ele"]

    if ele:
        str_ele = cond_sql_or("ele", ele)

        list_key = ["--all_children", "--get_ae", "--estimated_exact"]
        if all(k in arguments for k in list_key):
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

            str_ele = cond_sql_or("ele", list_name_needed)
    else:
        str_ele = []

    cmd_where = " AND ".join(str_ + str_ele)
    if not cmd_where:
        cmd_where = "(1)"
    # _     _     _
    #| |   (_)   | |
    #| |    _ ___| |_   _ __ _   _ _ __
    #| |   | / __| __| | '__| | | | '_ \
    #| |___| \__ \ |_  | |  | |_| | | | |
    #\_____/_|___/\__| |_|   \__,_|_| |_|
    if arguments["list_run"]:

        c.execute("""SELECT run_id,
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
        #
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
        d_energy = defaultdict(dict)

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
                              WHERE {cmd_where}""".format(cmd_where=cmd_where))

        data_cur_energy = c.fetchall()
        # Because formula is wrong for Anion and Cation
        data_cur_energy[:] = [x for x in data_cur_energy
                              if not ("+" in x[0] or "-" in x[0])]

        for info in data_cur_energy:
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

        #  /\ _|_  _  ._ _  o _   _. _|_ o  _  ._     _     ._
        # /--\ |_ (_) | | | | /_ (_|  |_ | (_) | |   (/_ >< |_)
        #                                                   |
        if arguments["--get_ae"] or arguments["--estimated_exact"]:

            str_ = str_ele + ['(basis_id=1)', '(method_id=1)']
            cmd_where = " AND ".join(str_)

            ae_exp = defaultdict()
            c.execute("""SELECT name ele,
                             formula,
                                 zpe,
                                kcal
                                FROM id_tab
                        NATURAL JOIN zpe_tab
                        NATURAL JOIN atomization_tab
                               WHERE {cmd_where}""".format(cmd_where=cmd_where))

            data_ae_zp = c.fetchall()
            for info in data_ae_zp:
                name = info[0]
                zpe = info[2]
                kcal = info[3]

                zpe = zpe * 4.55633e-06
                energy = kcal * 0.00159362
                ae_exp[name] = energy + zpe

         #  _
         # |_  _ _|_      _      _.  _ _|_    _  ._   _  ._ _
         # |_ _>  |_ o   (/_ >< (_| (_  |_   (/_ | | (/_ | (_| \/
         #                                                  _| /
        if arguments["--estimated_exact"]:
            # Get Davidson est. atomics energies
            cmd_where = " AND ".join(str_ele + ['(run_id = "21")'])

            c.execute("""SELECT name ele,
                              energy
                                FROM simple_energy_tab
                        NATURAL JOIN id_tab
                               WHERE {cmd_where}""".format(cmd_where=cmd_where))

            energy_th = defaultdict()
            for name, energy in c.fetchall():
                energy_th[name] = float(energy)

            # Calc est. molecul energies
            est_exact_energy = defaultdict(dict)

            for info in data_ae_zp:
                name = info[0]
                formula_raw = info[1]

                try:
                    emp_tmp = ae_exp[name]
                    for name_atome, number in eval(formula_raw):
                        emp_tmp += number * energy_th[name_atome]
                except KeyError:
                    pass
                else:
                    est_exact_energy[name] = -emp_tmp

        #
        #  /\ _|_  _  ._ _  o _   _. _|_ o  _  ._    _|_ |_
        # /--\ |_ (_) | | | | /_ (_|  |_ | (_) | |    |_ | |
        #
        if arguments["--get_ae"]:
            ae_th = defaultdict(dict)
            for info in data_cur_energy:
                run_id = info[1]
                name = info[-4]
                formula_raw = info[0]

                d_e_rid = d_energy[run_id]

                try:
                    ao_th_tmp = d_e_rid[name]
                    for name_atome, number in eval(formula_raw):
                        ao_th_tmp -= number * d_e_rid[name_atome]
                except KeyError:
                    pass
                else:
                    ae_th[run_id][name] = -ao_th_tmp
        # ___
        #  |  _. |_  |  _
        #  | (_| |_) | (/_
        #
        table = []

        line = "#Run_id method basis geo comments ele energy".split()

        if arguments["--estimated_exact"]:
            line += "estimated_exact diff_est_exact".split()

        if arguments["""--get_ae"""]:
            line += "ae_th ae_exp diff".split()

        table.append(line)

        for info in data_cur_energy:
            name = info[-4]
            run_id = info[1]

            line = list(info[1:7]) + [d_energy[run_id][name]]

            if (arguments["--ele"] and name not in arguments["--ele"]
                    and not arguments["--all_children"]):
                continue

            if arguments["--estimated_exact"]:

                line += [est_exact_energy[name]
                         if name in est_exact_energy else ""]
                line += [d_energy[run_id][name] - est_exact_energy[name]
                         if name in est_exact_energy and name in d_energy[run_id] else ""]

            if arguments["--get_ae"]:

                line += [ae_th[run_id][name] if name in ae_th[run_id] else ""]
                line += [ae_exp[name] if name in ae_exp else ""]
                line += [ae_exp[name] - ae_th[run_id][name]
                         if name in ae_exp and name in ae_th[run_id] else ""]

            table.append(line)
        #  _
        # / \ ._ _|  _  ._   |_
        # \_/ | (_| (/_ |    |_) \/
        #                        /
        cmd_order = arguments["--order_by"]
        for arg in cmd_order:
            try:
                index = table[0].index(arg)
            except ValueError:
                from misc.docopt import parse_section
                for i in parse_section('usage:', __doc__):
                    print i
                sys.exit(1)
            else:
                table = sorted(table, key=lambda x: x[index], reverse=True)
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
