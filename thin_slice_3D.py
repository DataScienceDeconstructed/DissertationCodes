
base_dir = "/scratch/chdavis/exp_5/NP_BRUSH/Umin_-0.175/rad_2/den_0.06/gap_0/len_32/NP_1024"

thin_film = []

with open(base_dir +"/last_frame.xyz" , 'r') as fp:
    for i, line in enumerate(fp):

        if i < 2:
            continue
        split_line = line.strip().split("\t")  # split the file line into its components
        if split_line[0] == '2':
            if ((float(split_line[3]) > 4 and float(split_line[3]) < 6) or
               (float(split_line[3]) > 400 and float(split_line[3]) < 600)
            ):
                thin_film.append(
                    str("He\t" +
                        split_line[1] + "\t" +
                        split_line[2] + "\t" +
                        split_line[3] + "\n"

                        ))
            elif (float(split_line[3]) > 4 and float(split_line[3]) > 200):
                thin_film.append(
                    str("H\t"+
                    split_line[1]+"\t"+
                    split_line[2] + "\t" +
                    split_line[3] + "\n"

                ))

with open(base_dir + "/thin.xyz", "w") as file:
    file.write(str(len(thin_film))+"\n")
    file.write(str("thin_film")+"\n")
    file.write("".join(thin_film))

print(len(thin_film))
