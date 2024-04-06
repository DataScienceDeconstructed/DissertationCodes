import os
import numpy as np
from scipy import stats

import matplotlib.pyplot as plt



#base_dir = "/media/clayton/Seagate/experiment_data/"
base_dir = "./exp_1"
processed = 0
total = 0
datadir = {}
Umin_list = []
rad_list = []
den_list = []
NP_list = []
# traverse root directory, and list directories as dirs and files as files

def get_data_keys(graphdata):
#gets all the keys needed to index dictionaries for retrieving data
# the data is grabbed, converted to a list, and sorted for processing purposes

    Umin_set = set()
    rad_set = set()
    den_set = set()
    NP_set = set()

    for current_Umin in graphdata.keys():
        Umin_set = Umin_set.union({current_Umin})
        for current_rad in graphdata[current_Umin].keys():
            rad_set = rad_set.union({current_rad})
            for current_den in graphdata[current_Umin][current_rad].keys():
                den_set = den_set.union({current_den})
                for current_NP in graphdata[current_Umin][current_rad][current_den].keys():
                    NP_set = NP_set.union({current_NP})

    Umin_list = list(Umin_set)
    Umin_list.sort()
    rad_list = list(rad_set)
    rad_list.sort()
    den_list = list(den_set)
    den_list.sort()
    NP_list = list(NP_set)
    NP_list.sort()

    return Umin_list, rad_list, den_list, NP_list
def plot(datadir, Umin_list, rad_list, den_list, NP_list):

  #  Umin_list = ['Umin_1', 'Umin_2']
  #  rad_list = ['rad_2', 'rad_4']
  #  den_list = ['den_1', 'den_2', 'den_3', 'den_4', 'den_5', 'den_6', 'den_7', 'den_8', 'den_9', 'den_10', 'den_11', 'den_12', 'den_13', 'den_14', 'den_15', 'den_16', 'den_17', 'den_18', 'den_19', 'den_20']
  #  NP_list = ['NP_64', 'NP_128', 'NP_256', 'NP_320', 'NP_384', 'NP_512',  'NP_768', 'NP_1024']

    mod_value = 3
    for Umin in Umin_list:
        for rad in rad_list:
            # build graph at this level
            den_line = []
            txt = "missing values"
            for i, den in enumerate(den_list):

                #since values aren't based on intergers anymore this is not needed
                #if you are at the point that you are wondering if you can remove this, then do it.
                #if i % mod_value != 0:
                #    continue

                # build data lines at this level
                x = []
                y = []
                line_full = True

                for NP in NP_list:
                    # build Line here
                    if Umin in datadir:
                        if rad in datadir[Umin]:
                            if den in datadir[Umin][rad]:
                                if NP in datadir[Umin][rad][den]:
                                    x.append(datadir[Umin][rad][den][NP][0])
                                    y.append(datadir[Umin][rad][den][NP][1])
                                else:
                                    line_full = False
                                    txt += Umin + " / " + rad + " / " + den + " / " + NP + "\n"
                            else:
                                line_full = False
                        else:
                            line_full = False
                    else:
                        line_full = False

                # record if line data is fully available i.e. nothing missing
                if line_full:
                    den_line.append([x.copy(), y.copy()])

            #build plot
            fig, ax = plt.subplots()
            for i, lines in enumerate(den_line):
                ax.plot(lines[0], lines[1], label='sigma = ' + str(mod_value*(i+1)*.03))


            ax.legend()
            ax.set_xlabel('Solvent NP Volume Fraction')
            ax.set_ylabel('Brush NP Volume Fraction')
            ax.set_title('Brush NP Volume Fraction Versus Solvent NP Volume Fraction \n Umin = '+ str(Umin) + ' , radius = ' + str(rad))

            plt.figtext(0.5, 0.01, txt, wrap=True, horizontalalignment='center', fontsize=12)
            plt.show()

    comment = "bp"
    # xp = np.linspace(-1, len(brushNPVolFrac[points:]), 100)
    # _ = plt.plot(xp, brush_p0(xp), '-', xp, brush_p1(xp), '--', range(len(brushNPVolFrac[points:])),
    #              brushNPVolFrac[points:], '.')
    # plt.ylim(0, 1)
    # plt.plot()

def calc_equilibrium(data):
# performs an average and 1st order linear approximation of the dataset and compares the distribution of errors to tell
# if the two approximations are distinguishable.

    rValue = (False,0.0)

    #get the point that marks 80% of the data
    points = int(len(data)*.8)
    #get the number of observations in the last 20% of data
    x_values = range(len(data[points:]))

    #create 0th and 1st order fits for the last 20% of data points
    data0fit = np.polyfit(x_values, data[points:], 0)
    data1fit = np.polyfit(x_values, data[points:], 1)

    #create polynomial objects from fits.
    data_p0 = np.poly1d(data0fit)
    data_p1 = np.poly1d(data1fit)

    #calculate errors for fits.
    e0 = data_p0(x_values) - data[points:]
    e1 = data_p1(x_values) - data[points:]

    #do t test to see if distributions are distinguishable

    test_results = stats.ttest_ind(e0, e1)

    # we want to be sure that distributions are really close so if there is up to a 50% chance that one distribution
    # is more extreme than the other we reject the idea that they are indistinguishable.
    if test_results.pvalue > .5:
        rValue = (True, data0fit[0])

    return rValue

def build_3d_animation(_file, _rad):
    color = (.5, .5, .5)
    frame = np.empty([1, 5], dtype=object)
    frame = np.append(frame, np.empty([1, 5], dtype=object), axis=0) # needed for the first animation expansion with a 1: slice
    frames = 0
    with open(_file) as fp:
        for line in fp:
            if line[0] == "7":
                frames += 1

            if line[0] == "0" or line[0]== "1" or line[0]== "2":
                if line[0] == "2":
                    rad = _rad
                    color = (1.0, 0.0, 0.0)
                else:
                    rad = 1.0
                data = line.split("\t")
                frame = np.append(frame, np.array([ [ float(data[1]), float(data[2]), float(data[3]), rad, color ] ]), axis=0)

    bcomment = "check dims"


#main code
breakout = False

error_list = {"no_files":[], "no_data":[]}
# walk the data path to access the data sets. this is the main part of the code
for root, dirs, files in os.walk(base_dir):
    path = root.split(os.sep)
    total += 1

    #are we in a data directory?

    if "NP" in root:
        # this if statement assumes that NP is in the leaf directory's name

        if ("brush_NP_volume_fraction.dat" in files) and ("solvent_NP_volume_fraction.dat" in files):
            #if the cvolume fraction files are in the directory then we can process
            brushNPVolFrac = None
            solvNPVolFrac = None

            #read the data
            #these datasets describe the NP volume fractions in the brush and solvent respectively at each recorded
            # time step
            with open(root+"/brush_NP_volume_fraction.dat", "r") as file:
                brushNPVolFrac = [float(x) for x in file.readlines()]

            with open(root + "/solvent_NP_volume_fraction.dat", "r") as file:
                solvNPVolFrac = [float(x) for x in file.readlines()]

            #make sure there is data
            if len(solvNPVolFrac) < 1 :
                print(root + " has no data.")
                error_list["no_data"].append(root)
                continue

            # make sure we have the same amount of data for both the brush and solvent
            assert len(solvNPVolFrac) == len(brushNPVolFrac)

            brush_eq = calc_equilibrium(brushNPVolFrac)
            solv_eq = calc_equilibrium(solvNPVolFrac)
            processed += 1

            if path[-4] not in datadir:
                datadir[path[-4]] = {}
            if path[-3] not in datadir[path[-4]]:
                datadir[path[-4]][path[-3]] = {}
            if path[-2] not in datadir[path[-4]][path[-3]]:
                datadir[path[-4]][path[-3]][path[-2]] = {}
            if path[-1] not in datadir[path[-4]][path[-3]][path[-2]]:
                datadir[path[-4]][path[-3]][path[-2]][path[-1]] = (solv_eq[1], brush_eq[1])

            frame_file = root+"/frames_exp_test_11.Umin"+path[-4][5:]+".rad"+path[-3][4:]+".den"+path[-2][4:]+".NP"+path[-1][3:]+".xyz"

        else:
            print(root)
            error_list["no_files"].append(root)




print(str(processed) + " sims have values out of "+ str(total))
print("that's " + str(100.0* processed / total) + " percent")
Umin_list, rad_list, den_list, NP_list = get_data_keys(datadir)
plot(datadir, Umin_list, rad_list, den_list, NP_list)
print("error list", error_list)
print("Done")