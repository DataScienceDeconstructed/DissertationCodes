#write out graphs from the processing

import os
import sys
from ComputationalEquilibriums import ReferenceDistribution
import numpy as np

from matplotlib import pyplot as plt

# post process the directories with data
#base_dir = "/project/chdavis/chdavis/exp_totals/NP_BRUSH/"
#base_dir = "/scratch/chdavis/exp_2_a/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_b/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_c/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_d/NP_BRUSH"
base_dir = "/scratch/chdavis/exp_2_e/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_f/NP_BRUSH"
#base_dir = "/scratch/chdavis/test/NP_BRUSH"
#comment that can be undone

dataset = {}

def read_dataset():
# walk the data path to access the data sets. this is the main part of the code
# for root, dirs, files in os.walk(base_dir):
    dataset = {}
    for root, dirs, files in os.walk(base_dir):
        print(root, dirs)
        error_list = {"no_files":[], "no_data":[]}
        path = root.split(os.sep)

        #check to make sure we aren't in a known bad directory
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


            # bins for z axis profiling
            bin_length = 0.5  # this bin length is used to cut the system height into intervals for binning
            total_bins = int(1000.0 / bin_length)  # 1000 is used because it is a sim max. i.e. the system can only have a height of 1000
            bin_values = np.asarray([x*bin_length  for x in range(total_bins)]) # z values for the bins

            system_dimensions = [0.0, 0.0, 0.0]  # default values that will be overwritten by file data

            #retreive the path values we use as keys
            Umin = float(dir_base.split("/")[-4].split("_")[-1])
            sigma =  float(dir_base.split("/")[-2].split("_")[-1])
            radius = float(dir_base.split("/")[-3].split("_")[-1])

            #add and dictionary componenets not already there
            if str(Umin) not in dataset.keys():
                dataset[str(Umin)] = {}
            if str(radius) not in dataset[str(Umin)].keys():
                dataset[str(Umin)][str(radius)] = {}
            if str(sigma) not in dataset[str(Umin)][str(radius)].keys():
                dataset[str(Umin)][str(radius)][str(sigma)] = {}
            if str(num_NPs) not in dataset[str(Umin)][str(radius)][str(sigma)].keys():
                dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)] = {}

            #read in the loading data
            with open(dir_base + "/post/loading_brush.dat", 'r') as fp:
                dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["loading_brush"] = [x for i,x in enumerate(fp.readlines()) if i > 0]
            with open(dir_base + "/post/loading_solv.dat", 'r') as fp:
                dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["loading_solv"] = [x for i,x in enumerate(fp.readlines()) if i > 0]
    return dataset

def build_concentration_graphs():
    pass

if __name__ == "__main__":
    dataset = read_dataset()
    pass