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

    @classmethod
    def from_dir(cls, directory):
        f = cls()
        for fd in os.listdir(directory):
            if fd == 'features.json':
                f.set_features(os.path.join(directory, fd))
            if fd == 'protocols.json':
                f.set_protocols(os.path.join(directory, fd))
        return f


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

    def __init__(self, morphology=None, config=None, conf_key=None):
        self._MORPHOLOGY = False
        self._morphology = None
        self._config = None
        if morphology:
            self.set_morphology(morphology)
        if config:
            self.set_config(config)
            if conf_key:
                self.make_config(conf_key)
            else:
                self.make_config('tmp_key')

    def __str__(self):
        print('<class Morphology:')
        print(f'\tmorphology: {self._morphology}',
              f'\tconf: {self._config}',
              '>', sep='\n')

    @classmethod
    def from_dir(cls, morph_dir, conf_key=None):
        if not os.path.exists(morph_dir):
            raise FileNotFoundError('%s not found' % morph_dir)
        if not os.path.isdir(morph_dir):
            raise NotADirectoryError('%s is not a directory' % morph_dir)
        if len(os.listdir(morph_dir)) != 1:
            return cls()
            # raise InvalidMorphologyDirectory('%d morphology directory must \
            #                                  contain a single morphology file')
        morph = os.path.join(morph_dir, os.listdir(morph_dir)[0])
        return cls(morph, conf_key=conf_key)


    def set_morphology(self, morphology):
        if not os.path.exists(morphology):
            raise FileNotFoundError('%s not found' % morphology)
        if not os.path.isfile(morphology):
            raise IsADirectoryError('%s is a directory' % morphology)
        self._morphology = morphology
        self.make_config('tmp_key')
        self._MORPHOLOGY = True

    def set_config(self, config):
        if not os.path.exists(config):
            raise FileNotFoundError('%s file not found' % config)
        if not os.path.split(config)[1] == 'morph.json':
            raise NoMorphologyConfig('%s is not a valid configuration' % config)
        with open(config, 'r') as fd:
            jj = json.load(fd)
        jj_key = jj.keys()
        if len(jj_key) != 1:
            raise MorphologyConfigError('%s config is wrong' % config)
        if jj[list(jj_key)[0]] != os.path.split(self._morphology)[1]:
            raise MorphologyConfigError('%s contain wrong morphology value' % config)
        self._config = config

    def make_config(self, conf_key):
        self._config = {
            conf_key: os.path.split(self._morphology)[1]
        }

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
        self._MORPHOLOGY = False
        self._MECHANISMS = False
        self._key = key
        if 'features' in kwargs and kwargs['features']:
            self.set_features(features=kwargs['features'])
        if 'protocols' in kwargs and kwargs['protocols']:
            self.set_protocols(protocols=kwargs['protocols'])
        if 'parameters' in kwargs and kwargs['parameters']:
            self.set_parameters(kwargs['parameters'])
        if 'morphology' in kwargs and kwargs['morphology']:
            self.set_morphology(kwargs['morphology'])
        if 'mechanisms' in kwargs and kwargs['mechanisms']:
            self.set_mechanisms(kwargs['mechanisms'])

    def set_features(self, features=None, protocols=None):
        if features:
            if type(features) == Features:
                self._features = features
            elif type(features) == str:
                self._features.set_features(features)
        if protocols:
            if type(protocols) == str:
                self._features.set_protocols(protocols)                                    
        
    def set_morphology(self, morphology, conf=None, conf_key=None):
        if type(morphology) == Morphology:
            self._morphology = morphology
        elif type(morphology) == str:
            if not conf_key:
                conf_key = self._key
            self._morphology = Morphology(morphology, conf, conf_key)
        self._MORPHOLOGY = True         

    def set_mechanisms(self, mechansisms):
        if type(mechansisms) == str:
            mods = [os.path.join(mechansisms, m) for m in os.listdir(mechansisms)]
        elif type(mechansisms) == list:
            mods = mechansisms
        for m in mods:
            if not os.path.exists(m):
                raise FileNotFoundError('%s not found' % m)
            if not os.path.isfile(m):
                raise IsADirectoryError('%s is a directory' % m)
        self._mechansisms = mods
        if not self._mechansisms:
            self._mechansisms = False
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
