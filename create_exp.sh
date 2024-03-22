#!/bin/bash


# this file creates a set of simulations using the burshes and Nanoparticles code created by Eric Spangler in Dr. Laradji's
# computational lab at the university of memphis.

# We begin by identifying the directory we are in and creating a directory to hold our experiment's results. In our case
# an experiment is a collection of simulations defined by the code below. There is an expectation that the basesim.sh
# file is also in this directory.

base_dir=$(pwd)
echo "base directory $base_dir"
base_file="$base_dir/basesim.sh"

# Check if the base sim file exists
if [ -f "$base_file" ]; then
    echo "Base sim file exists: $base_file"
else
    echo "base_file does not exist"
    echo "Aborting program"
    exit 1
fi

#check if slack alerting exists
# Assign the filename to a variable
slack_file="$base_dir/alert.slack"

# Check if the file exists
if [ ! -f "$slack_file" ]; then
    echo "File not found: $slack_file"
    echo "Aborting without alerting"
    exit 1
fi

# Read the slack data

mapfile -t slack < <(head -n 2 "$slack_file")

#name the experiment
exp_name='exp_1'
exp_type='NP_BRUSH'
exp_dir="$base_dir/$exp_name/$exp_type"
# Check if the directory exists
if [ -d "$exp_dir" ]; then
    echo "Experimental directory exists: $exp_dir"
    echo "Aborting program to preserve data. update exp_name or exp_type"
    exit 1
else
    echo "Creating experiment directory"
    mkdir -p $exp_dir
    if [ -d "$exp_dir" ]; then
      echo "Experiment directory created: $exp_dir"
    else
      echo "Experiment directory creation failure for: $exp_dir"
      echo "Aborting program"
      exit 1
    fi
fi

echo "Experiment directory $exp_dir"



# we identify the paths to the simulation generating, time adjusting, and interval adjusting code sets. we place them in
# variables that can be referenced later during the simulation creation process.
# we also create a list that helps control the number of nanparticles in the simulations

#the compiled mpd code home directory
mpd_dir='/home/chdavis/base_code/mpd-md'
if [ -d "$mpd_dir" ]; then
  echo "mpd directory exists: $mpd_dir"
else
  echo "### Aborting program. point mpd_dir to real directory that exists"
  exit 1
fi

#update for different experiment types
gen_dir="$mpd_dir/generate/brushesAndNanoparticles"

if [ -f "$gen_dir" ]; then
    echo "simulation generator exists: $gen_dir"
else
    echo "simulation generator file does not exist $gen_dir"
    echo "### Aborting program. update gen_dir"
    exit 1
fi

time_adjust="$mpd_dir/analysis/changeTime"
int_adjust="$mpd_dir/bin/changeIntervals"

if [ -f "$time_adjust" ] && [ -f "$int_adjust" ] ; then
    echo "time and interval adjusters exists:"
    echo "$time_adjust"
    echo "$int_adjust"

else
    echo "time or interval adjuster missing"
    echo "### Aborting program. Update time_adjust and/or int_adjust"
    exit 1
fi


# Assign the filename to a variable
spec="$base_dir/simulation_specs.sim"

# Check if the file exists
if [ ! -f "$spec" ]; then
    echo "sim spec file not found: $spec"
    ceho "Aborting because no spec to define behavior"
    exit 1
fi

# Open the file and loop through its contents

# Open the file and parse its contents
while IFS=' ' read -r line Uvalue radius aDen nanos; do

    # Check if the line starts with a hashtag
    if [[ $line == "#"* ]]; then
        continue  # Skip this line
    fi


    U_dir="$exp_dir/Umin_$Uvalue"
    rad_dir="$U_dir/rad_$radius"
    den_dir="$rad_dir/den_$aDen"
    sim_dir="$den_dir/NP_$nanos"

    #build a directory to hold the sim and go to that directory
    if [ -d "$sim_dir" ]; then
      echo "Sim directory exists: $sim_dir"
      echo "skipping sim"
      continue
    else
      echo "Creating sim directory"
      mkdir -p $sim_dir
      if [ -d "$sim_dir" ]; then
        echo "Sim directory created: $sim_dir"
        cd $sim_dir
      else
        echo "Experiment directory creation failure for: $sim_dir"
        echo "Aborting program couldn't create a directory is something wrong with permissions?"
        exit 1
      fi
    fi


    #set up type of sim based upon line value
    if [ "$line" -eq 1 ]; then
        echo "brush NP sim"
        echo $sim_dir
        file_name="${exp_name}_Umin${Uvalue}_rad${radius}_den${aDen}_NP${nanos}"
        file_name=${file_name//./\$}
        echo $file_name
        echo $gen_dir $file_name $RANDOM 800 $aDen $Uvalue 40 $nanos $radius 0 100 100 0.7 3.0
		    echo "$time_adjust $file_name 0 100000"
		    echo "$int_adjust $file_name 1000 100"
        exit 0
		    #copy the default basesim file into this directory, and update it for this simulation
		    cp "$base_dir/basesim.sh" ./

		    echo "$base_dir/MD $file_name" >> ./basesim.sh #add processing to submission file
		    echo "module load python3" >> ./basesim.sh #add python for analysis to submission file
		    echo "python3 /home/chdavis/Code/main.py $sim_dir/ $file_name ">> ./basesim.sh # execute analyis on the file after simulation.
        curl_command='curl -d "text=Clayton sim finished in $sim_dir" -d "${slack[1]}" -H "${slack[0]}" -X POST https://slack.com/api/chat.postMessage'
        echo "$(eval echo "$curl_command")" >> ./basesim.sh

		    # send the simulation off for processing to the cluster
		    sbatch ./basesim.sh

		#move back to the pwd to prepare the next processing

      else
        echo "ignored row"
    fi

    #go back to the base directory
    cd "$base_dir"
done < "$spec"

echo "exiting"
exit 0

# nanovalues=(64 128 256 320 384 512 768 1024)

# The meat of our code is a set of 4 nested loops. The loops work together to create and start series of simulations.
# The for loops are over Umin, np radius, polymer grafting density, and number of nanoparticle variables. The total
# number of simulations is equal to NoI(Umin) * NoI(np radius) * NoI(grafting density) * NoI(nanoparticles) where NoI is
# an operater that returns the number of intervals the for loops execute for each variable.

#The outter most loop is over Umin values. The values are dimensionaless and seperated by -0.175. For each Umin value in the
# loop execution, the loop calculates Umin values and then creates a subdirectory inside the experiment's directory.
#Todo we are replacing the convoluted math and indexing with a file that has exactly what we want
#for ((Uindex=1;Uindex<=2;Uindex +=1))
#do
#Umin_base=-0.175
#Umin=`echo 0.0 + $Uindex*$Umin_base | bc`

U_dir="$exp_dir/Umin_$Uindex"
echo $U_dir
mkdir $U_dir

# The next loop is over the radius of the particles. Again it is dimensionless. the delta for the radius values is 2. For
# each radius value a sum directory is created in the current Umin directory.
#Todo replacing with file read
#for((radius=2;radius<=4;radius +=2))
#do

#rad_flt=`echo $radius*1.0 | bc`
rad_dir="$U_dir/rad_$radius"
echo $rad_dir
mkdir $rad_dir

# the next loop is over the grafting density of the polymer brush in the simulation being crafted. for each value of grafting
# density a subdirectory is created in the current radius directory.
#Todo replace with file read
#for(( aDen=1;aDen<=20;aDen++ ))
#do
#	area_den=`echo 0.0 + $aDen*.03 | bc`
  den_dir="$rad_dir/den_$aDen"
	echo $den_dir
	mkdir $den_dir

  # the innermost loop for the script progresses over different values of nanoparticles for the simulation. Originally the
  # code used an algorithm that progressed according to 2^n where n was a value between 6 and 10; however, the exponential
  # growth left large gaps in the recorded data so a list was create that better captures the nanparticle saturations of interest.
  # for each value in the nanovalues list a directory is created inside the current grafting directory and a simulation is
  # started with that directory as its base directory for placing outputs.
	## Todo replace with file read approach
	#for i in ${nanovalues[@]}
	#do
		##nan_num=$(($((2**$nanos))+$((2**8))))
		#create the directory and filename base for simulation outputs
	#	nan_num=$i
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
		module load gcc/8.2.0
		module load fftw/3.8.0
		$gen_dir $file_name $RANDOM 800 $area_den $Umin 40 $nan_num $rad_flt 0 100 100 0.7 3.0
		$time_adjust $file_name 0 100000
		$int_adjust $file_name 1000 100

		#copy the default basesim file into this directory, and update it for this simulation
		cp "$base_dir/basesim.sh" ./

    echo "module load gcc/8.2.0" >> ./basesim.sh
    echo "module load fftw/3.8.0" >> ./basesim.sh
		echo "$base_dir/MD $file_name" >> ./basesim.sh #add processing to submission file
		echo "module load python3" >> ./basesim.sh #add python for analysis to submission file
		echo "python3 /home/chdavis/Code/main.py $sim_dir/ $file_name ">> ./basesim.sh # execute analyis on the file after simulation.
    #echo "" send alert that processing has completed here
		# send the simulation off for processing to the cluster
		sbatch ./basesim.sh

		#move back to the pwd to prepare the next processing
		cd "$base_dir"
#	done
#done

#done
#done
