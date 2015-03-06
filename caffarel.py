#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
<< Je veux des nombres !!! >>

Usage:
  caffarel.py get_energy [--run_id=<id>... | ([--method=<method_name>...]
                                              [--basis=<basis_name>...]
                                              [--geo=<geometry_name>...]
                                              [--comments=<comments>...])]
                         [(--ele=<element_name>... [--all_children]
                           | --like_toulouse
                           | --like_applencourt
                           | --like_run=<run_id>) ]
                         [--no_relativist]
                         [--ae]
                         [--without_pt2]
                         [--order_by=<column>...]
                         [--gnuplot | --plotly=<column>...]
"""

version = "0.0.1"

# -#-#-#-#-#-#-#-#- #
# D i s c l a m e r #
# -#-#-#-#-#-#-#-#- #
# Proof of concept : Procedural code with minimal function call can be clean

#
#  _____                           _         _____              __ _
# |_   _|                         | |    _  /  __ \            / _(_)
#   | | _ __ ___  _ __   ___  _ __| |_  (_) | /  \/ ___  _ __ | |_ _  __ _
#   | || '_ ` _ \| '_ \ / _ \| '__| __|     | |    / _ \| '_ \|  _| |/ _` |
#  _| || | | | | | |_) | (_) | |  | |_   _  | \__/\ (_) | | | | | | | (_| |
#  \___/_| |_| |_| .__/ \___/|_|   \__| ( )  \____/\___/|_| |_|_| |_|\__, |
#                | |                    |/                            __/ |
#                |_|                                                 |___/

import sys

#
# \  / _  ._ _ o  _  ._
#  \/ (/_ | _> | (_) | |
#
if sys.version_info[:2] != (2, 7):
    print "You need python 2.7."
    print "You can change the format (in src/objet.py) for 2.6"
    print "And pass the 2to3 utility for python 3"
    print "Send me a pull request after friend!"
    sys.exit(1)

#
# |  o |_  ._ _. ._
# |_ | |_) | (_| | \/
#                  /
try:
    from src.docopt import docopt
except:
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)


# ___  ___      _
# |  \/  |     (_)
# | .  . | __ _ _ _ __
# | |\/| |/ _` | | '_ \
# | |  | | (_| | | | | |
# \_|  |_/\__,_|_|_| |_|
#
if __name__ == '__main__':

    arguments = docopt(__doc__, version='G2 Api ' + version)

    # ___
    #  |  ._  o _|_
    # _|_ | | |  |_
    #
    # Set somme option, get l_ele and the commande used by sql

    from src.data_util import get_l_ele, get_children
    from src.data_util import ListEle, get_cmd

    # -#-#-#-#-#- #
    # O p t i o n #
    # -#-#-#-#-#- #

    print_children = True if arguments["--all_children"] else False
    need_all = False
    # -#-#-#-#- #
    # l _ e l e #
    # -#-#-#-#- #

    l_ele = get_l_ele(arguments)
    get_children = get_children(arguments)

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
    from src.data_util import get_zpe_aeexp
    from src.data_util import get_enr, complete_e_nr, get_ediff
    from src.data_util import get_ae_cal, get_ae_nr, get_ae_diff
    from src.data_util import convert, get_header_unit, get_values

    # -#-#-#- #
    # E c a l #
    # -#-#-#- #

    energy_opt = "var" if arguments["--without_pt2"] else "var+pt2"

    e_cal, run_info, f_info = get_ecal_runinfo_finfo(cmd_where, energy_opt)

    # -#-#- #
    # Z P E #
    # -#-#- #
    if arguments["--ae"] or arguments["--no_relativist"]:
        zpe_exp, ae_exp = get_zpe_aeexp(cond_filter_ele)
        convert("zpe_exp", zpe_exp)

    # -#-#-#-#-#-#-#-#-#-#-#-#- #
    # N o _ r e l a t i v i s t #
    # -#-#-#-#-#-#-#-#-#-#-#-#- #
    if arguments["--no_relativist"] or arguments["--ae"]:
        e_nr = get_enr(cond_filter_ele)
        complete_e_nr(e_nr, f_info, ae_exp, zpe_exp)

        e_diff, e_diff_rel = get_ediff(e_cal, e_nr)

        convert("e_cal", e_cal, opt=1)
        convert("e_diff", e_diff, opt=1)

    # -#- #
    # A E #
    # -#- #
    if arguments["--ae"]:
        ae_cal = get_ae_cal(f_info, e_cal)
        ae_nr = get_ae_nr(f_info, e_nr)
        ae_diff = get_ae_diff(ae_cal, ae_nr)

        convert("ae_cal", ae_cal, opt=1)
        convert("ae_nr", ae_nr)
        convert("ae_diff", ae_diff, opt=1)

    #  _
    # |_) ._ o ._ _|_
    # |   |  | | | |_
    #
    table_body = []

    # -#-#-#-#-#- #
    # H e a d e r #
    # -#-#-#-#-#- #

    header_name = "run_id method basis geo comments ele e_cal".split()

    if arguments["--no_relativist"]:
        header_name += "e_nr e_diff e_diff_rel".split()

    if arguments["--ae"]:
        header_name += "ae_cal ae_nr ae_diff".split()

    header_unit = get_header_unit(header_name)

    # -#-#-#- #
    # B o d y #
    # -#-#-#- #

    for run_id in run_info:

        line_basis = [run_id] + run_info[run_id][:4]

        for ele in a.to_print(e_cal[run_id]):

            line = list(line_basis) + [ele]
            line += get_values(ele, [e_cal[run_id]])

            if arguments["--no_relativist"]:
                line += get_values(ele, [e_nr,
                                         e_diff[run_id],
                                         e_diff_rel[run_id]])

            if arguments["--ae"]:
                line += get_values(ele, [ae_cal[run_id],
                                         ae_nr,
                                         ae_diff[run_id]])
            table_body.append(line)

    # -#-#-#-#-#- #
    # F o r m a t #
    # -#-#-#-#-#- #

    from src.print_util import order_by, format_table
    from src.print_util import print_table_energy
    from src.print_util import print_table_gnuplot

    table_body = order_by(arguments["--order_by"], header_name, table_body)
    table_body = format_table(header_name, table_body)

    #               ___
    #  /\   _  _ o o |  _. |_  |  _
    # /--\ _> (_ | | | (_| |_) | (/_
    #

    if not (arguments["--gnuplot"] or arguments["--plotly"]):
        print_table_energy(run_info, table_body, header_name, header_unit)

    #  __
    # /__ ._      ._  |  _ _|_
    # \_| | | |_| |_) | (_) |_
    #             |
    elif arguments["--gnuplot"]:
        print_table_gnuplot(table_body, header_name)

    #  _
    # |_) |  _ _|_   |
    # |   | (_) |_ o | \/
    #                  /
    elif arguments["--plotly"]:

        try:
            import plotly.plotly as py
            from plotly.graph_objs import Layout, ErrorY, XAxis, YAxis, Legend
            from plotly.graph_objs import Figure, Scatter, Data
        except:
            print "you need plotly to be installed and configure"
            print "https://plot.ly/python/getting-started/"
            sys.exit(1)

        def get_scatter(name, x, y, ye=None):

            if ye:
                return Scatter(x=x,
                               y=y,
                               # mode='markers',
                               name=name,
                               error_y=ErrorY(type='data',
                                              array=ye,
                                              visible=True)
                               )
            else:
                return Scatter(x=x,
                               y=y,
                               # mode='markers',
                               name=name)

        data = []
        for dict_name in arguments["--plotly"]:
            dict_ = eval(dict_name)

            for run_id, dict_rd in dict_.iteritems():

                x = [n for n in a.to_print(e_cal[run_id]) if n in dict_rd]

                l_val = [get_values(name, [dict_rd])[0] for name in x]
                try:
                    y = [val.e for val in l_val]
                    ye = [val.err for val in l_val]
                except AttributeError:
                    y = l_val
                    ye = None

                str_ = "run_id : %s (%s) <br> %s"
                legend = str_ % (run_id,
                                 dict_name,
                                 ", ".join(run_info[run_id]))

                data.append(get_scatter(legend, x, y, ye))

        data = Data(data)

#        yaxis_title = "%s (%s)" % (dict_name, unit_dict[dict_name])
        yaxis_title = "coucou"

        layout = Layout(title='Fig 1: G2 %s' % dict_name,
                        xaxis=XAxis(autotick=False,
                                    ticks='outside'),
                        yaxis=YAxis(title=yaxis_title),
                        legend=Legend(x=0,
                                      y=-1.)
                        )

        fig = Figure(data=data, layout=layout)

        plot_url = py.plot(fig, filename='G2')
        py.image.save_as(fig, filename='G2.svg')
