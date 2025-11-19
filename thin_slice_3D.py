
filename = "/scratch/chdavis/exp_4/NP_BRUSH/Umin_-0.175/rad_2/den_0.1/gap_0/len_64/NP_32/last_frame.xyz"

thin_film = []

with open(filename, 'r') as fp:
    for i, line in enumerate(fp):

        if i < 2:
            continue
        split_line = line.strip().split("\t")  # split the file line into its components
        if split_line[0] == '2' and float(split_line[3]) >4 and float(split_line[3])<6:

            thin_film.append(line)

print(len(thin_film))
