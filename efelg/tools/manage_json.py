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


# generate data structure containing data and metadata
"""
def gen_data_struct(filename, filename_meta, upload_flag= False):
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
        'contributors': {'name': '', 'message': ''}
    }
    
    return obj
"""

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


# extract cell info from the metadata file
"""
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
            # c_species = c_species.replace("_", "-")

        if "brain_structure" not in data or "brain_structure" is None:
            c_area = "unknown"
        else:
            c_area = data["brain_structure"]
            c_area = c_area.replace(" ", "-")
            # c_area = c_area.replace("_", "-")

        if "cell_soma_location" not in data or "cell_soma_location" is None:
            c_region = "unknown"
        else:
            c_region = data["cell_soma_location"]
            c_region = c_region.replace(" ", "-")
            # c_region = c_region.replace("_", "-")

        if "cell_type" not in data or "cell_type" is None:
            c_type = "unknown"
        else:
            c_type = data["cell_type"]
            c_type = c_type.replace(" ", "-")
            # c_type = c_type.replace("_", "-")

        if "etype" not in data or "etype" is None:
            c_etype = "unknown"
        else:
            c_etype = data["etype"]
            c_etype = c_etype.replace(" ", "-")
            # c_etype = c_etype.replace("_", "-")

        if "cell_id" not in data or "cell_id" is None:
            c_name = "unknown"
        else:
            c_name = data["cell_id"]
            c_name = c_name.replace(" ", "-")
            # c_name = c_name.replace("_", "-")

        if "filename" not in data or "filename" is None: 
            c_sample = "unknown"
        else:
            c_sample = data["filename"]
            c_sample = os.path.splitext(c_sample)[0]
            c_sample = c_sample.replace(" ", "-")
            # c_sample = c_sample.replace("_", "-")

    return c_species, c_area, c_region, c_type, c_etype, c_name, c_sample
"""

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
"""
def get_traces_info(filename, upload_flag = False):
    
    #
    data = neo.io.AxonIO(filename)
    bl = data.read_block()
    segments = bl.segments
    data._parse_header()
    header = data._axon_info
    sampling_rate = 1.e6 / header['protocol']['fADCSequenceInterval']  # read sampling rate

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
        stim_res = stimulus_extraction.stim_feats_from_header(header)
        stim = stim_res[1]
    
    amp_unit = stim[0][-1]
   
    # build dictionaries 
    traces = {}
    tonoff = {}
    for i, signal in enumerate(segments):
        voltage = np.array(signal.analogsignals[0]).astype(np.float64)
        voltage = [k[0] for k in voltage]
        stimulus = stim[i][3]
        label = "{0:.2f}".format(np.around(stimulus, decimals=3))
        traces.update({label: voltage})
        tonoff.update({label: {'ton': [stim[i][1]], 'toff': [stim[i][2]]}})

    return sampling_rate, tonoff, traces, volt_unit, amp_unit
"""

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


# generate json output from all authorized user traces
def generate_json_output(authorized_list, source_dir):
    output_file = {"Contributors": {}}

    for i in authorized_list:
        file_name = i + '.json'
        with open(os.path.join(source_dir, file_name), 'r') as f:
            json_file = json.load(f)

        if "contributors_affiliations" in json_file:
            contributor = json_file["contributors_affiliations"]
        elif "name" in json_file["contributors"]:
            contributor = json_file["contributors"]["name"]
        else:
            raise Exception("contributors_affiliations not found!")

        if "animal_species" in json_file:
            specie = json_file["animal_species"]
        elif "species" in json_file:
            specie = json_file["species"]
        else:
            raise Exception("animal_species not found!")

        if "brain_structure" in json_file:
            structure = json_file["brain_structure"]
        elif "area" in json_file:
            structure = json_file["area"]
        else:
            raise Exception("brain_structure not found!")

        if "cell_soma_location" in json_file:
            region = json_file["cell_soma_location"]
        elif "region" in json_file:
            region = json_file["region"]
        else:
            raise Exception("cell_soma_location not found!")

        if "cell_id" in json_file:
            cell_id = json_file["cell_id"]
        elif "name" in json_file:
            cell_id = json_file["name"]
        else:
            raise Exception("cell_id not found!")

        cell_type = json_file["type"]
        etype = json_file["etype"]
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


def extract_data(name, dict):
    if name.endswith(".abf"):
        metadata = name[:-4] + "_metadata.json"
        data = gen_data_struct(name, metadata, upload_flag=True)
    elif name.endswith(".json"):
        data = perform_conversions_json_file(name)
    
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


def create_file_name(data):
    filename_keys = ["animal_species", "brain_structure", "cell_soma_location", "type", "etype", "cell_id"]
    if "filename" in data.keys():
        filename_keys.append("filename")
    elif "sample" in data.keys():
        filename_keys.append("sample")
    else:
        raise Exception("filename not found!")
    return '____'.join([data[key] for key in filename_keys]) + ".json"
