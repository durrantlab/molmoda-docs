# Molar refractivity

The Wildman-Crippen molar refractivity (MR) is a physicochemical parameter that provides insights into compounds' molecular size and polarizability.
Molar refractivity, in particular, is used as a common descriptor for molecular size and polarizability, which are significant for predicting how a molecule interacts with biological targets and membranes.

## Methodology

MolModa uses the method defined by [Wildman and Crippen](https://doi.org/10.1021/ci990307l) to compute the molar refractivity.
This technique involves aggregating the contributions from each atom within a molecule to determine its overall MR value.
While MR is not strictly additive due to intramolecular interactions, these interactions can be accommodated by classifying atoms into distinct types based on their attached and neighboring atoms.

The foundational step in computing MR involves an atom classification system.
Atoms are classified into different types according to their nearest neighbors, second neighbors, and aromaticity.
This process results in a reduced set of atom types, designed to include atoms with similar chemical natures and similar contributions to MR.
Ultimately, the classification system encompasses 68 basic atom types, covering elements commonly found in organic molecules (e.g., C, H, N, O, S, P, halogens), metals, and noble gases.

### Calculation of Molar Refractivity

Once the atoms in a molecule are classified, the MR is calculated as the sum of the contributions of each atom type present in the molecule. The formula for the calculation is as follows:

\[ \text{MR}_{\text{calc}} = \sum_{i} n_{i} a_{i} \]

-   \( \text{MR}_{\text{calc}} \) is the calculated molar refractivity of the molecule.
-   \( n_{i} \) represents the number of atoms of type \( i \) present in the molecule.
-   \( a_{i} \) is the contribution of atoms of type \( i \) to the MR.

This equation is derived from the understanding that a molecule's MR can be approximated by summing the individual contributions of its constituent atoms, with each atom type having a unique contribution value based on its chemical environment.
