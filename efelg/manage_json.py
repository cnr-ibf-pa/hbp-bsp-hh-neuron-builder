from __future__ import print_function

import os
import re
import neo
import json
import hashlib
import numpy as np
import logging

logger = logging.getLogger(__name__)

def md5(filename):
    hash_md5 = hashlib.md5()
    
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def getCellInfo(filename, upload_flag=False):
    regex = '.*/(.+?)/(.+?)/(.+?)/(.+?)/(.+?)/(.+?)/(.+?)\.abf'
    pathanalyse = re.compile(regex)
    result = pathanalyse.match(filename)

    bn_ext = os.path.basename(filename)
    bn = os.path.splitext(bn_ext)[0]
    if upload_flag is True:
        c_species = 'udSp' 
        c_area = 'udSt'
        c_region = 'udRe'
        c_type = 'udTy'
        c_etype = 'udEt'
        c_name = 'udNm'
        c_sample = bn 
        return (c_species, c_area, c_region, c_type, c_etype, c_name, c_sample) 

    elif (result):
        c_species = result.group(1)
        c_area = result.group(2)
        c_region = result.group(3)
        c_type = result.group(4)
        c_etype = result.group(5)
        c_name = result.group(6).replace('_', '-')
        c_sample = result.group(7).replace('_', '-')
    
        return (c_species, c_area, c_region, c_type, c_etype, c_name, c_sample) 
    else:
        return ['' for i in range(6)]
            
def processSignal(signal):
    voltage = np.array(signal.analogsignals[0]).astype(np.float64)
    current = np.array(signal.analogsignals[1]).astype(np.float64)
    
    # when does voltage change
    c_changes = np.where( abs(np.gradient(current, 1.)) > 0.0 )[0]
    # detect on and off of current
    c_changes2 = np.where( abs(np.gradient(c_changes, 1.)) > 10.0 )[0]
    
    ion = c_changes[c_changes2[0]]
    ioff = c_changes[-1]
    
    # estimate hyperpolarization current
    hypamp = np.mean( current[0:ion] )
    
    # 10% distance to measure step current
    iborder = int((ioff-ion)*0.1)
    
    # depolarization amplitude
    amp = np.mean( current[ion+iborder:ioff-iborder] )
    
    # downsampling of the signal
    voltage = voltage[::3]
    
    return (amp, voltage.tolist())


def getTracesInfo(filename):
    data = neo.io.AxonIO(filename)
    segments = data.read_block(lazy=False, cascade=True).segments
    
    volt_unit = segments[0].analogsignals[0].units
    volt_unit = str(volt_unit.dimensionality)
    
    amp_unit = segments[0].analogsignals[1].units
    amp_unit = str(amp_unit.dimensionality)
    
    traces = {}
    for signals in segments:
        stimulus, trace = processSignal(signals)
        label = "{0:.2f}".format(np.around(stimulus, decimals=3))
        traces.update({label: trace})
        
    return (traces, volt_unit, amp_unit)
    
def genDataStruct(filename, upload_flag = False):
    logger.info("generating data struct with " + filename)
    if upload_flag:
        c_species, c_area, c_region, c_type, c_etype, c_name, c_sample = getCellInfo(filename, upload_flag)
        
    else:
        c_species, c_area, c_region, c_type, c_etype, c_name, c_sample = getCellInfo(filename)
    
    logger.info('gettracesinfofilename ' + filename)
    traces, volt_unit, amp_unit = getTracesInfo(filename)
    
    obj = {
        'abfpath': filename,
        'md5': md5(filename),
        'species': c_species,
        'area': c_area,
        'region': c_region,
        'type': c_type,
        'etype': c_etype,
        'name': c_name,
        'sample': c_sample,
        'volt_unit': volt_unit,
        'amp_unit': amp_unit,
        'traces': traces
    }
    
    return obj

