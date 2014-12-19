```Python
Welcom to the G2 Api! Grab all G2 data you're dreaming for.

Usage:
  G2_api.py (-h | --help)
  G2_api.py list_run [--ele=element_name...]
                     [--geo=geometry_name...]
                     [--basis=basis_name...]
                     [--method=method_name...]
  G2_api.py get_energy [--without_pt2]
                       [--get_ae]
                       [--order_by=name...]
                       [--run_id=id...]
                       [--ele=element_name...]
                       [--geo=geometry_name...]
                       [--basis=basis_name...]
                       [--method=method_name...]

  G2_api.py --version

Options:
  --help                 Here you go.
  --without_pt2          Show all the data without adding the PT2 when avalaible.
  --get_ae               Show the atomization energy (both theorical and experiment) when avalaible.
  All the other          Filter the data or ordering it. See example.


Example of use:
  ./G2_api.py list_run g2.db
  ./G2_api.py get_energy --run_id 11 --order_by num_elec --without_pt2
  ./G2_api.py get_energy --basis cc-pvdz --ele AlCl --ele Li2 --get_ae
```
