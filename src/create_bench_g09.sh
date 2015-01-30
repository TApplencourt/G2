#!/bin/bash
#
# Can use GNU parallel if installed

GEOMETRY="Experiment"
GEOMETRY="MP2"
BASIS="cc-pVDZ"
METHOD="CCSD(T)"


G2_input=G2_input.py

MOLECULES="$( $G2_input list_elements --geo=$GEOMETRY | tr ',' ' ')"

if [[ "$METHOD" == "HF" ]]
then
  GREP=grep_hf
  CREATE=create_hf
elif [[ "$METHOD" == "CCSD(T)" ]]
then
  GREP=grep_ccsdt
  CREATE=create_input
elif [[ "$METHOD" == "MP2" ]]
then
  GREP=grep_mp2
  CREATE=create_input
fi

cat << EOF > cmd.sh

MOL=\$1

function grep_mp2 ()
{
  grep EUMP2 \$MOL.out | cut -d "=" -f 3 | tr "D" "E" 

}

function grep_ccsdt ()
{
  grep -e "^ CCSD(T)=" \$MOL.out | cut -d '=' -f 2 | tr "D" "E" 

}

function grep_hf()
{
  grep "SCF Done" \$MOL.out | cut -d '=' -f 2 | cut -d 'A' -f 1 | tr "D" "E"
}

function create_hf()
{
  $G2_input get_g09 --geo=$GEOMETRY --ele=\$MOL | sed "s/cc-pvdz/$BASIS 6d,10f /g" > \$MOL.com
}

function create_input()
{
  $G2_input get_g09 --geo=$GEOMETRY --ele=\$MOL | sed "s/cc-pvdz/$BASIS 6d,10f $METHOD /g" > \$MOL.com
}

$CREATE
g09 < \$MOL.com > \$MOL.out
if [[ \$? -eq 0 ]] 
then
   rm \$MOL.com
   $GREP |  xargs printf "%-10s : %f\n" \$MOL  
   rm \$MOL.out
fi
EOF
chmod +x cmd.sh

METHOD=$( echo $METHOD | tr -d "()" )
date

# IF GNU PARALLEL
#
#   parallel --eta --keep-order -j 8 ./cmd.sh ::: $MOLECULES > g09_${METHOD}_${BASIS}_${GEOMETRY}
#
# ELSE
#
    for i in $MOLECULES
    do
     ./cmd.sh $i 
    done > g09_${METHOD}_${BASIS}_${GEOMETRY}
#
# END_IF

date
rm cmd.sh

