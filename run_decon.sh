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


cd deconvolution

python script_jsammet.py

cd ..

exit 0
