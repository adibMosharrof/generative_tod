#! /bin/bash

#SBATCH --time=2:00:00 # Time limit for the job (REQUIRED).
#SBATCH --job-name=inference # Job name
#SBATCH --ntasks=8 # Number of cores for the job. Same as SBATCH -n 8
#SBATCH --partition=V4V16_SKY32M192_L # Partition/queue to run the job in. (REQUIRED)
#SBATCH -e slurm_out/%j.err # Error file for this job.
#SBATCH -o slurm_out/%j.out # Output file for this job.
#SBATCH -A gol_msi290_uksr # Project allocation account name (REQUIRED)
#SBATCH --gres=gpu:1
module load ccs/Miniconda3
source activate ./envs
time python src/inference.py --config-name lcc_simple_tod_inference
