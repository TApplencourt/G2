G2 TestSet API
=============================

You can find in this repository all the G2 Test set molucule info like:
  * Geometries (Experimental, MP2, ...)
  * Energies (With many method and atomization one)
  * Zpe (from NIST, and for all calcul)
  * etc.

##Dependency
* Python >2.6


##Demonstration

![](http://giant.gfycat.com/TornJaggedAnemoneshrimp.gif)

(For a beter quality see the [Source](https://asciinema.org/api/asciicasts/15602))

##Usage

###### Input
Get the xyz, the multiplicty of the G2 molecule

```
Welcome to the G2 Api! Grab all the G2 data you're dreaming of.

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
```