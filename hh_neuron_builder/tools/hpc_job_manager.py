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

class Nsg:
    def __init__(self, username="", password="", core_num=0, node_num=0, \
            runtime=0, gennum=0, offsize=0, dest_dir="", source_opt_zip="", \
            opt_name="", source_feat="", username_fetch="", password_fetch="", \
            opt_res_dir=""):
        """
        Initialization function
        """
        self.username = username
        self.password = password
        self.username_fetch = username_fetch
        self.password_fetch = password_fetch
        self.core_num = core_num
        self.node_num = node_num
        self.runtime = runtime
        self.gennum = gennum
        self.offsize = offsize
        self.dest_dir = dest_dir
        self.opt_res_dir = opt_res_dir
        self.source_opt_zip = source_opt_zip
        self.opt_name = opt_name
        self.source_feat = source_feat
        self.fin_opt_folder = os.path.join(self.dest_dir, self.opt_name)
        self.zfName = os.path.join(self.fin_opt_folder, self.opt_name + '.zip')
        self.key = 'Application_Fitting-DA5A3D2F8B9B4A5D964D4D2285A49C57'
        self.url = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'
        self.tool = 'BLUEPYOPT_TG'

    def setFetchUsername(self, username_fetch):
        """
        Set username to fetch jobs from hpc systems
        """
        self.username_fetch = username_fetch
    

    def setFetchPassword(self, password_fetch):
        """
        Set password to fetch jobs from hpc systems
        """
        self.password_fetch = password_fetch


    def runNSG(self):
        """
        Launch process on NSG
        """

        CRA_USER = self.username
        PASSWORD = self.password
        KEY = self.key
        URL = self.url
        TOOL = self.tool
    
        headers = {'cipres-appkey' : KEY}
        #payload = {'tool' : TOOL, 'metadata.statusEmail' : 'false', 'vparam.number_cores_' : NCORES.value, 'vparam.number_nodes_' : NNODES.value, 'vparam.runtime_' : RT.value, 'vparam.filename_': 'init.py'}
        payload = {'tool' : TOOL, 'metadata.statusEmail' : 'false', 'vparam.number_cores_' : self.core_num, 'vparam.number_nodes_' : self.node_num, 'vparam.runtime_' : self.runtime, 'vparam.filename_': 'init.py'}

        # set file to be submitted
        files = {'input.infile_' : open(self.zfName,'rb')}

        # submit job with post
        r = requests.post('{}/job/{}'.format(URL, CRA_USER), auth=(CRA_USER, PASSWORD), data=payload, headers=headers, files=files)

        if r.status_code != 200:
            return {"status_code":r.status_code}
        else:
                
            # format text in xml
            root = xml.etree.ElementTree.fromstring(r.text)

            # extract job selfuri and resulturi
            outputuri = root.find('resultsUri').find('url').text
            selfuri = root.find('selfUri').find('url').text

            # extract job handle
            r = requests.get(selfuri, auth=(CRA_USER, PASSWORD), headers=headers)
            root = xml.etree.ElementTree.fromstring(r.text)
            jobname = root.find('jobHandle').text
            for child in root:
                if child.tag=='jobHandle':
                    jobname = child.text

            response = {"status_code":r.status_code, "outputuri":outputuri, \
                    "selfUri":selfuri, "jobname":jobname, "zfName":self.zfName}
            return response


    def fetch_job_list(self):
        """
        Retrieve job list from NSG servers.
        """

        # read/set NSG connection parameters
        KEY = self.key
        URL = self.url
        CRA_USER = self.username_fetch
        PASSWORD = self.password_fetch
        headers = {'cipres-appkey' : KEY, 'expand': 'true'}

        # 
	r_all = requests.get(URL + "/job/" + CRA_USER, auth=(CRA_USER, PASSWORD), headers=headers)
    	root_all = xml.etree.ElementTree.fromstring(r_all.text)
        job_list_dict = collections.OrderedDict()
        job_list = root_all.find('jobs')
        for job in job_list.findall('jobstatus'):
            job_title = job.find('selfUri').find('title').text
            job_url = job.find('selfUri').find('url').text

            job_list_dict[job_title] = collections.OrderedDict()
            job_list_dict[job_title]['url'] = job_url
        
        return job_list_dict


    def fetch_job_details(self, job_id):
        """
        Retrieve details from individual jobs from the job list given as argument
        Current status, current status timestamp and submission timestamp are fetched for every job
        """

        # read/set NSG connection parameters
        KEY = self.key
        URL = self.url
        CRA_USER = self.username_fetch
        PASSWORD = self.password_fetch
        headers = {'cipres-appkey' : KEY}

        r_job = requests.get(URL + "/job/" + CRA_USER + '/' + job_id, auth=(CRA_USER, PASSWORD), headers=headers)
    	root_job = xml.etree.ElementTree.fromstring(r_job.text)
            
        job_date_submitted = root_job.find('dateSubmitted').text
        job_res_url = root_job.find('resultsUri').find('url').text
        job_messages = root_job.find('messages').findall('message')
        job_stage = job_messages[-1].find('stage').text
        job_stage_ts = job_messages[-1].find('timestamp').text
            
        job_info_dict = collections.OrderedDict()
        job_info_dict["job_id"] = job_id 
        job_info_dict["job_date_submitted"] = job_date_submitted
        job_info_dict["job_res_url"] = job_res_url
        job_info_dict["job_stage"] = job_stage
        job_info_dict["job_stage_ts"] = job_stage_ts
            
        return job_info_dict 


    def fetch_job_results(self, job_res_url):
        """
        Fetch job output files from NSG 
        """
        # read/set NSG connection parameters
        KEY = self.key
        URL = self.url
        CRA_USER = self.username_fetch
        PASSWORD = self.password_fetch
        headers = {'cipres-appkey' : KEY}
        opt_res_dir = self.opt_res_dir

        # request all outpur file urls 
	r_all = requests.get(job_res_url, auth=(CRA_USER, PASSWORD), headers=headers)
        root = xml.etree.ElementTree.fromstring(r_all.text)
        all_down_uri = root.find('jobfiles').findall('jobfile')
        
        # create destination dir if not existing
        if not os.path.exists(opt_res_dir):
            os.mkdir(opt_res_dir)

        # for every file download it to the destination dir
        for i in all_down_uri:
            crr_down_uri = i.find('downloadUri').find('url').text
            r = requests.get(crr_down_uri, auth=(CRA_USER, PASSWORD), headers=headers) 
            d = r.headers['content-disposition']
            filename_list = re.findall('filename=(.+)', d)
            for filename in filename_list:
                with open(os.path.join(opt_res_dir,filename), 'wb') as fd:
                    for chunk in r.iter_content():
                        fd.write(chunk)
        return ""
    

    def createzip(self):
        """
        Create zip file to be submitted to NSG 
        """

        # folder named as the optimization
        if not os.path.exists(self.fin_opt_folder):
            os.makedirs(self.fin_opt_folder)
        else:
            shutil.rmtree(self.fin_opt_folder)
            os.makedirs(self.fin_opt_folder)
        
        # unzip source optimization file 
        z = zipfile.ZipFile(self.source_opt_zip, 'r')
        z.extractall(path = self.fin_opt_folder)
        z.close()
        
        # change name to the optimization folder
        source_opt_name = os.path.basename(self.source_opt_zip)[:-4]
        crr_dest_dir = os.path.join(self.fin_opt_folder, source_opt_name)
        fin_dest_dir = os.path.join(self.fin_opt_folder, self.opt_name)
        shutil.move(crr_dest_dir, fin_dest_dir)

        # copy feature files to the optimization folder
        features_file = os.path.join(self.source_feat, 'features.json')
        protocols_file = os.path.join(self.source_feat, 'protocols.json') 
        fin_feat_path = os.path.join(fin_dest_dir, 'config', 'features.json')
        fin_prot_path = os.path.join(fin_dest_dir, 'config', 'protocols.json')
        if os.path.exists(fin_feat_path):
            os.remove(fin_feat_path)
        if os.path.exists(fin_prot_path):
            os.remove(fin_prot_path)
        shutil.copy(features_file, os.path.join(fin_dest_dir, 'config'))
        shutil.copy(protocols_file, os.path.join(fin_dest_dir, 'config'))
        
        # change feature files primary keys
        fin_morph_path = os.path.join(fin_dest_dir, 'config', 'morph.json')
        with open(fin_morph_path, 'r') as morph_file:
            morph_json = json.load(morph_file)
            morph_file.close()
        with open(fin_feat_path, 'r') as feat_file:
            feat_json = json.load(feat_file)
            feat_file.close()
        with open(fin_prot_path, 'r') as prot_file:
            prot_json = json.load(prot_file)
            prot_file.close()
            
        os.remove(fin_feat_path)
        os.remove(fin_prot_path)

        fin_key = morph_json.keys()[0]
        feat_key = feat_json.keys()[0]
        prot_key = prot_json.keys()[0]
        
        feat_json[fin_key] = feat_json.pop(feat_key)
        prot_json[fin_key] = prot_json.pop(prot_key)

        # save feature files with changed keys
        with open(fin_feat_path, 'w') as feat_file:
            feat_file.write(json.dumps(feat_json, indent=2))
            feat_file.close()

        # save protocol files with changed keys
        with open(fin_prot_path, 'w') as prot_file:
            prot_file.write(json.dumps(prot_json, indent=2))
            prot_file.close()


        # remove unwanted files from the folder to be zipped
        for item in os.listdir(fin_dest_dir):
            if item.startswith('init') or item.endswith('.zip') \
            or item.startswith('__MACOSX'):
                os.remove(os.path.join(fin_dest_dir, item))

        with open(os.path.join(fin_dest_dir, 'init.py'),'w') as f:
            f.write('import os')
            f.write('\n')
            f.write('os.system(\'python opt_neuron.py --max_ngen=' + str(self.gennum) + ' --offspring_size=' + str(self.offsize) + ' --start --checkpoint ./checkpoints/checkpoint.pkl\')')
            f.write('\n')
        f.close()
        current_working_dir = os.getcwd()
        os.chdir(self.fin_opt_folder)

        # build optimization folder name
        crr_dir_opt = os.path.join('.', self.opt_name)

        foo = zipfile.ZipFile(self.zfName, 'w', zipfile.ZIP_DEFLATED)

        checkpoints_dir = os.path.join(crr_dir_opt, 'checkpoints')
        figures_dir = os.path.join(crr_dir_opt, 'figures')
        r_0_dir = os.path.join(crr_dir_opt, 'r_0')

        if os.path.exists(checkpoints_dir):
            shutil.rmtree(checkpoints_dir)
            os.makedirs(checkpoints_dir)
        if os.path.exists(figures_dir):
            shutil.rmtree(figures_dir)
            os.makedirs(figures_dir)
        if os.path.exists(r_0_dir):
            shutil.rmtree(r_0_dir)

        for root, dirs, files in os.walk('.'):
            if (root == os.path.join(crr_dir_opt, 'morphology')) or \
            (root == os.path.join(crr_dir_opt, 'config')) or \
            (root == os.path.join(crr_dir_opt, 'mechanisms')) or \
            (root == os.path.join(crr_dir_opt, 'model')):
                #
                for f in files:
                    foo.write(os.path.join(root, f))

            if (root == os.path.join(crr_dir_opt, 'checkpoints')) or \
            (root == os.path.join(crr_dir_opt, 'figures')):
                foo.write(os.path.join(root))

            if (root == crr_dir_opt):
                for f in files:
                    if f.endswith('.py'):
                        foo.write(os.path.join(root, f))                    
        foo.close()

        os.chdir(current_working_dir)


def replace_feature_files(source_dir, dest_dir):
    return True
