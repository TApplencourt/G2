#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Welcome to the G2 Api! Grab all the G2 data you're dreaming of.

Usage:
  G2_result.py (-h | --help)
  G2_result.py list_run [--order_by=<column>...]
                        [--ele=<element_name>... | --like_toulouse]
                        [--geo=<geometry_name>...]
                        [--basis=<basis_name>...]
                        [--method=<method_name>...]
                        [--all_children]
  G2_result.py get_energy [--order_by=<column>]
                          [--run_id=<id>...]
                          [--ele=<element_name>...  [--all_children] | --like_toulouse]
                          [--geo=<geometry_name>...]
                          [--basis=<basis_name>...]
                          [--method=<method_name>...]
                          [--without_pt2]
                          [--estimated_exact]
                          [--get_ae]

  G2_result.py --version

Options:
  --help                 Here you go.
  --without_pt2          Show all the data without adding the PT2 when avalaible.
  --get_ae               Show the atomization energy when avalaible
                         (both theorical and experiment).
  --all_children         Find all the children of the element
                         (Example for AlCl will find Al and Cl).
  --estimated_exact      Show the estimated exact energy.
  All the other          Filter the data or ordering it. See example.

Example of use:
  ./G2_result.py list_run --method CIPSI
  ./G2_result.py get_energy --run_id 11 --order_by e --without_pt2 --estimated_exact
  ./G2_result.py get_energy --basis "cc-pvdz" --ele AlCl --ele Li2 --get_ae --order_by ae_diff
"""

version = "1.0.4"

import sys
from collections import defaultdict
from collections import OrderedDict

try:
    from src.docopt import docopt
    from src.pprint_table import pprint_table
    from src.SQL_util import cond_sql_or
    from src.SQL_util import c
except:
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)


if __name__ == '__main__':

    arguments = docopt(__doc__, version='G2 Api ' + version)

    #  ___
    #   |  ._  o _|_
    #  _|_ | | |  |_
    #

    # For calculating the MAD we need the AE
    if arguments["list_run"]:
        arguments["--get_ae"] = True

    DEFAULT_CARACTER = ""
    # ______ _ _ _
    # |  ___(_) | |
    # | |_   _| | |_ ___ _ __
    # |  _| | | | __/ _ \ '__|
    # | |   | | | ||  __/ |
    # \_|   |_|_|\__\___|_|

    #
    # |  o  _ _|_    _  |  _  ._ _   _  ._ _|_
    # |_ | _>  |_   (/_ | (/_ | | | (/_ | | |_
    #

    # Set the list of element to get and to print
    # By defalt, if l_ele is empty get all

    if arguments["--ele"]:
        l_ele = set(arguments["--ele"])
    elif arguments["--like_toulouse"]:
        from src.misc_info import list_toulouse
        l_ele = set(list_toulouse)
    else:
        l_ele = set()

    # Add new ele to l_ele if need : all the children of a element
    # For example for the calculate the AE of AlCl we need Al and Cl
    if any(arguments[k] for k in ["--all_children",
                                  "--get_ae",
                                  "--estimated_exact"]):

        # Find all this children of the element; this is the new conditions
        cond = " ".join(cond_sql_or("name", l_ele))
        c.execute("""SELECT name, formula
                           FROM id_tab
                          WHERE {where_cond}""".format(where_cond=cond))

        for name, formula_raw in c.fetchall():
            l_ele.add(name)
            for atom, number in eval(formula_raw):
                l_ele.add(atom)

    #  _
    # |_ o | _|_  _  ._    _ _|_ ._ o ._   _
    # |  | |  |_ (/_ |    _>  |_ |  | | | (_|
    #                                      _|
    #
    # Create the cmd string who will be executed by the db

    d = {"run_id": "--run_id",
         "geo": "--geo",
         "basis": "--basis",
         "method": "--method"}

    cmd_filter = []
    for k, v in d.items():
        cmd_filter += cond_sql_or(k, arguments[v])

    cmd_filter_ele = cond_sql_or("ele", l_ele) if l_ele else []

    cmd_where = " AND ".join(cmd_filter + cmd_filter_ele)
    if not cmd_where:
        cmd_where = "(1)"

    #  _____
    # |  ___|
    # | |__ _ __   ___ _ __ __ _ _   _
    # |  __| '_ \ / _ \ '__/ _` | | | |
    # | |__| | | |  __/ | | (_| | |_| |
    # \____/_| |_|\___|_|  \__, |\__, |
    #                       __/ | __/ |
    #                      |___/ |___/

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

        cmd_filter = cmd_filter_ele + ['(basis_id=1)', '(method_id=1)']
        cmd_where = " AND ".join(cmd_filter)

        ae_exp = defaultdict()
        zpe_exp = defaultdict()

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
            ae_exp[name] = energy
            zpe_exp[name] = zpe

    #  _
    # |_  _ _|_      _      _.  _ _|_    _  ._   _  ._ _
    # |_ _>  |_ o   (/_ >< (_| (_  |_   (/_ | | (/_ | (_| \/
    #                                                  _| /
    if arguments["--estimated_exact"]:
        # Get Davidson est. atomics energies
        cmd_where = " AND ".join(cmd_filter_ele + ['(run_id = "21")'])

        c.execute("""SELECT name ele,
                              energy
                                FROM simple_energy_tab
                        NATURAL JOIN id_tab
                               WHERE {cmd_where}""".format(cmd_where=cmd_where))

        energy_th = defaultdict()
        for name, energy in c.fetchall():
            energy_th[name] = float(energy)

        # Calc estimated exact molecules energies
        est_exact_energy = defaultdict(dict)

        for info in data_ae_zp:
            name = info[0]
            formula_raw = info[1]

            try:
                emp_tmp = -ae_exp[name]
                for name_atome, number in eval(formula_raw):
                    emp_tmp += number * energy_th[name_atome]
            except KeyError:
                pass
            else:
                est_exact_energy[name] = emp_tmp

    #   /\ _|_  _  ._ _  o _   _. _|_ o  _  ._    _|_ |_
    #  /--\ |_ (_) | | | | /_ (_|  |_ | (_) | |    |_ | |
    if arguments["--get_ae"]:

        # Init all the dict
        ae_th = defaultdict(dict)
        ae_diff = defaultdict(dict)

        # Update dict if data avalaible
        for info in data_cur_energy:
            run_id = info[1]
            name = info[-4]
            formula_raw = info[0]

            d_e_rid = d_energy[run_id]

            try:
                ao_th_tmp = d_e_rid[name] + zpe_exp[name]
                for name_atome, number in eval(formula_raw):
                    ao_th_tmp -= number * d_e_rid[name_atome]
            except KeyError:
                pass
            else:
                ae_th[run_id][name] = -ao_th_tmp

            try:
                ae_diff[run_id][name] = ae_exp[name] - ae_th[run_id][name]
            except KeyError:
                pass
    #  _____     _     _
    # |_   _|   | |   | |
    #   | | __ _| |__ | | ___
    #   | |/ _` | '_ \| |/ _ \
    #   | | (_| | |_) | |  __/
    #   \_/\__,_|_.__/|_|\___|

    # Create the table which will be printed
    #  | o  _ _|_   ._    ._
    #  | | _>  |_   | |_| | |
    if arguments["list_run"]:

        d_mad = defaultdict()
        # mad = mean( abs( x_i - mean(x) ) )
        for run_id in ae_diff:
            l_energy = ae_diff[run_id].values()

            mean = sum(l_energy) / len(l_energy)
            abs_e_m = [abs(energy - mean) for energy in l_energy]
            mad = sum(abs_e_m) / len(l_energy)

            d_mad[run_id] = mad

        header = ["Run_id", "Method", "Basis", "Geo", "Comments", "mad"]

        # Group by Run_id and then put the mad if existing
        table_body = []
        from itertools import groupby
        for key, group in groupby(data_cur_energy, lambda x: x[1:6]):

            mad = d_mad[key[0]] if key[0] in d_mad else DEFAULT_CARACTER
            table_body.append(key + (mad,))

    #  _
    # |_ ._   _  ._ _
    # |_ | | (/_ | (_| \/
    #               _| /
    elif arguments["get_energy"]:

        table_body = []

        header = "#Run_id method basis geo comments ele e".split()

        if arguments["--estimated_exact"]:
            header += "e_est_exact e_diff".split()

        if arguments["--get_ae"]:
            header += "ae_th ae_exp ae_diff".split()

        for info in data_cur_energy:

            name = info[-4]
            run_id = info[1]

            line = list(info[1:7]) + [d_energy[run_id][name]]

            if (arguments["--ele"] and name not in arguments["--ele"]
                    and not arguments["--all_children"]):
                continue

            if arguments["--estimated_exact"]:

                line += [est_exact_energy[name]
                         if name in est_exact_energy else DEFAULT_CARACTER]
                line += [d_energy[run_id][name] - est_exact_energy[name]
                         if name in est_exact_energy and
                         name in d_energy[run_id] else DEFAULT_CARACTER]

            if arguments["--get_ae"]:

                line += [ae_th[run_id][name]
                         if name in ae_th[run_id] else DEFAULT_CARACTER]
                line += [ae_exp[name] if name in ae_exp else DEFAULT_CARACTER]
                line += [ae_diff[run_id][name]
                         if name in ae_th[run_id] else DEFAULT_CARACTER]

            table_body.append(line)

        # Order by l_ele if given
        if l_ele:
            table_body = [l for i in l_ele for l in table_body if l[5] == i]

    #  _
    # / \ ._ _|  _  ._   |_
    # \_/ | (_| (/_ |    |_) \/
    #                        /

    # Order by cli argument if given
    for arg in arguments["--order_by"]:
        try:
            index = header.index(arg)
        except ValueError:
            print "For --order_by you need a column name"
            sys.exit(1)
        else:
            table_body = sorted(
                table_body,
                key=lambda x: x[index],
                reverse=True)

    # ______     _       _
    # | ___ \   (_)     | |
    # | |_/ / __ _ _ __ | |_
    # |  __/ '__| | '_ \| __|
    # | |  | |  | | | | | |_
    # \_|  |_|  |_|_| |_|\__|
    table = [header] + table_body

    pprint_table(table)
    print "#GnuPlot cmd for energy : "
    print "# $gnuplot -e",
    print "\"set xtics rotate;",
    print "plot 'dat' u 7:xtic(6) w lp title 'energy';",
    print "pause -1 \""
