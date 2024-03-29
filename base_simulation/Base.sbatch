#!/bin/bash 
#
#all commands that start with SBATCH contain commands that are just used by SLURM for scheduling
#################
#set a job name  
#SBATCH --job-name=Electron_Hydro_Sim_Base
################# 
#a file for job output, you can check job progress, append the job ID with %j to make it unique
#SBATCH --output=Base.%j.out
#################
# a file for errors from the job
#SBATCH --error=dome.%j.err
#################
#time you think you need; default is 2 hours
#format could be dd-hh:mm:ss, hh:mm:ss, mm:ss, or mm
#SBATCH --time=00:30:00
#################
#Quality of Service (QOS); think of it as job priority, there is also --qos=long for with a max job length of 7 days, qos normal is 48 hours.
# REMOVE "normal" and set to "long" if you want your job to run longer than 48 hours,  
# NOTE- in the hns partition the default max run time is 7 days , so you wont need to include qos
 
#SBATCH --qos=normal

# We are submitting to the barnardlab partition, there are several on sherlock: normal, gpu, owners, hns, bigmem (jobs requiring >64Gigs RAM) 
# 
#SBATCH -p barnardlab
#################
#number of nodes you are requesting, the more you ask for the longer you wait
#SBATCH --nodes=1
#SBATCH --ntasks=1                   # Run a single task	
#SBATCH --cpus-per-task=28          # Number of CPU cores per task

# module load system
# module load parallel

#################
# --mem is memory per node; default is 4000 MB per CPU, remember to ask for enough mem to match your CPU request, since 
# sherlock automatically allocates 8 Gigs of RAM/CPU, if you ask for 8 CPUs you will need 32 Gigs of RAM, so either 
# leave --mem commented out or request >= to the RAM needed for your CPU request.
 
#SBATCH --mem=60000
#################

# Have SLURM send you an email when the job ends or fails, careful, the email could end up in your clutter folder
# Also, if you submit hundreds of jobs at once you will get hundreds of emails.
 
#SBATCH --mail-type=END,FAIL # notifications for job done & fail
# Remember to change this to your email 
#SBATCH --mail-user=hillerh@uw.edu


#now run normal batch commands

module load anaconda3_4.3.1
# export PYTHONPATH = ~/.local/lib/python3.6/site-packages:$PYTHONPATH
	
export PATH=~/.local/bin:$PATH
pip install --upgrade pip
pip install -r scipy numpy matplotlib configparser -—user
	

python ../runBaseScript.py BaseTipTest.txt