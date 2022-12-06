import os
import json


class ExecFileConf:

    @staticmethod
    def write_nsg_exec(dst_dir, max_gen, offspring, job_name, mode='start'):
        buffer = \
f"""
import os
import json

os.system('python3 opt_neuron.py --max_ngen={max_gen} --offspring_size={offspring} --{mode} --checkpoint ./checkpoints/checkpoint.pkl')
with open('resume_job_settings.json', 'w') as fd:
    json.dump({json.dumps({'offspring_size': offspring, 'max_gen': max_gen, 'job_name': job_name, hpc: 'nsg',})}, fd)
"""
        try:
            with open(os.path.join(dst_dir, 'init.py'), 'w') as fd:
                fd.write(buffer)
        except Exception as e:
            raise e

    @staticmethod
    def write_daint_exec(dst_dir, folder_name, offspring, max_gen, job_name, mode='start'):
        buffer_zipfolder = \
f"""
import os
import zipfile

retval = os.getcwd()
print("Current working directory %s" % retval)
os.chdir('..')
retval = os.getcwd()
print("Current working directory %s" % retval)

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

zipf = zipfile.ZipFile('output.zip', 'w')
zipdir('{ folder_name }', zipf)
"""

        with open(os.path.join(dst_dir, 'zipfolder.py'), 'w') as fd:
            fd.write(buffer_zipfolder)

        SLURM_JOBID = '{SLURM_JOBID}'
        IPYTHON_PROFILE = '{IPYTHON_PROFILE}'
        CHECKPOINTS_DIR = '{CHECKPOINTS_DIR}'

        buffer_sbatch = \
f"""
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
BLUEPYOPT_SEED=1 python opt_neuron.py --offspring_size={offspring} --max_ngen={max_gen} --{mode} --checkpoint "${CHECKPOINTS_DIR}/checkpoint.pkl"
echo '{json.dumps({'offspring_size': offspring, 'max_gen': max_gen, 'job_name': job_name, 'hpc': 'cscs'})}' > resume_job_settings.json
python zipfolder.py
"""
        try:
            with open(os.path.join(dst_dir, 'ipyparallel.sbatch'), 'w') as fd:
                fd.write(buffer_sbatch)
        except Exception as e:
            raise e
