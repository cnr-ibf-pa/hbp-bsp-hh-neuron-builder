"""
This script is used to create a a metadata file for a etrace.
"""


import os
import json

# you need to specify these two paths in order to generate the file
path_to_traces = ""
destination_path = ""


dictionary = {"Contributors": {}}

for name in os.listdir(path_to_traces):
    with open(os.path.join(path_to_traces, name), "r") as f:
        content = json.load(f)

    contributor = content["contributors_affiliations"]
    specie = content["animal_species"]
    structure = content["brain_structure"]
    region = content["cell_soma_location"]
    cell_type = content["cell_type"]
    etype = content["etype"]
    cell_id = content["cell_id"]

    if contributor not in dictionary["Contributors"]:
        dictionary["Contributors"][contributor] = {}

    if specie not in dictionary["Contributors"][contributor]:
        dictionary["Contributors"][contributor][specie] = {}

    if structure not in dictionary["Contributors"][contributor][specie]:
        dictionary["Contributors"][contributor][specie][structure] = {}

    if region not in dictionary["Contributors"][contributor][specie][structure]:
        dictionary["Contributors"][contributor][specie][structure][region] = {}

    if cell_type not in dictionary["Contributors"][contributor][specie][structure][region]:
        dictionary["Contributors"][contributor][specie][structure][region][cell_type] = {}

    if etype not in dictionary["Contributors"][contributor][specie][structure][region][cell_type]:
        dictionary["Contributors"][contributor][specie][structure][region][cell_type][etype] = {}

    if cell_id not in dictionary["Contributors"][contributor][specie][structure][region][cell_type][etype]:
        dictionary["Contributors"][contributor][specie][structure][region][cell_type][etype][cell_id] = {}

    if len(dictionary["Contributors"][contributor][specie][structure][region][cell_type][etype][cell_id]) == 0:
        dictionary["Contributors"][contributor][specie][structure][region][cell_type][etype][cell_id] = [name]
    elif name not in dictionary["Contributors"][contributor][specie][structure][region][cell_type][etype][cell_id]:
        dictionary["Contributors"][contributor][specie][structure][region][cell_type][etype][cell_id].append(name)


with open(destination_path, "w") as output_file:
    json.dump(dictionary, output_file)
