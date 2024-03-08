# Information

The Information section of our application is a dedicated space designed to offer users immediate access to critical molecular property information.
This feature enriches the user's understanding of molecular structures through a concise and informative display, encompassing a range of data points, including 2D representations, SMILES strings, and computed molecular properties.

## Molecular properties

<figure markdown>
![](/img/interface/lapatinib-info.png){ alight=left height=300 }
</figure>

### logP

The octanol−water partition coefficient (logP) for molecules is computed using the method described by [Wildman and Crippen](https://doi.org/10.1021/ci990307l).
The approach relies on classifying atoms within a molecule into one of 68 predefined atom types, each associated with a specific contribution to the molecule's logP value.
Atoms are classified based on their immediate chemical environment, considering factors such as the type of neighboring atoms, their aromaticity, and their bonding. This classification reduces ambiguity and ensures a consistent assignment of atom types across different molecules.

The logP of a molecule is calculated as the sum of the contributions of its constituent atoms, thus allowing for the estimation of a molecule's lipophilicity.
The logP value of a molecule is calculated using

\[ P_{\text{calc}} = \sum_{i} n_{i} a_{i} \]

where \(P_{\text{calc}}\) is the calculated logP value, \(n_{i}\) is the number of atoms of type \(i\) present in the molecule, and \(a_{i}\) is the contribution to logP for atom type \(i\).

### Weight

Molecular weight in g/mol.

### HBA

Total number of nitrogen and oxygen atoms. See Adv Drug Deliv Rev 46 3-26 (2001)

### HBD

Total number of N-H and O-H bonds. See Adv Drug Deliv Rev 46 3-26 (2001)

### MR

Wildman-Crippen molar refractivity. See JCICS 39 868-873 (1999)

### CSP3

Percentage of carbon atoms that are SP3 hybridized.

### Surf

Labute's approximate surface area. See J Mol Graph Mod 18 464-477 (2000)

### TPSA

Topological polar surface area. See J Med Chem 43 3714-3717 (2000)

### Violations

A molecule is druglike if it has 0 or 1 Lipinski violations
