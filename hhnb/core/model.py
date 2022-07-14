# Model class

"""
This package contains all the stuff to build up a Neuron Model object.
"""


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
    """ Private function that take a file and returns its content. """
    f = os.path.split(f)[1]
    f_name, f_ext = os.path.splitext(f)
    with open(f, 'r') as fd:
        if f_ext == '.json':
            buffer = json.load(fd)
        else:
            buffer = fd.read()
    return buffer


def _write_file_to_directory(src_file, dst_dir, dst_file=None):
    """
    Private function that copies a source file to the destination dir.
    The destination file can be also a json file and in this case,
    the output will be formatted as json. In the other case the
    source file will be treated as a binary file. Furthermore
    the copy can be explicitely named using the "dst_file" parameter
    otherwise the source file name will be used.   

    Parameters
    ----------
    src_file : str
        the source file path
    dst_dir : str
        the destination directory path where to copy the file
    dst_file : str, optional
        to be set if you want to overwrite the file name, by default None
    """
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
    """ Private function that make the subtree folder for the Neuron Model. """
    os.mkdir(os.path.join(model_dir, 'config'))
    os.mkdir(os.path.join(model_dir, 'mechanisms'))
    os.mkdir(os.path.join(model_dir, 'morphology'))
    os.mkdir(os.path.join(model_dir, 'template'))


class Model(ModelBase):
    """
    This Model extends the ModelBase class and offers some useful
    methods to handle the Model object automatically for
    the HHNB Workflow.
    """

    def __init__(self, model_dir, **kwargs):
        """
        Initialize the Model object by reading all the files present
        in the "model_dir" folder.
        For keyword argouments read the hhnb.core.model.Model doc.

        Parameters
        ----------
        model_dir : str
            the root folder of the Model
        """
        self._model_dir = model_dir
        key = os.path.split(self._model_dir)
        if 'key' in kwargs:
            key = kwargs.pop('key')
        if key[0] in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
            key = 'K' + key
        super().__init__(key, **kwargs)
        self._ETRACES = False


    def _check_if_file_exists(self, **kwargs):
        """
        Private method that checks if a file already exists
        in the Model folder subtree.

        Returns
        -------
        bool
            True if the file exists, False otherwise

        Raises
        ------
        TypeError
            if the argoument passed is wrong
        """
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
        """
        Thie method is used to initialize automatically a Model object
        by passing the model root folder as parameter, reads all the 
        files and the structure of the folder subtree and return a 
        Model object with the "key" set as the model global key. 

        Parameters
        ----------
        model_dir : str
            the model root folder
        key : str
            the model global key

        Returns
        -------
        hhnb.core.model.Model
            the model object

        Raises
        ------
        FileNotFoundError
            if the "model_dir" does not exist
        NotADirectoryError
            if the "model_dir" is not a directory
        """

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
        """
        This method update the current model optimization files using 
        the new ones in the "model_dir" folder passed as argoument.
        
        With "optimization files" is intendend any files that belog to 
        the following categories: ["parameters", "morphology", "mechanisms"].  

        Parameters
        ----------
        model_dir : str
            the model root folder from where get the new optimization files

        Raises
        ------
        FileNotFoundError
            if any optimization file is not found 
        """
        
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
        """
        Returns a dictionaire with the optimization files as keys and 
        their status (True if present, False otherwise) as a boolean value.
        """
        return {
            'morphology': self.get_morphology().get_raw_status(),
            'parameters': self._PARAMETERS,
            'mechanisms': self._MECHANISMS,
        }

    def get_optimization_files_status(self):
        """
        Returns a dictionaire with the optimization files as keys and
        their status as a message.
        """
        return {
            'morphology': self.get_morphology().get_status(),
            'parameters': '' if self._PARAMETERS else '"parameters.json" file NOT present',
            'mechanisms': '' if self._MECHANISMS else '"mechanisms" files NOT present'
        }

    def get_properties(self):
        """
        Returns the status of the Model properties. 
        """
        return {
            'features': self.get_features().get_status(),
            'optimization_files': self.get_optimization_files_status(),
            'model_key': self.get_key()
        }
    

class ModelUtil:
    """
    This is a class composed by all static method that handle a Model object.
    """

    @staticmethod
    def clone(model):
        """
        Static method that clone a Model object passed as argoument.

        Parameters
        ----------
        model : hhnb.core.model.Model
            the Model object to clone

        Returns
        -------
        hhnb.core.model.Model
            a new Model object with the same files and properties of the cloned one
        """
        return Model(
            features=model.get_features(),
            parameters=model.get_parameters(),
            morphology=model.get_morphology(),
            mechanisms=model.get_mechanisms(),
            key=model.get_key()
        )

    @staticmethod
    def write_to_workflow(model, workflow_id):
        """
        Write the whole Model object to the disk in the "workflow_id" subfolder
        and returns the new Model root folder. 

        Parameters
        ----------
        model : hhnb.core.model.Model
            the Model object to store
        workflow_id : str
            the workflow where to store the Model.

        Returns
        -------
        str
            the model root folder 

        Raises
        ------
        FileNotFoundError
            if the "workflow_id" folder does not exist
        """
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
        """
        This static method zip a Model object.
        It takes the Model root folder as source dir and the optional
        destination dir to write the zipped model and an optional
        zip file name.

        Parameters
        ----------
        src_dir : str
            the model root folder
        dst_dir : str, optional
            where to write the zipped model, by default the source folder is used as destination
        zip_name : str, optional
            the zip file name, by default the source folder name is used
        """
        if not dst_dir: 
            dst_dir = src_dir
        if not zip_name:
            zip_name = src_dir.split('/')[-1]
        shutil.make_archive(os.path.join(dst_dir, zip_name), 'zip', src_dir)
    
    # TODO: to change
    @staticmethod
    @dispatch(Model, str, str)
    def zip_model(model, dst_dir=None, zip_name=None):
        """
        This static method zip a Model object.
        It takes the Model object directly as model and the optional
        destination dir to write the zipped model and an optional
        zip file name.

        Parameters
        ----------
        model : hhnb.core.model.Model
            the model object
        dst_dir : str, optional
            where to write the zipped model, by default the source folder is used as destination
        zip_name : str, optional
            the zip file name, by default the source folder name is used
        """
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
        """
        This static method update the key of all Model's files with the 
        new one passed as argoument and then it will be set as the Model
        global key. Otherwise the files' keys are updated using the current
        Model global key.

        Parameters
        ----------
        model : hhnb.core.model.Model
            the model to update
        key : str, optional
            the new global key, by default the current model global key is used

        Raises
        ------
        TypeError
            if the model object passed is not an istance of hhnb.core.model.Model
        shutil.Error
            is any error occurred when trying to update the files' key
        """
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