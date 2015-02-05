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
                        [--without_pt2]
  G2_result.py list_ele --run_id=<id> [--mising]
  G2_result.py get_energy [--order_by=<column>]
                          [--run_id=<id>...]
                          [--ele=<element_name>...  [--all_children] | --like_toulouse]
                          [--geo=<geometry_name>...]
                          [--basis=<basis_name>...]
                          [--method=<method_name>...]
                          [--zpe]
                          [--estimated_exact [--literature]]
                          [--ae [--literature]]
                          [--without_pt2]
                          [--gnuplot]
                          [--auto | --small | --big]
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
  --without_pt2             Show all the data without adding the PT2 when avalaible.
Options for list_ele:
  --run_id                  Show the list_ele for this run_id
  --missing                 Show the diffence between "like_toulouse" list and "list_ele"

Options specifics to get_energy:
  --ae                        Show the atomization energy when avalaible
                                 (both theorical and experiment).
                                  ae_th = E_mol - \sum E_atom  + zpe
  --estimated_exact           Show the estimated exact energy.
                                  E_est_exact = \sum E^{exact}_{atom} - zpe
  --all_children              Show all the children of the element
                                  Example for AlCl will show Al and Cl.
  --gnuplot                   Print the result in a GNUPLOT readable format.
  --auto or --small or --big  Size of the display (by default is auto)
  All the other               Filter the data or ordering it. See example.

Example of use:
  ./G2_result.py list_run --method 'CCSD(T)'
  ./G2_result.py get_energy --run_id 11 --order_by e --without_pt2 --estimated_exact
  ./G2_result.py get_energy --basis "cc-pvdz" --ele AlCl --ele Li2 --ae --order_by ae_diff
"""

version = "3.0.1"

import os
import sys
if sys.version_info[:2] != (2, 7):
    print "You need python 2.7."
    print "You can change the format for 2.6"
    print "And pass the 2to3 utility for python 3"
    sys.exit(1)

from collections import defaultdict


try:
    from src.docopt import docopt
    from src.SQL_util import cond_sql_or
    from src.SQL_util import c, conn
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

    if not any([arguments['--small'], arguments['--big']]):
        arguments['--auto'] = True

    DEFAULT_CARACTER = ""

    # Usefull Variable:

    # Get & print

    # * l_ele           List element for geting the value

    # Calcule one

    # * e_th     Dict of energies theorical / calculated   (e_th[run_id][name])
    # * zpe_exp  Dict of zpe experimental                  (zpe_exp[name])
    # * e_ee     Dict of energy estimated exact            (e_ee[name])
    # * e_diff   Dict of e_th exact - estimated exact one  (e_diff[run_id][name])
    # * ae_th    Dict of atomization energye theorcai      (ae_th[run_id][name])
    # * ae_exp   Dict of atomization experimental          (ae_ext[name])
    # * ae_diff  Dict of ae_th energy - expriement one     (ae_diff[run_id][name])
    # * run_info Dict of the geo,basis,method,comments     (run_info[run_id])

    pouce = "{:>2.5f}"
    arpent = "{:>10.5f}"

    format_dict = {"e_th": arpent,
                   "zpe_exp": pouce,
                   "e_ee": arpent,
                   "e_diff": pouce,
                   "ae_th": pouce,
                   "ae_exp": pouce,
                   "ae_diff": pouce}
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

    from src.object import v_un

    # -#-#- #
    # S q l #
    # -#-#- #

    import sqlite3
    conn.row_factory = sqlite3.Row
    c_row = conn.cursor()

    cursor = c_row.execute("""SELECT formula,
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
                          WHERE {0}""".format(cmd_where.replace("name", "ele")))

    # -#-#-#- #
    # I n i t #
    # -#-#-#- #

    e_th = defaultdict(dict)
    run_info = defaultdict()
    f_info = defaultdict()

    # -#-#-#-#-#- #
    # F i l l I n #
    # -#-#-#-#-#- *

    for r in cursor:
        # Energy
        if r['s_energy']:
            value = float(r['s_energy'])

        if r['c_energy']:
            value = float(r['c_energy'])
            if not arguments["--without_pt2"]:
                value += float(r['c_pt2'])

        if r['q_energy']:
            value = v_un(float(r['q_energy']),
                         float(r['q_err']))

        e_th[r['run_id']][r['ele']] = value
        # Info
        run_info[r['run_id']] = [r['method'], r['basis'],
                                 r['geo'], r['comments']]

        f_info[r['ele']] = r['formula']

    #  __
    #   / ._   _    ()     /\   _     _     ._
    #  /_ |_) (/_   (_X   /--\ (/_   (/_ >< |_)
    #     |                                 |
    if any(arguments[k] for k in ["--zpe",
                                  "--ae",
                                  "--estimated_exact"]):

        # -#-#- #
        # S q l #
        # -#-#- #

        method_id = 10 if arguments["--literature"] else 1

        cond_filter = cond_filter_ele + ['(basis_id=1)',
                                         '(method_id=%d)' % (method_id)]

        cmd_where = " AND ".join(cond_filter)

        cursor = c_row.execute("""SELECT name,
                         formula,
                             zpe,
                            kcal,
                        kcal_err
                            FROM id_tab
                    NATURAL JOIN zpe_tab
                    NATURAL JOIN atomization_tab
                           WHERE {cmd_where}""".format(cmd_where=cmd_where))

        # -#-#-#- #
        # I n i t #
        # -#-#-#- #

        ae_exp = defaultdict()
        zpe_exp = defaultdict()

        # -#-#-#-#-#- #
        # F i l l I n #
        # -#-#-#-#-#- *

        for r in cursor:
            zpe = r['zpe'] * 4.55633e-06
            energy = r['kcal'] * 0.00159362
            energy_err = r['kcal_err'] * 0.00159362 if r['kcal_err'] else 0.

            ae_exp[r['name']] = v_un(energy, energy_err)
            zpe_exp[r['name']] = zpe

    #  _
    # |_  _ _|_      _      _.  _ _|_    _  ._   _  ._ _
    # |_ _>  |_ o   (/_ >< (_| (_  |_   (/_ | | (/_ | (_| \/
    #                                                  _| /
    if arguments["--estimated_exact"]:

        # -#-#- #
        # S q l #
        # -#-#- #

        # Get Davidson est. atomics energies
        cmd_where = " AND ".join(cond_filter_ele + ['(run_id = "21")'])

        c.execute("""SELECT name as name_atome,
                          energy as exact_energy
                            FROM simple_energy_tab
                    NATURAL JOIN id_tab
                           WHERE {cmd_where}""".format(cmd_where=cmd_where))

        # -#-#-#- #
        # I n i t #
        # -#-#-#- #

        e_ee = defaultdict()
        e_diff = defaultdict(dict)

        # -#-#-#-#-#- #
        # F i l l I n #
        # -#-#-#-#-#- *

        # Put exact energy for atom
        for name_atome, exact_energy in c.fetchall():
            e_ee[name_atome] = float(exact_energy)

        # Calc estimated exact molecules energies
        for name in set(ae_exp).union(set(zpe_exp)):

            emp_tmp = -ae_exp[name] - zpe_exp[name]

            for name_atome, number in eval(f_info[name]):
                emp_tmp += number * e_ee[name_atome]

            e_ee[name] = emp_tmp

        for run_id, e_th_rd in e_th.iteritems():
            for name, energies in e_th_rd.iteritems():
                try:
                    e_diff[run_id][name] = energies - e_ee[name]
                except KeyError:
                    pass

    #   /\ _|_  _  ._ _  o _   _. _|_ o  _  ._    _|_ |_
    #  /--\ |_ (_) | | | | /_ (_|  |_ | (_) | |    |_ | |
    if arguments["--ae"]:

        # -#-#-#- #
        # I n i t #
        # -#-#-#- #

        ae_th = defaultdict(dict)
        ae_diff = defaultdict(dict)

        # -#-#-#-#-#- #
        # F i l l I n #
        # -#-#-#-#-#- *

        for run_id, e_th_rd in e_th.iteritems():
            for name, energy in e_th_rd.iteritems():
                try:
                    ao_th_tmp = energy + zpe_exp[name]
                    for name_atome, number in eval(f_info[name]):
                        ao_th_tmp -= e_th_rd[name_atome] * number
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
    #
    # |  o  _ _|_   ._    ._
    # |_ | _>  |_   | |_| | |
    #
    if arguments["list_run"]:

        # -#-#- #
        # M A D #
        # -#-#- #
        # mad = mean( abs( x_i - mean(x) ) )

        d_mad = defaultdict()
        for run_id in ae_diff:
            l_energy = ae_diff[run_id].values()
            mad = sum(map(abs, l_energy)) / len(l_energy) * 630
            d_mad[run_id] = "{:>6.2f}".format(mad)

        # -#-#-#- #
        # I n i t #
        # -#-#-#- #
        table_body = []

        # -#-#-#-#-#- #
        # H e a d e r #
        # -#-#-#-#-#- #

        header_name = "Run_id Method Basis Geo Comments mad".split()
        header_unit = [DEFAULT_CARACTER] * 5 + ["kcal/mol"]

        # -#-#-#- #
        # B o d y #
        # -#-#-#- #

        for run_id, l in run_info.iteritems():
            mad = d_mad[run_id] if run_id in d_mad else DEFAULT_CARACTER

            line = [run_id] + l + [mad]
            table_body.append(line)

    #  _
    # |_ ._   _  ._ _
    # |_ | | (/_ | (_| \/
    #               _| /
    elif arguments["get_energy"]:

        # -#-#-#- #
        # I n i t #
        # -#-#-#- #

        def create_line(fd, n):

            def dump(f, d, n):
                return f.format(d[n]) if n in d else DEFAULT_CARACTER

            return [dump(format_dict[d[0]], d[1], n) for d in fd]

        def good_ele_to_print(n):
            return any([arguments["--all_children"], not arguments["--ele"],
                        n in arguments["--ele"]])

        table_body = []

        # -#-#-#-#-#- #
        # H e a d e r #
        # -#-#-#-#-#- #

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

        # -#-#-#- #
        # B o d y #
        # -#-#-#- #

        for run_id, e_th_rd in e_th.iteritems():

            comments = run_info[run_id][3]

            comments = comments.replace("1M_Dets_NO_10k_Dets_TruePT2",
                                        "1M_Dets_NO\n_10k_Dets_TruePT2")

            comments = comments.replace("1M_Dets_NO_1k_Dets_TruePT2",
                                        "1M_Dets_NO\n_1k_Dets_TruePT2")

            comments = comments.replace(
                "Davidson nonrelativistics atomics energies",
                "Davidson nonrelativistics\natomics energies")

            line_basis = [run_id] + run_info[run_id][:3] + [comments]

            for name in e_th_rd:
                line = list(line_basis) + [name]

                line += create_line([("e_th", e_th[run_id])],
                                    name)

                if not good_ele_to_print(name):
                    continue

                if arguments["--zpe"]:
                    line += create_line([("zpe_exp", zpe_exp)],
                                        name)

                if arguments["--estimated_exact"]:
                    line += create_line([("e_ee", e_ee),
                                         ("e_diff", e_diff[run_id])
                                         ],
                                        name)

                if arguments["--ae"]:
                    line += create_line([("ae_th", ae_th[run_id]),
                                         ("ae_exp", ae_exp),
                                         ("ae_diff", ae_diff[run_id])
                                         ],
                                        name)

                table_body.append(line)

        # -#-#-#-#- #
        # O r d e r #
        # -#-#-#-#- #

        # Order like_toulousse if needed.If not by l_ele.
        # If l_ele is None don't order
        order = list_toulouse if arguments["--like_toulouse"] else l_ele
        if order:
            table_body = [l for i in order for l in table_body if l[5] == i]

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
            table_body = sorted(table_body,
                                key=lambda x: x[index],
                                reverse=True)

    # ______     _       _
    # | ___ \   (_)     | |
    # | |_/ / __ _ _ __ | |_
    # |  __/ '__| | '_ \| __|
    # | |  | |  | | | | | |_
    # \_|  |_|  |_|_| |_|\__|

    #               ___
    #  /\   _  _ o o |  _. |_  |  _
    # /--\ _> (_ | | | (_| |_) | (/_
    #
    if not arguments["--gnuplot"]:
        # -#-#-#-#-#-#-#- #
        # B i g  Ta b l e #
        # -#-#-#-#-#-#-#- #

        table_body = [map(str, i) for i in table_body]
        table_data = [header_name] + [header_unit] + table_body

        rows, columns = os.popen('stty size', 'r').read().split()

        # -#-#-#-#-#- #
        # F i l t e r #
        # -#-#-#-#-#- #

        from src.terminaltables import AsciiTable

        if all([arguments['--auto'],
                int(columns) < 200,
                not arguments["list_run"]]) or arguments['--small']:

            # Super moche à changer
            table_data = [[line[0]] + line[5:] for line in table_data]

            table_roger = []
            a = "Run_id Method Basis Geo Comments".split()

            for run_id, l in run_info.iteritems():
                line = [run_id] + l
                table_roger.append(line)

            t = [a] + table_roger
            t = [map(str, i) for i in t]
            t = AsciiTable(t)
            print t.table()

        table = AsciiTable(table_data)
        print table.table(row_separator=2)
    #  __
    # /__ ._      ._  |  _ _|_
    # \_| | | |_| |_) | (_) |_
    #             |
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
