#!/bin/bash

#SBATCH --ntasks=2
#SBATCH --mem-per-cpu=32G
#SBATCH --nodes=2
#SBATCH --gpus-per-node=6

module purge

module load gcc/8.2.0
module load python_gpu/3.11.2
module load cuda/11.8.0
module load cudnn


cd deconvolution

python script_jsammet.py

cd ..

exit 0
