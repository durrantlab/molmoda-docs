# Detection

MolModa uses [fpocketweb](https://doi.org/10.1186/s13321-022-00637-0) to automatically detect and place boxes over each pocket.

## Fpocket

This WASM-compiled tool is based on [fpocket](https://doi.org/10.1186/1471-2105-10-168).
Fpocket uses a sophisticated yet intuitive methodology to identify and analyze potential ligand-binding pockets within protein structures.
This open-source software leverages the principles of Voronoi tessellation and alpha spheres, integrated into a comprehensive framework capable of handling large-scale datasets efficiently.
At its core, Fpocket employs the concept of alpha spheres.
In this geometric notion, a sphere touches four atoms of a protein on its boundary without enclosing any atom within its volume.
These spheres are instrumental in delineating the voids and crevices on the protein surface, indicative of potential binding sites.

### Voronoi Tessellation and Alpha Sphere Detection

The initial step involves decomposing the protein's 3D space into Voronoi cells using the Qhull algorithm.
This decomposition facilitates the identification of alpha spheres.
Fpocket then filters these spheres based on size criteria to discard those too small (indicative of tight atomic packing) or too large (signifying solvent-exposed regions), focusing on those of intermediate sizes that represent potential binding pockets.

### Clustering of Alpha Spheres

Subsequently, Fpocket undertakes a clustering process where alpha spheres in proximity are grouped together, forming clusters that signify potential pockets.
This process involves several stages, from initial rough segmentation based on neighbor lists to more refined clustering leveraging multiple linkage criteria, ensuring the comprehensive detection of pocket regions.

### Characterization and Ranking of Pockets

Once identified, potential pockets are characterized based on various descriptors, such as size, hydrophobicity, and the types of atoms defining the pocket perimeter.
A scoring function, derived using Partial Least Squares (PLS) regression, ranks these pockets based on their potential to bind small, drug-like molecules.
This ranking not solely determines drugability but highlights pockets with favorable binding characteristics.
