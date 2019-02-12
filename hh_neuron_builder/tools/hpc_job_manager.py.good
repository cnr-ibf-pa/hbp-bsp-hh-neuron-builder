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
    key = 'Application_Fitting-DA5A3D2F8B9B4A5D964D4D2285A49C57'
    url = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'
    headers = {'cipres-appkey' : key}
    tool = 'BLUEPYOPT_TG'

    @classmethod
    def checkNsgLogin(cls, username, password):                                           
        KEY = cls.key
        URL = cls.url + '/job/' + username                

        try:
            r = requests.get(URL, auth=(username, password), headers=cls.headers)               
        except Exception as e:
            return {'response':'KO', 'message':e.message}

        root = xml.etree.ElementTree.fromstring(r.text)                                 
        flag = "OK"

        if root.tag == "error":                                                         
            msg = root.find("displayMessage").text                                      
            flag = "KO"
        else:                                                                           
            msg = "Authenticated successfully"                                          

        return {"response": flag, "message": msg}

    @classmethod
    def runNSG(cls, username_submit, password_submit, core_num, node_num, \
            runtime, zfName):
        """
        Launch process on NSG
        """

        CRA_USER = username_submit
        PASSWORD = password_submit
        KEY = cls.key
        URL = cls.url
        TOOL = cls.tool

        payload = {'tool' : TOOL, 'metadata.statusEmail' : 'false', \
                'vparam.number_cores_' : core_num, 'vparam.number_nodes_' :\
                node_num, 'vparam.runtime_' : runtime, 'vparam.filename_': 'init.py'}

        # set file to be submitted
        files = {'input.infile_' : open(zfName,'rb')}

        # submit job with post
        r = requests.post('{}/job/{}'.format(URL, CRA_USER), auth=(CRA_USER, \
            PASSWORD), data=payload, headers=cls.headers, files=files)

        if r.status_code != 200:
            return {"status_code":r.status_code}
        else:

            # format text in xml
            root = xml.etree.ElementTree.fromstring(r.text)

            # extract job selfuri and resulturi
            outputuri = root.find('resultsUri').find('url').text
            selfuri = root.find('selfUri').find('url').text

            # extract job handle
            r = requests.get(selfuri, auth=(CRA_USER, PASSWORD), headers=cls.headers)
            root = xml.etree.ElementTree.fromstring(r.text)
            if not r.status_code == 200:
                jobname = "No jobname because error in submission"
            else:
                jobname = root.find('jobHandle').text

            response = {"status_code":r.status_code, "outputuri":outputuri, \
                    "selfUri":selfuri, "jobname":jobname, "zfName":zfName}
            return response

    @classmethod
    def fetch_job_list(cls, username_fetch, password_fetch):
        """
        Retrieve job list from NSG servers.
        """

        # read/set NSG connection parameters
        KEY = cls.key
        URL = cls.url
        CRA_USER = username_fetch
        PASSWORD = password_fetch

        # 
        r_all = requests.get(URL + "/job/" + CRA_USER, auth=(CRA_USER, \
            PASSWORD), headers=cls.headers)
        root_all = xml.etree.ElementTree.fromstring(r_all.text)

        # create final dictionary
        job_list_dict = collections.OrderedDict()
        job_list = root_all.find('jobs')
        for job in job_list.findall('jobstatus'):
            job_title = job.find('selfUri').find('title').text
            job_url = job.find('selfUri').find('url').text

            job_list_dict[job_title] = collections.OrderedDict()
            job_list_dict[job_title]['url'] = job_url

        return job_list_dict


    @classmethod
    def fetch_job_details(cls, job_id, username_fetch, password_fetch):
        """
        Retrieve details from individual jobs from the job list given as argument
        Current status, current status timestamp and submission timestamp are fetched for every job
        """

        # read/set NSG connection parameters
        KEY = cls.key
        URL = cls.url
        CRA_USER = username_fetch
        PASSWORD = password_fetch

        r_job = requests.get(URL + "/job/" + CRA_USER + '/' + job_id, \
                auth=(CRA_USER, PASSWORD), headers=cls.headers)
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

    @classmethod
    def fetch_job_results(cls, job_res_url, username_fetch, password_fetch, \
            opt_res_dir, wf_id):
        """
        Fetch job output files from NSG 
        """
        # read/set NSG connection parameters
        KEY = cls.key
        URL = cls.url
        CRA_USER = username_fetch
        PASSWORD = password_fetch
        opt_res_dir = opt_res_dir

        # request all output file urls 
        r_all = requests.get(job_res_url, auth=(CRA_USER, PASSWORD), \
                headers=cls.headers)
        root = xml.etree.ElementTree.fromstring(r_all.text)
        all_down_uri = root.find('jobfiles').findall('jobfile')

        # create destination dir if not existing
        if not os.path.exists(opt_res_dir):
            os.mkdir(opt_res_dir)

        # for every file download it to the destination dir
        for i in all_down_uri:
            crr_down_uri = i.find('downloadUri').find('url').text
            r = requests.get(crr_down_uri, auth=(CRA_USER, PASSWORD), \
                    headers=cls.headers) 
            d = r.headers['content-disposition']
            filename_list = re.findall('filename=(.+)', d)
            for filename in filename_list:
                with open(os.path.join(opt_res_dir,filename), 'wb') as fd:
                    for chunk in r.iter_content():
                        fd.write(chunk)

        fname = opt_res_dir + '_' +  wf_id

        if os.path.isfile(fname):
            shutil.remove(fname)

        shutil.make_archive(fname, 'zip', opt_res_dir)

        return ""

    @classmethod
    def createzip(cls, fin_opt_folder, source_opt_zip, \
            opt_name, source_feat, gennum, offsize, zfName):
        """
        Create zip file to be submitted to NSG 
        """

        # folder named as the optimization
        if not os.path.exists(fin_opt_folder):
            os.makedirs(fin_opt_folder)
        else:
            shutil.rmtree(fin_opt_folder)
            os.makedirs(fin_opt_folder)

        # unzip source optimization file 
        z = zipfile.ZipFile(source_opt_zip, 'r')
        z.extractall(path = fin_opt_folder)
        z.close()

        # change name to the optimization folder
        source_opt_name = os.path.basename(source_opt_zip)[:-4]
        crr_dest_dir = os.path.join(fin_opt_folder, source_opt_name)
        fin_dest_dir = os.path.join(fin_opt_folder, opt_name)
        shutil.move(crr_dest_dir, fin_dest_dir)

        # copy feature files to the optimization folder
        features_file = os.path.join(source_feat, 'features.json')
        protocols_file = os.path.join(source_feat, 'protocols.json') 
        fin_feat_path = os.path.join(fin_dest_dir, 'config', 'features.json')
        fin_prot_path = os.path.join(fin_dest_dir, 'config', 'protocols.json')
        if os.path.exists(fin_feat_path):
            os.remove(fin_feat_path)
        if os.path.exists(fin_prot_path):
            os.remove(fin_prot_path)
        shutil.copyfile(features_file, fin_feat_path)
        shutil.copyfile(protocols_file, fin_prot_path)

        # change feature files primary keys
        fin_morph_path = os.path.join(fin_dest_dir, 'config', 'morph.json')
        with open(fin_morph_path, 'r') as morph_file:
            morph_json = json.load(morph_file, \
                    object_pairs_hook=collections.OrderedDict)
            morph_file.close()
        with open(fin_feat_path, 'r') as feat_file:
            feat_json = json.load(feat_file, \
                    object_pairs_hook=collections.OrderedDict)
            feat_file.close()
        with open(fin_prot_path, 'r') as prot_file:
            prot_json = json.load(prot_file, \
                    object_pairs_hook=collections.OrderedDict)
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
            feat_file.write(json.dumps(feat_json, indent=4))
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
            f.write('os.system(\'python opt_neuron.py --max_ngen=' + str(gennum) + ' --offspring_size=' + str(offsize) + ' --start --checkpoint ./checkpoints/checkpoint.pkl\')')
            f.write('\n')
        f.close()

        # build optimization folder name
        crr_dir_opt = os.path.join(fin_opt_folder, opt_name)

        foo = zipfile.ZipFile(zfName, 'w', zipfile.ZIP_DEFLATED)

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

        for root, dirs, files in os.walk(fin_opt_folder):
            if (root == os.path.join(crr_dir_opt, 'morphology')) or \
                    (root == os.path.join(crr_dir_opt, 'config')) or \
                    (root == os.path.join(crr_dir_opt, 'mechanisms')) or \
                    (root == os.path.join(crr_dir_opt, 'model')):
                #
                for f in files:
                    final_zip_fname = os.path.join(root, f)
                    foo.write(final_zip_fname, \
                            final_zip_fname.replace(fin_opt_folder, '', 1))

            if (root == os.path.join(crr_dir_opt, 'checkpoints')) or \
                    (root == os.path.join(crr_dir_opt, 'figures')):
                        final_zip_fold_name = os.path.join(root)
                        foo.write(final_zip_fold_name, \
                                final_zip_fold_name.replace(fin_opt_folder, '',
                                    1))

            if (root == crr_dir_opt):
                for f in files:
                    if f.endswith('.py'):
                        final_zip_fname = os.path.join(root, f)
                        foo.write(final_zip_fname, \
                            final_zip_fname.replace(fin_opt_folder, '', 1))
        foo.close()

#
class OptSettings:
    params_default = {'wf_id': "", 'gennum': 2, 'offsize': 10, \
            'nodenum': 2, 'corenum': 1, 'runtime': 0.5, \
            'hpc_sys':  "", 'opt_sub_param_file': ""}

    @classmethod
    def get_params_default(cls):
        params = {
                'wf_id': cls.params_default["wf_id"], \
                'number_of_cores': cls.params_default["corenum"], \
                'number_of_nodes': cls.params_default["nodenum"], \
                'runtime': cls.params_default["runtime"], \
                'number_of_generations': cls.params_default["gennum"], \
                'offspring_size': cls.params_default["offsize"], \
                'hpc_sys': cls.params_default["hpc_sys"]
                }

        return params

    @classmethod
    def print_opt_params(cls, **kwargs):
        #
        if 'wf_id' in kwargs:
            wf_id = kwargs['wf_id']
        else:
            wf_id = cls.params_default['wf_id']

        #
        if 'gennum' in kwargs:
            gennum = kwargs['gennum']
        else:
            gennum = cls.params_default['gennum']

        #
        if 'offsize' in kwargs:
            offsize = kwargs['offsize']
        else:
            offsize = cls.params_default['offsize']

        #
        if 'nodenum' in kwargs:
            nodenum = kwargs['nodenum']
        else:
            nodenum = cls.params_default['nodenum']

        #
        if 'corenum' in kwargs:
            corenum = kwargs['corenum']
        else:
            corenum = cls.params_default['corenum']

        #
        if 'runtime' in kwargs:
            runtime = kwargs['runtime']
        else:
            runtime = cls.params_default['runtime']

        #
        if 'hpc_sys' in kwargs:
            hpc_sys = kwargs['hpc_sys']
        else:
            hpc_sys = cls.params_default['hpc_sys']

        #
        if 'opt_sub_param_file' in kwargs:
            opt_sub_param_file = kwargs['opt_sub_param_file']
        else:
            opt_sub_param_file = cls.params_default['opt_sub_param_file']

        

        params = {'wf_id':wf_id, 'number_of_cores': corenum, 'number_of_nodes': nodenum, \
                    'runtime': runtime, 'number_of_generations': gennum, \
                    'offspring_size': offsize, "hpc_sys": hpc_sys}

        with open(opt_sub_param_file, 'w') as pf:
            json.dump(params, pf)
        pf.close()

