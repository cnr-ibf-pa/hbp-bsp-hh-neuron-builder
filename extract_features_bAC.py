from neo import io
import matplotlib
matplotlib.use('Agg', warn=True)
import matplotlib.pyplot as plt
import numpy
import sys
import efel
#import igorpy
import os
import fnmatch
import json
import pprint
try:
    import cPickle as pickle
except:
    import pickle

import bluepyextract as bpext

import logging
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

with open('config.json') as json_file:
    config = json.load(json_file)
extractor = bpext.Extractor('bAC', config)

extractor.create_dataset()
extractor.plt_traces()

extractor.extract_features()
extractor.mean_features()
#extractor.plt_features()

extractor.feature_config_cells()
extractor.feature_config_all()
