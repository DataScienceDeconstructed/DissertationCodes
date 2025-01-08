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
base_dir = "/scratch/chdavis/test/NP_BRUSH"
processed = 0
total = 0

height_sigma = []


# walk the data path to access the data sets. this is the main part of the code
# for root, dirs, files in os.walk(base_dir):

for root, dirs, files in os.walk(base_dir):
    print(root, dirs)
    error_list = {"no_files":[], "no_data":[]}
    path = root.split(os.sep)
    if ("35" in root.split("/")[-4]) or ("BRUSH" in root.split("/")[-1]):
        #ignore the -.35 Umins because of the PBC issue in the Z direction
        continue

    #check to make sure you are in a directory with data.
    if ("NP" in root.split("/")[-1]):
        print("root " + root)
        num_NPs = int(root.split("/")[-1].split("_")[-1])
        print("num NPs", num_NPs)

        dir_base = root
        total += 1

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
        # poly_profile holds the number of polymers at sectional slice
        poly_profile_lag = []
        poly_profile_current = np.zeros(total_bins, dtype=int)
        np_profile_lag = []
        np_profile_current = np.zeros(total_bins, dtype=int)
        poly_avg_height_lag = []
        poly_avg_height_lag.append(0)
        tempheight = 0
        monocount = 0
        system_dimensions = [0.0, 0.0, 0.0]  # default values that will be overwritten by file data

        # retrieve radius from filename and calculate NP Volume. relies on naming conventions from create_exp.sh
        radius = float(dir_base.split("/")[-3].split("_")[-1])
        sigma =  float(dir_base.split("/")[-2].split("_")[-1])
        print("sigma ", sigma)

        print("radius ", radius)
        NP_Volume = 4.0 / 3.0 * np.pi * radius * radius * radius
        print("NP_Volume ", NP_Volume)

        print("Reading Simulation Global Values")

        # get information about the simulation
        filecheck = [s for s in files if ".mpd" in s]
        if len(filecheck) == 1:
            filename = filecheck[0]
        else:
            pass


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
        primary_process = True

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
            top = brush_analysis.get_brush_height(frame_file,
                                            parts,
                                            total_bins,
                                            bin_length,
                                            .2,
                                            brush_top_density,
                                                  save_to_dir=True,
                                                  dir_base=dir_base)
            print("top \t", top)

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
            np_profile_current = np.array(returndict["np_profile"])
            loading_array[:, 1] = loading_array[:, 1] * NP_Volume / Solvent_Volume
            loading_array[:, 0] = loading_array[:, 0] * NP_Volume / Brush_Volume

            with open(dir_base + "/loading_solv.dat", 'w') as fp:
                np.savetxt(fp, loading_array[:,1], fmt='%.6e', delimiter=' ', newline='\n', header=str(top), footer='', comments='# ',
                          encoding=None)
            with open(dir_base + "/loading_brush.dat", 'w') as fp:
                np.savetxt(fp, loading_array[:,0], fmt='%.6e', delimiter=' ', newline='\n', header=str(top), footer='', comments='# ',
                          encoding=None)

            #todo use np columnstack to put in the top of the brush for the profile
            with open(dir_base + "/z_profile.dat", 'w') as fp:
                np.savetxt(fp, np_profile_current, fmt='%.6e', delimiter=' ', newline='\n', header=str(top), footer='', comments='# ',
                          encoding=None)

            # fig, ax = plt.subplots()
            # ax.plot(loading_array[:, 1], color=(0,0,1), label="Solvent")
            # ax2 = ax.twinx()  # secondary axis
            # ax2.plot(loading_array[:, 0], color=(1,0,0), label="Brush")
            # plt.show()
        else:
            dummy = brush_analysis.retrieve_height(dir_base)
            height_sigma.append([radius, sigma, dummy[0], dummy[1]] )
print("height sigma")
rad = 2
sig=21
np_hVs = np.array([ [ x[1], x[2], x[3] ] for x in height_sigma if int(x[0]) ==rad and int(float(x[1])*100.)==sig])
print(np_hVs.shape)
fig, ax = plt.subplots()
ax.scatter(np_hVs[:, 2], np_hVs[:, 1],color=(0,0,1)) # sigma v height
plt.title("Phi vs Brush Height for r={} and s={}".format(rad,sig))
plt.xlabel('solvent volume fraction')
plt.ylabel('brush height')

plt.show()

sys.exit(0)

        # # process the simulation file
        # with open(dir_base + "/frames_" + filename[:-4] + ".xyz", 'r') as fp:
        #     for i, line in enumerate(fp):
        #         split_line = line.strip().split("\t")  # split the file line into its components
        #
        #         # if we have a distributions save it
        #         # there is a line for each particle plus a line for the number of particles and name of experiment.
        #         # that's why we have (parts+2) in each frame. that means each frame can be indexed by i % (parts + 2)
        #         if i % (parts + 2) == 0:
        #             if i > 0:  # skips the first time since no ditribution to process yet.
        #                 #storing distribution
        #                 info_lag.append(dist.Distribution)
        #                 # already processed one distribution so save it's max height
        #                 brushz_lag.append(dist.ReferenceValue)
        #                 # grab the polymer profile for the time step
        #                 poly_profile_lag.append(poly_profile_current)
        #                 # grab the np profile for the time step
        #                 np_profile_lag.append(np_profile_current)
        #                 # append the avg height list
        #                 poly_avg_height_lag.append(0)
        #                 monocount = 0
        #
        #                 # reset the distributions so that processing can continue.
        #                 dist = ReferenceDistribution(_type="Binary", _reference=0.0, _dist=[0, 0])
        #                 # reset the polymer profile
        #                 poly_profile_current = np.zeros(total_bins)
        #                 # reset the NP profile
        #                 np_profile_current = np.zeros(total_bins)
        #
        #         # grab and record the highest z value for a polymer. This is the brush max height.
        #         if split_line[0] == '1':  # spilt_line[0] will always exist even on break lines with the number of particles and name of exp.
        #             # line starting with 1 is a monomer on a polymer chain
        #             # update polymer z profiles
        #             tempheight = float(split_line[3])
        #
        #             bin = int(float(split_line[3]) / bin_length)
        #             poly_profile_current[bin] += 1
        #             if float(split_line[3]) > dist.ReferenceValue:  # check to see if z value is higher than current max
        #                 # update brush height in distribution class
        #                 dist.update_reference(float(split_line[3]))
        #
        #         # identify the NP inside and outside the brush
        #         if split_line[0] == '2':  # Line starting with a 2 is a np
        #             # update the z profile for NPs and
        #             bin = int(float(split_line[3]) / bin_length)
        #             np_profile_current[bin] += 1
        #             # pass the z value for the NP to the distribution. It will update according to current z height
        #             dist.update_distribution(float(split_line[3]))
        #
        #         if split_line[0] == '0':
        #             poly_avg_height_lag[-1] = tempheight
        #             tempheight = 0
        #
        #
        #
        # print("processing equilibriums")
        # print(str(len(info_lag)) + " frames in file")
        #
        # print("getting profiles")
        # profile_data = np.array(poly_profile_lag)
        # print("profile_data\t", profile_data.shape)
        # useful_data_avg = np.mean(profile_data[int(profile_data.shape[0]*.2):,:], axis=0)
        # print("useful_data\t", useful_data_avg.shape)
        #
        #
        # plt.plot(useful_data_avg[:140])
        # plt.show()
        #
        # pass
        #
        # print("plotting datafiles")
        # # write out data of note
        # # info lag holds the distribution informaiton for each time step
        # for i, x in enumerate(info_lag):
        #     print("frame " + str(i) +": "+ str(poly_avg_height_lag[i]) + "   " + str(brushz_lag[i]))
        #         #fp.write(str(brushz_lag[i]) + "\n")  # max height for the brush at each timestep
        #
        #
        # print("main derived value processing completed.")
        #
        #
        #
        #
