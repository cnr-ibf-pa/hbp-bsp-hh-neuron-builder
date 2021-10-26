"""
Workspace utils classes
"""

from json.decoder import JSONDecodeError
from hh_neuron_builder.settings import MEDIA_ROOT, HHF_TEMPLATE_DIR, TMP_DIR

from multipledispatch import dispatch
from hhnb.core.conf.exec_files_conf import ExecFileConf

from hhnb.core.lib.exception.workflow_exception import *
from hhnb.core.model import *

from datetime import datetime
import shutil
import os
import json
import requests

from hhnb.core.user import NsgUser


class _WorkflowBase:
    
    def __init__(self, username, workflow_id):
        self._username = username
        self._id = workflow_id
        self._workflow_path = os.path.join(MEDIA_ROOT, 'hhnb', 'workflows',
                                           self._username, self._id)
        self._result_dir = os.path.join(self._workflow_path, 'results')
        self._model_dir = os.path.join(self._workflow_path, 'model')
        self._tmp_dir = os.path.join(self._workflow_path, 'tmp')
        self._etraces_dir = os.path.join(self._workflow_path, 'etraces')
        
        self._optimization_settings = os.path.join(self._workflow_path,
                                                   'optimization_settings.json')
        if os.path.exists(self._model_dir) and any(os.scandir(self._model_dir)):
            self._model = Model.from_dir(self._model_dir, key=workflow_id)
        
    def get_user(self):
        return self._username

    def get_id(self):
        return self._id

    def get_workflow_path(self):
        return self._workflow_path

    def get_result_dir(self):
        return self._result_dir

    def get_model_dir(self):
        return self._model_dir

    def get_tmp_dir(self):
        return self._tmp_dir

    def get_etraces_dir(self):
        return self._etraces_dir

    def get_model(self):
        return self._model


    
class Workflow(_WorkflowBase):

    @classmethod
    def generate_user_workflow(cls, username, make_files=True):
        workflow_id = datetime.now().strftime('%Y%m%d%H%M%S')
        wf = cls(username, workflow_id)
        if make_files:
            wf.make_workflow_dirs()
        return wf
    
    @classmethod
    def generate_user_workflow_from_zip(cls, username, zip_file):
        workflow_id = datetime.now().strftime('%Y%m%d%H%M%S')
        wf = cls(username, workflow_id)
        shutil.unpack_archive(zip_file, wf.get_workflow_path())
        return wf 


    @classmethod
    def get_user_workflow_by_id(cls, username, workflow_id):
        wf = cls(username, workflow_id)
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
        with open(os.path.join(dst_path, file_name), mode) as fd_dst:
            if fd.multiple_chunks(chunk_size=4096):
                for chunk in fd.chunks(chunk_size=4096):
                    fd_dst.write(chunk)
            else:
                fd_dst.write(fd.read())

    def make_workflow_dirs(self):
        if os.path.exists(self._workflow_path):
            raise WorkflowExists('The workspace already exists. Use another path.')
        os.makedirs(self._workflow_path)
        shutil.copytree(HHF_TEMPLATE_DIR, self._model_dir)       
        os.mkdir(self._result_dir)
        os.mkdir(self._tmp_dir)
        os.mkdir(self._etraces_dir)

    def make_dir(self, dir):
        if os.path.exists(os.path.join(self._workflow_path, dir)):
            raise PathExists('The path "%s" already exists. Use another path' % dir)
        os.makedirs(os.path.join(self._workflow_path, dir))

    def copy_features(self, src_file, safe=True):
        self._copy_file(src_file, os.path.join(self._model_dir, 'config'), safe)

    def write_features(self, fd, mode='wb', safe=True):
        self._write_file(fd, 'features.json', 
                         os.path.join(self._model_dir, 'config',), mode, safe)
    
    def write_protocols(self, fd, mode='wb', safe=True):
        self._write_file(fd, 'protocols.json',
                         os.path.join(self._model_dir, 'config'), mode, safe)

    def load_model_zip(self, model_zip):
        unzipped_tmp_model_dir = os.path.join(self._tmp_dir, 'model')
        if os.path.exists(unzipped_tmp_model_dir):
            shutil.rmtree(unzipped_tmp_model_dir)
        os.mkdir(unzipped_tmp_model_dir)
        shutil.unpack_archive(model_zip, unzipped_tmp_model_dir, 'zip')
        if len(os.listdir(unzipped_tmp_model_dir)) == 1:
            unzipped_tmp_model_dir = os.path.join(unzipped_tmp_model_dir,   
                                                  os.listdir(unzipped_tmp_model_dir)[0])
        self._model.update_optimization_files(unzipped_tmp_model_dir)
        ModelUtil.update_key(model=self._model)

    def get_optimization_settings(self):
        try:
            with open(self._optimization_settings, 'r') as fd:
                try:
                    return json.load(fd)
                except JSONDecodeError:
                    return {}
        except FileNotFoundError:
            raise FileNotFoundError("%s not found" % self._optimization_settings)

    def set_optimization_settings(self, optimization_settings):
        with open(self._optimization_settings, 'w') as fd:
            json.dump(optimization_settings, fd, indent=4)


    def remove_file(self, file_path):
        directory, filename = os.path.split(file_path)
        if not os.path.exists(os.path.join(self._model_dir, directory)):
            raise FileNotFoundError('%s directory not exists' % directory)
        if filename == '*':
            for f in os.listdir(os.path.join(self._model_dir, directory)):
                os.remove(os.path.join(self._model_dir, directory, f))
        else:
            full_file_path = os.path.join(self._model_dir, file_path) 
            if not os.path.exists(full_file_path):
                raise FileNotFoundError('%s not found' % file_path)
            os.remove(full_file_path)

    def get_properties(self):
        props = {
            'id': self._id,
            'model': self._model.get_properties(), 
            'optimization_settings': os.path.exists(self._optimization_settings),
            'etraces': any(os.scandir(self._etraces_dir))
        }
        return props

    def clean_tmp_dir(self):
        if len(os.listdir(self._tmp_dir)) > 0:
            shutil.rmtree(self._tmp_dir)
            if not os.path.exists(self._tmp_dir):
                os.mkdir(self._tmp_dir)
    

class WorkflowUtil:

    @staticmethod
    def set_model_key(workflow, key=None):

        ModelUtil.update_key(workflow.get_model(), key)

    @staticmethod
    def set_default_parameters(workflow):
        shutil.copy(os.path.join(HHF_TEMPLATE_DIR, '..', 'parameters.json'),
                    os.path.join(workflow.get_model_dir(), 'config'))
        workflow.get_model().set_parameters()

    @staticmethod
    def clone_workflow(workflow):
        new_workflow = Workflow.generate_user_workflow(workflow.get_user(), make_files=False)
        shutil.copytree(workflow.get_workflow_path(), new_workflow.get_workflow_path())
        return new_workflow

    @staticmethod
    def make_archive(workflow, zip_name, dir_name, file_list):
        zip_path = os.path.join(workflow.get_tmp_dir(), zip_name)
        if os.path.exists(zip_path):
            os.remove(zip_path)
        tmp_dir = os.path.join(workflow.get_tmp_dir(), dir_name)
        os.mkdir(tmp_dir)
        for f in file_list:
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
        return WorkflowUtil.make_archive(workflow=workflow,
                                         zip_name='features.zip',
                                         dir_name='feature',
                                         file_list=file_list)

        # zip_name = os.path.join(workflow.get_tmp_dir(), 'features.zip')
        # if os.path.exists(zip_name):
        #     os.remove(zip_name)
        # tmp_feat_dir = os.path.join(workflow.get_tmp_dir(), 'features')
        # os.mkdir(tmp_feat_dir)
        # shutil.copy(workflow.get_model().get_features().get_features(), tmp_feat_dir)
        # shutil.copy(workflow.get_model().get_features().get_protocols(), tmp_feat_dir)
        # shutil.make_archive(zip_name.split('.zip')[0], 'zip', tmp_feat_dir)
        # shutil.rmtree(tmp_feat_dir)
        # return zip_name
        
    @staticmethod
    def make_model_archive(workflow):
        zip_name = os.path.join(workflow.get_tmp_dir(), 'model.zip')
        shutil.make_archive(
            base_name=os.path.splitext(zip_name)[0],
            format='zip',
            root_dir=workflow.get_model_dir(),
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
        if settings['hpc'] == 'NSG':
            ExecFileConf.write_nsg_exec(dst_dir=tmp_model_dir,
                                        max_gen=settings['gen-max'],
                                        offspring=settings['offspring'])
        elif settings['hpc'] == 'DAINT-CSCS' or settings['hpc'] == 'SA-CSCS':
            ExecFileConf.write_daint_exec(dst_dir=tmp_model_dir,
                                          folder_name=workflow.get_model().get_key(),
                                          offspring=settings['offspring'],
                                          max_gen=settings['gen-max'])
        
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
        
        for mod in mechanisms:
            file_path = os.path.join(workflow.get_model_dir(), 'mechanisms', mod['name'])
            r = requests.get(url=mod['url'], verify=False)
            with open(file_path, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=4096):
                    fd.write(chunk)
        workflow.get_model().set_mechanisms()

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




























        

""" 
    class (Workflow):
    
    def check_features(self):
        feats = os.path.exists(os.path.join(self.model_dir, 'config', 'features.json')) 
        prots = os.path.exists(os.path.join(self.model_dir, 'config', 'protocols.json'))
        if feats and prots:
            return True, 'OK'
        elif feats and not prots:
            return False, '"protocols.json" not found'
        elif not feats and prots:
            return False, '"features.json" not found'
        else:
            return False, '"features.json" and "protocols.json" not found'

    def check_parameters(self):
        params = os.path.exists(os.path.join(self.model_dir, 'config', 'parameters.json'))
        if params: 
            return True, 'OK'
        return False, '"parameters.json" not found'

    def check_morphology(self):
        morph = len(os.listdir(os.path.join(self.model_dir, 'morphology'))) == 1
        jmorph = os.path.exists(os.path.join(self.model_dir, 'config', 'morph.json'))  
        if morph and jmorph:
            return True, 'OK'
        elif morph and not jmorph:
            return False, '"morph.json" not found'
        elif not morph and jmorph:
            return False, 'Morphology file not found'
        else:
            return False, 'Morphology file and "morph.json" not found'

    def check_mechanisms(self):
        if len(os.listdir(os.path.join(self.model_dir, 'mechanisms'))) > 0:
            return True, 'OK'
        return False, 'Mechanisms files not found'

    def check_model(self):
        feats = self.check_features()
        params = self.check_parameters()
        morphs = self.check_morphology()
        mechans = self.check_mechanisms()
        return feats, params, morphs, mechans

    def check_settings(self):
        msett = os.path.join()

    def check_tmp_dir(self):
        self.workflow_path   """

""" 
def _is_model_obj(obj):
    if type(obj) != Model:
        return False
    return True


class WorkflowUtil:

    @staticmethod
    def check_features(model):
        if not _is_model_obj(model):
            raise TypeError('%s is not a Model object' % model)
        return model.get_features().get_status()
        
    @staticmethod
    def check_for_model(model):
        pass


    @staticmethod
    def run_optimization(model, *args):
        pass


    @staticmethod
    def run_analysis(model, *args):
        pass """