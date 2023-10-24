#!/bin/bash

#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=32G
#SBATCH --gpus=1
#SBATCH --gres=gpumem:16G

module purge

module load gcc/8.2.0
module load python_gpu/3.11.2
module load cuda/11.8.0
module load cudnn


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

cd deconvolution

for d in $1/*/ ; do
        python script_folder.py d
done

cd ..

exit 0

