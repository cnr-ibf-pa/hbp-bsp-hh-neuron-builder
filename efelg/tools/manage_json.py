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
    sampling_rate, tonoff, traces, volt_unit, amp_unit = get_traces_info(filename, upload_flag)
    
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
        'traces': traces,
        'tonoff': tonoff,
        'sampling_rate': sampling_rate,
        'contributors': {'name':"", 'message':""}
    }
    
    return obj

# extract cell info from the metadata file
def get_cell_info(filename, upload_flag=False):
    if upload_flag:
        c_species = "cellSpecies"
        c_area = "cellArea"
        c_region = "cellRegion"
        c_type = "cellType"
        c_etype = "cellEtype"
        c_name = "cellName"
        c_sample = os.path.splitext(os.path.basename(filename))[0]
    else:
        with open(filename) as f:
            data = json.load(f)
        if "animal_species" not in data or "animal_species" is None:
            c_species = "unknown"
        else:
            c_species = data["animal_species"]
            c_species = c_species.replace(" ", "-")
            #c_species = c_species.replace("_", "-")

        if "brain_structure" not in data or "brain_structure" is None:
            c_area = "unknown"
        else:
            c_area = data["brain_structure"]
            c_area = c_area.replace(" ", "-")
            #c_area = c_area.replace("_", "-")

        if "cell_soma_location" not in data or "cell_soma_location" is None:
            c_region = "unknown"
        else:
            c_region = data["cell_soma_location"]
            c_region = c_region.replace(" ", "-")
            #c_region = c_region.replace("_", "-")

        if "cell_type" not in data or "cell_type" is None:
            c_type = "unknown"
        else:
            c_type = data["cell_type"]
            c_type = c_type.replace(" ", "-")
            #c_type = c_type.replace("_", "-")

        if "etype" not in data or "etype" is None:
            c_etype = "unknown"
        else:
            c_etype = data["etype"]
            c_etype = c_etype.replace(" ", "-")
            #c_etype = c_etype.replace("_", "-")

        if "cell_id" not in data or "cell_id" is None:
            c_name = "unknown"
        else:
            c_name = data["cell_id"]
            c_name = c_name.replace(" ", "-")
            #c_name = c_name.replace("_", "-")

        if "filename" not in data or "filename" is None: 
            c_sample = "unknown"
        else:
            c_sample = data["filename"]
            c_sample = os.path.splitext(c_sample)[0]
            c_sample = c_sample.replace(" ", "-")
            #c_sample = c_sample.replace("_", "-")

    return (c_species, c_area, c_region, c_type, c_etype, c_name, c_sample) 

# extract data info (i.e. voltage trace, stimulus and stimulus unit) from experimental and metadata files
def get_traces_info(filename, upload_flag = False):
    
    #
    data = neo.io.AxonIO(filename)
    segments = data.read_block(lazy=False, cascade=True).segments
    header = data.read_header() # read file header
    sampling_rate = 1.e6 / header['protocol']['fADCSequenceInterval'] # read sampling rate

    volt_unit = segments[0].analogsignals[0].units
    volt_unit = str(volt_unit.dimensionality)

    if not upload_flag:
        crr_dict = get_metadata(filename)
        stim_res = stimulus_extraction.stim_feats_from_meta(crr_dict, len(segments))
        if not stim_res[0]:
            stim_res = stimulus_extraction.stim_feats_from_header(data.read_header())
        if not stim_res[0]:
            return 0
        stim = stim_res[1]
    else:
        stim_res = stimulus_extraction.stim_feats_from_header(data.read_header())
        stim = stim_res[1]
    
    #amp_unit = str(crr_dict['stimulus_unit'])
    amp_unit = stim[0][-1]
   
    traces = {}
    tonoff = {}
    for i, signal in enumerate(segments):
        voltage = np.array(signal.analogsignals[0]).astype(np.float64)
        stimulus = stim[i][3]
        label = "{0:.2f}".format(np.around(stimulus, decimals=3))
        traces.update({label: voltage.tolist()})
        tonoff.update({label: {'ton': [stim[i][1]], 'toff': [stim[i][2]]}})

    return (sampling_rate, tonoff, traces, volt_unit, amp_unit)


# read metadata file into a json dictionary
def get_metadata(filename):
    filepath, name = os.path.split(filename)
    name_no_ext, extension = os.path.splitext(name)
    metadata_file = os.path.join(filepath, name_no_ext + '_metadata.json')

    with open(metadata_file) as f:
        data = json.load(f)

    return data


# extract authorized collab from metadata file
def extract_authorized_collab(metadata_file):
    with open(metadata_file) as meta:
        all_meta = json.load(meta)
    
    return all_meta['authorized_collabs']


# generate json output from all authorized user traces
def generate_json_output(authorized_list, source_dir):
    output_file = {"Contributors": {}}

    for i in authorized_list:
        file_name = i + '.json'
        with open(os.path.join(source_dir, file_name), 'r') as f:
            json_file = json.load(f)

        contributor = json_file["contributors"]["name"]
        specie = json_file["species"]
        structure = json_file["area"]
        region = json_file["region"]
        cell_type = json_file["type"]
        etype = json_file["etype"]
        cell_id = json_file["name"]
        filename = file_name

        if contributor not in output_file["Contributors"]:
            output_file["Contributors"][contributor] = {}

        if specie not in output_file["Contributors"][contributor]:
            output_file["Contributors"][contributor][specie] = {}

        if structure not in output_file["Contributors"][contributor][specie]:
            output_file["Contributors"][contributor][specie][structure] = {}

        if region not in output_file["Contributors"][contributor][specie][structure]:
            output_file["Contributors"][contributor][specie][structure][region] = {}

        if cell_type not in output_file["Contributors"][contributor][specie][structure][region]:
            output_file["Contributors"][contributor][specie][structure][region][cell_type] = {}

        if etype not in output_file["Contributors"][contributor][specie][structure][region][cell_type]:
            output_file["Contributors"][contributor][specie][structure][region][cell_type][etype] = {}

        if cell_id not in output_file["Contributors"][contributor][specie][structure][region][cell_type][etype]:
            output_file["Contributors"][contributor][specie][structure][region][cell_type][etype][cell_id] = {}

	if len(output_file["Contributors"][contributor][specie][structure][region][cell_type][etype][cell_id]) == 0:
            output_file["Contributors"][contributor][specie][structure][region][cell_type][etype][cell_id] = [filename]

        elif i not in output_file["Contributors"][contributor][specie][structure][region][cell_type][etype][cell_id]:
            output_file["Contributors"][contributor][specie][structure][region][cell_type][etype][cell_id].append(filename)

    return output_file
