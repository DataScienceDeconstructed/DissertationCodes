These codes are using in my Dissertation work.

create_exp.sh:
    purpose: This is the main code. It orchestrates the creation as well as submission of a series of NP + polymer brush
composite simulations to the cluster for processing.
    requires:
        MD - the Molecular Dynamics code from Mohamed Laradji's Computational Physics Lab at the University of Memphis
        basesim.sh
        main.py


basesim.sh:
    purpose: a template file for submitting jobs to the cluster at UofM. The create_exp.sh file loads this file into
        memory and concatenates it with a series of simulation specific commands for the cluster to execute. Create_exp
        then submits this file to the cluster for processing. there is one file created per simulation.
    requires:
        None

main.py:
    purpose: this Python file holds code for parsing the output of simulations. basesim.sh has a couple of lines placed
        in it by create_exp.sh that force the cluster to load main.py after each simulation. The code performs quick
        processing that characterizes the distribution of NPs inside and outside the polymer brush as well as their
        density profiles.
    requires:
        ComputationalEquilibriums.py

ComputationalEquilibriums.py
    purpose: this Python code creates a utility class with member variables and functions that make tracking the NP
        brush loading easier. It is used to track the current brush height, and to build the distribution of NPs inside
        and outside the brush.
    requires:
        None