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


def gen_data_struct(filename, filename_meta, upload_flag= False):
    sampling_rate, tonoff, traces, volt_unit, amp_unit = get_traces_info(filename, upload_flag)
    obj = {
        'abfpath': filename,
        'md5': md5(filename),
        'sample': os.path.splitext(os.path.basename(filename))[0],
        'volt_unit': volt_unit,
        'amp_unit': amp_unit,
        'traces': traces,
        'tonoff': tonoff,
        'sampling_rate': sampling_rate,
        'contributors': {'message': ''}
    }    
    return obj


def get_cell_info(filename, upload_flag=False, cell_name="cellName"):
    with open(filename, "r") as f:
        metadata = json.load(f)
    if upload_flag:
        c_species = "cellSpecies"
        c_area = "cellArea"
        c_region = "cellRegion"
        c_type = "cellType"
        c_etype = "cellEtype"
        c_name = cell_name
        c_sample = os.path.splitext(os.path.basename(filename))[0]
    else:
        with open(filename) as f:
            data = json.load(f)
        if "animal_species" not in data:
            c_species = "unknown"
        else:
            c_species = data["animal_species"]
            c_species = c_species.replace(" ", "-")
            # c_species = c_species.replace("_", "-")

        if "brain_structure" not in data:
            c_area = "unknown"
        else:
            c_area = data["brain_structure"]
            c_area = c_area.replace(" ", "-")
            # c_area = c_area.replace("_", "-")

        if "cell_soma_location" not in data:
            c_region = "unknown"
        else:
            c_region = data["cell_soma_location"]
            c_region = c_region.replace(" ", "-")
            # c_region = c_region.replace("_", "-")

        if "cell_type" not in data:
            c_type = "unknown"
        else:
            c_type = data["cell_type"]
            c_type = c_type.replace(" ", "-")
            # c_type = c_type.replace("_", "-")

        if "etype" not in data:
            c_etype = "unknown"
        else:
            c_etype = data["etype"]
            c_etype = c_etype.replace(" ", "-")
            # c_etype = c_etype.replace("_", "-")

        if "cell_id" not in data:
            c_name = "unknown"
        else:
            c_name = data["cell_id"]
            c_name = c_name.replace(" ", "-")
            # c_name = c_name.replace("_", "-")

        if "filename" not in data: 
            c_sample = "unknown"
        else:
            c_sample = data["filename"]
            c_sample = os.path.splitext(c_sample)[0]
            c_sample = c_sample.replace(" ", "-")
            # c_sample = c_sample.replace("_", "-")
        
        if "cell_id" not in data:
            c_name = "unknown"
        else:
            c_name = data["cell_id"]
            c_name = c_name.replace(" ", "-")
            # c_name = c_name.replace("_", "-")
    return c_species, c_area, c_region, c_type, c_etype, c_name, c_sample

# extract data info (i.e. voltage trace, stimulus and stimulus unit) from experimental and metadata files

def get_traces_info(filename, upload_flag = False):

    if (filename.endswith(".json")):
        with open(filename) as json_file:
            data = json.load(json_file)
            metadata = data
    elif (filename.endswith(".abf")):
        data = neo.io.AxonIO(filename)
        metadata = get_metadata(filename)
   
    bl = data.read_block()
    segments = bl.segments
    data._parse_header()
    header = data._axon_info
    # sampling_rate = 1.e6 / header['protocol']['fADCSequenceInterval']  # read sampling rate
    a_pow = 1
    if upload_flag:
        if ("stimulus_unit" in metadata) and (not metadata["stimulus_unit"].lower() in ["na", "unknown"]):
            if metadata["stimulus_unit"].lower() == "a":
                a_pow = 9
            elif metadata["stimulus_unit"].lower() == "ma":
                a_pow = 6
            elif metadata["stimulus_unit"].lower() == "ua":
                a_pow = 3
            elif metadata["stimulus_unit"].lower() == "pa":
                a_pow = -3
            metadata["stimulus_increment"] = [value * pow(10, a_pow) for value in metadata["stimulus_increment"]]
            metadata["stimulus_first_amplitude"] = [value * pow(10, a_pow) for value in metadata["stimulus_first_amplitude"]]
            metadata["stimulus_unit"] = "nA"
        if ("sampling_rate_unit" in metadata) and (not metadata["sampling_rate_unit"].lower() in ["hz", "unknown"]):
            if metadata["sampling_rate_unit"].lower() == "khz":
                metadata["sampling_rate"] = [value * pow(10, 3) for value in metadata["sampling_rate"]]
            metadata["sampling_rate_unit"] = "Hz"
        
        if "sampling_rate" not in metadata:
            sampling_rate = "unknown"
        else:
            sampling_rate = str(metadata["sampling_rate"][0])

    #
    volt_unit = segments[0].analogsignals[0].units
    volt_unit = str(volt_unit.dimensionality)

    # extract stimulus
    if not upload_flag:
        crr_dict = get_metadata(filename)
        stim_res = stimulus_extraction.stim_feats_from_meta(crr_dict, len(segments))
        if not stim_res[0]:
            stim_res = stimulus_extraction.stim_feats_from_header(header)
        if not stim_res[0]:
            return 0
        stim = stim_res[1]
    else:
        #stim_res = stimulus_extraction.stim_feats_from_header(header)
        stim_res = stimulus_extraction.stim_feats_from_meta(metadata, len(segments))
        stim = stim_res[1]
    
    amp_unit = stim[0][-1]
   
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


# extract authorized collab from metadata file
def extract_authorized_collab(metadata_file):
    with open(metadata_file) as meta:
        all_meta = json.load(meta)
    
    return all_meta['authorized_collabs']


# perform units conversions
def perform_conversions_json_file(filename):
    with open(filename, "r") as input_file:

        data = json.load(input_file)

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

        return data


def extract_data(name, dict=None, metadata_dict=None, upload_flag=True):
    data = None
    if metadata_dict:
        data = metadata_dict
        data.update({'type': 'anonymous'})
    
    if name.endswith(".abf"):
        metadata = name[:-4] + "_metadata.json"
        if data:
            data.update(gen_data_struct(name, metadata, upload_flag=upload_flag))
        else:
            data = gen_data_struct(name, metadata, upload_flag=upload_flag)
    elif name.endswith(".json"):
        if data:
            data.update(perform_conversions_json_file(name))
        else:
            data = perform_conversions_json_file(name)
    
    if dict:
        filled_keys = {
            "cell_id": dict["cell_name"],
            "contributors_affiliations": dict["contributors"],
            "animal_species": dict["species"],
            "brain_structure": dict["structure"],
            "cell_soma_location": dict["region"],
            "type": dict["type"],
            "etype": dict["etype"]
        }

        for key in filled_keys:
            data[key] = filled_keys[key]
    

    return data


def create_file_name(data, cell_id=None):
    filename_keys = ["animal_species", "brain_structure", "cell_soma_location", "type", "etype", "cell_id"]
    if "filename" in data.keys():
        filename_keys.append("filename")
    elif "sample" in data.keys():
        filename_keys.append("sample")
    else:
        raise Exception("filename not found!")
    return '____'.join([data[key] for key in filename_keys]) + ".json"
