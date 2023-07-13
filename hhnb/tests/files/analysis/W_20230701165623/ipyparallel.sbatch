
#!/bin/bash -l

mkdir logs
#SBATCH --job-name=bluepyopt_ipyparallel
#SBATCH --error=logs/ipyparallel_%j.log
#SBATCH --output=logs/ipyparallel_%j.log
#SBATCH --partition=normal
#SBATCH --constraint=mc

export PMI_NO_FORK=1
export PMI_NO_PREINITIALIZE=1
export PMI_MMAP_SYNC_WAIT_TIME=300 
#set -e
#set -x

module load daint-mc cray-python/3.9.4.1
# If needed for analysis

module use /apps/hbp/ich002/hbp-spack-deployments/softwares/23-02-2022/modules/tcl/cray-cnl7-haswell

# always load neuron module
module load neuron/8.0.2
module load py-matplotlib
module load py-bluepyopt

nrnivmodl mechanisms

export USEIPYP=1
export IPYTHONDIR="`pwd`/.ipython"
export IPYTHON_PROFILE=ipyparallel.${SLURM_JOBID}
ipcontroller --init --sqlitedb --ip='*' --profile=${IPYTHON_PROFILE} &
sleep 30
srun ipengine --profile=${IPYTHON_PROFILE} &
CHECKPOINTS_DIR="checkpoints"
BLUEPYOPT_SEED=1 python opt_neuron.py --offspring_size=10 --max_ngen=2 --start --checkpoint "${CHECKPOINTS_DIR}/checkpoint.pkl"
echo '{"offspring_size": 10, "max_gen": 2, "job_name": "W_20230701165623", "hpc": "cscs"}' > resume_job_settings.json
python zipfolder.py
