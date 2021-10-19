# Model class

from hhnb.core.lib.exception.model_exception import *
from hhnb.core.lib.model import *

from hh_neuron_builder.settings import TMP_DIR

from multipledispatch import dispatch
from uuid import uuid4 as uuid

import shutil
import json
import os


_TMP_DIR = os.path.join(TMP_DIR, 'model')


def _read_file(f):
    f = os.path.split(f)[1]
    f_name, f_ext = os.path.splitext(f)
    with open(f, 'r') as fd:
        if f_ext == '.json':
            buffer = json.load(fd)
        else:
            buffer = fd.read()
    return buffer


def _write_file_to_directory(src_file, dst_dir, dst_file=None):
        if not dst_file:
            dst_file = os.path.split(src_file)[1]
        f_name, f_ext = os.path.splitext(dst_file)
        with open(os.path.join(dst_dir, dst_file), 'w') as fd:
            if f_ext == '.json':
                j_src = json.load(open(src_file, 'r'))
                json.dump(j_src, fd, indent=4)
            else:
                buffer = open(src_file, 'r').read()
                fd.write(buffer)


def _create_subdir(cls, model_dir):
        os.mkdir(os.path.join(model_dir, 'config'))
        os.mkdir(os.path.join(model_dir, 'mechanisms'))
        os.mkdir(os.path.join(model_dir, 'morphology'))
        os.mkdir(os.path.join(model_dir, 'template'))



class Model(ModelBase):

    def __init__(self, model_dir, **kwargs):
        self._model_dir = model_dir
        key = os.path.split(self._model_dir)
        if 'key' in kwargs:
            key = kwargs.pop('key')
        print(key)
        super().__init__(key, **kwargs)

    @classmethod
    def from_zip(cls, zip_model):
        m = cls()
        # TODO: to be complete
        return m

    @classmethod
    def from_dir(cls, model_dir, key):
        model = cls(model_dir, key=key)
        
        if not os.path.exists(model_dir):
            raise FileNotFoundError('Model dir %s not found' % model_dir)
        if not os.path.isdir(model_dir):
            raise NotADirectoryError('Model dir %s is not a directory')
        
        # check if exists sub directories otherwise return an empty model instance 
        if not any(os.scandir(model_dir)):
            return model

        # building subdirs
        config_dir = os.path.join(model_dir, 'config')
        morph_dir = os.path.join(model_dir, 'morphology')
        mechanisms_dir = os.path.join(model_dir, 'mechanisms')
        
        # check for features
        try:
            model.set_features(Features.from_dir(config_dir))
        except FileNotFoundError:
            pass

        # check for parameters
        try:
            model.set_parameters(os.path.join(config_dir, 'parameters.json'))
        except FileNotFoundError:
            pass

        # check for morphology
        try:
            model.set_morphology(Morphology.from_dir(morph_dir))
        except FileNotFoundError:
            pass

        # check for mechanisms
        try:
            model.set_mechanisms(mechanisms_dir)
        except FileNotFoundError:
            pass

        return model

    @dispatch(str)
    def update_optimization_files(self, model_dir):
        print('update_optimization_files() called on %s' % model_dir)
        try:
            # parameters
            parameters = shutil.copy(os.path.join(model_dir, 'config', 'parameters.json'),
                                     os.path.join(self._model_dir, 'config'))
            self.set_parameters(parameters)
            # morphology
            for m in os.listdir(os.path.join(model_dir, 'morphology')):
                morph = shutil.copy(os.path.join(model_dir, 'morphology', m),
                                    os.path.join(self._model_dir, 'morphology'))
                conf_file = shutil.copy(os.path.join(model_dir, 'config', 'morph.json'),
                                        os.path.join(self._model_dir, 'config'))
                print(morph)
                print(conf_file)
            self.set_morphology(morphology=morph, conf_file=conf_file)
            # mechanisms
            for m in os.listdir(os.path.join(model_dir, 'mechanisms')):
                shutil.copy(os.path.join(model_dir, 'mechanisms', m),
                            os.path.join(self._model_dir, 'mechanisms'))
            self.set_mechanisms(os.path.join(self._model_dir, 'mechanisms'))
            # python's files

        except FileNotFoundError():
            raise FileNotFoundError()


    def get_optimization_files_raw_status(self):
        return {
            'morphology': self.get_morphology().get_raw_status(),
            'parameters': self._PARAMETERS,
            'mechanisms': self._MECHANISMS
        }

    def get_optimization_files_status(self):
        return {
            'morphology': self.get_morphology().get_status(),
            'parameters': '' if self._PARAMETERS else '"parameters.json" file NOT present',
            'mechanisms': '' if self._MECHANISMS else '"mechanisms" files NOT present'
        }

    def get_properties(self):
        return {
            'features': self.get_features().get_status(),
            'optimization_files': self.get_optimization_files_status()
        }
        
    

class ModelUtil:

    @staticmethod
    def clone(model):
        return Model(
            features=model.get_features(),
            parameters=model.get_parameters(),
            morphology=model.get_morphology(),
            mechanisms=model.get_mechanisms(),
            key=model.get_key()
        )

    @staticmethod
    def write_to_workflow(model, workflow_id):
        if not os.path.exists(workflow_id):
            raise FileNotFoundError('%s path not found' % workflow_id)
        model_dir = os.path.join(workflow_id, 'model')
        if os.path.exists(model_dir):
            os.rmtree(model_dir)
        ModelUtil.create_model_subdir(model_dir)
        _write_file_to_directory(model.get_features().get_features(), 
                   os.path.join(model_dir, 'config'), 'features.json')
        _write_file_to_directory(model.get_features().get_protocols(),
                   os.path.join(model_dir, 'config'), 'protocols.json')
        _write_file_to_directory(model.get_parameters(), 
                   os.path.join(model_dir, 'config'), 'parameters.json')
        _write_file_to_directory(model.get_morphology(), 
                    os.path.join(model_dir, 'morphology'))
        for m in model.get_mechanisms():
            shutil.copy(m, os.path.join(model_dir, 'mechanisms'))
        
        return model_dir

    @staticmethod
    @dispatch(str, str, str)
    def zip_model(src_dir, dst_dir=None, zip_name=None):
        if not zip_name:
            zip_name = src_dir.split('/')[-1]
        shutil.make_archive(os.path.join(dst_dir, zip_name), 'zip', src_dir)
    
    # TODO: to change
    @staticmethod
    @dispatch(Model, str, str)
    def zip_model(model, dst_dir=None, zip_name=None):
        if not dst_dir:
            dst_dir = os.path.join(_TMP_DIR, uuid)
            while True:
                if not os.path.exists(dst_dir):
                    break
                dst_dir = os.path.join(_TMP_DIR, uuid)
        if not zip_name:
            zip_name = os.path.split(zip_name)[1]
        zip_name = zip_name.split('.zip')[0]
        zip_path = os.path.join(dst_dir, zip_name)
        shutil.make_archive(base_name=zip_path, 
                     format='zip', 
                     root_dir=ModelUtil.write_to_workflow(model, os.path.join(dst_dir)),
                     base_dir='model')
        return zip_path


    @staticmethod
    def update_key(model, key):
        config_dir = os.path.join(os.path.join(model._model_dir, 'config'))
        for config in [os.path.join(config_dir, c) for c in os.listdir(config_dir)]:
            with open(config, 'r') as fd:
                jj = json.load(fd)
            jj_k = jj.keys()
            if len(jj_k) != 1:
                raise shutil.Error('Conf file key error')
            if jj_k[0] != key:
                jjj = {key: jj[jj_k[0]]}
                os.remove(config)
                with open(config, 'w') as fd:
                    json.dump(jjj, fd, indent=4)

        opt_file = os.path.join(model._model_dir, 'opt_neuron.py')
        with open(opt_file, 'r') as fd:
            lines = fd.readlines()
        for l in lines:
            if l.startswith('evaluator = model.evaluator.create'):
                x = l.split("'")
                y = x[0] + "'" + key + "'" + x[2]
                z = lines.index(l)
                lines[z] = y
        with open(opt_file, 'w') as fd:
            fd.writelines(lines)

