# TD001. Epidermal growth factor receptor inhibitors

TODO:

!!! tip

    You may download and open the [MolModa file](./td001.molmoda){:download="td001.molmoda"} and see the final results of this tutorial.

## Learning objectives

At the end of this tutorial, you should be able to

-   Load a structure from the Protein Data Bank;
-   Process and prepare a protein for docking;
-   Identify binding pockets;
-   Load in multiple compounds from a single SMILES file;
-   Dock multiple ligands into a single protein and analyze the results.

## Protein

### Load PDB

[3W32](https://www.rcsb.org/structure/3w32)

<figure markdown>
![](../../../img/docking/td001/load-pdb.png){ alight=left height=300 }
</figure>

### Remove water molecules

=== "1. Original"

    <figure markdown>
    ![](../../../img/docking/td001/waters/pdb-expanded-nav.png)
    </figure>

=== "2a. Hide waters"

    <figure markdown>
    ![](../../../img/docking/td001/waters/pdb-hide-waters.png)
    </figure>

=== "2b. Delete waters"

    <figure markdown>
    ![](../../../img/docking/td001/waters/pdb-delete-waters.png)
    </figure>

=== "3. Result"

    <figure markdown>
    ![](../../../img/docking/td001/waters/pdb-remove-waters.png)
    </figure>

### Protonation

TODO:

=== "1. Original"

    <figure markdown>
    ![](../../../img/docking/td001/prot/protein-before-prot.png)
    </figure>

=== "2. Menu"

    <figure markdown>
    ![](../../../img/docking/td001/prot/pdb-prot-menu.png)
    </figure>

=== "3. Popup"

    <figure markdown>
    ![](../../../img/docking/td001/prot/pdb-prot-popup.png)
    </figure>

=== "4. Protonated"

    <figure markdown>
    ![](../../../img/docking/td001/prot/protein-after-prot.png)
    </figure>

TODO: delete deprotonated protein

## Pockets

TODO:

=== "1. Detect pockets"

    <figure markdown>
    ![](../../../img/docking/td001/pockets/pocket-detection.png)
    </figure>

=== "2. Found pockets"

    <figure markdown>
    ![](../../../img/docking/td001/pockets/all-pockets.png)
    </figure>

=== "3. Pocket properties"

    You may download the [Pocket properties CSV file](./fpocketweb-properties.csv){:download="fpocketweb-properties.csv"} as well.

    <figure markdown>
    ![](../../../img/docking/td001/pockets/pocket-properties.png)
    </figure>

=== "4. Selected pocket"

    <figure markdown>
    ![](../../../img/docking/td001/pockets/pocket-select.png)
    </figure>

=== "5. Modified pocket"

    <figure markdown>
    ![](../../../img/docking/td001/pockets/modified-pocket.png)
    </figure>

=== "6. Remove compounds"

    <figure markdown>
    ![](../../../img/docking/td001/pockets/pocket-no-molecules.png)
    </figure>

## Compounds

[SMILES file](./td001.smiles){:download="td001.smiles"}

=== "1. Open molecules"

    <figure markdown>
    ![](../../../img/docking/td001/molecules/open-molecules.png)
    </figure>

=== "2. Loaded molecules"

    <figure markdown>
    ![](../../../img/docking/td001/molecules/loaded-molecules.png)
    </figure>

=== "3. Example molecule"

    <figure markdown>
    ![](../../../img/docking/td001/molecules/example-molecule.png)
    </figure>

### Protonate

=== "1. Before"

    <figure markdown>
    ![](../../../img/docking/td001/prot/compound-before-prot.png)
    </figure>

=== "2. Options"

    <figure markdown>
    ![](../../../img/docking/td001/prot/compound-prot-popup.png)
    </figure>

=== "3. After"

    <figure markdown>
    ![](../../../img/docking/td001/prot/compound-after-prot.png)
    </figure>

## Docking

=== "1. Menu"

    <figure markdown>
    ![](../../../img/docking/td001/dock/docking-menu.png)
    </figure>

=== "2. Docking options"

    <figure markdown>
    ![](../../../img/docking/td001/dock/docking-options.png)
    </figure>

=== "3. Running"

    <figure markdown>
    ![](../../../img/docking/td001/dock/docking-running.png)
    </figure>

### Exhaustiveness

#### 8

=== "1. Docked poses"

    <figure markdown>
    ![](../../../img/docking/td001/dock/docked-poses.png)
    </figure>

=== "2. Scores"

    <figure markdown>
    ![](../../../img/docking/td001/dock/docking-scores-exhaustive.8.png)
    </figure>

=== "3. Top hit"

    <figure markdown>
    ![](../../../img/docking/td001/dock/top-hit-exhastive.8.png)
    </figure>

#### 32

=== "1. Scores"

    <figure markdown>
    ![](../../../img/docking/td001/dock/docking-scores-exhaustive.32.png)
    </figure>

=== "2. Top hit"

    <figure markdown>
    ![](../../../img/docking/td001/dock/top-hit-exhastive.32.png)
    </figure>

### Pose refinement

=== "1. Pose refinement"

    <figure markdown>
    ![](../../../img/docking/td001/dock/refined-dock.png)
    </figure>

=== "2. Scores"

    <figure markdown>
    ![](../../../img/docking/td001/dock/refined-scores.png)
    </figure>

=== "2. Top poses"

    <figure markdown>
    ![](../../../img/docking/td001/dock/top-poses.png)
    </figure>
