# TfR1 dimer refolds + ipSAE on Modal

Re-checks the 20 submitted TfR1 binders against the **homodimer** ectodomain (UniProt P02786 residues 121-760, two copies, chains A and B) with the binder as chain C. The original screen used a monomer crop of the apical domain (191-383).

| Step | What | Where |
|---|---|---|
| 1 | Boltz-2.1 structure-and-binding job per binder (2 x 640 aa target with automatic MSA, binder with empty MSA, 1 sample, about $0.20 each) | Boltz connector or CLI |
| 2 | `download-results` for the 20 ids | `run_tfr1_dimer.ps1` (Windows PowerShell) |
| 3 | ipSAE (Dunbrack `ipsae.py`, PAE 10, dist 10) for C vs A and C vs B, plus heavy-atom contacts (4.5 A) mapped to UniProt numbering and to TfR1 domains | `tfr1_dimer_ipsae.py` on Modal |

Output CSV columns: `ipsae_C_A`, `ipsae_C_B`, `ipsae_best`, `ipsae_min`, pDockQ2, LIS, `n_contact_res_A/B`, `contact_res_A/B`, `domains_A/B`, `apical_frac_A/B`, `binds_both_copies`.

## Honest status
- The job inputs and the scoring code were run. The scoring code was tested on a stand-in structure with synthetic PAE, not on real Boltz API archives.
- Not verified: the exact file names inside Boltz's `prediction_archive.tar.gz`. The script looks for any `*pae*.npz` plus a `.cif`; if no PAE file is there it says so per job instead of failing silently.
- Domain boundaries (protease-like 121-188 and 606-760, apical 189-383, helical 384-605) are the usual literature values, approximate.
- No sequences are stored in this repo. The job ids and the dimer sequence are public or non-sensitive; binder sequences are not here.
