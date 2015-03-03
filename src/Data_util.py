#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module is usefull for getting energy values related (e_cal, ae, etc.) from the db.
You can:
    - Create sql commands ;
    - Parse the data.
"""
#  _
# /   _  | |  _   _ _|_ o  _  ._
# \_ (_) | | (/_ (_  |_ | (_) | |
#
from collections import defaultdict
from collections import namedtuple


from src.object import v_un

from src.Requirement_util import config

from src.SQL_util import c, c_row
from src.SQL_util import cond_sql_or

import sys


#
# |  o  _ _|_    _  |  _  ._ _   _  ._ _|_
# |_ | _>  |_   (/_ | (/_ | | | (/_ | | |_
#

# Set the list of element to get and to print
# By defalt, if l_ele is empty get all

class ListEle(object):
    """
    ListEle encapsulates all the info related to a list_ele.
        - l_ele giving in imput
        - l_ele_to_get all the element need to get
        - l_ele_order maybe
        - And have a to print method
    """
    def __init__(self, l_ele, get_children, print_children):
        """
        Construct a new ListEle.
        get_children: If you need all children of l_ele
        print_children: If you need to print all the children
        """
        self.l_ele = list(l_ele)
        self.l_ele_to_get = list(l_ele)

        # Add all the children of a element to l_ele_to_get if need.
        # For example for the calculate the AE of AlCl we need Al and Cl

        if not self.l_ele:
            self.need_to_define = True
        else:
            self.need_to_define = False
            if get_children:
                self.get_children()

        self.l_ele_order = list()
        self.print_children = print_children

    # -#-#-#-#-#-#-#-#-#-#-# #
    # G e t  c h i l d r e n #
    # -#-#-#-#-#-#-#-#-#-#-# #
    def get_children(self):
        """
        Find all this children of all the elements and
        and add them to l_ele_to_get
        """
        cond = " ".join(cond_sql_or("name", self.l_ele_to_get))

        c.execute("""SELECT name, formula
                                   FROM id_tab
                                  WHERE {where_cond}""".format(where_cond=cond))

        for name, formula_raw in c.fetchall():
            for atom, number in eval(formula_raw):
                if atom not in self.l_ele_to_get:
                    self.l_ele_to_get.insert(0, atom)

    def to_print(self):
        """
        Tell what element you need to print.
        For example if you have set l_ele_order it will return this.
        WARNING /!\:
            If you ask for all ele aka l_ele=list(). You need to set l_ele
            EXPLICITY after getting it.
        """
        if self.need_to_define:
            print "You need to set l_ele."
            print "Maybe you want all the element, so tell what element are available"
            sys.exit(1)
        elif self.l_ele_order:
            return self.l_ele_order
        elif self.print_children:
            return self.l_ele_to_get
        else:
            return self.l_ele

    def __str__(self):
        """Return a string of the elements"""
        return str([self.l_ele, self.l_ele_to_get])


# -#-#-#-#-#-#-# #
# L i s t  e l e #
# -#-#-#-#-#-#-# #
def get_l_ele(arguments):
    """
    Return the good list of element needed using arguments dict.
    arguments need to have all this key:
        --ele ; --like_toulouse ; --like_applencourt ; --like_run_id 
    """
    if arguments["--ele"]:
        l_ele = arguments["--ele"]
        get_children = False

    elif arguments["--like_toulouse"]:
        from src.misc_info import list_toulouse
        l_ele = list_toulouse
        # So we need all_children
        get_children = True
    elif arguments["--like_applencourt"]:
        from src.misc_info import list_applencourt
        l_ele = list_applencourt
        # So we need all_children
        get_children = True
    elif arguments["--like_run_id"]:
        c.execute("""SELECT name FROM output_tab
                          WHERE run_id = {0}""".format(arguments["--like_run_id"]))

        l_ele = [i[0] for i in c.fetchall()]

        # So we dont need all_children
        get_children = False
    else:
        l_ele = list()
        get_children = False

    return [l_ele, get_children]


# ______ _ _ _
# |  ___(_) | |
# | |_   _| | |_ ___ _ __
# |  _| | | | __/ _ \ '__|
# | |   | | | ||  __/ |
# \_|   |_|_|\__\___|_|

#  _
# |_ o | _|_  _  ._    _ _|_ ._ o ._   _
# |  | |  |_ (/_ |    _>  |_ |  | | | (_|
#                                      _|
def get_cmd(arguments, l_ele_obj, need_all):
    """
    Create the cmd string who will be executed by the db
    arguments need all this key:
        --run_id; --geo; --basis; --method
    """
    d = {"run_id": "--run_id",
         "geo": "--geo",
         "basis": "--basis",
         "method": "--method"}

    cond_filter = []
    for k, v in d.items():
        try:
            cond_filter += cond_sql_or(k, arguments[v])
        except KeyError:
            raise

    l_ele_to_get = l_ele_obj.l_ele_to_get

    # We need to find the run_id who containt ALL the ele is needed
    if l_ele_to_get:
        cond_filter_ele = cond_sql_or("name", l_ele_to_get)
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
        if l_ele_to_get and need_all:
            cmd_having = "count(name) = {0}".format(len(l_ele_to_get))
        else:
            cmd_having = "(1)"

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

        if not l_run_id:
            print "Not run for you'r imput sorry"
            sys.exit()
        else:
            # Now only the run_id count. It containt all the information
            cond_filter = ["run_id in (" + ",".join(map(str, l_run_id)) + ")"]

            cmd_where = " AND ".join(cond_filter + cond_filter_ele)

    return [cond_filter_ele, cmd_where]


#  _
# |_ ._   _  ._ _        _  _. |  _
# |_ | | (/_ | (_| \/   (_ (_| | (_
#               _| /
#

# -#-#-#-#-#-#-#-#- #
#  F u n c t i o n  #
# -#-#-#-#-#-#-#-#- #
def get_ecal_runinfo_finfo(cmd_where, cipsi_type):
    """
    Return 3 dict:
        * e_cal    Dict of energies theorical / calculated    (e_cal[run_id][name])
        * run_info Dict of the geo,basis,method,comments      (run_info[run_id])
        * f_info   Dict of formula (run_id[name])
    """
    # -#-#- #
    # S Q L #
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
    e_cal = defaultdict(dict)
    run_info = defaultdict()
    f_info = defaultdict()

    # -#-#-#-#-#-#- #
    # F i l l _ i n #
    # -#-#-#-#-#-#- #
    num_formula = namedtuple('num_formula', ['num_atoms', 'formula'])
    for r in cursor:
        # Energy
        if r['s_energy']:
            value = float(r['s_energy'])

        if r['c_energy']:
            if cipsi_type == "var":
                value = float(r['c_energy'])
            elif cipsi_type == "pt2":
                value = float(r['c_pt2'])
            elif cipsi_type == "var+pt2":
                value = float(r['c_energy']) + float(r['c_pt2'])

        if r['q_energy']:
            value = v_un(float(r['q_energy']),
                         float(r['q_err']))

        e_cal[r['run_id']][r['ele']] = value
        # Info
        run_info[r['run_id']] = [r['method'], r['basis'],
                                 r['geo'], r['comments']]

        if not r['ele'] in f_info:
            f_info[r['ele']] = num_formula(r['num_atoms'], eval(r['formula']))

    return [e_cal, run_info, f_info]


#  __
#   / ._   _    ()     /\   _     _     ._
#  /_ |_) (/_   (_X   /--\ (/_   (/_ >< |_)
#     |                                 |
# Not realy usefull anymore can we use e_nr for calcul the ae
# But is e_nr is not avalaible use zpe and ae_exp

# -#-#-#- #
# D i c t #
# -#-#-#- #

# Dict for knowing what tab us for the ZPE / AE
ae_zpe_exp_dict = {"NIST": 1,
                   "literature": 10}


# -#-#-#-#-#-#-#-#- #
#  F u n c t i o n  #
# -#-#-#-#-#-#-#-#- #
def get_zpe_aeexp(cond_filter_ele):
    """
    Return 2 dict:
        * zpe_exp  Dict of zpe experimental                   (zpe_exp[name])
        * ae_exp   Dict of atomization experimental energis   (ae_ext[name])
    """

    # -#-#- #
    # S Q L #
    # -#-#- #
    try:
        zpe_ae_user = config.get("ZPE_AE", "value")
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

    # -#-#-#-#-#-#- #
    # F i l l _ i n #
    # -#-#-#-#-#-#- #
    for r in cursor:
        zpe = r['zpe'] * 4.55633e-06
        energy = r['kcal'] * 0.00159362
        energy_err = r['kcal_err'] * 0.00159362 if r['kcal_err'] else 0.

        ae_exp[r['name']] = v_un(energy, energy_err)
        zpe_exp[r['name']] = zpe

    return [ae_exp, zpe_exp]

#  _
# |_  _ _|_      _      _.  _ _|_    _  ._   _  ._ _
# |_ _>  |_ o   (/_ >< (_| (_  |_   (/_ | | (/_ | (_| \/
#                                                  _| /

# -#-#-#- #
# D i c t #
# -#-#-#- #

# Dict for knowing the run_id reference for estimated exact energy
e_nr_name_id_dict = {"Rude": "Any",
                     "Feller": 61,
                     "O'Neill": 62,
                     "Davidson": 21,
                     "Chakravorty": 67}


# -#-#-#-#-#-#-#-#- #
#  F u n c t i o n  #
# -#-#-#-#-#-#-#-#- #
def get_enr(cond_filter_ele):
    """
    Return 1 dict:
        * e_nr   Dict of estimated exact no relativist energy  (e_nr[name])
    """
    # -#-#- #
    # S Q L #
    # -#-#- #
    # Get Davidson est. atomics energies
    try:
        run_id_mol = e_nr_name_id_dict[config.get("estimated_exact",
                                                  "method")]
        run_id_atom = e_nr_name_id_dict[config.get("estimated_exact",
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

    # -#-#-#-#-#-#- #
    # F i l l _ i n #
    # -#-#-#-#-#-#- #
    # Put exact energy non relativist for atom and molecule
    for name, exact_energy in c.fetchall():
        e_nr[name] = float(exact_energy)

    return e_nr


def complete_e_nr(e_nr, f_info, ae_exp, zpe_exp):
    """
    Take and append 1 dict:
        * e_nr   Dict of estimated exact no relativist energy  (e_nr[name])
    If all the e_nr is not avalaible try to calcul it roughly:
        * e_nr = ae + zpe + sum e_atom
    """

    # Now we treat the rest
    # We have the energy but not the estimated_exact nr
    need_to_do = set(f_info).difference(e_nr)
    # We can calculette rudly this one
    # with e_nr = ae + zpe + sum e_atom
    can_do = set(ae_exp).intersection(zpe_exp).intersection(f_info)

    for name in need_to_do.intersection(can_do):
        emp_tmp = -ae_exp[name] - zpe_exp[name]

        for name_atome, number in f_info[name].formula:
            emp_tmp += number * e_nr[name_atome]

        e_nr[name] = emp_tmp

    return e_nr


def get_ediff(e_cal, e_nr):
    """
    Return 2 dict:
        * e_diff     Dict of e_cal exact - estimated exact one  (e_diff[run_id][name])
        * e_diff_rel Dict of e_diff/e_nr[name]                  (e_diff_ref[run_id][name])
    """
    # -#-#-#- #
    # I n i t #
    # -#-#-#- #
    # Now ce can calcule the e_diff (e_cal - e_nr)
    e_diff = defaultdict(dict)
    e_diff_rel = defaultdict(dict)

    # -#-#-#-#-#-#- #
    # F i l l _ i n #
    # -#-#-#-#-#-#- #
    for run_id, e_cal_rd in e_cal.iteritems():
        for name, energies in e_cal_rd.iteritems():
            try:
                e_diff[run_id][name] = (energies - e_nr[name])
                e_diff_rel[run_id][name] = e_diff[
                    run_id][name] / e_nr[name]
            except KeyError:
                pass

    for run_id, e_diff_rd in e_diff.iteritems():
        for name, energies in e_diff_rd.iteritems():
            e_diff_rel[run_id][name] = energies / e_nr[name]

    return [e_diff, e_diff_rel]


#  /\ _|_  _  ._ _  o _   _. _|_ o  _  ._
# /--\ |_ (_) | | | | /_ (_|  |_ | (_) | |
#

# -#-#-#-#-#-#-#-#- #
#  F u n c t i o n  #
# -#-#-#-#-#-#-#-#- #
def get_ae_cal(f_info, e_cal):
    """
    return one dict
        * ae_cal   Dict of atomization energies calculated    (ae_cal[run_id][name])
                   ae_cal = e_cal_mol - sum e_cal_atom 
    """

    # -#-#-#- #
    # I n i t #
    # -#-#-#- #
    ae_cal = defaultdict(dict)

    # -#-#-#-#-#-#- #
    # F i l l _ i n #
    # -#-#-#-#-#-#- #
    for run_id, e_cal_rd in e_cal.iteritems():
        for name, energy in e_cal_rd.iteritems():
            try:
                ae_cal_tmp = -energy
                for name_atome, number in f_info[name].formula:
                    ae_cal_tmp += e_cal_rd[name_atome] * number
            except KeyError:
                pass
            else:
                ae_cal[run_id][name] = ae_cal_tmp

    return ae_cal


def get_ae_nr(f_info, e_nr):
    """
    Return one dict
        * ae_nr    Dict of no relativist atomization energies (ae_nr[name])
        ae_nr = e_nr_mol - sum e_nr_atom
    """
    # -#-#-#- #
    # I n i t #
    # -#-#-#- #
    ae_nr = defaultdict()

    # -#-#-#-#-#-#- #
    # F i l l _ i n #
    # -#-#-#-#-#-#- #
    for name in f_info:
        try:
            ae_nr_tmp = -e_nr[name]
            for name_atome, number in f_info[name].formula:
                ae_nr_tmp += e_nr[name_atome] * number

            ae_nr[name] = ae_nr_tmp
        except KeyError:
            pass

    return ae_nr


def get_ae_diff(ae_cal, ae_nr):
    """
    Return one dict
        * ae_diff  Dict of ae_cal energy - no relativist      (ae_diff[run_id][name])
         ae_diff = ae_cal - ae_nr
    """
    # -#-#-#- #
    # I n i t #
    # -#-#-#- #
    ae_diff = defaultdict(dict)

    # -#-#-#-#-#-#- #
    # F i l l _ i n #
    # -#-#-#-#-#-#- #
    for run_id, ae_cal_rd in ae_cal.iteritems():
        for name, ae in ae_cal_rd.iteritems():
            try:
                ae_diff[run_id][name] = ae - ae_nr[name]
            except KeyError:
                pass

    return ae_diff
