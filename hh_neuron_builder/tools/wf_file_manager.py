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
    def checkUploadedModel(cls, file_path="", folder_path=""):
        '''
        Check that the uploaded model .zip file contains all necessary 
        files and folder
        '''

        if not file_path.endswith(".zip"):
            return {"KO", "The uploaded file is not a .zip file"}
        
        # unzip file
        zip_ref = zipfile.ZipFile(file_path, 'r')                           
        zip_ref.extractall(folder_path)
        zip_ref.close() 

        basename = os.path.basename(str(file_path))
        filename_noext = os.path.splitext(basename)
        opt_folder = os.path.join(folder_path, filename_noext[0])        
        if not os.path.exists(opt_folder):
            return {"KO", "The unzipped folder has not the same name as the \
                    .zip file. Please upload a well formatted .zip"}
        else:
            # check that all folders exist
            folder_list = ["checkpoints", "config", "figures", "mechanisms", \
                    "model", "morphology", "opt_neuron.py"]
            for f in folder_list:
                if not os.path.exists(os.path.join(opt_folder, f)):
                    return {"response":"KO", "message":"Folder/file '" + f + "' does not exist in the \
                            optimization folder. Please upload a well formatted \
                            .zip file"}

            # validate json files in config folder
            jsonfile_list = ["features.json", "morph.json", "parameters.json", \
                    "protocols.json"]
            keys = []
            for i,j in enumerate(jsonfile_list):
                c_filename = os.path.join(opt_folder, "config", j)
                try:
                    with open(c_filename, "r") as read_file:
                        json_data = json.load(read_file)
                        keys.append(json_data.keys()[0])
                        read_file.close()
                except ValueError as error:
                    return {"response":"KO", "message":"File '" + c_filename + "' is either not \
                            present or not readable in 'config' folder. Please \
                            check your .zip file"}
            all_keys = list(set(keys))
            if len(all_keys) != 1:
                return {"response":"KO", "message":"All .json files in the\
                        'config' folder must contain the same data key. \
                        Please upload a well formatted .zip file"}
            else:
                for line in open(os.path.join(opt_folder, "opt_neuron.py")):
                    if line.startswith('evaluator = model.evaluator.create'):
                        start = "model.evaluator.create('"
                        end = "', "
                        opt_key = line[line.find(start)+len(start):line.rfind(end)]
                        if opt_key != all_keys[0]:
                            return {"response":"KO", "message":"Line 75 in 'opt_neuron.py' \
                                must contain the same key as the one \
                                contained in the .json files in the \
                                'config' folder. Please upload a well \
                                formatted .zip file"}

            # validate files in folder mechanisms 
            file_list = os.listdir(os.path.join(opt_folder, "mechanisms"))
            modfilelist = [x for x in file_list if x[-4:]==".mod"]
            if not file_list or len(file_list) != len(modfilelist):
                return {"response":"KO", "message":"The folder 'mechanisms' \
                        must not be empty and must contain only .mod files"}


            # validate files in folder 'model'
            file_list = ['__init__.py', 'analysis.py', 'evaluator.py', 'template.py']
            for f in file_list:
                if not os.path.exists(os.path.join(opt_folder, "model", f)):
                    return {"response":"KO", "message":"File '" + f + "' does not exist in the \
                            'model' folder. Please upload a well formatted \
                            .zip file"}


            # check that only one file is present in morphology
            morph_list_dir = os.listdir(os.path.join(opt_folder, "morphology"))
            if len(morph_list_dir) != 1:
                return {"response":"KO", "message":"Folder 'morphology' must \
                        contain only one file. " + str(len(morph_list_dir)) + \
                        "files are present in the folder. Please upload a well formatted \
                        .zip file"}
            else:
                with open(os.path.join(opt_folder, "config", "morph.json")) as json_file:
                    morph_data = json.load(json_file)
                    if morph_list_dir[0] != morph_data.values()[0]: 
                        return {"response":"KO", "message":"The file in the \
                                'morphology' folder must have the same name\
                                of the key in the 'morph.json' file in the\
                                'config' folder"}
                    
            # validate .mod files in mechanisms
            mechdir = os.listdir(os.path.join(opt_folder, "mechanisms"))
            modlist = [x for x in mechdir if x.endswith(".mod")]
            if not modlist:
                return {"response":"KO", "message":"No .mod file in folder\
                        'mechanisms'. Please check your .zip file"}


            return {"response":"OK", "message":"Folder exists"}
            


    @classmethod
    def checkSimFolders(cls, folder_path=""):

        if not os.path.isdir(folder_path):
            resp = {"response":"KO", "message": "Optimization result " + \
                    "does not exist. Check your files"}
            return resp
        #
        check_folder = os.path.join(folder_path, 'checkpoints')
        mec_folder = os.path.join(folder_path, 'mechanisms')
        morph_folder = os.path.join(folder_path, 'morphology')

        # check checkpoints folder
        if not os.path.isdir(check_folder):
            resp = {"response":"KO", "message":"'checkpoints' folder " + \
                    "NOT present"}
            return resp
        list_hoc_files = \
            [cf for cf in os.listdir(check_folder) if cf.endswith(".hoc")]
        if not list_hoc_files:
            resp = {"response":"KO", "message":"No .hoc file is present \
                            in the final simulation folder"}
            return resp

        # check morphology folder
        if not os.path.isdir(morph_folder):
            resp = {"response":"KO", "message":"'morphology' folder NOT present"}
            return resp
        elif not os.listdir(morph_folder):
            resp = {"response":"KO", "message":"The folder 'morphology' is \
                    empty"}
            return resp
        
        # check mechanisms folder
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

        return {"response":"OK", "message":"Folders and files structure are correct."}
        

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
