import os
import sys

try:
    import sqlite3
except:
    print "Sorry, you need sqlite3"
    sys.exit(1)


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

path = os.path.dirname(sys.argv[0]) + "/misc/g2.db"
if not isSQLite3(path):
    print "'%s' is not a SQLite3 database file" % path
    print sys.exit(1)

conn = sqlite3.connect(path)
c = conn.cursor()


def cond_sql_or(table_name, l_value):

    l = []
    dmy = " OR ".join(['%s = "%s"' % (table_name, i) for i in l_value])
    if dmy:
        l.append("(%s)" % dmy)

    return l


def get_coord(id, atom, geo_name):
    c.execute(''' SELECT x,y,z FROM coord_tab NATURAL JOIN geo_tab
                WHERE id =?  AND
                      atom=? AND
                      name = ?''', [id, atom, geo_name])

    return c.fetchall()


def full_dict(d, geo_name, only_neutral=True):

    for i, dic_ele in d.items():

        if only_neutral:
            if "+" in i or "-" in i:
                del d[i]
                continue

        formula_clean = []
        a = []
        for [atom, nb] in dic_ele["formula"]:
            for l in range(0, nb):
                formula_clean.append(atom)

            list_ = get_coord(dic_ele["id"], atom, geo_name)
            if not list_:
                del d[i]
                break
            else:
                a += list_

        dic_ele["formula_clean"] = formula_clean
        dic_ele["list_xyz"] = a

    return dict(d)


def dict_raw():
    c.execute(
        '''SELECT id,name,formula,charge,multiplicity,num_atoms,num_elec,symmetry FROM id_tab''')

    d = {}
    for i in c.fetchall():
        d[str(i[1])] = {"id": str(i[0]),
                        "formula": eval(i[2]),
                        "charge": int(i[3]),
                        "multiplicity": int(i[4]),
                        "num_atoms": int(i[5]),
                        "symmetry": str(i[6])}

    return d


def list_geo(where_cond='(1)'):
    c.execute('''SELECT DISTINCT geo_tab.name
                            FROM coord_tab
                    NATURAL JOIN geo_tab
                      INNER JOIN id_tab
                              ON coord_tab.id = id_tab.id
                           WHERE {where_cond}'''.format(where_cond=where_cond))
    return [i[0] for i in c.fetchall()]


def list_ele(where_cond):
    c.execute('''SELECT DISTINCT id_tab.name
                            FROM coord_tab
                    NATURAL JOIN geo_tab
                      INNER JOIN id_tab
                              ON coord_tab.id = id_tab.id
                           WHERE {where_cond}'''.format(where_cond=where_cond))
    return [i[0] for i in c.fetchall()]


def get_xyz(geo, ele, only_neutral=True):
    a = dict_raw()
    b = full_dict(a, geo, only_neutral)

    dic_ = b[ele]

    xyz_file_format = [dic_["num_atoms"]]

    line = " ".join(map(str, [ele,
                              "Geo:", geo,
                              "Mult:", dic_["multiplicity"],
                              "symmetry:", dic_["symmetry"]]))
    xyz_file_format.append(line)

    for atom, xyz in zip(dic_["formula_clean"], dic_["list_xyz"]):
        line_xyz = "    ".join(map(str, xyz))
        line = "    ".join([atom, line_xyz])

        xyz_file_format.append(line)

    return "\n".join(map(str, xyz_file_format))


def get_g09(geo, ele, only_neutral=True):
    a = dict_raw()
    b = full_dict(a, geo, only_neutral)

    dic_ = b[ele]

    line = " ".join(map(str, [ele,
                              "Geo:", geo,
                              "Mult:", dic_["multiplicity"],
                              "symmetry:", dic_["symmetry"]]))

    g09_file_format = [ "# cc-pvdz", "", line, "", "%d %d"%(dic_["charge"], dic_["multiplicity"]) ]

    for atom, xyz in zip(dic_["formula_clean"], dic_["list_xyz"]):
        line_xyz = "    ".join(map(str, xyz))
        line = "    ".join([atom, line_xyz])

        g09_file_format.append(line)
    g09_file_format.append("\n\n\n")
    return "\n".join(map(str, g09_file_format))

