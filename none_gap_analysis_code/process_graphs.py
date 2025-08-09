import os
import numpy as np
from scipy import stats

import matplotlib.pyplot as plt

profile_plotting = False;

#base_dir = "/media/clayton/Seagate/experiment_data/"
base_dir = "/project/chdavis/chdavis/exp_totals/NP_BRUSH/"

datadir = {}
Umin_list = []
rad_list = []
den_list = []
NP_list = []
load_p={}
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
    NP_list =  [int(x[3:]) for x in NP_list]
    NP_list.sort()
    NP_list = ["NP_"+str(x) for x in NP_list]

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
            den_values = []
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
                #if line_full:
                if len(x) == len(y) :
                    den_line.append([x.copy(), y.copy()])
                    den_values.append(den)
            #build plot
            fig, ax = plt.subplots()
            print_line = True # this will print fewer lines for nicer visual
            for i, lines in enumerate(den_line):
                #print_line = not print_line
                if print_line:
                    ax.plot(lines[0], lines[1], label='s = ' + str(mod_value*(i+1)*.01)[:4])
                    #ax.plot(lines[0], lines[1], label='s = ' + den_values[i][4:8])

                vol_frac_file = base_dir + "volume_fraction_data/" + str(Umin.replace(".","__")) +"_"+ str(rad.replace(".","__")) + "_" + str(mod_value*(i+1)*.01).replace(".","__")[:5]+ ".dat"
                with open(vol_frac_file, 'w') as fp:
                    for i, x in enumerate(lines[0]):
                        fp.write(str(x) + " , " + str(lines[1][i]) + "\n")

            ax.set_xlabel('Solvent NP Volume Fraction')
            ax.set_ylabel('Brush NP Volume Fraction')
            ax.set_title('Brush NP Volume Fraction Versus Solvent NP Volume Fraction \n Umin = '+ str(Umin) + ' , radius = ' + str(rad))

            plt.figtext(1.5, 0.01, txt, wrap=True, fontsize=12)
            ax.legend(loc='upper right')

            plt.savefig(base_dir+'vfracgraphs_Umin_'+ str(Umin) + '_radius_' + str(rad)+'.png')
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

    #get the point that marks 20% of the data
    points = int(len(data)*.2)
    #get the number of observations in the last 20% of data
    x_values = range(len(data[points:]))
    print(len(x_values))
    #create 0th and 1st order fits for the last 20% of data points
    data0fit = np.polyfit(x_values, data[points:], 0)
    data1fit = np.polyfit(x_values, data[points:], 1)

    #create polynomial objects from fits.
    data_p0 = np.poly1d(data0fit)
    data_p1 = np.poly1d(data1fit)

    #calculate errors for fits.
    # note there is a chance for 0 error in both distributions because all NPs could be in the brush at this point.
    e0 = data_p0(x_values) - data[points:]
    e1 = data_p1(x_values) - data[points:]

    #do t test to see if distributions are distinguishable

    test_results = stats.ttest_ind(e0, e1) # test with null hypothesis that they are the same


    # we want to be sure that distributions are really close so if there is up to a 50% chance that one distribution
    # is more extreme than the other we reject the idea that they are indistinguishable.
    if test_results.pvalue < .05:
        # the distributions are not significantly different.
        # we use .5 instead of 0.05 to make it harder to reject the null hypothesis
        print("failed to distinguish 0th and 1st order")
    else:
        # distributions are not distinguishable
        rValue = (True, data0fit[0])


    return rValue

def aggregate_brush_NP_percentage(polymer_pdf, np_pdf):
    rValue =0.0
    eps = .0000001

    for i in range(len(polymer_pdf)):
        if polymer_pdf[i]>eps: #we're in the brush
            rValue += np_pdf[i]

    return rValue

def plot_profiles(root, files):
    system_dimensions = [0.0,0.0,0.0]

    mpd_file = [x for x in files if ".mpd" in x]



    with open(root +"/" + mpd_file[0], 'r') as fp:
        for i, line in enumerate(fp):
            if i == 9:# this is the line with the sim dimensions when MD is used to create the file.
                split_line = line.strip().split(" ") # split the file line into its components
                system_dimensions = [float(split_line[1]),float(split_line[2]), float(split_line[3])]

    max_height_index = int(system_dimensions[2] / 10) + 1 # each bin is 10 units high

    if ("np_profile.dat" in files) and ("polymer_profile.dat" in files):
        np_profile = None
        polymer_profile = None
        height = None

        with open(root + "/np_profile.dat", "r") as file:
            np_data = np.array([ [ float( x.split(" ")[0] ), float( x.split(" ")[1] ) ] for x in file.readlines()])
            height = np_data[:, 0]
            np_profile = np_data[:, 1] / np.sum(np_data[:, 1])
            np_profile = np_profile[:max_height_index]
            height = height[:max_height_index]

        with open(root + "/polymer_profile.dat", "r") as file:
            polymer_data = np.array([ [ float( x.split(" ")[0] ), float( x.split(" ")[1] ) ] for x in file.readlines()])
            polymer_profile = polymer_data[:, 1] / np.sum(polymer_data[:, 1])
            polymer_profile = polymer_profile[:max_height_index]

        # fig, ax = plt.subplots()
        #
        # ax.plot(height, np_profile, label='NP')
        # ax.plot(height, polymer_profile, label='Polymers')
        #
        # ax.set_xlabel('System Height')
        # ax.set_ylabel('Normalized Object Density')
        # ax.set_title('NP and Brush Density \n' + "/".join(root.split("/")[-4:]))
        #
        # ax.legend(loc='upper right')

        #plt.savefig(root + '/densityplots.png')

        load_percentage = aggregate_brush_NP_percentage(polymer_profile,np_profile)
        return load_percentage


#main code

def calculate_b_v_S_graphs(datadir, load_p):
    # calculate graphs for brush concentration versus solvent concentration
    breakout = False
    processed = 0
    total = 0

    #for root, dirs, files in os.walk(base_dir):
    #    print(root, dirs)
    error_list = {"no_files":[], "no_data":[]}
    # walk the data path to access the data sets. this is the main part of the code
    for root, dirs, files in os.walk(base_dir):
        path = root.split(os.sep)


        #are we in a data directory?

        if ("NP" in root.split("/")[-1]):
            # this if statement assumes that NP is in the leaf directory's name
            total += 1
            if profile_plotting:
            # this if statement controls simulation level density plotting
            # plot_profiles gets the Profiles for the polymer and teh NPs in each simulation
                plot_profiles(root, files)

            if ("brush_NP_volume_fraction.dat" in files) and ("solvent_NP_volume_fraction.dat" in files):
                #if the volume fraction files are in the directory then we can process
                brushNPVolFrac = None
                solvNPVolFrac = None

                #read the data
                #these datasets describe the NP volume fractions in the brush and solvent respectively at each recorded
                # time step
                with open(root+"/brush_NP_volume_fraction.dat", "r") as file:
                    brushNPVolFrac = [float(x) for x in file.readlines()]

                with open(root + "/solvent_NP_volume_fraction.dat", "r") as file:
                    solvNPVolFrac = [float(x) for x in file.readlines()]


                if len(solvNPVolFrac) < 10 :
                    # this if makes sure there is data in the directory
                    print(root + " has no data.")
                    error_list["no_data"].append(root)
                    continue

                # make sure we have the same amount of data for both the brush and solvent
                assert len(solvNPVolFrac) == len(brushNPVolFrac)

                brush_eq = calc_equilibrium(brushNPVolFrac)
                solv_eq = calc_equilibrium(solvNPVolFrac)
                if brush_eq[0]:
                    processed += 1

                if path[-4] not in datadir:
                    datadir[path[-4]] = {}
                    load_p[path[-4]] = {}
                if path[-3] not in datadir[path[-4]]:
                    datadir[path[-4]][path[-3]] = {}
                    load_p[path[-4]][path[-3]] = {}
                if path[-2] not in datadir[path[-4]][path[-3]]:
                    datadir[path[-4]][path[-3]][path[-2]] = {}
                    load_p[path[-4]][path[-3]][path[-2]] = {}
                if path[-1] not in datadir[path[-4]][path[-3]][path[-2]]:
                    datadir[path[-4]][path[-3]][path[-2]][path[-1]] = (solv_eq[1], brush_eq[1])
                    load_p[path[-4]][path[-3]][path[-2]][path[-1]] = (solv_eq[1], brush_eq[1],plot_profiles(root, files))

               # frame_file = root+"/frames_exp_test_11.Umin"+path[-4][5:]+".rad"+path[-3][4:]+".den"+path[-2][4:]+".NP"+path[-1][3:]+".xyz"

            else:
                print(root)
                error_list["no_files"].append(root)




    print(str(processed) + " sims have values out of "+ str(total))
    print("that's " + str(100.0* processed / total) + " percent")
    Umin_list, rad_list, den_list, NP_list = get_data_keys(datadir)
    plot(datadir, Umin_list, rad_list, den_list, NP_list)
    print("error list", error_list)
    print("Done")

if __name__ == "__main__":
    calculate_b_v_S_graphs(datadir, load_p)