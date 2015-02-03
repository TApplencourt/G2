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
                        [--literature]
  G2_result.py list_ele --run_id=<id> [--mising]
  G2_result.py get_energy [--order_by=<column>]
                          [--run_id=<id>...]
                          [--ele=<element_name>...  [--all_children] | --like_toulouse]
                          [--geo=<geometry_name>...]
                          [--basis=<basis_name>...]
                          [--method=<method_name>...]
                          [--without_pt2]
                          [--zpe]
                          [--estimated_exact [--literature]]
                          [--ae [--literature]]
                          [--gnuplot]
  G2_result.py --version

Options:
  --help        Here you go.
  list_run      List all the data avalaible and the MAD
  list_ele      List the element in the selected run_id
  get_energy    Print the energy & energy related values
                    (PT2, error bar, atomization energies,
                    estimated_exact, ...)

Options for list_run and get_energy:
  --order_by                You can order by a collumn name displayed:
                                `--order_by mad` for example.
  --ele OR --like_toulouse  Show only run's who contain ALL of the element required.
  --geo,basis,method        Show only run's who satisfy ALL the requirements.
                                For example `--geo MP2 --basis cc-pvDZ`
                                show only the run who contain
                                both this geo and this basis set.
  --literature              If you want to use the literature ZPE/AE,
                                and not the NIST one for the calcul of
                                the MAD, estimated_exact and the theorical
                                atomization energies.

Options for list_ele:
  --run_id                  Show the list_ele for this run_id
  --missing                 Show the diffence between "like_toulouse" list and "list_ele"

Options specifics to get_energy:
  --without_pt2         Show all the data without adding the PT2 when avalaible.
  --ae                  Show the atomization energy when avalaible
                           (both theorical and experiment).
                            ae_th = E_mol - \sum E_atom  + zpe
  --estimated_exact     Show the estimated exact energy.
                            E_est_exact = \sum E^{exact}_{atom} - zpe
  --all_children        Show all the children of the element
                            Example for AlCl will show Al and Cl.
  --gnuplot             Print the result in a GNUPLOT readable format.
  All the other         Filter the data or ordering it. See example.

Example of use:
  ./G2_result.py list_run --method 'CCSD(T)'
  ./G2_result.py get_energy --run_id 11 --order_by e --without_pt2 --estimated_exact
  ./G2_result.py get_energy --basis "cc-pvdz" --ele AlCl --ele Li2 --ae --order_by ae_diff
"""

version = "2.5.4"

import sys
from collections import defaultdict

try:
    from src.docopt import docopt
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
        arguments["--ae"] = True

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

    # Add all the children of a element to l_ele if need.
    # For example for the calculate the AE of AlCl we need Al and Cl
    if l_ele and any(arguments[k] for k in ["--all_children",
                                            "--ae",
                                            "--estimated_exact"]):

        # Find all this children of the element; this is the new conditions
        cond = " ".join(cond_sql_or("name", l_ele))

        c.execute("""SELECT name, formula
                           FROM id_tab
                          WHERE {where_cond}""".format(where_cond=cond))

        for name, formula_raw in c.fetchall():
            for atom, number in eval(formula_raw):
                l_ele.add(atom)

    # Ordered l_ele for the printing in order
    l_ele_to_print = list_toulouse if arguments["--like_toulouse"] else l_ele

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

    cond_filter = []
    for k, v in d.items():
        cond_filter += cond_sql_or(k, arguments[v])

    # We need to find the run_id who containt ALL the ele is needed
    if l_ele:
        cond_filter_ele = ["".join(["name in ('", "','".join(l_ele), "')"])]
    else:
        cond_filter_ele = []

    # Maybe we dont need to filter
    # Else just simplify the expresion :
    #   geo basis method -> run_id
    if not any((cond_filter, cond_filter_ele)):
        cmd_where = "(1)"
    else:
        cmd_where_tmp = " AND ".join(cond_filter + cond_filter_ele)

        # Select all the run_id where all the condition is good
        cmd_having = "count(name) = {0}".format(len(l_ele)) if l_ele else "(1)"

        c.execute("""SELECT run_id
                    FROM (SELECT run_id,
                                   name,
                            method_name method,
                             basis_name basis,
                            geo_name geo
                          FROM output_tab
                          WHERE {0})
                    GROUP BY run_id
                    HAVING {1}""".format(cmd_where_tmp, cmd_having))

        l_run_id = [i[0] for i in c.fetchall()]

        # Now only the run_id count. It containt all information
        cond_filter = ["run_id in (" + ",".join(map(str, l_run_id)) + ")"]

        cmd_where = " AND ".join(cond_filter + cond_filter_ele)

    #  _____
    # |  ___|
    # | |__ _ __   ___ _ __ __ _ _   _
    # |  __| '_ \ / _ \ '__/ _` | | | |
    # | |__| | | |  __/ | | (_| | |_| |
    # \____/_| |_|\___|_|  \__, |\__, |
    #                       __/ | __/ |
    #                      |___/ |___/

    from src.object import *

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
                          c_pt2,
                       q_energy,
                          q_err
                           FROM output_tab
                     INNER JOIN id_tab
                             ON output_tab.name = id_tab.name
                          WHERE {}""".format(cmd_where.replace("name", "ele")))

    data_cur_energy = c.fetchall()
    # Because formula is wrong for Anion and Cation
    data_cur_energy[:] = [x for x in data_cur_energy
                          if not ("+" in x[0] or "-" in x[0])]

    for info in data_cur_energy:
        run_id = info[1]
        name = info[6]
        s_energy = info[7]
        c_energy = info[8]
        c_pt2 = info[9]
        q_energy = info[10]
        q_err = info[11]

        if s_energy:
            d_energy[run_id][name] = float(s_energy)

        if c_energy:
            d_energy[run_id][name] = float(c_energy)
            if not arguments["--without_pt2"]:
                d_energy[run_id][name] += float(c_pt2)

        if q_energy:
            d_energy[run_id][name] = v_un(float(q_energy), float(q_err))

    #  __
    #   / ._   _    ()     /\   _     _     ._
    #  /_ |_) (/_   (_X   /--\ (/_   (/_ >< |_)
    #     |                                 |
    if any(arguments[k] for k in ["--zpe",
                                  "--ae",
                                  "--estimated_exact"]):

        method_id = 10 if arguments["--literature"] else 1

        cond_filter = cond_filter_ele + ['(basis_id=1)',
                                         '(method_id=%d)' % (method_id)]

        cmd_where = " AND ".join(cond_filter)

        ae_exp = defaultdict()
        zpe_exp = defaultdict()

        c.execute("""SELECT name,
                         formula,
                             zpe,
                            kcal,
                        kcal_err
                            FROM id_tab
                    NATURAL JOIN zpe_tab
                    NATURAL JOIN atomization_tab
                           WHERE {cmd_where}""".format(cmd_where=cmd_where))

        data_ae_zp = c.fetchall()
        for info in data_ae_zp:
            name = info[0]
            zpe = info[2]
            kcal = info[3]
            kcal_err = info[4]

            zpe = zpe * 4.55633e-06
            energy = kcal * 0.00159362
            energy_err = kcal_err * 0.00159362 if kcal_err else 0.

            ae_exp[name] = v_un(energy, energy_err)
            zpe_exp[name] = zpe

    #  _
    # |_  _ _|_      _      _.  _ _|_    _  ._   _  ._ _
    # |_ _>  |_ o   (/_ >< (_| (_  |_   (/_ | | (/_ | (_| \/
    #                                                  _| /
    if arguments["--estimated_exact"]:
        # Get Davidson est. atomics energies
        cmd_where = " AND ".join(cond_filter_ele + ['(run_id = "21")'])

        c.execute("""SELECT name,
                          energy
                            FROM simple_energy_tab
                    NATURAL JOIN id_tab
                           WHERE {cmd_where}""".format(cmd_where=cmd_where))

        est_exact_energy = defaultdict(dict)
        for name, energy in c.fetchall():
            est_exact_energy[name] = float(energy)

        # Calc estimated exact molecules energies
        for info in data_ae_zp:
            name = info[0]
            formula_raw = info[1]

            try:
                emp_tmp = -ae_exp[name] - zpe_exp[name]
                for name_atome, number in eval(formula_raw):
                    emp_tmp += number * est_exact_energy[name_atome]
            except KeyError:
                pass
            else:
                est_exact_energy[name] = emp_tmp

    #   /\ _|_  _  ._ _  o _   _. _|_ o  _  ._    _|_ |_
    #  /--\ |_ (_) | | | | /_ (_|  |_ | (_) | |    |_ | |
    if arguments["--ae"]:

        # Init all the dict
        ae_th = defaultdict(dict)
        ae_diff = defaultdict(dict)

        # Update dict if data avalaible
        for info in data_cur_energy:
            run_id = info[1]
            name = info[6]
            formula_raw = info[0]

            d_e_rid = d_energy[run_id]

            try:
                ao_th_tmp = d_e_rid[name] + zpe_exp[name]
                for name_atome, number in eval(formula_raw):
                    ao_th_tmp -= d_e_rid[name_atome] * number
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
            d_mad[run_id] = sum(map(abs, l_energy)) / len(l_energy)

        header_name = "Run_id Method Basis Geo Comments mad".split()
        header_unit = [DEFAULT_CARACTER] * 5 + ["kcal/mol"]

        # Group by Run_id and then put the mad if existing
        table_body = []
        from itertools import groupby
        for key, group in groupby(data_cur_energy, lambda x: x[1:6]):

            mad = d_mad[key[0]] * 630 if key[0] in d_mad else DEFAULT_CARACTER
            table_body.append(key + (mad,))

    #  _
    # |_ ._   _  ._ _
    # |_ | | (/_ | (_| \/
    #               _| /
    elif arguments["get_energy"]:

        table_body = []

        header_name = "run_id method basis geo comments ele e".split()
        header_unit = [DEFAULT_CARACTER] * 6 + ["Hartree"]

        if arguments["--zpe"]:
            header_name += "zpe".split()
            header_unit += "Hartree".split()

        if arguments["--estimated_exact"]:
            header_name += "e_est_exact e_diff".split()
            header_unit += "Hartree Hartree".split()
        if arguments["--ae"]:
            header_name += "ae_th ae_exp ae_diff".split()
            header_unit += "Hartree Hartree Hartree".split()

        for info in data_cur_energy:

            name = info[6]
            run_id = info[1]

            comments = info[5].replace("1M_Dets_NO_10k_Dets_TruePT2",
                                       "1M_Dets_NO\n_10k_Dets_TruePT2")

            comments = comments.replace("1M_Dets_NO_1k_Dets_TruePT2",
                                        "1M_Dets_NO\n_1k_Dets_TruePT2")

            comments = comments.replace(
                "Davidson nonrelativistics atomics energies",
                "Davidson nonrelativistics\natomics energies")

            line = list(info[1:5])
            line += [comments, info[6], d_energy[run_id][name]]

            if (arguments["--ele"] and name not in arguments["--ele"]
                    and not arguments["--all_children"]):
                continue

            if arguments["--zpe"]:
                line += [zpe_exp[name]
                         if name in zpe_exp else DEFAULT_CARACTER]

            if arguments["--estimated_exact"]:

                line += [est_exact_energy[name]
                         if name in est_exact_energy else DEFAULT_CARACTER]

                line += [d_energy[run_id][name] - est_exact_energy[name]
                         if name in est_exact_energy and
                         name in d_energy[run_id] else DEFAULT_CARACTER]

            if arguments["--ae"]:

                line += [ae_th[run_id][name]
                         if name in ae_th[run_id] else DEFAULT_CARACTER]
                line += [ae_exp[name] if name in ae_exp else DEFAULT_CARACTER]
                line += [ae_diff[run_id][name]
                         if name in ae_th[run_id] else DEFAULT_CARACTER]

            table_body.append(line)

        # Order by l_ele if given
        if l_ele:
            table_body = [
                l for i in l_ele_to_print for l in table_body if l[5] == i]

    #  _____ _                           _                      _
    # |  ___| |                         | |                    ( )
    # | |__ | | ___ _ __ ___   ___ _ __ | |_   _ __ _   _ _ __ |/ ___
    # |  __|| |/ _ \ '_ ` _ \ / _ \ '_ \| __|  | '__| | | | '_ \  / __|
    # | |___| |  __/ | | | | |  __/ | | | |_   | |  | |_| | | | | \__ \
    # \____/|_|\___|_| |_| |_|\___|_| |_|\__|  |_|   \__,_|_| |_| |___/
    #
    # List all the element of a run_id
    if arguments["list_ele"]:

        run_id = arguments["--run_id"]

        c.execute("""SELECT name
                    FROM output_tab
                    WHERE run_id = (?)""", run_id)

        l_ele = [ele[0] for ele in c.fetchall()]

        header_name = ["ele"]
        header_unit = [""]

        if arguments["--mising"]:
            from src.misc_info import list_toulouse

            table_body = [[ele] for ele in list_toulouse if ele not in l_ele]
        else:
            table_body = [[ele] for ele in l_ele]

    #  _
    # / \ ._ _|  _  ._   |_
    # \_/ | (_| (/_ |    |_) \/
    #                        /

    # Order by cli argument if given
    for arg in arguments["--order_by"]:
        try:
            index = header_name.index(arg)
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

    from src.terminaltables import AsciiTable

    table_body = [["{:>10.5f}".format(i) if isinstance(i, float) else i
                   for i in line]
                  for line in table_body]

    # AsciiTable need str
    table_body = [map(str, i) for i in table_body]

    if not arguments["--gnuplot"]:

        table_data = [header_name] + [header_unit] + table_body
        table = AsciiTable(table_data)
        print table.table
    else:
        JOIN_CARACTER = ", "
        print "#" + ", ".join(header_name)
        for i in table_body:
            print ", ".join([l.replace(" ", "") for l in i])

        print "#GnuPlot cmd for energy : "
        print "# $gnuplot -e",
        print "\"set xtics rotate;",
        print "plot 'dat' u 7:xtic(6) w lp title 'energy';",
        print "pause -1 \""
