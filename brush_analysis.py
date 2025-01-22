import os
from ComputationalEquilibriums import ReferenceDistribution
import numpy as np


def get_brush_height(filename,
                     parts,         # particles in the simulation
                     total_bins,    # total number of bins
                     bin_length,     # length of the bins
                     equil_percent,   # 1 minus what percentage of the simulation time to include in the calculation
                     brush_top_density,
                     save_to_dir=False,
                     dir_base=""):

# process the simulation file
    poly_profile_lag = []
    poly_profile_current = np.zeros(total_bins, dtype=int)


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

        if (save_to_dir):
            with open(dir_base + "/profile_brush.dat", 'w') as fp:
                np.savetxt(fp, useful_data_avg, fmt='%.6e', delimiter=' ', newline='\n', header='', footer='',
                           comments='# ',
                           encoding=None)

        top_indexes = [i for i, x in enumerate(useful_data_avg) if x < brush_top_density and i > int(1.0/ bin_length)+1]
        return top_indexes[0] * bin_length

def get_brush_height_inflection(filename,
                     parts,         # particles in the simulation
                     total_bins,    # total number of bins
                     bin_length,     # length of the bins
                     equil_percent,   # 1 minus what percentage of the simulation time to include in the calculation
                     brush_top_density,
                     save_to_dir=False,
                     dir_base=""):

# process the simulation file
    poly_profile_lag = []
    poly_profile_current = np.zeros(total_bins, dtype=int)


    with (open(filename, 'r') as fp):
        for i, line in enumerate(fp):
            split_line = line.strip().split("\t")  # split the file line into its components

            # there is a line for each particle plus a line for the number of particles and name of experiment.
            # that's why we have (parts+2) in each frame. that means each frame can be indexed by i % (parts + 2)
            if i % (parts + 2) == 0:
                if i > 0:  # skips the first time since no data to save yet.
                    # add the polymer profile for the time step to the array holding the rest.
                    poly_profile_lag.append(poly_profile_current)
                    # reset the polymer profile
                    poly_profile_current = np.zeros(total_bins)

            if split_line[0] == '1':  # spilt_line[0] will always exist even on break lines with the number of particles and name of exp.
                #1 is the code for monomer. add this monomer to the current polymer profile.
                bin = int(float(split_line[3]) / bin_length)
                poly_profile_current[bin] += 1

        #with all polymer profiles available
        profile_data = np.array(poly_profile_lag)
        #takes the percentage of the polymers that happen after equilibrium and averages them together.
        useful_data_avg = np.mean(profile_data[int(profile_data.shape[0] * equil_percent):, :], axis=0)
        #take 1st and section direivative of profile
        grad_useful_data_avg = np.gradient(useful_data_avg)
        grad_2 = np.gradient(grad_useful_data_avg)
        zero_crossings = np.where(np.diff(np.signbit(grad_2)))[0]

        # Get the sign of the differences
        signs = np.sign(grad_useful_data_avg)
        # Calculate the second differences of the sign array
        peaks = np.diff(signs)
        z_values = np.asarray([x*bin_length  for x in range(total_bins)])

        inflection_point = np.zeros(len(z_values))
        grad_1_min = np.argmin(grad_useful_data_avg)
        assert(grad_2[grad_1_min - 1] < 0.0 < grad_2[grad_1_min + 1] and
               grad_2[grad_1_min-2] < 0.0 and
               grad_2[grad_1_min+2] > 0.0)
        inflection_point[grad_1_min] += 500
        profiles = np.column_stack((z_values,
                                    useful_data_avg,
                                    grad_useful_data_avg,
                                    grad_2,
                                    inflection_point
                                    ))
        if (save_to_dir):
            with open(dir_base + "/brush_profile.dat", 'w') as fp:
                np.savetxt(fp, profiles, fmt='%.6e', delimiter=' ', newline='\n', header='', footer='',
                           comments='# ',
                           encoding=None)


        return  grad_1_min * bin_length
def calc_loading(filename,
                 parts,
                 top,
                 radius,
                 total_bins,
                 bin_length,
                 avg_timesteps=20):

    info_lag = []
    dist = ReferenceDistribution(_type="Binary", _reference=top, _dist=[0, 0])
    np_profile_current = np.zeros(total_bins)
    poly_profile_current = np.zeros(total_bins)
    np_profile_avg = np.zeros((avg_timesteps,total_bins))
    poly_profile_avg = np.zeros((avg_timesteps, total_bins))
    avg_count = 0
    returndict = {}
# process the simulation file
    with open(filename, 'r') as fp:
        for i, line in enumerate(fp):
            split_line = line.strip().split("\t")  # split the file line into its components

            # there is a line for each particle plus a line for the number of particles and name of experiment.
            # that's why we have (parts+2) in each frame. that means each frame can be indexed by i % (parts + 2)
            if i % (parts + 2) == 0:
                if i > 0:  # skips the first time since no ditribution to process yet.
                    #storing distribution
                    info_lag.append(dist.Distribution)
                    # reset the distributions so that processing can continue.
                    dist = ReferenceDistribution(_type="Binary", _reference=top, _dist=[0, 0])
                    #reset histogram
                    np_profile_avg[avg_count,:] = np_profile_current
                    poly_profile_avg[avg_count, :] = poly_profile_current
                    avg_count += 1
                    if avg_count == avg_timesteps:
                        avg_count = 0
                    np_profile_current = np.zeros(total_bins)
                    poly_profile_current = np.zeros(total_bins)

                    # identify the NP inside and outside the brush
            if split_line[0] == '1':  # Line starting with a 1 is a monomer
                # update histogram
                poly_profile_current[int(float(split_line[3]) / bin_length)] += 1

            # identify the NP inside and outside the brush
            if split_line[0] == '2':  # Line starting with a 2 is a np
                # pass the z value for the NP to the distribution. It will update according to current z height
                dist.update_distribution(float(split_line[3]), radius)
                #update histogram
                np_profile_current[int(float(split_line[3])/bin_length)] += 1

    #conver the profiles to density functions along the z axis
    np_profile_result = np.mean(np_profile_avg, axis=0)
    np_profile_result = np_profile_result / np.sum(np_profile_result)
    poly_profile_result = np.mean(poly_profile_avg, axis=0)
    poly_profile_result = poly_profile_result / np.sum(poly_profile_result)

    returndict = {"loading": info_lag, "np_profile": np_profile_result, "poly_profile": poly_profile_result}
    return returndict

def retrieve_height(dir_base
                 ):
    height = 0
    count = 0
    data = []
    with open(dir_base + "/loading_brush.dat", 'r') as fp:
        height = fp.readline()

    with open(dir_base + "/loading_solv.dat", 'r') as fp:
        data = fp.readlines()
    data = [float(x) for x in data if '#' not in x]
    return (float(height[1:]), np.mean(np.array(data[int(len(data)*.2):])))

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
