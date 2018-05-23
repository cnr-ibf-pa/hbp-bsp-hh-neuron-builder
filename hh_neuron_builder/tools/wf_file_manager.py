import io
import json
import os
import requests
import xml.etree.ElementTree
import time
import sys
import zipfile
import shutil
from shutil import copy2
import collections
import re

class CheckConditions:
    @classmethod
    def checkSimFiles(cls, sim_path=""):                                           
        sim_name = ''
        list_dir = os.listdir(sim_path) 
        for i in list_dir:
            if i.endswith('.zip'):
                sim_name = os.path.splitext(i)[0]
                break
        if sim_name == "":
            resp = {"response":"KO", "message":"NO simulation .zip file or NO \
                    correct output from optimization"}
            return resp

        check_folder = os.path.join(sim_path, sim_name, 'checkpoints')
        mec_folder = os.path.join(sim_path, sim_name, 'mechanisms')
        morph_folder = os.path.join(sim_path, sim_name, 'morphology')

        if not os.path.isdir(check_folder):
            resp = {"response":"KO", "message":"'checkpoints' folder NOT present"}
            return resp
        
        if not os.path.isdir(morph_folder):
            resp = {"response":"KO", "message":"'morphology' folder NOT present"}
            return resp
        elif not os.listdir(morph_folder):
            resp = {"response":"KO", "message":"The folder 'morphology' is \
                    empty"}
            return resp
        
        if not os.path.isdir(mec_folder):
            resp = {"response":"KO", "message":"'mechanisms' folder NOT present"}
            return resp
        else:
            mec_list_dir = os.listdir(mec_folder)
            list_mod = [i for i in mec_list_dir if i.endswith('.mod')] 
            if not list_mod:
                resp = {"response":"KO", "message":"The folder 'mechanisms'\
                        does NOT contain any .mod file'"}
                return resp
        
        if not os.path.isfile(os.path.join(check_folder, 'cell.hoc')) \
                and not (os.path.isfile(os.path.join(sim_path, \
                'template.hoc'))):
            resp = {"response":"KO", "message":"Neither 'cell.hoc' nor \
                            'template.hoc' file present in the final simulation \
                            folder"}
            return resp
        
        # if all conditions are met
        resp = {"response":"OK", "message":"All needed files are present"}
        return resp

class FetchFiles:
    @classmethod
    def fetchOptSetFile(cls, opt_set_file_path=""):
        if os.path.isfile(opt_set_file_path):
            with open(opt_set_file_path) as pf:
                opt_set = json.load(pf)
                pf.close()
            opt_set_dict = {
                    "status":"OK", \
                    "hpc_sys": opt_set["hpc_sys"], \
                    "gennum": opt_set["number_of_generations"], \
                    "offsize": opt_set["offspring_size"], \
                    "nodenum": opt_set["number_of_nodes"], \
                    "corenum": opt_set["number_of_cores"], \
                    "runtime": opt_set["runtime"], \
                    "wf_id": opt_set["wf_id"], \
                    }
        else:
            opt_set_dict = {"status":"KO"}

        return opt_set_dict
