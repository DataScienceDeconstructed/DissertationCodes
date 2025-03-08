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
exp_data='/scratch/chdavis'
exp_name='exp_3_a'
exp_type='NP_BRUSH'
exp_dir="$exp_data/$exp_name/$exp_type"
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
#mpd_dir='/home/chdavis/base_code/mpd-md'
mpd_dir='/home/chdavis/CLionProjects/mpd-md'
if [ -d "$mpd_dir" ]; then
  echo "mpd directory exists: $mpd_dir"
else
  echo "### Aborting program. point mpd_dir to real directory that exists"
  exit 1
fi

md_file="$mpd_dir/MD"


# Check if the md file exists
if [ -f "$md_file" ]; then
    echo "MD file exists: $md_file"
else
    echo "MD does not exist at $md_file"
    echo "Aborting program, provide MD file at $md_file"
    exit 1
fi

#update for different experiment types
gen_dir="$mpd_dir/generate/brushesAndNanoparticles"
brush_gen="$mpd_dir/generate/brushes"

if [ -f "$gen_dir" ]; then
    echo "simulation generator exists: $gen_dir"
else
    echo "simulation generator file does not exist $gen_dir"
    echo "### Aborting program. update gen_dir"
    exit 1
fi

time_adjust="$mpd_dir/analysis/changeTime"
gamma_adjust="$mpd_dir/bin/changeGamma"
int_adjust="$mpd_dir/bin/changeIntervals"
time_delta="$mpd_dir/analysis/changeDeltaT"

if [ -f "$time_adjust" ] && [ -f "$int_adjust" ] && [ -f "$time_delta" ] ; then
    echo "time and interval adjusters exists:"
    echo "$time_adjust"
    echo "$int_adjust"

else
    echo "time or interval adjuster missing"
    echo "### Aborting program. Update time_adjust int_adjust, and/or time_delta"
    exit 1
fi


if [ -f "$gamma_adjust" ]  ; then
    echo "gamma adjuster exists:"
    echo "$gamma_adjust"


else
    echo "gamma adjuster missing"
    echo "### Aborting program. Update gamma"
    exit 1
fi

# Assign the filename to a variable
#spec="$base_dir/simulation_specs.sim"
#spec="$base_dir/brushs03d04dfa-a56d-4014-937a-bf94d5a26a0b.sim"
#spec="$base_dir/brushs_Umin35_r2_extendedad23bbc1-4469-437b-a8c1-cc5a056cbcd5.sim"
#spec="$base_dir/brushs_Umin1_r2c1fd98db-34c9-4cd9-bdc3-12f59dfa1c80.sim"
#spec="$base_dir/brushs_var_Umin1_r2bf52bec7-53e7-4b0d-a326-349e09813c4c.sim"
#spec="$base_dir/brushs_Umin1_r278b43740-daf3-4184-8b99-f3b6c328a3e6.sim"
#spec="$base_dir/brushs_Umin075_r234820025-d03b-4cef-94a9-c3f4503b6d56.sim"
#spec="$base_dir/brushs_Umin01_exp_r2a8d09447-5994-4f52-b306-1844a1c7045d.sim"
#spec="$base_dir/brushs_Umin_small_exp_r29377cca7-d76c-450a-b393-802f44986e4e.sim"
spec="$base_dir/brushs_gaps22227555-4271-46d0-8606-40eaf0b04b04.sim"
# Check if the file exists
if [ ! -f "$spec" ]; then
    echo "sim spec file not found: $spec"
    ceho "Aborting because no spec to define behavior"
    exit 1
fi

#load modules for mpd code
module load gcc/8.2.0
module load fftw/3.8.0

curl -d "text=Clayton Sims starting in $exp_dir " -d "${slack[1]}" -H "${slack[0]}" -X POST https://slack.com/api/chat.postMessage

# Open the file and parse its contents
while IFS=' ' read -r line Uvalue radius aDen nanos; do

    # Check if the line starts with a hashtag
    if [[ $line == "#"* ]]; then
        echo "skipping $line"
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
        file_name=${file_name//./\-} # can't use decimels apparently because of mpd code
        echo $file_name
        $gen_dir $file_name $RANDOM 800 $aDen $Uvalue 40 $nanos $radius 0 100 100 0.7 3.0

		    #these are for warming up
        $gamma_adjust $file_name 20.0
        $time_adjust $file_name 0 10
		    $int_adjust $file_name 10 10

		    #copy the default basesim file into this directory, and update it for this simulation
		    cp "$base_dir/basesim.sh" ./

        #echo "module load gcc/8.2.0" >> ./basesim.sh
        # warm up system with high gamma
        echo "module load fftw/3.3.10/gcc-8.5.0/openmpi-4.1.6" >> ./basesim.sh
		    echo "$mpd_dir/MD $file_name" >> ./basesim.sh #add processing to submission file

		    #update system parameters and run to completion.
		    echo "echo 'updating simulation gamma and time files' " >> ./basesim.sh
		    echo "$gamma_adjust $file_name 1.0" >> ./basesim.sh
        echo "$time_adjust $file_name 0 100000" >> ./basesim.sh
		    echo "$int_adjust $file_name 100 100" >> ./basesim.sh
        echo "$mpd_dir/MD $file_name" >> ./basesim.sh #add processing to submission file


		    echo "module load python/3.12.1/gcc.8.5.0" >> ./basesim.sh #add python for analysis to submission file
		    echo "python3 $base_dir/main.py $sim_dir/ $file_name ">> ./basesim.sh # execute analyis on the file after simulation.

        echo 'slurm_file=$(find . -type f -name "slurm*" -print -quit)'>> ./basesim.sh # execute analyis on the file after simulation.
        echo 'slurm_lines=$(tail -n 5 $slurm_file)' >> ./basesim.sh
		    #curl_command="curl -d \"text=Clayton sim finished in $sim_dir \n " ' $slurm_lines ' " \" " "-d \"${slack[1]}\" -H \"${slack[0]}\" -X POST https://slack.com/api/chat.postMessage"
        #echo "$curl_command"
        echo -n "curl -d \"text=Clayton sim finished in $sim_dir \n "' $slurm_lines '" \" " "-d \"${slack[1]}\" -H \"${slack[0]}\" -X POST https://slack.com/api/chat.postMessage" >> ./basesim.sh

		    # send the simulation off for processing to the cluster
		    sbatch ./basesim.sh

		#move back to the pwd to prepare the next processing
    elif [ "$line" -eq 2 ]; then
       #process just brush
       echo "brush Only sim"
        echo $sim_dir
        # we use the radius variable to pass in the gap size and nanos to pass in the chain length
        gap="$radius"
        length="$nanos"
        file_name="${exp_name}_Umin${Uvalue}_rad${radius}_den${aDen}_NP${nanos}"
        file_name=${file_name//./\-} # can't use decimels apparently because of mpd code
        echo $file_name
        $brush_gen $file_name $RANDOM 800 $aDen 0 100 $length 0.7 3.0

        # Read the 10th line of the file (system dimensions)
        line=$(sed -n '10p' "$file_name")
        echo $line

        # Extract the 4 values from the line (assuming space-separated values)
        read -r value1 value2 value3 value4 <<< "$line"
        echo $value2

        # add the gap to the x direction
        new_value2=$(echo "$value2 + $gap" | bc)
        echo $new_value2

        # Replace the 10th line with the modified second value
        sed -i "10s/$value2/$new_value2/" "$file_name"

        # Read the 10th line of the file
        line=$(sed -n '10p' "$file_name")
        echo $line



		    ##these are for warming up
        #$gamma_adjust $file_name 20.0
        #$time_adjust $file_name 0 10
		    #$int_adjust $file_name 10 10

		    #copy the default basesim file into this directory, and update it for this simulation
		    cp "$base_dir/basesim.sh" ./

        ##echo "module load gcc/8.2.0" >> ./basesim.sh
        ## warm up system with high gamma
        #echo "module load fftw/3.3.10/gcc-8.5.0/openmpi-4.1.6" >> ./basesim.sh
		    #echo "$mpd_dir/MD $file_name" >> ./basesim.sh #add processing to submission file

		    #update system parameters and run to completion.
		    echo "echo 'updating simulation gamma and time files' " >> ./basesim.sh
		    #echo "$gamma_adjust $file_name 1.0" >> ./basesim.sh
        echo "$time_adjust $file_name 0 100000" >> ./basesim.sh
		    echo "$int_adjust $file_name 100 100" >> ./basesim.sh
        echo "$mpd_dir/MD $file_name" >> ./basesim.sh #add processing to submission file

        ## hold off on auto python analysis
		    #echo "module load python/3.12.1/gcc.8.5.0" >> ./basesim.sh #add python for analysis to submission file
		    #echo "python3 $base_dir/main.py $sim_dir/ $file_name ">> ./basesim.sh # execute analyis on the file after simulation.

        echo 'slurm_file=$(find . -type f -name "slurm*" -print -quit)'>> ./basesim.sh # execute analyis on the file after simulation.
        echo 'slurm_lines=$(tail -n 5 $slurm_file)' >> ./basesim.sh
		    #curl_command="curl -d \"text=Clayton sim finished in $sim_dir \n " ' $slurm_lines ' " \" " "-d \"${slack[1]}\" -H \"${slack[0]}\" -X POST https://slack.com/api/chat.postMessage"
        #echo "$curl_command"
        echo -n "curl -d \"text=Clayton sim finished in $sim_dir \n "' $slurm_lines '" \" " "-d \"${slack[1]}\" -H \"${slack[0]}\" -X POST https://slack.com/api/chat.postMessage" >> ./basesim.sh

		    # send the simulation off for processing to the cluster
		    sbatch ./basesim.sh

    else
        echo "ignored row"
    fi

    #go back to the base directory
    cd "$exp_data"
    echo $line
done < "$spec"

curl -d "text=Clayton Sims have all started in $exp_dir " -d "${slack[1]}" -H "${slack[0]}" -X POST https://slack.com/api/chat.postMessage

echo "exiting"
exit 0
