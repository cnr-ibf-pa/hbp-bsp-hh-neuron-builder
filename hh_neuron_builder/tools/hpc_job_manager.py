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
    def __init__(self, username, password, core_num, node_num, runtime, gennum, offsize, dest_dir, source_opt_zip, opt_name, source_feat):
        """
        Initialization function
        """
        self.username = username
        self.password = password
        self.core_num = core_num
        self.node_num = node_num
        self.runtime = runtime
        self.gennum = gennum
        self.offsize = offsize
        self.dest_dir = dest_dir
        self.source_opt_zip = source_opt_zip
        self.opt_name = opt_name
        self.source_feat = source_feat
        self.fin_opt_folder = os.path.join(self.dest_dir, self.opt_name)
        self.zfName = os.path.join(self.fin_opt_folder, self.opt_name + '.zip')
        self.key = 'Application_Fitting-DA5A3D2F8B9B4A5D964D4D2285A49C57'
        self.url = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'
        self.tool = 'BLUEPYOPT_TG'


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
        CRA_USER = self.username
        PASSWORD = self.password
        headers = {'cipres-appkey' : KEY}

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


    def fetch_job_details(self, job_id, job_list_dict):
        """
        Retrieve details from individual jobs from the job list given as argument
        Current status, current status timestamp and submission timestamp are fetched for every job
        """

        # read/set NSG connection parameters
        KEY = self.key
        URL = self.url
        CRA_USER = self.username
        PASSWORD = self.password
        headers = {'cipres-appkey' : KEY}

        r_job = requests.get(URL + "/job/" + CRA_USER + '/' + job_id, auth=(CRA_USER, PASSWORD), headers=headers)
    	root_job = xml.etree.ElementTree.fromstring(r_job.text)
            
        job_date_submitted = root_job.find('dateSubmitted').text
        job_res_url = root_job.find('resultsUri').find('url').text
        job_messages = root_job.find('messages').findall('message')
        job_stage = job_messages[-1].find('stage').text
        job_stage_ts = job_messages[-1].find('timestamp').text
            
        job_list_dict[job_id]['job_date_submitted'] = job_date_submitted
        job_list_dict[job_id]['job_res_url'] = job_res_url
        job_list_dict[job_id]['job_stage'] = job_stage
        job_list_dict[job_id]['job_stage_ts'] = job_stage_ts
            
        return "" 


    def fetch_job_results(self, job_res_url, dest_dir = ""):
        """
        Fetch job output files from NSG 
        """
        # read/set NSG connection parameters
        KEY = self.key
        URL = self.url
        CRA_USER = self.username
        PASSWORD = self.password
        headers = {'cipres-appkey' : KEY}

        # request all outpur file urls 
	r_all = requests.get(job_res_url, auth=(CRA_USER, PASSWORD), headers=headers)
        root = xml.etree.ElementTree.fromstring(r_all.text)
        all_down_uri = root.find('jobfiles').findall('jobfile')
        
        # create destination dir if not existing
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)

        # for every file download it to the destination dir
        for i in all_down_uri:
            crr_down_uri = i.find('downloadUri').find('url').text
            r = requests.get(crr_down_uri, auth=(CRA_USER, PASSWORD), headers=headers) 
            d = r.headers['content-disposition']
            filename_list = re.findall('filename=(.+)', d)
            for filename in filename_list:
                with open(os.path.join(dest_dir,filename), 'wb') as fd:
                    print("writing file " + os.path.join(dest_dir, filename)) 
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

        z = zipfile.ZipFile(self.source_opt_zip, 'r')
        z.extractall(path = self.fin_opt_folder)
        z.close()
        
        source_opt_name = os.path.basename(self.source_opt_zip)[:-4]
        crr_dest_dir = os.path.join(self.fin_opt_folder, source_opt_name)
        fin_dest_dir = os.path.join(self.fin_opt_folder, self.opt_name)
        shutil.move(crr_dest_dir, fin_dest_dir)

        features_file = os.path.join(self.source_feat, 'features.json')
        protocols_file = os.path.join(self.source_feat, 'protocols.json') 
        fin_feat_path = os.path.join(fin_dest_dir, 'config', 'features.json')
        fin_prot_path = os.path.join(fin_dest_dir, 'config', 'protocols.json')
        if os.path.exists(fin_feat_path):
            os.remove(fin_feat_path)
        if os.path.exists(fin_prot_path):
            os.remove(fin_prot_path)

        #
        shutil.copy(features_file, os.path.join(fin_dest_dir, 'config'))
        shutil.copy(protocols_file, os.path.join(fin_dest_dir, 'config'))
        
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

        os.chdir(self.fin_opt_folder)
        foo = zipfile.ZipFile(self.zfName, 'w', zipfile.ZIP_DEFLATED)

        crr_dir_opt = os.path.join('.', self.opt_name)
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


def replace_feature_files(source_dir, dest_dir):
    return True
