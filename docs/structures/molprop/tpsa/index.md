# Topological polar surface area

TODO: Topological polar surface area. See J Med Chem 43 3714-3717 (2000)

## Methodology

MolModa computes the polar surface area using the method described in [Ertl, Rhote, and Selzer](https://doi.org/10.1021/jm000942e).

The process of calculating the Topological Polar Surface Area (TPSA) is streamlined into a series of steps, beginning with the identification of polar fragments within a molecule.
This identification is performed by analyzing the molecule's topological information, which can be represented in formats such as SMILES.
These topological descriptors allow for the recognition of various polar fragments, including those containing polar atoms such as oxygen, nitrogen, sulfur, and phosphorus, considering their specific bonding patterns.
Following the identification of these fragments, the next step involves the summation of their contributions to the molecule's overall polar surface area.
Each fragment type is associated with a predetermined surface area value, obtained from empirical data, which reflects its contribution to the total polar surface area of the molecule.

The mathematical formulation of this calculation is represented by the equation

$$
\text{TPSA} = \sum_{i=1}^{n} c_i \times n_i,
$$

where

-   \( c_i \) denotes the surface area contribution of the \(i^{th}\) polar fragment type, and
-   \( n_i \) indicates the number of occurrences of this fragment within the molecule.

The sum is taken over all \( n \) distinct types of polar fragments identified in the molecule. This approach simplifies the traditional PSA calculation by leveraging the molecule's topological information, bypassing the need for computationally intensive 3D structure generation and direct surface area computation.
