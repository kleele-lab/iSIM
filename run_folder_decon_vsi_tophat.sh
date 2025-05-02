#!/bin/bash

#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=32G
#SBATCH --gpus=1
#SBATCH --gres=gpumem:32G
#SBATCH --time=4:00:00

module purge

module load stack/2024-06
module load gcc/12.2.0
module load python_cuda/3.9.18
module load cuda/12.1.1
module load cudnn/8.9.7.29-12
module load stack/2024-06 openjdk/11.0.20.1_1


# Avoiding the JIT error
export XLA_FLAGS=--xla_gpu_cuda_data_dir=$CUDA_EULER_ROOT
export CUDA_DIR=$CUDA_EULER_ROOT

# Checking the inputs
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
python script_folder_vsi_tophat.py $1

# Return to initial location
cd ..

exit 0

#use via: sbatch run_folder_decon.sh /nfs/nas22/fs2202/biol_bc_kleele_2/path_to_image

