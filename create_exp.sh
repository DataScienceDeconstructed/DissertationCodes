#!/bin/bash


# this file creates a set of simulations using the burshes and Nanoparticles code created by Eric Snaper in Dr. Laradji's
# computational lab at the university of memphis.

# We begin by identifying the directory we are in and creating a directory to hold our experiment's results. In our case
# an experiment is a collection of simulations defined by the code below. There is an expectation that the basesim.sh
# file is also in this directory.

base_dir=$(pwd)
echo "base directory $base_dir"
exp_name='exp_test_11'
exp_dir="$base_dir/$exp_name"
echo "exp directory $exp_dir"
mkdir $exp_dir

# we identify the paths to teh simulation generating, time adjusting, and interval adjusting code sets. we place them in
# variables that can be referenced later during the simulation creation process.
# we also create a list that helps control the number of nanparticles in the simulations
# ToDo: move the basesim file to a central location and pull it like we do here
gen_dir='/home/chdavis/Code/mpd-md/generate/brushesAndNanoparticles'
time_adjust='/home/chdavis/Code/mpd-md/analysis/changeTime'
int_adjust='/home/chdavis/Code/mpd-md/bin/changeIntervals'
nanovalues=(64 128 256 320 384 512 768 1024)

# The meat of our code is a set of 4 nested loops. The loops work together to create and start series of simulations.
# The for loops are over Umin, np radius, polymer grafting density, and number of nanoparticle variables. The total
# number of simulations is equal to NoI(Umin) * NoI(np radius) * NoI(grafting density) * NoI(nanoparticles) where NoI is
# an operater that returns the number of intervals the for loops execute for each variable.

#The outter most loop is over Umin values. The values are dimensionaless and seperated by -0.175. For each Umin value in the
# loop execution, the loop calculates Umin values and then creates a subdirectory inside the experiment's directory.
for ((Uindex=1;Uindex<=2;Uindex +=1))
do
Umin_base=-0.175
Umin=`echo 0.0 + $Uindex*$Umin_base | bc`

U_dir="$exp_dir/Umin_$Uindex"
echo $U_dir
mkdir $U_dir

# The next loop is over the radius of the particles. Again it is dimensionaless. the delta for the radius values is 2. For
# each radius value a sum directory is created in the current Umin directory.
for((radius=2;radius<=4;radius +=2))
do

rad_flt=`echo $radius*1.0 | bc`
rad_dir="$U_dir/rad_$radius"
echo $rad_dir
mkdir $rad_dir

# the next loop is over the grafting desnity of the polymer brush in the simulation being crafted. for each value of grafting
# density a subdirectory is created in the current radius directory.
for(( aDen=1;aDen<=20;aDen++ ))
do	
	area_den=`echo 0.0 + $aDen*.03 | bc`
  den_dir="$rad_dir/den_$aDen"
	echo $den_dir
	mkdir $den_dir

  # the innermost loop for the script progresses over different values of nanoparticles for the simulation. Originally the
  # code used an algorithm that progressed according to 2^n where n was a value between 6 and 10; however, the exponential
  # growth left large gaps in the recorded data so a list was create that better captures the nanparticle saturations of interest.
  # for each value in the nanovalues list a directory is created inside the current grafting directory and a simulation is
  # started with that directory as its base directory for placing outputs.
	##for (( nanos=6;nanos<=10;nanos +=1))
	##for (( nanos=6;nanos<=9;nanos +=1))
	for i in ${nanovalues[@]}
	do
		##nan_num=$(($((2**$nanos))+$((2**8))))
		#create the directory and filename base for simulation outputs
		nan_num=$i
		nanos=$nan_num
		echo $nan_num
		sim_dir="$den_dir/NP_$nanos"
		echo $sim_dir
		mkdir $sim_dir
		cd $sim_dir # move into the simulation directory
    file_name="$exp_name.Umin$Uindex.rad$radius.den$aDen.NP$nanos"

		##echo "filename -> $file_name"
		##echo "UMin -> $Umin"

		# generate the files needed for the simulation and adjust default time variables
		$gen_dir $file_name $RANDOM 800 $area_den $Umin 40 $nan_num $rad_flt 0 100 100 0.7 3.0
		$time_adjust $file_name 0 100000
		$int_adjust $file_name 1000 100

		#copy the default basesim file into this directory, and update it for this simulation
		cp "$base_dir/basesim.sh" ./

		echo "$base_dir/MD $file_name" >> ./basesim.sh #add processing to submission file
		echo "module load python3" >> ./basesim.sh #add python for analysis to submission file
		echo "python3 /home/chdavis/Code/main.py $sim_dir/ $file_name ">> ./basesim.sh # execute analytist on the file after simulation.

		# send the simulation off for processing to the cluster
		sbatch ./basesim.sh

		#move back to the pwd to prepare the next processing
		cd "$base_dir"
	done
done

done
done
