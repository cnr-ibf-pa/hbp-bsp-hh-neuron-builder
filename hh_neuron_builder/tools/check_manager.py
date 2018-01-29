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
import pprint
import collections
import re

class simRun:

    @classmethod
    def checkSimFiles(cls, sim_path=""):                                           
        # to be checked folder model_name -> folder mechanisms -> *.mod files
        #               folder model_name -> folder morphology -> morphology
        #                   file loaded by cell.hoc
        #               folder model_name -> folder checkpoints -> cell.hoc
        sim_name = ''
        list_dir = os.listdir(sim_path) 
        for i in list_dir:
            if i.endswith('.zip'):
                sim_name = os.path.splitext(i)[0]
                continue
        if sim_name == "":
            resp = {"response":"KO", "message":"No simulation .zip file"}
            print(resp)
            return resp
        check_folder = os.path.join(sim_path, sim_name, 'checkpoints')
        mec_folder = os.path.join(sim_path, sim_name, 'mechanisms')
        morph_folder = os.path.join(sim_path, sim_name, 'morphology')
        print(check_folder)
        print(mec_folder)
        print(morph_folder)
        if not os.path.isdir(check_folder) or not os.path.isdir(mec_folder) \
                or not os.path.isdir(morph_folder):
            resp = {"response":"KO", "message":"Simulation folder incomplete."}
            return resp

        if not os.path.isfile(os.path.join(check_folder, 'cell.hoc')) \
                and not (os.path.isfile(os.path.join(sim_path, \
                        'template.hoc'))):
                resp = {"response":"KO", "message":"Neither 'cell.hoc' nor \
                        'template.hoc' file present in the final simulation \
                        folder."}
                print(resp)
                return resp
        if not os.path.isdir(mec_folder):
                    resp = {"response":"KO", "message":"The folder 'mechamisms'\
                            is not present in the final simulation folder'"}
                    print(resp)
                    return resp
        else:
            mec_list_dir = os.listdir(mec_folder)
            list_mod = [i if i.endswith('.mod') else None for i in mec_list_dir] 
            print(list_mod)
            if not list_mod:
                resp = {"response":"KO", "message":"The folder 'mechanisms'\
                    of the final simulation folder does not contain any .mod file'"}
                print(resp)
                return resp

        if not os.listdir(morph_folder):
            resp = {"response":"KO", "message":"The folder 'morphology'\
                of the final simulation folder is empty'"}
            print(resp)
            return resp
        else: 
            resp = {"response":"OK", "message":"All needed files are present"}
            print(resp)
            return resp

