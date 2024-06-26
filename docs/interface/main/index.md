# Main

The main window is the core interface of our application, designed to provide quick access to critical project components: the viewer, jobs, and data.
This design ensures users can manage their molecular research projects effectively.

## Viewer

The viewer component is essential for visualizing molecules, such as proteins and compounds.
Through the styles window, it offers a range of customizable visual representations, allowing for detailed and specific views of molecular structures.
Functionality integrated with the navigator facilitates the selective display and updating of molecule visuals within the viewer, enhancing the interactive experience.

<figure markdown>
![](../../img/interface/lapatinib-hover-atom.png){ alight=left height=300 }
</figure>

## Jobs

Within the jobs section, users can track the progress of tasks in real-time.
This includes ongoing jobs like molecular docking, their completion status, and runtime.
A job history feature is also available, providing a record of past jobs for analysis and review.

<figure markdown>
![](../../img/docking/td001/dock/docking-running.png){ alight=left height=300 }
</figure>

## Data

The data section organizes critical information from calculations including details on binding pockets, compound properties, docking scores, and poses.
It features sortable and filterable tables, making it easier for users to access and analyze their data efficiently, supporting informed decision-making in their projects.

=== "Pocket"

    <figure markdown>
    ![](../../img/docking/td001/pockets/pocket-properties.png){ alight=left height=300 }
    </figure>

=== "Docking"

    <figure markdown>
    ![](../../img/docking/td001/dock/docking-scores-exhaustive.8.png){ alight=left height=300 }
    </figure>
