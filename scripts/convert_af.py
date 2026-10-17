# Convert AlphaFold Server CIF models to PDB. Usage: python convert_af.py <fold_dir> <design_number>
import gemmi, sys, os
d, n = sys.argv[1], sys.argv[2]
out = "inputs/lasv_pdbs"; os.makedirs(out, exist_ok=True)
for m in range(5):
    p = f"{d}/fold_lasv_{n}_model_{m}.cif"
    if os.path.exists(p):
        st = gemmi.read_structure(p); st.setup_entities()
        st.write_pdb(f"{out}/lasv_{n}_model_{m}.pdb")
