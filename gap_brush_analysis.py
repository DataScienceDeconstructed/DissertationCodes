import numpy as np


def build_density_voxels(filename,
                     parts,         # particles in the simulation
                     equil_percent,   # 1 minus what percentage of the simulation time to include in the calculation
                     system_dimensions,
                     unit_voxel = [1.0, 1.0, 1.0],
                     save_to_dir=False,
                     dir_base=""):

    print("particles\t", parts)
    voxel_array_dims = (int(system_dimensions[0]//unit_voxel[0]) + 1,
                        int(system_dimensions[1]//unit_voxel[1]) + 1,
                        int(system_dimensions[2]//unit_voxel[2]) + 1,
                        2)
    error = True

    voxel_array = np.zeros(voxel_array_dims)

    #warmup is effectively the number of frames to skip in the simulation waiting for equilibrium
    warmup = int((100000/100*(parts+2)) * equil_percent)
    print("Warmup \t", warmup)
    postwarmup = 0

    last_line = 0
    with open(filename, 'r') as fp:
        for i, line in enumerate(fp):
            last_line = i
            if i < warmup:
                continue
            split_line = line.strip().split("\t")  # split the file line into its components

            # there is a line for each particle plus a line for the number of particles and name of experiment.
            # that's why we have (parts+2) in each frame. that means each frame can be indexed by i % (parts + 2)
            if i % (parts + 2) == 0:
                postwarmup += 1 # counts number of postwarmup frames
                if i == 0: # first line is header info
                    continue

            # process record
            if  split_line[0] == '1' or \
                split_line[0] == '2' :  # spilt_line[0] will always exist even on break lines with the number of particles and name of exp.
                x = int(float(split_line[1])/unit_voxel[0])
                y = int(float(split_line[2])/unit_voxel[1])
                z = int(float(split_line[3])/unit_voxel[2])
                p = int(split_line[0]) - 1 # indexing particle type 0 = monomer, 1 = NP
                voxel_array[x][y][z][p] += 1

        print("last line: {}".format(last_line))

        if (save_to_dir):
            with open(dir_base + "/voxel_data.dat", 'wb') as fp:
                np.save(fp, 1.0 / np.float32(postwarmup) * voxel_array) # division gives the postwarmup per frame average

        if postwarmup >= (100000/100 - warmup):
            error = False
        print("processed data", postwarmup)
        return voxel_array, error
