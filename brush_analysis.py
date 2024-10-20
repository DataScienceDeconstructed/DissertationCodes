import os
from ComputationalEquilibriums import ReferenceDistribution
import numpy as np


def get_brush_height(filename,
                     parts,         # particles in the simulation
                     total_bins,    # total number of bins
                     bin_length,     # length of the bins
                     equil_percent,   # 1 minus what percentage of the simulation time to include in the calculation
                     brush_top_density):
# process the simulation file
    poly_profile_lag = []
    poly_profile_current = np.zeros(total_bins, dtype=int)

    #with open(dir_base + "/frames_" + filename[:-4] + ".xyz", 'r') as fp:
    with open(filename, 'r') as fp:
        for i, line in enumerate(fp):
            split_line = line.strip().split("\t")  # split the file line into its components

            # there is a line for each particle plus a line for the number of particles and name of experiment.
            # that's why we have (parts+2) in each frame. that means each frame can be indexed by i % (parts + 2)
            if i % (parts + 2) == 0:
                if i > 0:  # skips the first time since no data to save yet.
                    # grab the polymer profile for the time step
                    poly_profile_lag.append(poly_profile_current)
                    # reset the polymer profile
                    poly_profile_current = np.zeros(total_bins)

            # grab and record the highest z value for a polymer. This is the brush max height.
            if split_line[0] == '1':  # spilt_line[0] will always exist even on break lines with the number of particles and name of exp.
                bin = int(float(split_line[3]) / bin_length)
                poly_profile_current[bin] += 1

        profile_data = np.array(poly_profile_lag)
        useful_data_avg = np.mean(profile_data[int(profile_data.shape[0] * equil_percent):, :], axis=0)
        top_indexes = [i for i, x in enumerate(useful_data_avg) if x < brush_top_density and i > int(1.0/ bin_length)+1]
        return top_indexes[0] * bin_length

def calc_loading(filename,
                 parts,
                 top,
                 radius,
                 num_NPs):

    info_lag = []
    dist = ReferenceDistribution(_type="Binary", _reference=top, _dist=[0, 0])
    R_sum = arr = np.zeros((num_NPs, 3))
    R2d_sum = arr = np.zeros((num_NPs, 1))
    NP_index = 0
# process the simulation file
    with open(filename, 'r') as fp:
        for i, line in enumerate(fp):
            split_line = line.strip().split("\t")  # split the file line into its components

            if i == 50:
                #reset R calculations after equilibrium
                # this is just a test
                R_sum = arr = np.zeros((num_NPs, 3))
                R2d_sum = arr = np.zeros((num_NPs, 1))

            # there is a line for each particle plus a line for the number of particles and name of experiment.
            # that's why we have (parts+2) in each frame. that means each frame can be indexed by i % (parts + 2)
            if i % (parts + 2) == 0:
                if i > 0:  # skips the first time since no ditribution to process yet.
                    #storing distribution
                    info_lag.append(dist.Distribution)

                    # reset the distributions so that processing can continue.
                    dist = ReferenceDistribution(_type="Binary", _reference=top, _dist=[0, 0])
                    NP_index = 0

            # identify the NP inside and outside the brush
            if split_line[0] == '2':  # Line starting with a 2 is a np
                # pass the z value for the NP to the distribution. It will update according to current z height
                dist.update_distribution(float(split_line[3]), radius)
                R_sum[NP_index] += np.array([float(split_line[1]),
                                            float(split_line[2]),
                                            float(split_line[3])])
                R2d_sum[NP_index] += np.array([float(split_line[1])*float(split_line[1]) +
                                            float(split_line[2])*float(split_line[2]) +
                                            float(split_line[3])*float(split_line[3])])
                NP_index += 1
    R_avg = R_sum / len(info_lag)
    R2d_avg = R2d_sum / len(info_lag)
    Ravg_2d = np.sum(R_avg * R_avg, axis=1)
    Rstd = np.sqrt(  np.transpose(R2d_avg) - Ravg_2d)

    return info_lag

# def original(filename):
# # process the simulation file
#     with open(dir_base + "/frames_" + filename[:-4] + ".xyz", 'r') as fp:
#         for i, line in enumerate(fp):
#             split_line = line.strip().split("\t")  # split the file line into its components
#
#             # if we have a distributions save it
#             # there is a line for each particle plus a line for the number of particles and name of experiment.
#             # that's why we have (parts+2) in each frame. that means each frame can be indexed by i % (parts + 2)
#             if i % (parts + 2) == 0:
#                 if i > 0:  # skips the first time since no ditribution to process yet.
#                     #storing distribution
#                     info_lag.append(dist.Distribution)
#                     # already processed one distribution so save it's max height
#                     brushz_lag.append(dist.ReferenceValue)
#                     # grab the polymer profile for the time step
#                     poly_profile_lag.append(poly_profile_current)
#                     # grab the np profile for the time step
#                     np_profile_lag.append(np_profile_current)
#                     # append the avg height list
#                     poly_avg_height_lag.append(0)
#                     monocount = 0
#
#                     # reset the distributions so that processing can continue.
#                     dist = ReferenceDistribution(_type="Binary", _reference=0.0, _dist=[0, 0])
#                     # reset the polymer profile
#                     poly_profile_current = np.zeros(total_bins)
#                     # reset the NP profile
#                     np_profile_current = np.zeros(total_bins)
#
#             # grab and record the highest z value for a polymer. This is the brush max height.
#             if split_line[0] == '1':  # spilt_line[0] will always exist even on break lines with the number of particles and name of exp.
#                 # line starting with 1 is a monomer on a polymer chain
#                 # update polymer z profiles
#                 tempheight = float(split_line[3])
#
#                 bin = int(float(split_line[3]) / bin_length)
#                 poly_profile_current[bin] += 1
#                 if float(split_line[3]) > dist.ReferenceValue:  # check to see if z value is higher than current max
#                     # update brush height in distribution class
#                     dist.update_reference(float(split_line[3]))
#
#             # identify the NP inside and outside the brush
#             if split_line[0] == '2':  # Line starting with a 2 is a np
#                 # update the z profile for NPs and
#                 bin = int(float(split_line[3]) / bin_length)
#                 np_profile_current[bin] += 1
#                 # pass the z value for the NP to the distribution. It will update according to current z height
#                 dist.update_distribution(float(split_line[3]))
#
#             if split_line[0] == '0':
#                 poly_avg_height_lag[-1] = tempheight
#                 tempheight = 0
