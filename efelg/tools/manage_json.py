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
    stim = stim_res[1]


    """
    # extract stimulus
    if upload_flag
        
    else:
        if not stim_res[0]:
            stim_res = stimulus_extraction.stim_feats_from_header(header)
        if not stim_res[0]:
            return 0
        stim = stim_res[1]
    """
    
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
def perform_conversions_json(filename):
    with open(filename, "r") as input_file:

        data = json.load(input_file)

        #if ("stimulus_unit" in metadata) and (not metadata["stimulus_unit"].lower() in ["na", "unknown"]):
        if ("amp_unit" in data) and (not data["amp_unit"].lower() in ["na", "unknown"]):
            a_pow = 1
            if data["amp_unit"].lower() == "a":
                a_pow = 9
            elif data["amp_unit"].lower() == "ma":
                a_pow = 6
            elif data["amp_unit"].lower() == "ua":
                a_pow = 3
            elif data["amp_unit"].lower() == "pa":
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
            data["stimulus_increment"] = [value * pow(10, a_pow) for value in data["stimulus_increment"]]
            data["stimulus_first_amplitude"] = [value * pow(10, a_pow) for value in data["stimulus_first_amplitude"]]
            data["amp_unit"] = "nA"
        
        if ("volt_unit" in data) and (not data["volt_unit"].lower() in ["mv", "unknown"]):
            v_pow = 1
            if data["volt_unit"].lower() == "v":
                v_pow = 3

            temp = dict()
            for key in data["traces"]:
                temp[key] = [float(value) * pow(10, v_pow) for value in data["traces"][key]]
            data["traces"] = temp.copy()
            temp.clear()
            data["volt_unit"] = "mV"

        if ("sampling_rate_unit" in data) and (not data["sampling_rate_unit"].lower() in ["hz", "unknown"]):
            if data["sampling_rate_unit"].lower() == "khz":
                data["sampling_rate"] = [value * pow(10, 3) for value in data["sampling_rate"]]
            data["sampling_rate_unit"] = "Hz"

        return data


def extract_data(filepath, metadata_dict=None):

    if filepath.endswith(".abf"):
        sampling_rate, tonoff, traces, volt_unit, amp_unit = get_traces_abf(filepath)
        data = {
            'abfpath': filepath,
            'md5': md5(filepath),
            'volt_unit': volt_unit,
            'amp_unit': amp_unit,
            'traces': traces,
            'tonoff': tonoff,
            'sampling_rate': sampling_rate
        }
    elif filepath.endswith(".json"):
        with open(filepath, "r") as f:
            data = json.load(f)

    filename = os.path.basename(filepath)
    data["filename"] = filename[:filename.index(".")]

    if metadata_dict:
        update_file_name(data, metadata_dict)
    
    #data = perform_conversion_json(data)
    
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