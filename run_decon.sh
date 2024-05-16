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

# Make sure there is only one argument, i.e., folder path
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

# Run decon
for f in $1/ ; do
        if [[ "$f" == *.ome.tif ]]
        then
                python script_image.py $f
        fi
done

# Return to initial location
cd ..

exit 0
