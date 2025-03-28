#updated to process the new approach via laradji
# need to process with 80% of simulation data
# create new file with saturation values

import os
import sys
from ComputationalEquilibriums import ReferenceDistribution
import numpy as np
import brush_analysis

from matplotlib import pyplot as plt

# post process the directories with data
#base_dir = "/project/chdavis/chdavis/exp_totals/NP_BRUSH/"
#base_dir = "/scratch/chdavis/exp_2_a/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_b/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_c/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_d/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_e/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_f/NP_BRUSH"

base_dir = "/scratch/chdavis"
processed = 0
total = 0

height_sigma = []


# walk the data path to access the data sets. this is the main part of the code
# for root, dirs, files in os.walk(base_dir):

for root, dirs, files in os.walk(base_dir):
    print(root, dirs)
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
        print("root " + root)
        num_NPs = int(root.split("/")[-1].split("_")[-1])
        print("num NPs", num_NPs)

        dir_base = root
        total += 1  #number of directories with data

        # dist holds number of particles loaded in brush and floating in solvent at each time step
        dist = ReferenceDistribution(_type="Binary", _reference=0.0, _dist=[0, 0])
        significance_level = 0.05
        sim_track = 0

        # info_lag holds the dist objects for each time step
        info_lag = []
        # brushz_lag holds the brush height at each time step
        brushz_lag = []

        # bins for z axis profiling
        bin_length = 0.5  # this bin length is used to cut the system height into intervals for binning
        total_bins = int(1000.0 / bin_length)  # 1000 is used because it is a sim max. i.e. the system can only have a height of 1000
        bin_values = np.asarray([x*bin_length  for x in range(total_bins)]) # z values for the bins

        # poly_profile holds the number of polymers at sectional slice
        poly_profile_lag = []
        poly_profile_current = np.zeros(total_bins, dtype=int)
        np_profile_lag = []
        np_profile_current = np.zeros(total_bins, dtype=int)

        #hold average height based "top" calculation
        poly_avg_height_lag = []
        poly_avg_height_lag.append(0)
        tempheight = 0
        monocount = 0

        system_dimensions = [0.0, 0.0, 0.0]  # default values that will be overwritten by file data

        # retrieve radius from filename and calculate NP Volume. relies on naming conventions from create_exp.sh

        sigma =  float(dir_base.split("/")[-2].split("_")[-1])
        print("sigma ", sigma)

        radius = float(dir_base.split("/")[-3].split("_")[-1])
        print("radius ", radius)
        NP_Volume = 4.0 / 3.0 * np.pi * radius * radius * radius
        print("NP_Volume ", NP_Volume)

        print("Reading Simulation Global Values")

        # get information about the simulation
        filecheck = [s for s in files if ".mpd" in s]

        if len(filecheck) == 1:
            filename = filecheck[0]
        else:
            pass # why is this else clause here?


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

        if primary_process :
            print("Opening Simulation Data File")

            with open(dir_base + "/frames_" + filename[:-4] + ".xyz", 'r') as fp:
                for i, line in enumerate(fp):
                    if i == 0:
                        parts = int(line.strip())  # the first line has the number of particles in the simulation
                    if i == 1:
                        name = line.strip()  # I don't think we use this anymore it can probably go
                    if i > 1:
                        break

            print("processing brush")

            frame_file = dir_base + "/frames_" + filename[:-4] + ".xyz"
            #get top of brush
            top = brush_analysis.get_brush_height_inflection(frame_file,
                                            parts,
                                            total_bins,
                                            bin_length,
                                            .2,
                                            save_to_dir=True,
                                            dir_base=dir_base)

            print("top \t", top)
            if top < 2:
                print("*******************************************\nBAD TOP calculation in "+root+"******************************************")


            # calculate volumes for brush and solvent
            Solvent_Volume = system_dimensions[0]*system_dimensions[1]*(system_dimensions[2]-top)
            Brush_Volume = system_dimensions[0] * system_dimensions[1] * top
            print("solvent volume\t", Solvent_Volume)
            print("brush volume\t", Brush_Volume)

            #get NPs in brush

            returndict = brush_analysis.calc_loading(frame_file,
                                                  parts,
                                                  top,
                                                  radius,
                                                  total_bins,
                                                  bin_length
                                                  )
            loading_array = np.array(returndict["loading"])
            loading_array[:, 1] = loading_array[:, 1] * NP_Volume / Solvent_Volume
            loading_array[:, 0] = loading_array[:, 0] * NP_Volume / Brush_Volume

            np_profile_current = np.array(returndict["np_profile"])
            poly_profile_current = np.array(returndict["poly_profile"])

            results_dir = "/post"
            if not os.path.exists(dir_base + results_dir):
                os.makedirs(dir_base + results_dir)

            with open(dir_base + results_dir + "/loading_solv.dat", 'w') as fp:
                np.savetxt(fp, loading_array[:,1], fmt='%.6e', delimiter=' ', newline='\n', header=str(top), footer='', comments='# ',
                          encoding=None)
            with open(dir_base + results_dir + "/loading_brush.dat", 'w') as fp:
                np.savetxt(fp, loading_array[:,0], fmt='%.6e', delimiter=' ', newline='\n', header=str(top), footer='', comments='# ',
                          encoding=None)

            with open(dir_base + results_dir + "/z_profile.dat", 'w') as fp:
                np.savetxt(fp, np_profile_current, fmt='%.6e', delimiter=' ', newline='\n', header=str(top), footer='', comments='# ',
                          encoding=None)

            #save a file with profile data
            #record the top of the brush and system
            # use 1 because things are normalized to a pdf for the profiles
            brush_top = np.zeros(total_bins, dtype=np)
            brush_top[int(top//bin_length)] += 1
            brush_top[int(system_dimensions[2]//bin_length)] += 1
            z_data = np.column_stack((bin_values, np_profile_current, poly_profile_current, brush_top))
            with open(dir_base + results_dir +  "/z_profile_data.dat", 'w') as fp:
                np.savetxt(fp, z_data, fmt='%.6e', delimiter=' ', newline='\n', header=str(top), footer='', comments='# ',
                          encoding=None)


        else:
            dummy = brush_analysis.retrieve_height(dir_base)
            height_sigma.append([radius, sigma, dummy[0], dummy[1]] )

print("processing finished")

