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
  ./G2_result.py list_run --method cipsi
  ./G2_result.py get_energy --run_id 11 --order_by energy --without_pt2
  ./G2_result.py get_energy --basis cc-pvdz --ele AlCl --ele Li2 --get_ae --order_by diff
```
