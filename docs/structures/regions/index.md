# Regions

A region defines the 3D volume that docking and other site-specific calculations will focus on. Regions are shown in the [Navigator](../../interface/navigator/) alongside molecules and can be hidden, focused, or deleted in the same way.

MolModa provides two ways to create a region, both under the `Regions` menu.

## New Region

`Regions` :material-arrow-right: `New Region` ([guided tour](https://molmoda.org/?tour=newregion){:target="_blank"}) adds a new box or spherical region to the project. You specify the center, dimensions, and shape directly. This is the right choice when you already know the coordinates of the site you want to target, or when you want full manual control over the docking volume.

## Region From Molecule(s)

`Regions` :material-arrow-right: `Region From Molecule(s)` ([guided tour](https://molmoda.org/?tour=regionfrommolecules){:target="_blank"}) creates a region that surrounds one or more selected molecules. This is convenient when a co-crystallized ligand or a detected pocket already marks the site of interest: select the relevant entries in the Navigator, run the plugin, and a region is generated to encompass them.

## Working with regions

Once a region exists, you can:

- Toggle its visibility from the Navigator to keep the viewer uncluttered.
- Focus the view on it to inspect placement relative to the protein.
- Use it as the docking volume when running `Binding` :material-arrow-right: `Docking` :material-arrow-right: `Compound Docking/Scoring` ([guided tour](https://molmoda.org/?tour=webina){:target="_blank"}).

Regions can be deleted from the Navigator if they are no longer needed; like other deletions, this action is irreversible.
