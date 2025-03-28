
import os
import sys
from ComputationalEquilibriums import ReferenceDistribution
import numpy as np
import brush_analysis

#from matplotlib import pyplot as plt

# post process the directories with data

base_dir = #base_dir = "/scratch/chdavis/exp_3_c/NP_BRUSH"
processed = 0
total = 0

height_sigma = []


# walk the data path to access the data sets. this is the main part of the code
# for root, dirs, files in os.walk(base_dir):

for root, dirs, files in os.walk(base_dir):
    # walking the directories from the root directory
    error_list = {"no_files":[], "no_data":[]}
    path = root.split(os.sep)

    #check to make sure we aren't in a known bad directory
    if len(root.split("/")) < 4:
        continue

    if ("35" in root.split("/")[-4]) or ("BRUSH" in root.split("/")[-1]):
        #ignore the -.35 Umins because of the PBC issue in the Z direction
        #ignore Brush because of the NP_Brush directory
        continue

    #check to make sure you are in a directory with data.
    if ("NP" in root.split("/")[-1]):
        print("Data Directory: " + root)
        num_NPs = int(root.split("/")[-1].split("_")[-1])
        print("num NPs", num_NPs)

        dir_base = root
        total += 1  #number of directories with data

        system_dimensions = [0.0, 0.0, 0.0]  # default values that will be overwritten by file data

        # retrieve values from path. relies on naming conventions from create_exp.sh
        # Umin_-0.175/rad_2/den_0.03/den_64/den_32/NP_1024/

        poly_len = float(dir_base.split("/")[-2].split("_")[-1])
        gap_len = float(dir_base.split("/")[-3].split("_")[-1])
        sigma =  float(dir_base.split("/")[-4].split("_")[-1])
        radius = float(dir_base.split("/")[-5].split("_")[-1])
        print("radius: ", radius,
              "\tsigma: ", sigma,
              "\tgap: ", gap_len,
              "\tpoly len: ", poly_len)

        NP_Volume = 4.0 / 3.0 * np.pi * radius * radius * radius
        #print("NP_Volume ", NP_Volume)

        print("Reading Simulation Global Values")

        # get information about the simulation
        filecheck = [s for s in files if ".mpd" in s]

        filename= None
        if len(filecheck) == 1:
            filename = filecheck[0]
        else:
            pass # why is this else clause here?

        if filename is None:
            print(root + "\t" + filename + ".mpd doesn't exist")
            continue

        with open(dir_base +"/"+ filename, 'r') as fp:
            for i, line in enumerate(fp):
                if i == 9:  # this is the line with the sim dimensions when MD is used to create the file.
                    split_line = line.strip().split(" ")  # split the file line into its components
                    system_dimensions = [float(split_line[1]), float(split_line[2]), float(split_line[3])]

        # grab the number of particles and the name of the experiment from the save file
        parts = None
        name = None

        # calculate the density for the top of the brush. If the density is less than this on average
        # we are at the top of the brush
        brush_top_density = 1.0 / system_dimensions[0] / system_dimensions[1] /bin_length


        primary_process = True # primary process holds standard processing. the else clause is for experiments