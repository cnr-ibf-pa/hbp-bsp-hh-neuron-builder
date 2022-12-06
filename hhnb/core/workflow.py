"""
Workspace utils classes
"""

from hh_neuron_builder.settings import MEDIA_ROOT, HHF_TEMPLATE_DIR, HHF_PARAMETERS_TEMPLATE_DIR, TMP_DIR, LOG_ROOT_PATH

from hhnb.core.conf.exec_files_conf import ExecFileConf

from hhnb.core.lib.exception.workflow_exception import *
from hhnb.core.model import *

from json.decoder import JSONDecodeError
from pyunicore.client import PathFile as UnicorePathFile
from datetime import datetime
from sys import prefix as env_prefix
# from pathlib import Path

import shutil
import os
import json
import requests
import subprocess
import zipfile


class _WorkflowBase:
    
    def __init__(self, user_sub, workflow_id):
        self._user_sub = user_sub
        if workflow_id[0] in '1234567890':
            workflow_id = 'W_' + workflow_id 
        self._id = workflow_id
        self._workflow_path = os.path.abspath(os.path.join(MEDIA_ROOT, 'hhnb', 'workflows',
                                                           self._user_sub, self._id))
        self._results_dir = os.path.join(self._workflow_path, 'results')
        self._analysis_dir = os.path.join(self._workflow_path, 'analysis')
        self._model_dir = os.path.join(self._workflow_path, 'model')
        self._tmp_dir = os.path.join(self._workflow_path, 'tmp')
        self._etraces_dir = os.path.join(self._workflow_path, 'etraces')
        
        self._optimization_settings = os.path.join(self._workflow_path,
                                                   'optimization_settings.json')
        
        if os.path.exists(self._model_dir) and any(os.scandir(self._model_dir)):
            self._model = Model.from_dir(self._model_dir, key=workflow_id)

    def __repr__(self):
        return self.__class__

    def __str__(self):
        return f'<Workflow {self._id}>'

    def get_user(self):
        return self._user_sub

    def get_id(self):
        return self._id

    def get_workflow_path(self):
        return self._workflow_path

    def get_results_dir(self):
        return self._results_dir

    def get_analysis_dir(self):
        return self._analysis_dir

    def get_model_dir(self):
        return self._model_dir

    def get_tmp_dir(self):
        return self._tmp_dir

    def get_etraces_dir(self):
        return self._etraces_dir

    def get_model(self):
        return self._model

    
class Workflow(_WorkflowBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hhf_flag = False

    @classmethod
    def generate_user_workflow(cls, user_sub, make_files=True):
        workflow_id = datetime.now().strftime('%Y%m%d%H%M%S')
        wf = cls(user_sub, workflow_id)
        if make_files:
            wf.make_workflow_dirs()
        return wf
    
    @classmethod
    def generate_user_workflow_from_zip(cls, user_sub, zip_file):
        workflow_id = datetime.now().strftime('%Y%m%d%H%M%S')
        wf = cls(user_sub, workflow_id)
        shutil.unpack_archive(zip_file, wf.get_workflow_path())
        return wf 

    @classmethod
    def generate_user_workflow_from_path(cls, user_sub, path_to_clone):
        old_wf_id = os.path.split(path_to_clone)[1]
        user_dir = os.path.join(MEDIA_ROOT, 'hhnb', 'workflows', user_sub) 
        wf = cls(user_sub, old_wf_id)
        if not os.path.exists(user_dir):
            os.mkdir(user_dir)
        shutil.copytree(path_to_clone, os.path.join(user_dir, old_wf_id))
        return wf

    @classmethod
    def get_user_workflow_by_id(cls, user_sub, workflow_id):
        wf = cls(user_sub, workflow_id)
        return wf

    def _copy_file(self, src_file, dst_path, safe=True):
        if src_file in os.listdir(dst_path) and safe:
            raise FileExistsError('%s exists yet on %s. Try with safe=False flag.' 
                                  % (src_file, dst_path))
        shutil.copy(src_file, dst_path)

    def _write_file(self, fd, file_name, dst_path, mode='w', safe=True):
        if file_name in dst_path and safe:
            raise FileExistsError('%s exists yet on %s. Try with safe=False flag.' 
                                  % (file_name, dst_path))
        file_path = os.path.join(dst_path, file_name)
        with open(file_path, mode) as fd_dst:
            if fd.multiple_chunks(chunk_size=4096):
                for chunk in fd.chunks(chunk_size=4096):
                    fd_dst.write(chunk)
            else:
                fd_dst.write(fd.read())
        return file_path

    def make_workflow_dirs(self):
        if os.path.exists(self._workflow_path):
            raise WorkflowExists('The workspace already exists. Use another path.')
        os.makedirs(self._workflow_path)
        shutil.copytree(HHF_TEMPLATE_DIR, self._model_dir) 

        #  force empty dir to be created in model directory
        sub_dir = ['config', 'mechanisms', 'model', 'morphology']
        for sub_path in [os.path.join(self._model_dir, f) for f in sub_dir]:
            if not os.path.exists(sub_path):
                os.mkdir(sub_path)

        os.mkdir(self._results_dir)
        os.mkdir(self._analysis_dir)
        os.mkdir(self._tmp_dir)
        os.mkdir(self._etraces_dir)

    def make_dir(self, dir):
        if os.path.exists(os.path.join(self._workflow_path, dir)):
            raise PathExists('The path "%s" already exists. Use another path' % dir)
        os.makedirs(os.path.join(self._workflow_path, dir))

    def copy_features(self, src_file, safe=True):
        self._copy_file(src_file, os.path.join(self._model_dir, 'config'), safe)

    def write_features(self, fd, mode='wb', safe=True):
        dir_path = os.path.join(self._model_dir, 'config')
        file_path = self._write_file(fd, 'features.json', dir_path, mode, safe) 
        self.get_model().set_features(features=file_path)
    
    def write_protocols(self, fd, mode='wb', safe=True):
        dir_path = os.path.join(self._model_dir, 'config')
        file_path = self._write_file(fd, 'protocols.json', dir_path, mode, safe)
        self.get_model().set_features(protocols=file_path)

    def load_model_zip(self, model_zip):
        unzipped_tmp_model_dir = os.path.join(self._tmp_dir, 'model')
        if os.path.exists(unzipped_tmp_model_dir):
            shutil.rmtree(unzipped_tmp_model_dir)
        os.mkdir(unzipped_tmp_model_dir)
        shutil.unpack_archive(model_zip, unzipped_tmp_model_dir)
        
        
        # The ModelCatalog model case
        # if len(os.listdir(unzipped_tmp_model_dir)) == 1:
            # unzipped_tmp_model_dir = os.path.join(unzipped_tmp_model_dir,   
                                                #   os.listdir(unzipped_tmp_model_dir)[0])
        
        # The uploaded results case  
        # else:
        for f in os.listdir(unzipped_tmp_model_dir):
            if 'output' in f:
                shutil.unpack_archive(os.path.join(unzipped_tmp_model_dir, f), 
                                        unzipped_tmp_model_dir)
        
        for model_folder in os.listdir(unzipped_tmp_model_dir):
            if os.path.isdir(os.path.join(unzipped_tmp_model_dir, model_folder)):
                print(os.path.join(unzipped_tmp_model_dir, model_folder))
            else:
                os.remove(os.path.join(unzipped_tmp_model_dir, model_folder))

        unzipped_tmp_model_dir = os.path.join(unzipped_tmp_model_dir,   
                                              os.listdir(unzipped_tmp_model_dir)[0])

        shutil.rmtree(self._model_dir)
        if not os.path.exists(self._model_dir):
            os.mkdir(self._model_dir)
        shutil.copytree(unzipped_tmp_model_dir, self._model_dir, dirs_exist_ok=True)
        
        # The uploaded origin model case
        self._model.update_optimization_files(unzipped_tmp_model_dir)
        ModelUtil.update_key(model=self._model)
        
        

    def _set_optimization_settings(self, optimization_settings):
        with open(self._optimization_settings, 'w') as fd:
            json.dump(optimization_settings, fd, indent=4)

    def get_optimization_settings(self):
        try:
            with open(self._optimization_settings, 'r') as fd:
                try:
                    return json.load(fd)                    
                except JSONDecodeError:
                    return {}
        except FileNotFoundError:
            return {}

    def add_optimization_settings(self, update_json):
        settings = self.get_optimization_settings()
        settings.update(update_json)
        self._set_optimization_settings(settings)

    def get_resume_settings(self):
        try:
            with open(os.path.join(self._model_dir, 'resume_job_settings.json'),
                      'r') as fd:
                return json.load(fd)
        except FileNotFoundError:
            pass
        except JSONDecodeError:
            pass
        return {}

    def remove_file(self, file_path):
        directory, filename = os.path.split(file_path)
        target_dir = os.path.abspath(os.path.join(self._model_dir, directory))

        if os.path.commonpath([os.path.abspath(self._workflow_path), target_dir]) != \
            os.path.abspath(self._workflow_path):
            raise PermissionError('Can\'t delete files on %s' % target_dir)
            
        if filename == '*':
            shutil.rmtree(target_dir)
            os.mkdir(target_dir)
        
        elif not filename:
            if os.path.isdir(target_dir):
                shutil.rmtree(target_dir)
            elif directory.endswith("*"):
                d = directory[:-1] # removed "*" chars
                for dd in os.listdir(self._model_dir):
                    if dd.startswith(d):
                        shutil.rmtree(os.path.join(self._model_dir, dd))
        else:
            full_file_path = os.path.join(self._model_dir, file_path) 
            if os.path.exists(full_file_path):
                os.remove(full_file_path)

        if not os.path.exists(target_dir):
            raise FileNotFoundError('%s directory not exists' % directory)

    def get_properties(self):

        analysis_flag = False
        if len(os.listdir(self._analysis_dir)) == 1:
            analysis_model_dir = os.path.join(self._analysis_dir,
                                              os.listdir(self._analysis_dir)[0])
            if os.path.isdir(analysis_model_dir) != \
                ['mechanisms', 'morphology', 'checkpoints']:
                analysis_flag = True

        optset_flag = (False, 'Optimization parameters NOT set')
        if os.path.exists(self._optimization_settings):
            with open(self._optimization_settings, 'r') as fd:
                jj = json.load(fd)
            if jj.get('hpc') == 'SA':
                if jj.get('sa-hpc') and jj.get('sa-project'):
                    optset_flag = (True, '')
            elif jj.get('hpc') == 'DAINT-CSCS':
                if jj.get('project'):
                    optset_flag = (True, '')
            elif jj.get('hpc') == 'NSG':
                if not jj.get('username_submit') or not jj.get('password_submit'):
                    optset_flag = (False, 'NSG credentials required')
                else: 
                    optset_flag = (True, '')
                    
        props = {
            'id': self._id,
            'model': self._model.get_properties(), 
            'optimization_settings': optset_flag,
            'etraces': any(os.scandir(self._etraces_dir)),
            'job_submitted': self.get_optimization_settings().get('job_submitted', False),
            'results': any(os.scandir(self._results_dir)),
            'resume': os.path.exists(os.path.join(self._model_dir, 'checkpoints', 'checkpoint.pkl')),
            'analysis': analysis_flag
        }
        return props

    def clean_tmp_dir(self):
        if len(os.listdir(self._tmp_dir)) > 0:
            shutil.rmtree(self._tmp_dir)
            if not os.path.exists(self._tmp_dir):
                os.mkdir(self._tmp_dir)

    def clean_analysis_dir(self):
        shutil.rmtree(self.get_analysis_dir())
        if not os.path.exists(self.get_analysis_dir()):
            os.mkdir(self.get_analysis_dir())


class WorkflowUtil:

    @staticmethod
    def set_model_key(workflow, key=None):

        ModelUtil.update_key(workflow.get_model(), key)

    @staticmethod
    def set_default_parameters(workflow):
        src_params = os.path.join(HHF_TEMPLATE_DIR, '..', 'parameters.json') 
        dst_params = os.path.join(workflow.get_model_dir(), 'config')
        shutil.copy(src_params, dst_params)
        workflow.get_model().set_parameters(dst_params)

    @staticmethod
    def clone_workflow(workflow):
        new_workflow = Workflow.generate_user_workflow(workflow.get_user(), make_files=False)
        shutil.copytree(workflow.get_workflow_path(), new_workflow.get_workflow_path())
        if os.path.exists(new_workflow._optimization_settings):
            os.remove(new_workflow._optimization_settings)
        return new_workflow

    @staticmethod
    def make_archive(workflow, zip_name, dir_name, file_list):
        zip_path = os.path.join(workflow.get_tmp_dir(), zip_name)
        if os.path.exists(zip_path):
            os.remove(zip_path)
        tmp_dir = os.path.join(workflow.get_tmp_dir(), dir_name)
        os.mkdir(tmp_dir)

        wf_path = workflow.get_workflow_path()

        for f in file_list:
            if not os.path.exists(f):
                raise FileNotFoundError(f'{f} file not found!')
            if not os.path.commonpath([wf_path, f]) == wf_path:
                raise PermissionError(f'file "{f} is not inside the workflow path!')
            shutil.copy(f, tmp_dir)
        shutil.make_archive(os.path.splitext(zip_path)[0], 'zip', tmp_dir)
        shutil.rmtree(tmp_dir)
        return zip_path
        
    @staticmethod
    def make_workflow_archive(workflow):
        zip_path = os.path.join(TMP_DIR, workflow.get_id())
        shutil.make_archive(base_name=zip_path,
                            format='zip',
                            root_dir=workflow.get_workflow_path())
        return zip_path + '.zip'

    @staticmethod
    def make_features_archive(workflow):
        file_list = [
            workflow.get_model().get_features().get_features(),
            workflow.get_model().get_features().get_protocols()
        ]
        return WorkflowUtil.make_archive(
            workflow=workflow,
            zip_name=workflow.get_id() + '_features.zip',
            dir_name='feature',
            file_list=file_list
        )
        
    @staticmethod
    def make_model_archive(workflow):
        zip_name = os.path.join(workflow.get_tmp_dir(), 
                                workflow.get_id() + '_orig_model.zip')
        shutil.make_archive(
            base_name=os.path.splitext(zip_name)[0],
            format='zip',
            root_dir=workflow.get_model_dir(),
        )
        return zip_name

    @staticmethod
    def make_results_archive(workflow):
        zip_name = os.path.join(workflow.get_tmp_dir(),
                                workflow.get_id() + '_results.zip')
        shutil.make_archive(
            base_name=os.path.splitext(zip_name)[0],
            format='zip',
            root_dir=workflow.get_results_dir()
        )
        return zip_name

    @staticmethod
    def make_analysis_archive(workflow):
        zip_name = os.path.join(workflow.get_tmp_dir(),
                                workflow.get_id() + '_analysis.zip')
        shutil.make_archive(
            base_name=os.path.splitext(zip_name)[0],
            format='zip',
            root_dir=workflow.get_analysis_dir()
        )
        return zip_name

    @staticmethod
    def make_optimization_model(workflow):
        
        # fixing all model's keys
        ModelUtil.update_key(workflow.get_model())
        
        tmp_model_dir = shutil.copytree(src=workflow.get_model_dir(), 
                                        dst=os.path.join(workflow.get_tmp_dir(), 'opt_model',
                                                         workflow.get_model().get_key()))

        # craeting directories and script
        try:
            os.mkdir(os.path.join(tmp_model_dir, 'checkpoints'))
            os.mkdir(os.path.join(tmp_model_dir, 'figures'))
        except FileExistsError:
            pass

        settings = workflow.get_optimization_settings()
        if settings['hpc'] == 'NSG' or \
            (settings['hpc'] == 'SA' and settings['sa-hpc'] == 'nsg'):
            ExecFileConf.write_nsg_exec(dst_dir=tmp_model_dir,
                                        max_gen=settings['gen-max'],
                                        offspring=settings['offspring'],
                                        mode=settings['mode'])
        elif settings['hpc'] == 'DAINT-CSCS' or \
            (settings['hpc'] == 'SA' and settings['sa-hpc'] == 'pizdaint'):
            ExecFileConf.write_daint_exec(dst_dir=tmp_model_dir,
                                          folder_name=workflow.get_model().get_key(),
                                          offspring=settings['offspring'],
                                          max_gen=settings['gen-max'],
                                          mode=settings['mode'])
        
        return tmp_model_dir 

    @staticmethod
    def download_from_hhf(workflow, hhf_dict):
        WorkflowUtil.set_default_parameters(workflow)

        morph = hhf_dict.get('morphology')
        etraces = hhf_dict.get('electrophysiologies', [])
        mechanisms = hhf_dict.get('modFiles', [])

        if morph:
            file_name = morph['name']
            if os.path.splitext(file_name)[1] == '':
                file_name += '.asc'
            file_path = os.path.join(workflow.get_model_dir(),
                                        'morphology', file_name)
            r = requests.get(url=morph['url'], verify=False)
            with open(file_path, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=4096):
                    fd.write(chunk)
            workflow.get_model().set_morphology(morphology=file_path)
        
        for etrace in etraces:
            file_path = os.path.join(workflow.get_etraces_dir(), etrace['name'])
            r = requests.get(url=etrace['url'], verify=False)
            with open(file_path + '.abf', 'wb') as fd:
                for chunk in r.iter_content(chunk_size=4096):
                    fd.write(chunk)
            r = requests.get(url=etrace['metadata'], verify=False)
            with open(file_path + '_metadata.json', 'wb') as fd:
                for chunk in r.iter_content(chunk_size=4096):
                    fd.write(chunk)
        
        mechanisms_dir = os.path.join(workflow.get_model_dir(), 'mechanisms')
        for mod in mechanisms:
            file_path = os.path.join(mechanisms_dir, mod['name'])
            r = requests.get(url=mod['url'], verify=False)
            with open(file_path, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=4096):
                    fd.write(chunk)
        workflow.get_model().set_mechanisms(mechanisms_dir)

    @staticmethod
    def list_model_files(workflow):
        model_files = {}
        
        for root, dirs, files in os.walk(workflow.get_model_dir()):
            if os.path.split(root)[1] == 'config':
                model_files.update({'config': files})
            if os.path.split(root)[1] == 'morphology':
                model_files.update({'morphology': files})
            if os.path.split(root)[1] == 'mechanisms':
                model_files.update({'model': files})
            if root == workflow.get_model_dir():
                model_files.update({'root': files})
                
        return model_files
        
    @staticmethod
    def write_file_content(workflow, file_path, file_content):
        full_path = os.path.join(workflow.get_model_dir(), file_path)
        if os.path.splitext(file_path)[1] == '.json':
            jj = json.loads(file_content)
            with open(full_path, 'w') as fd:
                json.dump(jj, fd, indent=4)
        else:
            with open(full_path, 'wb') as fd:
                fd.write(file_content)

    @staticmethod
    def download_job_result_files(workflow, data):
        hpc_system = data['root_url']
        file_list = data['file_list']

        if hpc_system == 'nsg':
            for f in file_list.keys():
                r = requests.get(url=file_list[f],
                                 headers=data['headers'],
                                 auth=(data['username'], data['password']))
                if r.status_code != 200:
                    continue
                dst = os.path.join(workflow.get_results_dir(), f)
                with open(dst, 'wb') as fd:
                    for chunk in r.iter_content(chunk_size=4096):
                        fd.write(chunk)

        elif hpc_system == 'unicore':
            for f in file_list.keys():
                if type(file_list[f]) == UnicorePathFile:
                    dst = os.path.join(workflow.get_results_dir(), f)
                    file_list[f].download(dst)
        
        elif hpc_system.startswith('https://bspsa.cineca.it'):
            for f in file_list:
                r = requests.get(url=data['root_url'] + f['id'] + '/',
                                 headers=data['headers'],)
                if r.status_code != 200:   
                    continue
                if f['name'].startswith('/'):
                    f['name'] = f['name'][1:]
                dst = os.path.join(workflow.get_results_dir(), f['name'])
                with open(dst, 'wb') as fd:
                    for chunk in r.iter_content(chunk_size=4096):
                        fd.write(chunk)
        
        else:
            raise Exception('No hpc system found!')

    @staticmethod
    def run_analysis(workflow, job_output):
        analysis_dir = workflow.get_analysis_dir()
        shutil.unpack_archive(job_output, analysis_dir)
        
        output_dir = None
        for f in [os.path.join(analysis_dir, f) for f in os.listdir(analysis_dir)]:
            if os.path.isdir(f):
                output_dir = f
            else:
                os.remove(f)
        if not output_dir:
            raise FileNotFoundError('Output folder not found')
        

        analysis_file = os.path.join(output_dir, 'model', 'analysis.py')
        if not os.path.exists(analysis_file):
            raise FileNotFoundError('"analysis.py" not found')

        evaluator_file = os.path.join(output_dir, 'model', 'evaluator.py')
        if not os.path.exists(evaluator_file):
            raise FileNotFoundError('"evaluator.py" not found')

        figures_dir = os.path.join(output_dir, 'figures')
        if os.path.exists(figures_dir):
            shutil.rmtree(figures_dir)
        os.mkdir(figures_dir)

        checkpoint_dir = os.path.join(output_dir, 'checkpoints')
        if os.path.exists(checkpoint_dir):
            checkpoint_dir_content = os.listdir(checkpoint_dir)
            if not 'checkpoint.pkl' in checkpoint_dir_content:
                for f in checkpoint_dir_content:
                    if f.endswith('.pkl'):
                        os.rename(os.path.join(checkpoint_dir, f),
                                  os.path.join(checkpoint_dir, 'checkpoint.pkl'))
        else:
            raise AnalysisProcessError('Checkpoints folder not found! Maybe the optimization process failed.')

        # Set resume job flag in the optimization settings if the chekpoint control doesn't raise any error.
        workflow.add_optimization_settings({'resume_job': True})

        opt_neuron_file = os.path.join(output_dir, 'opt_neuron.py')
        with open(opt_neuron_file, 'r') as fd:
            buffer = fd.readlines()
        buffer = ['import matplotlib\n', 'matplotlib.use(\'Agg\')\n'] + buffer
        with open(opt_neuron_file, 'w') as fd:
            fd.writelines(buffer)
        
        r_0_dir = os.path.join(output_dir, 'r_0')
        if os.path.exists(r_0_dir):
            shutil.rmtree(r_0_dir)
        os.mkdir(r_0_dir)
        
        # delete compiled mods files directory
        compiled_mods_dir = os.path.join(output_dir, 'x86_64')
        if os.path.exists(compiled_mods_dir):
            shutil.rmtree(compiled_mods_dir)
        curr_dir = os.getcwd()
       
        log_file_path = os.path.join(LOG_ROOT_PATH, 'analysis', workflow.get_user())
        if not os.path.exists(log_file_path):
            os.makedirs(log_file_path)
            
        log_file = os.path.join(log_file_path, workflow.get_id() + '.log')

        build_mechanisms_command = f'source {env_prefix}/bin/activate; nrnivmodl mechanisms > {log_file}'
        opt_neuron_analysis_command = f'source {env_prefix}/bin/activate; python ./opt_neuron.py --analyse --checkpoint ./checkpoints > {log_file}'
        
        os.chdir(output_dir)
        p0 = subprocess.call(build_mechanisms_command, shell=True, executable='/bin/bash')
        p1 = subprocess.call(opt_neuron_analysis_command, shell=True, executable='/bin/bash')
        os.chdir(curr_dir)

        if p0 > 0:
            raise MechanismsProcessError()#p0.returncode, build_mechanisms_command, stderr=p0.stderr)
        if p1 > 0:
            error = 'Can\'t identify the error.'
            for f in os.listdir(os.path.join(output_dir, 'checkpoints')):
                if not f.endswith('.pkl'):
                    error = 'Checkpoint not found! Maybe the optimization process failed.'
                    break
            raise AnalysisProcessError(error)#p1.returncode, opt_neuron_analysis_command, stderr=p1.stderr)

    @staticmethod
    def make_naas_archive(workflow):

        analysis_dir_name = os.listdir(workflow.get_analysis_dir())[0]
        src_dir = os.path.join(workflow.get_analysis_dir(), analysis_dir_name)
        dst_dir = os.path.join(workflow.get_tmp_dir(), analysis_dir_name)
        tmp_analysis_dir = shutil.copytree(src_dir, dst_dir)

        for f in os.listdir(tmp_analysis_dir):
            f_path = os.path.join(tmp_analysis_dir, f)
            if f != 'mechanisms' and f != 'morphology' and f != 'checkpoints':
                if os.path.isdir(os.path.join(f_path)):
                    shutil.rmtree(f_path)
                else:
                    os.remove(f_path)            

        # rename .hoc file
        hoc_file = None
        checkpoints_dir = os.path.join(tmp_analysis_dir, 'checkpoints')
        for f in os.listdir(checkpoints_dir):
            if f.endswith('.hoc'):
                hoc_file = f
        if not hoc_file:
            raise FileNotFoundError('".hoc" file not found')
        os.rename(
            src=os.path.join(checkpoints_dir, hoc_file),
            dst=os.path.join(checkpoints_dir, 'cell.hoc')
        )

        # create naas archive on root wf path
        naas_archive = shutil.make_archive(
            base_name=os.path.join(workflow.get_workflow_path(),
                                   analysis_dir_name),
            format='zip',
            root_dir=workflow.get_tmp_dir()
        )

        # moving naas archive to tmp dir
        return shutil.move(naas_archive, workflow.get_tmp_dir())

    @staticmethod
    def load_parameters_template(workflow, template_type):
        if template_type not in ['pyramidal', 'interneuron']:
            raise UnknownParametersTemplate
        
        shutil.copy(
            os.path.join(HHF_PARAMETERS_TEMPLATE_DIR, template_type, 'parameters.json'),
            os.path.join(workflow.get_model_dir(), 'config')
        )

    @staticmethod
    def clean_model(workflow):
        try:
            shutil.rmtree(os.path.join(workflow.get_model_dir(), 'checkpoints'))
            shutil.rmtree(os.path.join(workflow.get_model_dir(), 'tools'))
            shutil.rmtree(os.path.join(workflow.get_model_dir(), 'figures'))
            for dd in os.listdir(workflow.get_model_dir()):
                if dd.startswith('r_seed'):
                    shutil.rmtree(os.path.join(workflow.get_model_dir(), dd))
            shutil.rmtree(os.path.join(workflow.get_model_dir(), 'mod_nsgportal'))
            shutil.rmtree(os.path.join(workflow.get_model_dir(), 'x86_64'))
        except FileNotFoundError:
            pass                
        