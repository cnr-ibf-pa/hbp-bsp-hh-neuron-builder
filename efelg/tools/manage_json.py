import os
import neo
import json
import hashlib
import numpy as np
import quantities as pq
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


def get_traces_abf(filename):

    data = neo.io.AxonIO(filename)
    metadata = get_metadata(filename)
   
    bl = data.read_block()
    segments = bl.segments
    data._parse_header()
    header = data._axon_info
    
    stim_res = stimulus_extraction.stim_feats_from_meta(metadata, len(segments))
    if not stim_res[0]:
        stim_res = stimulus_extraction.stim_feats_from_header(header)
    if not stim_res[0]:
        return 0
    stim = stim_res[1]
    
    volt_unit = str(segments[0].analogsignals[0].units.dimensionality)    
    amp_unit = stim[0][-1]

    if "sampling_rate" not in metadata:
        sampling_rate = "unknown"
    else:
        sampling_rate = str(metadata["sampling_rate"][0])
   
    # build dictionaries 
    traces = {}
    tonoff = {}

    for i, signal in enumerate(segments):
        # signal conversion to mV
        if not (signal.analogsignals[0].units == pq.mV):
            signal.analogsignals[0].units = pq.mV
        voltage = np.array(signal.analogsignals[0]).astype(np.float64)
        voltage = [k[0] for k in voltage]
        stimulus = stim[i][3]
        label = "{0:.2f}".format(np.around(stimulus, decimals=3))
        traces.update({label: voltage})
        tonoff.update({label: {'ton': [stim[i][1]], 'toff': [stim[i][2]]}})

    return sampling_rate, tonoff, traces, volt_unit, amp_unit


# read metadata file into a json dictionary
def get_metadata(filename):
    filepath, name = os.path.split(filename)
    name_no_ext, extension = os.path.splitext(name)
    metadata_file = os.path.join(filepath, name_no_ext + '_metadata.json')

    with open(metadata_file) as f:
        data = json.load(f)

    return data


# perform units conversions
def perform_conversions_json(data):
    print('========================= PERFORM CONVERSION =======================')
    if ("stimulus_unit" in data) and (not data["stimulus_unit"].lower() in ["na", "unknown"]):
        a_pow = 1
        stimlus_unit = data["stimulus_unit"].lower()
        if stimlus_unit == "a":
            a_pow = 9
        elif stimlus_unit == "ma":
            a_pow = 6
        elif stimlus_unit == "ua":
            a_pow = 3
        elif stimlus_unit == "pa":
            a_pow = -3
        
        temp = dict()
        for key in data["traces"]:
            temp[str(round(float(key) * pow(10, a_pow), 3))] = data["traces"][key]
        data["traces"] = temp.copy()
        temp.clear()
        for key in data["tonoff"]:
            temp[str(round(float(key) * pow(10, a_pow), 3))] = data["tonoff"][key]
        data["tonoff"] = temp.copy()
        temp.clear()
        data["stimulus_unit"] = "nA"
        if "stimulus_increment" in data:
            data["stimulus_increment"] = [value * pow(10, a_pow) for value in data["stimulus_increment"]]
        if "stimulus_first_amplitude" in data:
            data["stimulus_first_amplitude"] = [value * pow(10, a_pow) for value in data["stimulus_first_amplitude"]]
    
    if ("voltage_unit" in data) and (not data["voltage_unit"].lower() in ["mv", "unknown"]):
        v_pow = 1
        if data["voltage_unit"].lower() == "v":
            v_pow = 3

        temp = dict()
        for key in data["traces"]:
            temp[key] = [float(value) * pow(10, v_pow) for value in data["traces"][key]]
        data["traces"] = temp.copy()
        temp.clear()
        data["voltage_unit"] = "mV"

    if ("sampling_rate_unit" in data) and (not data["sampling_rate_unit"].lower() in ["hz", "unknown"]):
        if data["sampling_rate_unit"].lower() == "khz":
            data["sampling_rate"] = [value * pow(10, 3) for value in data["sampling_rate"]]
        data["sampling_rate_unit"] = "Hz"


def extract_data(filepath, metadata_dict=None):
    if filepath.endswith(".abf"):
        sampling_rate, tonoff, traces, voltage_unit, stimulus_unit = get_traces_abf(filepath)
        data = {
            'abfpath': filepath,
            'md5': md5(filepath),
            'voltage_unit': voltage_unit,
            'stimulus_unit': stimulus_unit,
            'traces': traces,
            'tonoff': tonoff,
            'sampling_rate': sampling_rate
        }
    elif filepath.endswith(".json"):
        with open(filepath, "r") as f:
            data = json.load(f)
    
    new_keys = {
        "type": "cell_type",
        "name": "cell_id",
        "area": "brain_structure",
        "sample": "filename",
        "species": "animal_species",
        "region": "cell_soma_location",
        "amp_unit": "stimulus_unit",
        "volt_unit": "voltage_unit",
        "v_unit": "voltage_unit"
    }

    # update dictionary keys
    for key in new_keys:
        if key in data:
            if not new_keys[key] in data:
                data[new_keys[key]] = data[key]
            data.pop(key)
        if not new_keys[key] in data:
            data[new_keys[key]] = "unknown"

    if "contributors" in data:
        if "name" in data["contributors"]:
            if not 'contributors_affiliations' in data:
                data['contributors_affiliations'] = data['contributors']['name']
    if not 'contributors_affiliations' in data:
        data['contributors_affiliations'] = 'unknown'

    perform_conversions_json(data)

    filename = os.path.basename(filepath)
    data["filename"] = filename[:filename.index(".")]

    if metadata_dict:
       update_file_name(data, metadata_dict)
   
    return data


def create_file_name(data):
    filename_keys = [
        "animal_species", "brain_structure", "cell_soma_location", "cell_type", "etype", "cell_id", "filename"
    ]
    return '____'.join([data[key] for key in filename_keys]) + ".json"


def update_file_name(data, metadata_dict):
    data["cell_id"] = metadata_dict["cell_name"]
    data["contributors_affiliations"] = metadata_dict["contributors"]
    data["animal_species"] = metadata_dict["species"]
    data["brain_structure"] = metadata_dict["structure"]
    data["cell_soma_location"] = metadata_dict["region"]
    data["cell_type"] = metadata_dict["type"]
    data["etype"] = metadata_dict["etype"]
