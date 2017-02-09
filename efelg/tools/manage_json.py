from __future__ import print_function

import os
import re
import neo
import json
import hashlib
import numpy as np
import logging
from . import stimulus_extraction

logger = logging.getLogger(__name__)

# generate hash md5 code for the filename passed as parameter
def md5(filename):
    hash_md5 = hashlib.md5()
    
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# generate data strcuture containing data and metadata
def gen_data_struct(filename, filename_meta, upload_flag = False):
    c_species, c_area, c_region, c_type, c_etype, c_name, c_sample = get_cell_info(filename_meta, upload_flag)
    traces, volt_unit, amp_unit = get_traces_info(filename, upload_flag)
    
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

# extract cell info from the metadata file
def get_cell_info(filename, upload_flag=False):
    if upload_flag:
        c_species = "species"
        c_area = "area"
        c_region = "region"
        c_type = "type"
        c_etype = "etype"
        c_name = "name"
        c_sample = os.path.splitext(os.path.basename(filename))[0]
    else:
        with open(filename) as f:
            data = json.load(f)
        if "animal_species" not in data or "animal_species" is None:
            c_species = "unknown"
        else:
            c_species = data["animal_species"]
            c_species = c_species.replace(" ", "-")

        if "brain_structure" not in data or "brain_structure" is None:
            c_area = "unknown"
        else:
            c_area = data["brain_structure"]
            c_area = c_area.replace(" ", "-")

        if "cell_soma_location" not in data or "cell_soma_location" is None:
            c_region = "unknown"
        else:
            c_region = data["cell_soma_location"]
            c_region = c_region.replace(" ", "-")

        if "cell_type" not in data or "cell_type" is None:
            c_type = "unknown"
        else:
            c_type = data["cell_type"]
            c_type = c_type.replace(" ", "-")

        if "etype" not in data or "etype" is None:
            c_etype = "unknown"
        else:
            c_etype = data["etype"]
            c_etype = c_etype.replace(" ", "-")

        if "cell_id" not in data or "cell_id" is None:
            c_name = "unknown"
        else:
            c_name = data["cell_id"]
            c_name = c_name.replace(" ", "-")

        if "filename" not in data or "filename" is None: 
            c_sample = "unknown"
        else:
            c_sample = data["filename"]
            c_sample = os.path.splitext(c_sample)[0]
            c_sample = c_sample.replace(" ", "-")

    return (c_species, c_area, c_region, c_type, c_etype, c_name, c_sample) 

# extract data info (i.e. voltage trace, stimulus and stimulus unit) from experimental and metadata files
def get_traces_info(filename, upload_flag = False):
    
    #
    data = neo.io.AxonIO(filename)
    segments = data.read_block(lazy=False, cascade=True).segments

    volt_unit = segments[0].analogsignals[0].units
    volt_unit = str(volt_unit.dimensionality)

    if not upload_flag:
        crr_dict = get_metadata(filename)
        stim_res = stimulus_extraction.stim_feats_from_meta(crr_dict, len(segments))
        stim = stim_res[1]
    else:
        stim_res = stimulus_extraction.stim_feats_from_header(data.read_header())
        stim = stim_res[1]
    
    #amp_unit = str(crr_dict['stimulus_unit'])
    amp_unit = stim[0][-1]

    traces = {}
    for i, signal in enumerate(segments):
        voltage = np.array(signal.analogsignals[0]).astype(np.float64)
        voltage = voltage[::3]
        stimulus = stim[i][3]
        label = "{0:.2f}".format(np.around(stimulus, decimals=3))
        traces.update({label: voltage.tolist()})
        
    return (traces, volt_unit, amp_unit)


# read metadata file into a json dictionary
def get_metadata(filename):
    filepath, name = os.path.split(filename)
    name_no_ext, extension = os.path.splitext(name)
    metadata_file = os.path.join(filepath, name_no_ext + '_metadata.json')

    with open(metadata_file) as f:
        data = json.load(f)

    return data
