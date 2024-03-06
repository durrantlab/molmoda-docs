# Proteins

The `File` menu, shown below, contains several ways to import or load structures into MolModa.

<figure markdown>
![](/img/menus/file-structures.png){ alight=left height=300 }
</figure>

## Protein Data Bank

You can load structures directly from the [Protein Data Bank (PDB)](https://www.rcsb.org/) by clicking `File` :material-arrow-right: `PDB ID`.

<figure markdown>
![](/img/structures/load-pdb.png){ alight=left height=300 }
</figure>

For example, we can load in [1XDN](https://www.rcsb.org/structure/1XDN), a RNA editing ligase 1 from *Trypanosoma brucei*.

<figure markdown>
![](/img/structures/pdb-1xdn-initial.png){ alight=left width=800 }
</figure>

MolModa will automatically load all chains; [8GTT](https://www.rcsb.org/structure/8GTT) for example, will have all seven chains shown by expanding `8GTT` in the [navigator][navigator].

<figure markdown>
![](/img/structures/pdb-8gtt-initial.png){ alight=left width=800 }
</figure>

## AlphaFold

Not all structures are available in the PDB.
You can also load structures directly from the [AlphaFold Protein Structure Database](https://alphafold.ebi.ac.uk/) by clicking `File` :material-arrow-right: `AlphaFold`.

<figure markdown>
![](/img/structures/load-alphafold.png){ alight=left height=300 }
</figure>

Let's go ahead and load the same RNA-editing ligase, but from the Alphafold Protein Structure Database.
We do this by providing the UniProt accession number, [P86927](https://alphafold.ebi.ac.uk/entry/P86927).

<figure markdown>
![](/img/structures/af-p86927.png){ alight=left height=300 }
</figure>

<!-- LINKS -->

[navigator]: /interface/navigator
