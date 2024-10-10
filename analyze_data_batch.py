#updated to process the new approach via laradji
# need to process with 80% of simulation data
# create new file with saturation values

import os
from ComputationalEquilibriums import ReferenceDistribution
import numpy as np
import sys
from scipy import stats

# post process the directories with data
base_dir = "/project/chdavis/chdavis/exp_totals/NP_BRUSH/"
processed = 0
total = 0

# walk the data path to access the data sets. this is the main part of the code
# for root, dirs, files in os.walk(base_dir):

for root, dirs, files in os.walk(base_dir):
    print(root, dirs)
    error_list = {"no_files":[], "no_data":[]}
    path = root.split(os.sep)
    if ("35" in root.split("/")[-4]):
        continue

    #are we in a data directory?
    if ("NP" in root.split("/")[-1]):
        print("root " + root)
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
        bin_length = 10.0  # this bin length is used to cut the system height into intervals for binning
        total_bins = int(
            1000.0 / bin_length)  # 1000 is used because it is a sim max. i.e. the system can only have a height of 1000
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
        radius = float(dir_base.split("/")[-4].split("_")[-1])
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
#frames_exp_1_Umin-0-35_rad2_den0-21_NP320.xyz

        with open(dir_base +"/"+ filename, 'r') as fp:
            for i, line in enumerate(fp):
                if i == 9:  # this is the line with the sim dimensions when MD is used to create the file.
                    split_line = line.strip().split(" ")  # split the file line into its components
                    system_dimensions = [float(split_line[1]), float(split_line[2]), float(split_line[3])]

        # grab the number of particles and the name of the experiment from the save file
        parts = None
        name = None
        print("Opening Simulation Data File")

        with open(dir_base + "/frames_" + filename[:-4] + ".xyz", 'r') as fp:
            for i, line in enumerate(fp):
                if i == 0:
                    parts = int(line.strip())  # the first line has the number of particles in the simulation
                if i == 1:
                    name = line.strip()  # I don't think we use this anymore it can probably go
                if i > 1:
                    break

        print("processing densities")

        # process the simulation file
        with open(dir_base + "/frames_" + filename[:-4] + ".xyz", 'r') as fp:
            for i, line in enumerate(fp):
                split_line = line.strip().split("\t")  # split the file line into its components

                # if we have a distributions save it
                # there is a line for each particle plus a line for the number of particles and name of experiment.
                # that's why we have (parts+2) in each frame. that means each frame can be indexed by i % (parts + 2)
                if i % (parts + 2) == 0:
                    if i > 0:  # skips the first time since no ditribution to process yet.
                        # process distributions for Chi squared metric
                        # run this for the first and last info sets.
                        # iterative sets just show that the density growth is not exceptional.
                        # probably need to handle it in 2^N steps.
                        # code below needs refactor to handle multiple lag deltas.
                        info_lag.append(dist.Distribution)
                        # already processed one distribution so save it's max height
                        brushz_lag.append(dist.ReferenceValue)
                        # grab the polymer profile for the time step
                        poly_profile_lag.append(poly_profile_current)
                        # grab the np profile for the time step
                        np_profile_lag.append(np_profile_current)
                        # append the avg height list
                        poly_avg_height_lag.append(0)
                        monocount = 0

                        # reset the distributions so that processing can continue.
                        dist = ReferenceDistribution(_type="Binary", _reference=0.0, _dist=[0, 0])
                        # reset the polymer profile
                        poly_profile_current = np.zeros(total_bins)
                        # reset the NP profile
                        np_profile_current = np.zeros(total_bins)

                # grab and record the highest z value for a polymer. This is the brush height.
                if split_line[0] == '1':  # spilt_line[0] will always exist even on break lines with the number of particles and name of exp.
                    # line starting with 1 is a monomer on a polymer chain
                    # update polymer z profiles
                    tempheight = float(split_line[3])

                    bin = int(float(split_line[3]) / bin_length)
                    poly_profile_current[bin] += 1
                    if float(split_line[3]) > dist.ReferenceValue:  # check to see if z value is higher than current max
                        # update brush height in distribution class
                        dist.update_reference(float(split_line[3]))

                # identify the NP inside and outside the brush
                if split_line[0] == '2':  # Line starting with a 2 is a np
                    # update the z profile for NPs and
                    bin = int(float(split_line[3]) / bin_length)
                    np_profile_current[bin] += 1
                    # pass the z value for the NP to the distribution. It will update according to current z height
                    dist.update_distribution(float(split_line[3]))

                if split_line[0] == '0':
                    poly_avg_height_lag[-1] = tempheight
                    tempheight = 0



                # technicaly it is possible that this CODE could be counting some NPs as outside the brush that are below
                # the highet of the brush IF the NP is encountered before a polymer with a height greater than the z value
                # of the NP is encountered after the NP; however, the brushes start in an entropiclly disadvantaged configuration
                # of total elongation so this scenario is impossible in the first frame. Consequent frames are unlikely to
                # suffer as the polymers' heights should all contract at roughly the same miniscule rate for each timestep.
                # the real concern is in nonequilibrium situations when there is a great difference in the delta between
                # brush heights between t(i) and t(i+1). talk to Laradji about this.

        print("processing equilibriums")
        print(str(len(info_lag)) + " frames in file")

        # lags = [int(2 ** c) for c in range(int(np.log2(len(info_lag) / 2)))]
        # rValue = [-1, 0]

        print("plotting datafiles")
        # write out data of note
        # info lag holds the distribution informaiton for each time step
        for i, x in enumerate(info_lag):
            print("frame " + str(i) +": "+ str(poly_avg_height_lag[i]) + "   " + str(brushz_lag[i]))
                #fp.write(str(brushz_lag[i]) + "\n")  # max height for the brush at each timestep


        print("main derived value processing completed.")




