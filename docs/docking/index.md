# Docking

MolModa's docking workflow predicts how small molecules bind to a target protein, returning both a pose (geometry) and an affinity score. Docking is run from `Binding` :material-arrow-right: `Docking` :material-arrow-right: `Compound Docking/Scoring` ([guided tour](https://molmoda.org/?tour=webina){:target="_blank"}).

For a step-by-step walkthrough, see the [TD001 tutorial](tutorials/td001/).

## Preparing for docking

Before running a docking calculation, you typically need to:

1. Load a protein ([Protein Data Bank, AlphaFold](../structures/loading/proteins/), or a local file) and a set of [compounds](../structures/loading/compounds/) (PubChem, file, text, or the molecular editor).
2. Protonate the protein and the compounds at the relevant pH (`Proteins` :material-arrow-right: `Protonate/Deprotonate Proteins` ([guided tour](https://molmoda.org/?tour=reduce){:target="_blank"}); `Compounds` :material-arrow-right: `Build` :material-arrow-right: `Protonate/Deprotonate Compounds` ([guided tour](https://molmoda.org/?tour=protonatecomps){:target="_blank"})).
3. Identify a binding [pocket](../structures/pockets/) (`Proteins` :material-arrow-right: `Pocket Detection` ([guided tour](https://molmoda.org/?tour=fpocketweb){:target="_blank"})) or define a custom region (`Regions` :material-arrow-right: `New Region` ([guided tour](https://molmoda.org/?tour=newregion){:target="_blank"}) or `Regions` :material-arrow-right: `Region From Molecule(s)` ([guided tour](https://molmoda.org/?tour=regionfrommolecules){:target="_blank"})).

## Analyzing results

After docking, two analysis plugins help you interpret the output:

- `2D Interaction Diagram` (`Binding` :material-arrow-right: `Analysis`) ([guided tour](https://molmoda.org/?tour=poseview){:target="_blank"}) — generates a PoseView diagram showing protein-ligand interactions for a selected pose.
- `Evaluate Docking Performance` (`Binding` :material-arrow-right: `Docking`) ([guided tour](https://molmoda.org/?tour=evalscreen){:target="_blank"}) — calculates receiver-operating-characteristic (ROC) and enrichment-factor curves, useful for benchmarking a docking protocol against known actives and decoys.

Docking scores and poses are organized in the [Data panel](../interface/main/#data), where you can sort, filter, and select entries for closer inspection.
