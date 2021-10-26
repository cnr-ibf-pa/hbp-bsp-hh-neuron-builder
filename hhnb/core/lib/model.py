from .exception.model_exception import *
from multipledispatch import dispatch

import os
import json


class Features:

    def __init__(self, features=None, protocols=None):
        self._FEATURES = False
        self._PROTOCOLS = False
        self._features = None
        self._protocols = None
        if features:
            self.set_features(features)
        if protocols:
            self.set_protocols(protocols)

    def __str__(self):
        print('<class Features:')
        print(f'\tfeatures: {(self._FEATURES), (self._features)}',
              f'\tprotocols: {(self._PROTOCOLS), (self._protocols)}',
              '>', sep='\n')

    def set_features(self, features):
        if not os.path.exists(features):
            raise FileNotFoundError('%s not found' % features)
        if not os.path.isfile(features):
            raise IsADirectoryError('%s is a directory' % features)
        self._features = features
        self._FEATURES = True

    def set_protocols(self, protocols):
        if not os.path.exists(protocols):
            raise FileNotFoundError('%s not found' % protocols)
        if not os.path.isfile(protocols):
            raise IsADirectoryError('%s is a directory' % protocols)
        self._protocols = protocols
        self._PROTOCOLS = True

    def get_features(self):
        return self._features

    def get_protocols(self):
        return self._protocols

    def get_raw_status(self):
        return {
            'features': self._FEATURES,
            'protocols': self._PROTOCOLS
        }

    def get_status(self):
        return {
            'features': '' if self._FEATURES else '"features.json" file NOT present',
            'protocols': '' if self._PROTOCOLS else '"protocols.json" file NOT present'
        }


class Morphology:

    def __init__(self, morphology=None, key=None):
        self._MORPHOLOGY = False
        self._morphology = None
        self._config = None
        if morphology:
            self.set_morphology(morphology)

    def __str__(self):
        print('<class Morphology:')
        print(f'\tmorphology: {self._morphology}',
              f'\tconf: {self._config}',
              '>', sep='\n')

    def set_morphology(self, morphology, key=None):
        if not os.path.exists(morphology):
            raise FileNotFoundError('%s not found' % morphology)
        if not os.path.isfile(morphology):
            raise IsADirectoryError('%s is a directory' % morphology)
        self._morphology = morphology
        self._MORPHOLOGY = True
        if not key:
            key = 'tmp_key'
        self._config = {key: os.path.split(morphology)[1]}
    
    def set_config(self, conf):
        self._config = conf
        
    def get_morphology(self):
        return self._morphology

    def get_config(self):
        return self._config

    def get_config_key(self):
        with open(self._config, 'r') as fd:
            jj = json.load(fd)
        return jj.keys()[0]

    def get_raw_status(self):
        return {
            'morphology': self._MORPHOLOGY
        }

    def get_status(self):
        return {
            'morphology': '' if self._MORPHOLOGY else '"morphology" file NOT present'
        }


class ModelBase:

    def __init__(self, key, **kwargs):
        self._PARAMETERS = False
        self._MECHANISMS = False
        self._mechanisms = None
        self._parameters = None
        self._features = None
        self._morphology = None 
        self._key = key
        self.set_features(Features())
        self.set_morphology(Morphology())
        if 'features' in kwargs and kwargs['features']:
            self.set_features(features=kwargs['features'])
        if 'morphology' in kwargs and kwargs['morphology']:
            self.set_morphology(kwargs['morphology'])
        if 'protocols' in kwargs and kwargs['protocols']:
            self.set_protocols(protocols=kwargs['protocols'])
        if 'parameters' in kwargs and kwargs['parameters']:
            self.set_parameters(kwargs['parameters'])
        if 'mechanisms' in kwargs and kwargs['mechanisms']:
            self.set_mechanisms(kwargs['mechanisms'])

    @dispatch(Features)
    def set_features(self, features):
        self._features = features

    @dispatch(str, str)
    def set_features(self, features, protocols):
        self._features.set_features(features)
        self._protocols.set_protocols(protocols)

    def set_morphology(self, morphology):
        if type(morphology) == Morphology:
            self._morphology = morphology
        else:
            self._morphology = Morphology(morphology)

    def set_mechanisms(self, mechanisms):
        if type(mechanisms) == list:
            self._mechanisms = mechanisms
        if type(mechanisms) == str:
            if os.path.isdir(mechanisms):
                self._mechanisms = [
                    os.path.join(mechanisms, m) for m in os.listdir(mechanisms)
                ]
            else:
                self._mechanisms = mechanisms
        for m in self._mechanisms:
            if not os.path.exists(m):
                raise FileNotFoundError('%s not found' % m)
            if not os.path.isfile(m):
                raise IsADirectoryError('%s is a directory' % m)
        if not self._mechanisms:
            self._MECHANISMS = False
        else:
            self._MECHANISMS = True

    def set_parameters(self, parameters):
        if not os.path.exists(parameters):
            raise FileNotFoundError('%s not found' % parameters)
        self._parameters = parameters
        self._PARAMETERS = True

    def set_key(self, key):
        self._key = key

    def get_features(self):
        return self._features

    def get_mechanisms(self):
        return self._mechansisms

    def get_parameters(self):
        return self._parameters

    def get_morphology(self):
        return self._morphology

    def get_key(self):
        return self._key
