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
base_dir = "/scratch/chdavis/exp_2_c/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_d/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_e/NP_BRUSH"
#base_dir = "/scratch/chdavis/exp_2_f/NP_BRUSH"
#base_dir = "/scratch/chdavis/test/NP_BRUSH"
#comment that can be undone

dataset = {}
bad_repos = []
def read_dataset(bad_repos):
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
            #bin_values = np.asarray([x*bin_length  for x in range(total_bins)]) # z values for the bins

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
                dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["brush_height"] = float(fp.readline().replace("#", ""))
                dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["loading_brush"] = [x for i,x in enumerate(fp.readlines())]

            #if the data was bad
            if dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["brush_height"] < 1.0:
                del dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]
                bad_repos.append(root)
                continue

            with open(dir_base + "/post/loading_solv.dat", 'r') as fp:
                dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["loading_solv"] = [x for i,x in enumerate(fp.readlines()) if i > 0]

            # get information about the simulation
            filecheck = [s for s in files if ".mpd" in s]

            filename = ""
            if len(filecheck) == 1:
                filename = filecheck[0]
            else:
                pass  # why is this else clause here?

            system_dimensions = []
            with open(dir_base + "/" + filename, 'r') as fp:
                split_line = fp.readlines()[9].strip().split()
                system_dimensions = [float(split_line[1]), float(split_line[2]), float(split_line[3])]

            dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["system_dimensions"] = system_dimensions

            # 1 NP movement changes for phi
            dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["brush_phi_unit"] =  4.0 / 3.0 * np.pi * radius * radius * radius / (
                    system_dimensions[0]*system_dimensions[1]*(dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["brush_height"] ))
            dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["solv_phi_unit"] = 4.0 / 3.0 * np.pi * radius * radius * radius / (
                system_dimensions[0] * system_dimensions[1] * (system_dimensions[2] -
                dataset[str(Umin)][str(radius)][str(sigma)][str(num_NPs)]["brush_height"]))


    return dataset

def build_concentration_graphs(_dataset):
        graphs = {}
        t = [float(x) for x in range(1002)]
        title = ['brush','solv']


        for u in _dataset.keys():
            graphs[u] = {}
            for r in _dataset[u].keys():
                graphs[u][r] ={}



                for si, s in enumerate(_dataset[u][r].keys()):
                    graphs[u][r][s] =  {"graph": {"brush":[], "solv":[], "brush-mean":[], "solv-mean":[], "brush-equil":[], "solv-equil":[], "NP-level":[] }}
                    #the graph data needs to be updated to handle multiple sigma
                    #graphs[u][r][s]["graph"]["brush"].append([])
                    #graphs[u][r][s]["graph"]["solv"].append([])
                    #graphs[u][r][s]["graph"]["brush-mean"].append([])
                    #graphs[u][r][s]["graph"]["brush-equil"].append([])
                    #graphs[u][r][s]["graph"]["solv-mean"].append([])
                    #graphs[u][r][s]["graph"]["solv-equil"].append([])
                    #graphs[u][r][s]["graph"]["NP-level"].append([])
                    plt.figure(1)
                    plt.clf()
                    plt.figure(2)
                    plt.clf()

                    keys = [str(y) for y in sorted([int(x) for x in _dataset[u][r][s].keys()])]
                    for nps in keys:#sorted numerically
                        # this is indexing on sigmas but should index on nps
                        graphs[u][r][s]["graph"]["brush"].append([float(x) for x in _dataset[u][r][s][nps]["loading_brush"]])
                        graphs[u][r][s]["graph"]["solv"].append([float(x) for x in _dataset[u][r][s][nps]["loading_solv"]])
                        graphs[u][r][s]["graph"]["brush-mean"].append(
                            [np.mean(
                                graphs[u][r][s]["graph"]["brush"][-1])])
                        graphs[u][r][s]["graph"]["solv-mean"].append(
                            [np.mean(
                                graphs[u][r][s]["graph"]["solv"][-1])])
                        graphs[u][r][s]["graph"]["NP-level"].append([nps])


                        plt.figure(1)
                        brush_data = np.asarray([float(x) for x in _dataset[u][r][s][nps]["loading_brush"]])
                        brush_equil = verify_equilibrium(brush_data[len(brush_data)//2:], _dataset[u][r][s][nps]["brush_phi_unit"])
                        graphs[u][r][s]["graph"]["brush-equil"].append([brush_equil])

                        t = [float(x) for x in range(len(brush_data))]
                        plt.plot(t[:len(brush_data)], brush_data,
                                 label='brush NP = ' + nps + ' Eq = ' +
                                 str(np.mean(brush_data[len(brush_data)//2:]))[0:6]
                                 )

                        plt.figure(2)
                        solv_data = np.asarray([float(x) for x in _dataset[u][r][s][nps]["loading_solv"]])
                        solv_equil = verify_equilibrium(solv_data[len(solv_data) // 2:], _dataset[u][r][s][nps]["solv_phi_unit"])
                        graphs[u][r][s]["graph"]["solv-equil"].append([solv_equil])

                        t = [float(x) for x in range(len(solv_data))]
                        plt.plot(t[:len(solv_data)], solv_data,
                             label='solv NP = ' + nps+ ' Eq = ' +
                                   str(np.mean(solv_data[len(solv_data) // 2:]))[0:6]
                                 )


                    # Adding labels and title
                    for i in range(2):
                        plt.figure(i+1)
                        plt.xlabel('timestep')
                        plt.ylabel('Phi')

                        plt.title('Nanoparticle Volume Fraction \n Umin = '+ u +' rad = '+r+' sigma = '+s )

                        plt.legend(loc='upper left')
                        plt.savefig(base_dir+ '/umin_'+u+'_radius_'+r+'_sigma_'+s+'_'+title[i]+'.png', bbox_inches='tight')
                    pass

        # Show the plot
        #plt.show()

        pass

def verify_equilibrium(_data, delta):
    rValue = False
    fit_params = np.polyfit(range(len(_data)), _data, 1)
    std = np.std(_data)
    #when would value increase by a std?
    if fit_params[0] > 10**-15:

        t_future_std = std / np.abs(fit_params[0])
        t_future_NP = delta / np.abs(fit_params[0]) # when will the fit's value exceed having 1 more NP included or expelled?
    else:
        # if the value is really close to zero just assign a large time
        t_future_NP = 10**9

    if t_future_NP > len(_data) * 2:
        #equilibrium is considered reached if Phi is stable over twice the current timeline.
        rValue = True
    else:
        pass
    return rValue

if __name__ == "__main__":
    dataset = read_dataset(bad_repos)
    build_concentration_graphs(dataset)
    print("******************\nBAD REPOS \n")
    for repo in bad_repos:
        print(bad_repos)
    pass