#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Welcome! добро пожаловать! Vladimir say Hi.
You can create or modify a run_id and put_in new data in it.

Usage:
  vladimir.py (-h | --help)
  vladimir.py put_in --path=<path>
                     (--method=<method_name> --basis=<basis_name>
                      --geo=<geometry_name> --comment=<comment>|
                      --run_id=<id>)
                     (--simple | --cipsi [--epp] | --qmc)
                     [--overwrite]
"""

version = "0.0.2"

import sys

try:
    from src.docopt import docopt
    from src.SQL_util import conn, add_or_get_run, get_mol_id
    from src.SQL_util import add_simple_energy, add_cipsi_energy, add_qmc_energy
    from src.SQL_util import commit_and_dump
    from src.misc_info import old_name_to_new
except:
    raise
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)

if __name__ == '__main__':

    arguments = docopt(__doc__, version='G2 Api ' + version)

    if arguments["--run_id"]:
        run_id = arguments["--run_id"]
    else:
        l = [arguments[i] for i in ["--method",
                                    "--basis",
                                    "--geo",
                                    "--comment"]]
        run_id = add_or_get_run(*l)

    print run_id

    with open(arguments["--path"], "r") as f:
        data = [line for line in f.read().split("\n") if line]

    for line in data:

        list_ = line.split("#")[0].split()

        name = list_[0]
        name = old_name_to_new[name] if name in old_name_to_new else name
        id_ = get_mol_id(name)
        print name, id_,

        if arguments["--simple"]:
            e = list_[1]

            print e
            add_simple_energy(run_id, id_, e,
                              overwrite=arguments["--overwrite"])

        elif arguments["--cipsi"]:
            e, pt2 = list_[1:]
            if arguments["--epp"]:
                pt2 = float(pt2) - float(e)

            print e, pt2
            add_cipsi_energy(run_id, id_, e, pt2,
                             overwrite=arguments["--overwrite"])

        elif arguments["--qmc"]:
            e, err = list_[1:]

            print e, err
            add_qmc_energy(run_id, id_, e, err,
                           overwrite=arguments["--overwrite"])

    commit_and_dump(conn)
