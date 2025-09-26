import numpy as np

def calc_RDP(_filename,
             _system_dims,
             _parts,
             _gap,
             _NPs,
             _poly_len):

    part_data_brush = np.zeros((_NPs,3))
    part_data_gap = np.zeros((_NPs, 3))

    NPs_brush = 0
    NPs_gap = 0
    border = _system_dims[0] - _gap
    height_array = np.zeros((2, int(_system_dims[2])+1 ))
    height_cum_array = np.zeros((2, int(_system_dims[2]) + 1))

    height_top_percentage = 1.0 - (1./float(_poly_len)*0.5) # this should give us half the end points of the polymers

    # retrieve NP locations
    with open(_filename, 'r') as fp:
        for i, line in enumerate(fp):

            if i < 2:
                continue
            split_line = line.strip().split("\t")  # split the file line into its components
            if split_line[0] == '2':

                if float(split_line[1]) < border :
                    part_data_brush[NPs_brush,0] = float(split_line[1])
                    part_data_brush[NPs_brush,1] = float(split_line[2])
                    part_data_brush[NPs_brush,2] = float(split_line[3])
                else:
                    part_data_gap[NPs_gap, 0] = float(split_line[1])
                    part_data_gap[NPs_gap, 1] = float(split_line[2])
                    part_data_gap[NPs_gap, 2] = float(split_line[3])

            if split_line[0] == '1':

                if float(split_line[1]) < border:
                    height_array[0, int(float(split_line[3]))] += 1
                else:
                    height_array[1, int(float(split_line[3]))] += 1

    height_array[0, :] /= np.sum(height_array[0, :])
    height_array[1, :] /= np.sum(height_array[1, :])

    height_cum_array[0, :] = np.cumsum(height_array[0, :])
    height_cum_array[1, :] = np.cumsum(height_array[1, :])

    #since the height arrays are of length Z units the index is the height of the brush needed
    index_brush = np.argmax(height_cum_array[0, :] > height_top_percentage)
    index_gap   = np.argmax(height_cum_array[1, :] > height_top_percentage)

    # filter rows where the 3rd element > threshold
    filtered_brush = part_data_brush[part_data_brush[:, 2] > index_brush]
    filtered_gap = part_data_gap[part_data_gap[:, 2] > index_gap]

    # now compute pairwise differences on this reduced array
    pairwise_brush_diff = filtered_brush[:, None, :] - filtered_brush[None, :, :]
    pairwise_gap_diff = filtered_gap[:, None, :] - filtered_gap[None, :, :]

    brush_distances = np.linalg.norm(pairwise_brush_diff, axis=-1)
    gap_distances = np.linalg.norm(pairwise_gap_diff, axis=-1)

    brush_hist = np.histogram(brush_distances, bins=int(_system_dims[0]) )
    gap_hist =  np.histogram(gap_distances, bins=int(_system_dims[0]) )

    return
def build_density_voxels(filename,
                     parts,         # particles in the simulation
                     equil_percent,   # 1 minus what percentage of the simulation time to include in the calculation
                     system_dimensions,
                     unit_voxel = [1.0, 1.0, 1.0],
                     save_to_dir=False,
                     dir_base=""):
    eps = 0.0001
    unit_voxel[0] = system_dimensions[0] / float(int(system_dimensions[0]))
    unit_voxel[1] = system_dimensions[1] / float(int(system_dimensions[1]))
    unit_voxel[2] = system_dimensions[2] / float(int(system_dimensions[2]))

    print("particles\t", parts)
    # a note about the np.round: since we are dividing the array into an integer number in each direction.
    # the floating point division can go either a little above or a little below the correct
    # value 120.0000000001 or 199.999999999 so the rounding helps make sure we have the right number.
    voxel_array_dims = (int( np.round( system_dimensions[0]/unit_voxel[0])) ,
                        int( np.round( system_dimensions[1]/unit_voxel[1])) ,
                        int( np.round( system_dimensions[2]/unit_voxel[2])),
                        2)
    error = True

    voxel_array = np.zeros(voxel_array_dims)

    #warmup is effectively the number of frames to skip in the simulation waiting for equilibrium
    warmup = int((100000/100*(parts+2)) * equil_percent)
    print("Warmup \t", warmup)
    postwarmup = 0

    oob = 0

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
                if float(split_line[1]) > system_dimensions[0]:
                    x  = int( ( float(split_line[1]) - system_dimensions[0])/unit_voxel[0])
                    oob += 1
                if float(split_line[2]) > system_dimensions[1]:
                    y  = int( ( float(split_line[2]) - system_dimensions[1])/unit_voxel[1])
                    oob += 1
                if float(split_line[3]) > system_dimensions[2]:
                    z = int( ( float(split_line[3]) - eps)/unit_voxel[2])
                    oob += 1
                try:
                    voxel_array[x][y][z][p] += 1
                except Exception as e:
                    print (e)
                    print ("x ",x,"\ty ",y,"\tz ",z)
                    print (system_dimensions)
                    print(voxel_array.shape)

        print("last line: {}".format(last_line))
        print("oob: {}".format(oob))

        if (save_to_dir):
            with open(dir_base + "/voxel_data.dat", 'wb') as fp:
                np.save(fp, 1.0 / np.float32(postwarmup) * voxel_array) # division gives the postwarmup per frame average

        if postwarmup >= (100000/100 - warmup):
            error = False
        print("processed data", postwarmup)
        return voxel_array, error
