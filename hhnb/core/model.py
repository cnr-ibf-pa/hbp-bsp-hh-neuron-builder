# Model class

import datetime
from hhnb.core.lib.exception.model_exception import *
from hhnb.core.lib.model import *

from hh_neuron_builder.settings import TMP_DIR

from filecmp import cmp as compare_files
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
        if key[0] in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
            key = 'K' + key
        super().__init__(key, **kwargs)
        self._ETRACES = False


    def _check_if_file_exists(self, **kwargs):
        if len(kwargs) > 1:
            raise TypeError(f'{__name__} takes only 1 keyword argument')
        
        keyword_list = ['paramters', 'protocols', 'features', 'morphology']
        key = list(kwargs.keys())[0]
        
        if key not in keyword_list:
            raise TypeError(f'{__name__} take only 1 of the following\
                            arguments {keyword_list}')

        if key == 'features' or key == 'protocols' or key == 'parameters':
            file_path = os.path.join(self._model_dir, 'config')
        elif key == 'morphology':
            file_path = os.path.join(self._model_dir, 'morphology')

        try:
            c = compare_files(kwargs[key],
                              os.path.join(file_path, os.path.split(kwargs[key])[1]))
        except FileNotFoundError:
            return False
        return c

    # def set_features(self, features=None, protocols=None):
        # f = self._features.get_features()
        # if not self._check_if_file_exists(features=f):
            # shutil.copy(f)
        # super().set_features(features=features, protocols=protocols)

    # def set_features(self, features=None, protocols=None):
    #     if not features and not protocols:
    #         if os 

    # def set_morphology(self, morphology=None):
    #     if not morphology:
    #         morphology = os.path.join(
    #             self._model_dir, 
    #             os.listdir(os.path.join(self._model_dir, 'morphology'))[0]
    #         )

    #     super().set_morphology(morphology)

    # def set_mechanisms(self, mechansisms=None):
    #     if not mechansisms:
    #         mechansisms = os.path.join(self._model_dir, 'mechanisms')
    #     super().set_mechanisms(mechansisms=mechansisms)

    # def set_parameters(self, parameters=None):
    #     if not parameters:
    #         parameters = os.path.join(self._model_dir, 'config', 'parameters.json')
    #     super().set_parameters(parameters=parameters)


    # @classmethod
    # def from_zip(cls, zip_model):
    #     model = cls()
    #     # TODO: to be complete
    #     tmp_unzip_model = os.path.join(TMP_DIR, datetime.datetime.now())
    #     shutil.unpack_archive(zip_model, tmp_unzip_model)
    #     pass


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
            feat = os.path.join(config_dir, 'features.json')
            prot = os.path.join(config_dir, 'protocols.json')
            features = Features()
            if os.path.exists(feat):
                features.set_features(feat)
            if os.path.exists(prot):
                features.set_protocols(prot)
            model.set_features(features)
        except FileNotFoundError:
            pass

        # check for parameters
        try:
            parameters = os.path.join(config_dir, 'parameters.json')
            model.set_parameters(parameters)
        except FileNotFoundError:
            pass

        # check for morphology
        try:
            morphs = os.listdir(morph_dir)
            if len(morphs) == 1:                
                morphology = Morphology(os.path.join(morph_dir, morphs[0]))
                model.set_morphology(morphology)
        except FileNotFoundError:
            pass

        # check for mechanisms
        try:
            model.set_mechanisms(mechanisms_dir)
        except FileNotFoundError:
            pass

        return model

    def update_optimization_files(self, model_dir):
        
        config_dir = os.path.join(model_dir, 'config')
        morph_dir = os.path.join(model_dir, 'morphology')
        mechans_dir = os.path.join(model_dir, 'mechanisms')
        
        try:
            # paramenters
            if os.path.exists(config_dir) and \
                os.path.exists(os.path.join(config_dir, 'parameters.json')):
                parameters = shutil.copy(os.path.join(config_dir, 'parameters.json'),
                                         os.path.join(self._model_dir, 'config'))
                self.set_parameters(parameters)

            # morphology
            if os.path.exists(morph_dir) and len(os.listdir(morph_dir)) == 1:
                shutil.rmtree(os.path.join(self._model_dir, 'morphology'))
                try:
                    os.remove(os.path.join(self._model_dir, 'config', 'morph.json'))
                except FileNotFoundError:
                    pass
                shutil.copytree(morph_dir, self._model_dir)
                self.set_morphology(
                    os.listdir(os.path.join(self._model_dir, 'morphology')[0])
                )
                # with open(os.path.join(self._model_dir, 'config'), 'w') as morph_conf:
                #     json.dump(self.get_morphology().get_config(), morph_conf)


            # mechanisms
            if os.path.exists(mechans_dir) and len(os.listdir(mechans_dir)) > 0:
                shutil.rmtree(os.path.join(self._model_dir, 'mechanisms'))
                shutil.copytree(mechans_dir, self._model_dir)
                self.set_mechanisms(os.path.join(self._model_dir, 'mechanisms'))

            # # for m in os.listdir(os.path.join(model_dir, 'morphology')):
            # #     morph = shutil.copy(os.path.join(model_dir, 'morphology', m),
            # #                         os.path.join(self._model_dir, 'morphology'))
            # shutil.rmtree(os.path.join(self._model_dir, 'morphology'))
            # shutil.copytree(os.path.join(model_dir, 'morphology'),
            #                 os.path.join(self._model_dir, 'morphology'))
            
            # conf_file = shutil.copy(os.path.join(model_dir, 'config', 'morph.json'),
            #                         os.path.join(self._model_dir, 'config'))
                                
            # self.set_morphology(morphology=morph)
            
            # # mechanisms
            
            # # for m in os.listdir(os.path.join(model_dir, 'mechanisms')):
            # #     shutil.copy(os.path.join(model_dir, 'mechanisms', m),
            # #                 os.path.join(self._model_dir, 'mechanisms'))

            # shutil.rmtree(os.path.join(self._model_dir, 'mechanisms'))
            # shutil.copytree(os.path.join(model_dir, ''))

            # self.set_mechanisms(os.path.join(self._model_dir, 'mechanisms'))
            # # python's files

            # parameters
            pass

        except FileNotFoundError as e:
            raise FileNotFoundError(e)

    def get_optimization_files_raw_status(self):
        return {
            'morphology': self.get_morphology().get_raw_status(),
            'parameters': self._PARAMETERS,
            'mechanisms': self._MECHANISMS,
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
            'optimization_files': self.get_optimization_files_status(),
            'model_key': self.get_key()
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
            dst_dir = os.path.join(_TMP_DIR, str(uuid()))
            while True:
                if not os.path.exists(dst_dir):
                    break
                dst_dir = os.path.join(_TMP_DIR, str(uuid()))
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
    def update_key(model, key=None):
        if type(model) != Model:
            raise TypeError('%s is not a model instance' % model)
        if key:
            model.set_key(key)
        else:
            key = model.get_key()
        config_dir = os.path.join(os.path.join(model._model_dir, 'config'))
        for config in [os.path.join(config_dir, c) for c in os.listdir(config_dir)]:
            with open(config, 'r') as fd:
                jj = json.load(fd)
            jj_k = list(jj.keys())
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