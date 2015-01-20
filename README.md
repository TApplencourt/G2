G2 Test set API
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


###### Input
Get the xyz, the multiplicty of the G2 molecule

```
Welcome to the G2 Api! Grab all the G2 data you're dreaming of.

Usage:
  G2_input.py (-h | --help)
  G2_input.py list_geometries         [--ele=<element_name>...]
  G2_input.py list_elements      --geo=<geometry_name>...
  G2_input.py get_xyz            --geo=<geometry_name>...
                                 --ele=<element_name>...
                                      [(--save [--path=<path>])]
  G2_input.py get_g09            --geo=<geometry_name>...
                                 --ele=<element_name>...
                                      [(--save [--path=<path>])]
  G2_input.py get_multiplicity   --ele=<element_name>

Example of use:
  ./G2_input.py list_geometries
  ./G2_input.py list_elements --geo Experiment
  ./G2_input.py get_xyz --geo Experiment --ele NaCl --ele H3CCl

```

###### Result
Get energies, zpe, atomization energy
```
Welcome to the G2 Api! Grab all the G2 data you're dreaming of.

Usage:
  G2_result.py (-h | --help)
  G2_result.py list_run [--order_by=<column>...]
                        [--ele=<element_name>...]
                        [--geo=<geometry_name>...]
                        [--basis=<basis_name>...]
                        [--method=<method_name>...]
                        [--all_children]
  G2_result.py get_energy [--order_by=<column>]
                          [--run_id=<id>...]
                          [--ele=<element_name>...]
                          [--geo=<geometry_name>...]
                          [--basis=<basis_name>...]
                          [--method=<method_name>...]
                          [--without_pt2]
                          [--estimated_exact]
                          [--get_ae]
                          [--all_children]
  G2_result.py --version

Options:
  --help                 Here you go.
  --without_pt2          Show all the data without adding the PT2 when avalaible.
  --get_ae               Show the atomization energy (both theorical and experiment) when avalaible.
  --all_children         Find all the children of the ele.
  --estimated_exact      Show the estimated exact energy.
  All the other          Filter the data or ordering it. See example.

Example of use:
  ./G2_result.py list_run --method CIPSI
  ./G2_result.py get_energy --run_id 11 --order_by e --without_pt2 --estimated_exact
  ./G2_result.py get_energy --basis cc-pvdz --ele AlCl --ele Li2 --get_ae --order_by ae_diff
```