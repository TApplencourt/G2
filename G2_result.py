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
                        [--without_pt2]
  G2_result.py list_ele --run_id=<id> [--missing]
  G2_result.py get_energy [--order_by=<column>]
                          [--run_id=<id>...]
                          [--ele=<element_name>...  [--all_children] | --like_toulouse]
                          [--geo=<geometry_name>...]
                          [--basis=<basis_name>...]
                          [--method=<method_name>...]
                          [--zpe]
                          [--estimated_exact]
                          [--ae]
                          [--without_pt2]
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
  --without_pt2             Show all the data without adding the PT2 when avalaible.
Options for list_ele:
  --run_id                  Show the list_ele for this run_id
  --missing                 Show the diffence between "like_toulouse" list and "list_ele"

Options specifics to get_energy:
  --ae                        Show the atomization energy when avalaible
                                 (both theorical and experiment).
                                  ae_cal = E_mol - \sum E_atom  + zpe
  --estimated_exact           Show the estimated exact energy.
                                  E_est_exact = \sum E^{exact}_{atom} - zpe
  --all_children              Show all the children of the element
                                  Example for AlCl will show Al and Cl.
  --gnuplot                   Print the result in a GNUPLOT readable format.
  All the other               Filter the data or ordering it. See example.

Example of use:
  ./G2_result.py list_run --method 'CCSD(T)'
  ./G2_result.py get_energy --run_id 11 --order_by e_cal --without_pt2 --estimated_exact
  ./G2_result.py get_energy --basis "cc-pVDZ" --ele AlCl --ele Li2 --ae --order_by ae_diff
"""

version = "3.0.1"


import sys
if sys.version_info[:2] != (2, 7):
    print "You need python 2.7."
    print "You can change the format for 2.6"
    print "And pass the 2to3 utility for python 3"
    sys.exit(1)

from collections import defaultdict
from collections import OrderedDict
from collections import namedtuple

try:
    from src.docopt import docopt
    from src.SQL_util import cond_sql_or
    from src.SQL_util import c, c_row
except:
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)

import os
try:
    import ConfigParser
    Config = ConfigParser.ConfigParser()
    Config.read(os.path.dirname(__file__) + "/config.cfg")

except:
    raise

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

    # -#-#-#-#-#-#-#- #
    # V a r i a b l e #
    # -#-#-#-#-#-#-#- #

    # Get & print

    # * l_ele    List element for geting the value
    # * f_info   namedTuple for the num of atoms and the formula (f_info[name])

    # Calcule one

    # * e_cal    Dict of energies theorical / calculated   (e_cal[run_id][name])
    # * zpe_exp  Dict of zpe experimental                  (zpe_exp[name])
    # * e_nr     Dict of energy estimated exact            (e_nr[name])
    # * e_diff   Dict of e_cal exact - estimated exact one  (e_diff[run_id][name])
    # * ae_cal   Dict of atomization energye theorical      (ae_cal[run_id][name])
    # * ae_nr    Dict of non relativist atomization energy (ae_nr[name])
    # * ae_exp   Dict of atomization experimental          (ae_ext[name])
    # * ae_diff  Dict of ae_cal energy - no relativiste     (ae_diff[run_id][name])
    # * run_info Dict of the geo,basis,method,comments     (run_info[run_id])

    # Format dict
    format_dict = defaultdict()
    for name, value in Config.items("Format_dict"):
        format_dict[name] = Config.get("Format_mesure", value)

    # Unit_dict
    unit_dict = defaultdict()
    for name, value in Config.items("Unit_dict"):
        unit_dict[name] = value

    # Dict for knowing the run_id reference for estimated exact energy
    e_nr_name_id_dict = {"Rude": "Any",
                         "Feller": 61,
                         "O'Neill": 62,
                         "Davidson": 21,
                         "Chakravorty": 67}

    # Dict for knowing what tab us for the ZPE / AE
    ae_zpe_exp_dict = {"NIST": 1,
                       "literature": 10}

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
        cond_filter_ele = cond_sql_or("name", l_ele)
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

    cursor = c_row.execute("""SELECT formula,
                      num_atoms,
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

    e_cal_unorder = defaultdict(dict)
    run_info = defaultdict()
    f_info = defaultdict()

    # -#-#-#-#-#- #
    # F i l l I n #
    # -#-#-#-#-#- *

    Num_formula = namedtuple('num_formula', ['num_atoms', 'formula'])
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

        e_cal_unorder[r['run_id']][r['ele']] = value
        # Info
        run_info[r['run_id']] = [r['method'], r['basis'],
                                 r['geo'], r['comments']]

        if not r['ele'] in f_info:
            f_info[r['ele']] = Num_formula(r['num_atoms'], eval(r['formula']))

    # -#-#-#-#- #
    # O r d e r #
    # -#-#-#-#- *

    e_cal = defaultdict(OrderedDict)
    order = list_toulouse if arguments["--like_toulouse"] else l_ele
    if order:
        for run_id in e_cal_unorder:
            for i in order:
                e_cal[run_id][i] = e_cal_unorder[run_id][i]
    else:
        e_cal = e_cal_unorder

    #  __
    #   / ._   _    ()     /\   _     _     ._
    #  /_ |_) (/_   (_X   /--\ (/_   (/_ >< |_)
    #     |                                 |
    # Not realy usefull anymore
    if any(arguments[k] for k in ["--zpe",
                                  "--ae",
                                  "--estimated_exact"]):

        # -#-#- #
        # S q l #
        # -#-#- #
        try:
            zpe_ae_user = Config.get("ZPE_AE", "value")
        except KeyError:
            print "WARNING bad ZPE AE type"
            raise

        if zpe_ae_user == "recomended":
            cond = ['basis_id=(1)']
        else:
            method_id = ae_zpe_exp_dict[zpe_ae_user]
            cond = ['(basis_id=1)', '(method_id=%d)' % (method_id)]

        cond_filter = cond_filter_ele + cond
        cmd_where = " AND ".join(cond_filter)

        cursor = c_row.execute("""SELECT name,
                         formula,
                             zpe,
                            kcal,
                   min(kcal_err) as kcal_err
                            FROM id_tab
                    NATURAL JOIN zpe_tab
                    NATURAL JOIN atomization_tab
                           WHERE {cmd_where}
                           GROUP BY name""".format(cmd_where=cmd_where))

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
    if any(arguments[k] for k in ["--ae",
                                  "--estimated_exact"]):

        # -#-#- #
        # S q l #
        # -#-#- #

        # Get Davidson est. atomics energies

        try:
            run_id_mol = e_nr_name_id_dict[Config.get("estimated_exact",
                                                      "method")]
            run_id_atom = e_nr_name_id_dict[Config.get("estimated_exact",
                                                       "atomic")]
        except KeyError:
            print "WARNING bad method in cfg"
            print "Will use by default Feller and Chakravorty"
            run_id_mol = e_nr_name_id_dict["Feller"]
            run_id_atom = e_nr_name_id_dict["Chakravorty"]

        cmd_id = cond_sql_or("run_id", [run_id_atom, run_id_mol])

        cmd_where = " AND ".join(cond_filter_ele + cmd_id)
        c.execute("""SELECT name as name_atome,
                          energy as exact_energy
                            FROM simple_energy_tab
                    NATURAL JOIN id_tab
                           WHERE {cmd_where}""".format(cmd_where=cmd_where))

        # -#-#-#- #
        # I n i t #
        # -#-#-#- #

        e_nr = defaultdict()

        # -#-#-#-#-#- #
        # F i l l I n #
        # -#-#-#-#-#- *

        # Put exact energy for atom
        for name, exact_energy in c.fetchall():
            e_nr[name] = float(exact_energy)

        # We have the energy but not the estimated_exact
        need_to_do = set(f_info).difference(e_nr)
        # We can calculette rudly this one
        # with e_nr = ae + zpe + sum e_atom
        can_do = set(ae_exp).intersection(zpe_exp).intersection(f_info)

        for name in need_to_do.intersection(can_do):
            emp_tmp = -ae_exp[name] - zpe_exp[name]

            for name_atome, number in f_info[name].formula:
                emp_tmp += number * e_nr[name_atome]

            e_nr[name] = emp_tmp

        # -#-#-#- #
        # I n i t #
        # -#-#-#- #

        e_diff = defaultdict(dict)

        # -#-#-#-#-#- #
        # F i l l I n #
        # -#-#-#-#-#- *

        for run_id, e_cal_rd in e_cal.iteritems():
            for name, energies in e_cal_rd.iteritems():
                try:
                    e_diff[run_id][name] = energies - e_nr[name]
                except KeyError:
                    pass

    #                                                  _
    #  /\ _|_  _  ._ _  o _   _. _|_ o  _  ._    |\ | |_)
    # /--\ |_ (_) | | | | /_ (_|  |_ | (_) | |   | \| | \
    #
    if arguments["--ae"]:

        # -#-#-#- #
        # I n i t #
        # -#-#-#- #

        ae_nr = defaultdict()

        # -#-#-#-#-#- #
        # F i l l I n #
        # -#-#-#-#-#- *

        for name in f_info:
            try:
                ae_nr_tmp = -e_nr[name]
                for name_atome, number in f_info[name].formula:
                    ae_nr_tmp += e_nr[name_atome] * number

                ae_nr[name] = ae_nr_tmp
            except KeyError:
                pass

    #
    #   /\ _|_  _  ._ _  o _   _. _|_ o  _  ._    _|_ |_
    #  /--\ |_ (_) | | | | /_ (_|  |_ | (_) | |    |_ | |
    #
    if arguments["--ae"]:

        # -#-#-#- #
        # I n i t #
        # -#-#-#- #

        ae_cal = defaultdict(dict)
        ae_diff = defaultdict(dict)

        # -#-#-#-#-#- #
        # F i l l I n #
        # -#-#-#-#-#- *

        for run_id, e_cal_rd in e_cal.iteritems():
            for name, energy in e_cal_rd.iteritems():
                try:
                    ao_th_tmp = -energy
                    for name_atome, number in f_info[name].formula:
                        ao_th_tmp += e_cal_rd[name_atome] * number
                except KeyError:
                    pass
                else:
                    ae_cal[run_id][name] = ao_th_tmp

                try:
                    ae_diff[run_id][name] = ae_cal[run_id][name] - ae_nr[name]
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
        for run_id, ae_diff_rd in ae_diff.iteritems():
            #            l_energy = ae_diff_rd.values()

            l_energy = [val for name, val in ae_diff_rd.iteritems()
                        if f_info[name].num_atoms > 1]

            try:
                mad = 630 * sum(map(abs, l_energy)) / len(l_energy)
            except ZeroDivisionError:
                mad = DEFAULT_CARACTER
            else:
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

        # STR_TO_DICT is a dict binding the name with a dict
        # STR_TO_DICT[ae_diff] = ae_diff[run_id] for example
        # Use with precausion
        STR_TO_DICT = defaultdict(dict)

        # nl is a list of the dictionary name to use (aka key of STR_TO_DICT)
        # ELE is the element name
        def _get_value(nl):
            return [STR_TO_DICT[str_][ELE] if ELE in STR_TO_DICT[str_]
                    else DEFAULT_CARACTER for str_ in nl]

        def _change_unit(nl):
            for str_ in nl:
                if unit_dict[str_] == "Hartree":
                    pass
                elif unit_dict[str_] == "kcal/mol":
                    STR_TO_DICT[str_][ELE] *= 630.

        def _get_values_convert(nl):
            _change_unit(nl)
            return _get_value(nl)

        def _good_ele_to_print(n):
            return any([arguments["--all_children"], not arguments["--ele"],
                        n in arguments["--ele"]])

        table_body = []

        # -#-#-#-#-#- #
        # H e a d e r #
        # -#-#-#-#-#- #

        header_name = "run_id method basis geo comments ele e_cal".split()

        if arguments["--zpe"]:
            header_name += "zpe_exp".split()

        if arguments["--estimated_exact"]:
            header_name += "e_nr e_diff".split()

        if arguments["--ae"]:
            header_name += "ae_cal ae_nr ae_diff".split()

        header_unit = [
            unit_dict[n] if n in unit_dict else DEFAULT_CARACTER for n in header_name]

        # -#-#-#- #
        # B o d y #
        # -#-#-#- #

        for run_id, e_cal_rd in e_cal.iteritems():

            line_basis = [run_id] + run_info[run_id][:4]

            for ELE in e_cal_rd:
                line = list(line_basis) + [ELE]

                STR_TO_DICT["e_cal"] = e_cal[run_id]
                line += _get_values_convert("e_cal".split())

                if not _good_ele_to_print(ELE):
                    continue

                if arguments["--zpe"]:

                    STR_TO_DICT["zpe_exp"] = zpe_exp
                    line += _get_values_convert("zpe_exp".split())

                if arguments["--estimated_exact"]:
                    STR_TO_DICT["e_nr"] = e_nr
                    STR_TO_DICT["e_diff"] = e_diff[run_id]
                    line += _get_values_convert("e_nr e_diff".split())

                if arguments["--ae"]:
                    STR_TO_DICT["ae_cal"] = ae_cal[run_id]
                    STR_TO_DICT["ae_nr"] = ae_nr
                    STR_TO_DICT["ae_diff"] = ae_diff[run_id]
                    line += _get_values_convert("ae_cal ae_nr ae_diff".split())

                table_body.append(line)

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

    #  _                               _
    # |_ |  _  ._ _   _  ._ _|_ / _   |_)     ._
    # |_ | (/_ | | | (/_ | | |_  _>   | \ |_| | |
    #
    # List all the element of a run_id
    if arguments["list_ele"]:

        run_id = arguments["--run_id"]

        c.execute("""SELECT name
                    FROM output_tab
                    WHERE run_id = (?)""", run_id)

        l_ele = [str(ele[0]) for ele in c.fetchall()]

        if arguments["--missing"]:
            from src.misc_info import list_toulouse
            table_body = [ele for ele in list_toulouse if ele not in l_ele]
        else:
            table_body = [ele for ele in l_ele]

        print " ".join(table_body)

    #               ___
    #  /\   _  _ o o |  _. |_  |  _
    # /--\ _> (_ | | | (_| |_) | (/_
    #
    elif not arguments["--gnuplot"]:

        # -#-#-#-#-#- #
        # F o r m a t #
        # -#-#-#-#-#- #

        for line in table_body:
            for i, name in enumerate(header_name):
                if name in format_dict:
                    if line[i]:
                        line[i] = format_dict[name].format(line[i])
                    else:
                        line[i] = DEFAULT_CARACTER

        # -#-#-#-#-#-#-#- #
        # B i g  Ta b l e #
        # -#-#-#-#-#-#-#- #
        from src.terminaltables import AsciiTable

        table_body = [map(str, i) for i in table_body]
        table_data = [header_name] + [header_unit] + table_body

        table_big = AsciiTable(table_data)

        # -#-#-#-#-#- #
        # F i l t e r #
        # -#-#-#-#-#- #

        # Table_big.ok Check if the table will fit in the terminal
        mode = Config.get("Size", "mode")
        if all([mode == "Auto",
                not table_big.ok,
                not arguments["list_run"]]) or mode == "Small":

            # Split into two table
            # table_run_id  (run _id -> method,basis, comment)
            # table_data_small (run_id -> energy, etc)
            table_run_id = ["Run_id Method Basis Geo Comments".split()]

            for run_id, l in run_info.iteritems():
                line = [run_id] + l
                table_run_id.append(line)

            t = AsciiTable([map(str, i) for i in table_run_id])
            print t.table()

            table_data_small = [[line[0]] + line[5:] for line in table_data]
            t = AsciiTable(table_data_small)
            print t.table(row_separator=2)

        else:
            print table_big.table(row_separator=2)
    #  __
    # /__ ._      ._  |  _ _|_
    # \_| | | |_| |_) | (_) |_
    #             |
    else:

        def _value(var):

            DEFAULT_CARACTER = "-"
            if not var:
                return DEFAULT_CARACTER, DEFAULT_CARACTER
            try:
                return str(var.e), str(var.err)
            except AttributeError:
                return str(var), "0."
            except:
                raise

        print "#" + header_name[0] + " " + " ".join(header_name[5:])
        table_data_small = [[line[0]] + line[5:] for line in table_body]

        for line in table_data_small:
            l = tuple(map(str, line[:2]))
            for i in line[2:]:
                l += _value(i)

            print " ".join(l)

        print "#GnuPlot cmd"
        print ""
        print "for energy: "
        print "#$gnuplot -e",
        print "\"set datafile missing '-';",
        print "set xtics rotate;",
        print "plot 'dat' u 3:xtic(2) w lp title 'energy';",
        print "pause -1\""
        print ""
        print "for ae_diff: "
        print "#$gnuplot -e",
        print "\"set datafile missing '-';",
        print "set xtics rotate;",
        print "plot 'dat' u 9:xtic(2) w lp title 'ae_diff';",
        print "pause -1\""
