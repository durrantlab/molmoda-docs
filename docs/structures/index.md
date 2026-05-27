# Structures

Computational drug discovery starts with the right structures: a target protein and a set of candidate compounds. This section covers how to bring those structures into MolModa and prepare them for downstream analysis.

- [Loading structures](loading/) — import proteins from the Protein Data Bank or AlphaFold, and compounds from PubChem, files, text, or the built-in molecular editor.
- [Pockets](pockets/) — identify and characterize potential binding sites on the protein surface.
- [Regions](regions/) — define the 3D box or sphere used to focus a docking calculation.

Once structures are loaded, several preparation plugins are available:

- `Protonate/Deprotonate Proteins` ([guided tour](https://molmoda.org/?tour=reduce){:target="_blank"}) and `Protonate/Deprotonate Compounds` ([guided tour](https://molmoda.org/?tour=protonatecomps){:target="_blank"}) assign appropriate protonation states for a given pH.
- `Align Proteins` ([guided tour](https://molmoda.org/?tour=alignproteins){:target="_blank"}) superimposes multiple protein structures onto a reference for comparison.
- `Rebuild Compound Coordinates` ([guided tour](https://molmoda.org/?tour=regen3dcoords){:target="_blank"}) regenerates 3D coordinates for a small molecule.
- `Edit Compound` ([guided tour](https://molmoda.org/?tour=editcompound){:target="_blank"}) opens the molecular editor on an already-loaded compound.
- `Find Similar Proteins` (RCSB sequence search) and `Find Similar Compounds` ([guided tour](https://molmoda.org/?tour=pubchemfindsimilar){:target="_blank"}) (PubChem analog search) help you build out a set of related structures.
- `Compound Names` ([guided tour](https://molmoda.org/?tour=pubchemnames){:target="_blank"}), `PubChem Properties` ([guided tour](https://molmoda.org/?tour=pubchemprops){:target="_blank"}), and `PubChem Bioassays` ([guided tour](https://molmoda.org/?tour=pubchembioassays){:target="_blank"}) annotate compounds with information retrieved from PubChem.
