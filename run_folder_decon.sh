#!/bin/bash

#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=32G
#SBATCH --gpus=1
#SBATCH --gres=gpumem:16G

module purge

module load stack/2024-06
module load gcc
module load python_cuda/3.11.6
module load cuda
module load cudnn/8.9.7.29-12


if [ $# -eq 0 ];
then
  echo "$0: Missing arguments"
  exit 1
elif [ $# -gt 1 ];
then
  echo "$0: Too many arguments: $@"
  exit 1
else
  echo "Reading folder: $1"
fi

# Enter folder with python script
cd deconvolution

# Check for images in mother dir
python script_folder.py $1

# Return to initial location
cd ..

exit 0

#use via: sbatch run_folder_decon.sh /nfs/nas22/fs2202/biol_bc_kleele_2/path_to_image

