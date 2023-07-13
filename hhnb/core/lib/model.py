""" This package provide some useful classes and methods to easily handle a model instance. """

from .exception.model_exception import *

import os
import json


class Features:
    """
    An easy way to handle the features and protocols files.
    """

    def __init__(self, features=None, protocols=None):
        """
        Instantiate a Features object.

        Parameters
        ----------
        features : str, optional
                   the features file, by default is set to None
        protocols : str, optional
                    the protocols file, by default is set to None
        """
        self._FEATURES = False
        self._PROTOCOLS = False
        self._features = None
        self._protocols = None
        if features:
            self.set_features(features)
        if protocols:
            self.set_protocols(protocols)

    def __str__(self):
        """
        String representation of the Features instance.
        """
        return f'<Features (features: "{(self._FEATURES), (self._features)}", protocols: "{(self._PROTOCOLS), (self._protocols)}">'

    def set_features(self, features):
        """
        Set the features file.

        Parameters
        ----------
        features : str
            the features file path.

        Raises
        ------
        FileNotFoundError
            If the file is not found.
        IsADirectoryError
            If the path is pointing to a directory.
        """
        if not os.path.exists(features):
            raise FileNotFoundError('%s not found' % features)
        if not os.path.isfile(features):
            raise IsADirectoryError('%s is a directory' % features)
        self._features = features
        self._FEATURES = True

    def set_protocols(self, protocols):
        """
        Set the protocols file.

        Parameters
        ----------
        protocols : str
            the protocols file path.

        Raises
        ------
        FileNotFoundError
            if the file is not found.
        IsADirectoryError
            if the path is pointing a directory.
        """
        if not os.path.exists(protocols):
            raise FileNotFoundError('%s not found' % protocols)
        if not os.path.isfile(protocols):
            raise IsADirectoryError('%s is a directory' % protocols)
        self._protocols = protocols
        self._PROTOCOLS = True

    def get_features(self):
        """
        Returns the features file path.
        """
        return self._features

    def get_protocols(self):
        """
        Returns the protocols file path.
        """
        return self._protocols

    def get_raw_status(self):
        """
        Returns the instance status.
        """
        return {
            'features': self._FEATURES,
            'protocols': self._PROTOCOLS
        }

    def get_status(self):
        """
        Returns the instance status with a description message instead of a boolean value.
        """
        return {
            'features': '' if self._FEATURES else '"features.json" file NOT present',
            'protocols': '' if self._PROTOCOLS else '"protocols.json" file NOT present'
        }


class Morphology:
    """
    An easy way to handle the morphology of the model.
    """

    def __init__(self, morphology=None, key=None):
        """
        Instantiate a Morphology object.

        Parameters
        ----------
        morphology : str, optional
            the morphology file path, by default is set to None
        key : str, optional
            the model global key, by default is set to None
        """
        self._MORPHOLOGY = False
        self._morphology = None
        self._config = None
        if morphology:
            self.set_morphology(morphology)

    def __str__(self):
        """
        String representation of the Features instance.
        """
        return f'<Morphology (morphology: "{self._morphology}", conf: "{self._config}")>'

    def set_morphology(self, morphology, key=None):
        """
        Set the model morphology providing the file in ".asc" format
        and optionally the model global key to generate the morphology
        config file.

        Parameters
        ----------
        morphology : str
            the morphology file path. The morphology must be in ".asc" format.
        key : str, optional
            the model global key to generate the config file, if set to None
            a temporarily key will be used.

        Raises
        ------
        FileNotFoundError
            if the file is not found.
        IsADirectoryError
            if the path is pointing a directory.
        """
        if not os.path.exists(morphology):
            raise FileNotFoundError('%s not found.' % morphology)
        if not os.path.isfile(morphology):
            raise IsADirectoryError('%s is a directory.' % morphology)
        if not morphology.endswith('.asc'):
            raise InvalidMorphologyFile('%s is not ".asc" morphology format.' % morphology)

        self._morphology = morphology
        self._MORPHOLOGY = True
        if not key:
            key = 'tmp_key'
        self._config = {key: os.path.split(morphology)[1]}

    def set_config(self, conf):
        """
        Set a new config object for the current morphology.

        Parameters
        ----------
        conf : dict
            the conf object must have this form: "{'key': 'morph_name.asc'}".
        """
        self._config = conf

    def get_morphology(self):
        """ Returns the morphology file. """
        return self._morphology

    def get_config(self):
        """ Returns the config object. """
        return self._config

    def get_config_key(self):
        """ Get the config key. """
        with open(self._config, 'r') as fd:
            jj = json.load(fd)
        return jj.keys()[0]

    def get_raw_status(self):
        """ Returns the instance status. """
        return {
            'morphology': self._MORPHOLOGY
        }

    def get_status(self):
        """ Returns the instance status with a description message instead of a bool value. """
        return {
            'morphology': '' if self._MORPHOLOGY else '"morphology" file NOT present'
        }


class ModelBase:
    """
    A primitive version of the model class.
    Useful to set and get only the files that are required from the model.
    """

    def __init__(self, key, **kwargs):
        """
        Instantiate a Model object.
        The accepted kwargs can be: 'features', 'morphology',
        'protocols', 'mechanisms' and 'parameters'.

        Parameters
        ----------
        key : str
            set the model global key.
        """
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
            self.set_features(protocols=kwargs['protocols'])
        if 'parameters' in kwargs and kwargs['parameters']:
            self.set_parameters(kwargs['parameters'])
        if 'mechanisms' in kwargs and kwargs['mechanisms']:
            self.set_mechanisms(kwargs['mechanisms'])

    def set_features(self, *args, **kwargs):
        """
        Set the model features and protocols.
        This method accepts a unique Features instance as argument,
        or can be called by passing a "features" and/or "protocols" kwargs with the relative file

        Raises
        ------
        TypeError
            if the parameter(s) passed is(are) wrong.
        """
        if len(args) == 1:
            if type(args[0]) == Features:
                self._features = args[0]
            else:
                raise TypeError('set_features() takes Features object.')
        elif len(args) == 0:
            for k in kwargs.keys():
                if k != 'features' and k != 'protocols':
                    raise TypeError('set_features() got an unexpected\
                                     keyword argument %s' % k)
            if 'features' in kwargs.keys():
                self._features.set_features(kwargs['features'])
            if 'protocols' in kwargs.keys():
                self._features.set_protocols(kwargs['protocols'])
        else:
            raise TypeError('set_features() takes 1 position arguments')

    def set_morphology(self, morphology):
        """
        Set the model morphology. This method can be accept a Morphology instance or
        the morphology file path.

        Parameters
        ----------
        morphology : Morphology | str
            the morphology to be used.
        """
        if type(morphology) == Morphology:
            self._morphology = morphology
        else:
            self._morphology = Morphology(morphology)

    def set_mechanisms(self, mechanisms):
        """
        Set the mechanisms files for the model.
        The mechanisms file can be a list of file, a directory containing the mechanisms file or a list of files.

        Parameters
        ----------
        mechanisms : str | list
            the mechanism files for the model.

        Raises
        ------
        FileNotFoundError
            if a mechanism file is not found.
        IsADirectoryError
            if it tries to access a file but is a directory.
        """
        self._mechanisms = []

        if type(mechanisms) == list:
            self._mechanisms = mechanisms

        elif type(mechanisms) == str:
            if os.path.isdir(mechanisms):
                self._mechanisms = [
                    os.path.join(mechanisms, m) for m in os.listdir(mechanisms)
                ]
            else:
                self._mechanisms.append(mechanisms)

        for m in self._mechanisms:
            if not os.path.exists(m):
                raise FileNotFoundError('%s not found' % m)
            if not os.path.isfile(m):
                raise IsADirectoryError('%s is a directory' % m)
            if not m.endswith('.mod'):
                raise InvalidMechanismFile('%s is not a valid Mechanism file. \
                                           Only accept ".mod" extension.' % m)
        if not self._mechanisms:
            self._MECHANISMS = False
        else:
            self._MECHANISMS = True

    def set_parameters(self, parameters):
        """
        Set the parameter file used by the model.

        Parameters
        ----------
        parameters : str
            the parameter file path.

        Raises
        ------
        FileNotFoundError
            if the parameter file is not found.
        """
        if not os.path.exists(parameters):
            raise FileNotFoundError('%s not found' % parameters)
        self._parameters = parameters
        self._PARAMETERS = True

    def set_key(self, key):
        """ Set the global model key. """
        self._key = key

    def get_features(self):
        """ Get the Features instance used by the model. """
        return self._features

    def get_mechanisms(self):
        """ Get the mechanism file list. """
        return self._mechanisms

    def get_parameters(self):
        """ Get the parameters file path. """
        return self._parameters

    def get_morphology(self):
        """ Get the Morphology instance used by the model. """
        return self._morphology

    def get_key(self):
        """ Get the global model key. """
        return self._key
