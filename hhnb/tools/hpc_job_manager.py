from hhnb.tools import unicore_client

from pyunicore import client as new_unicore_client

import json
import os
import requests
import xml.etree.ElementTree
import sys
import traceback
import zipfile
import tarfile
import shutil
import collections
import re

import urllib3
urllib3.disable_warnings()


class Nsg:
    key = 'Application_Fitting-DA5A3D2F8B9B4A5D964D4D2285A49C57'
    url = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'
    headers = {'cipres-appkey': key}
    tool = 'BLUEPYOPT_TG'

    @classmethod
    def check_nsg_login(cls, username, password):
        KEY = cls.key
        URL = cls.url + '/job/' + username                

        try:
            r = requests.get(URL, auth=(username, password), headers=cls.headers)               
        except Exception as e:
            return {'response': 'KO', 'message': e.message}

        root = xml.etree.ElementTree.fromstring(r.text)                                 
        flag = "OK"
        if r.status_code != 200 or root.tag == "error":                                                         
            msg = root.find("displayMessage").text                                      
            flag = "KO"
        else:                                                                           
            msg = "Authenticated successfully"                                          

        return {"response": flag, "message": msg}

    @classmethod
    def runNSG(cls, username_submit, password_submit, core_num, node_num, runtime, zfName):
        """
        Launch process on NSG.
        """

        CRA_USER = username_submit
        PASSWORD = password_submit
        KEY = cls.key
        URL = cls.url
        TOOL = cls.tool

        payload = {
            'tool': TOOL,
            'metadata.statusEmail': 'false',
            'vparam.number_cores_': core_num,
            'vparam.number_nodes_': node_num,
            'vparam.runtime_': runtime,
            'vparam.filename_': 'init.py'
        }

        # set file to be submitted
        files = {'input.infile_': open(zfName, 'rb')}

        # submit job with post
        r = requests.post('{}/job/{}'.format(URL, CRA_USER), auth=(CRA_USER, PASSWORD), data=payload, headers=cls.headers, files=files)

        if r.status_code != 200:
            return {'response': "KO", "status_code": r.status_code, "jobname": "Error in submission"}
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
                job_name = "No jobname because error in submission"
                resp = 'KO'
            else:
                job_name = root.find('jobHandle').text
                resp = 'OK'

            response = {
                "status_code": r.status_code,
                "outputuri": outputuri,
                "selfUri": selfuri,
                "jobname": job_name,
                "zfName": zfName,
                'response': resp
            }
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

        r_all = requests.get(URL + "/job/" + CRA_USER, auth=(CRA_USER, PASSWORD), headers=cls.headers)
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
        Retrieve details from individual jobs from the job list given as argument.
        Current status, current status timestamp and submission timestamp are fetched for every job.
        """

        # read/set NSG connection parameters
        KEY = cls.key
        URL = cls.url
        CRA_USER = username_fetch
        PASSWORD = password_fetch

        r_job = requests.get(URL + "/job/" + CRA_USER + '/' + job_id, auth=(CRA_USER, PASSWORD), headers=cls.headers)
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
    def fetch_job_results(cls, job_res_url, username_fetch, password_fetch, opt_res_dir, wf_id):
        """
        Fetch job output files from NSG.
        """
        # read/set NSG connection parameters
        KEY = cls.key
        URL = cls.url
        CRA_USER = username_fetch
        PASSWORD = password_fetch
        opt_res_dir = opt_res_dir

        # request all output file urls 
        r_all = requests.get(job_res_url, auth=(CRA_USER, PASSWORD), headers=cls.headers)
        root = xml.etree.ElementTree.fromstring(r_all.text)
        all_down_uri = root.find('jobfiles').findall('jobfile')

        # create destination dir if not existing
        if not os.path.exists(opt_res_dir):
            os.mkdir(opt_res_dir)

        # for every file download it to the destination dir
        for i in all_down_uri:
            crr_down_uri = i.find('downloadUri').find('url').text
            r = requests.get(crr_down_uri, auth=(CRA_USER, PASSWORD), headers=cls.headers)
            d = r.headers['content-disposition']
            filename_list = re.findall('filename=(.+)', d)
            for filename in filename_list:
                with open(os.path.join(opt_res_dir,filename), 'wb') as fd:
                    for chunk in r.iter_content():
                        fd.write(chunk)

        fname = opt_res_dir + '_' + wf_id

        if os.path.isfile(fname):
            shutil.remove(fname)

        shutil.make_archive(fname, 'zip', opt_res_dir)
        
        OptFolderManager.create_opt_res_zip(fin_folder=opt_res_dir, filetype="", wf_id=wf_id)

        return ""


class UnicoreClient:

    class __UnicoreClient:

        def __init__(self, token):
            self.token = token
            self.tr = new_unicore_client.Transport(self.token.split('Bearer ')[1])
            self.daint_client = new_unicore_client.Client(self.tr, 'https://brissago.cscs.ch:8080/DAINT-CSCS/rest/core')

        def get_token(self):
            return self.token

        def get_daint_client(self):
            return self.daint_client

    instance = None

    @staticmethod
    def get_instance(token):
        if not UnicoreClient.instance:
            UnicoreClient.instance = UnicoreClient.__UnicoreClient(token)
        return UnicoreClient.instance

    def __get_daint_client(self):
        return self.instance.get_daint_client()


class Unicore:
    """
    Class for submitting jobs with Unicore
    """

    MAX_SIZE = 20240000
    SA_CSCS_JOBS_URL = "https://bspsa.cineca.it/jobs/pizdaint/bsp_pizdaint_01/"
    SA_CSCS_FILES_URL = "https://bspsa.cineca.it/files/pizdaint/bsp_pizdaint_01/"


    @classmethod
    def check_login(cls, username="", token="", hpc=""):  # , proxies={}):
        auth = unicore_client.get_oidc_auth(token=token) 
        base_url = unicore_client.get_sites()[hpc]['url']
        role = unicore_client.get_properties(base_url, auth)['client']['role']['selected']  # , proxies)['client']['role']['selected']

        resp = {"response": "KO", "message": "This account is not allowed to submit job on " + hpc + " booster partition"}
        if role == "user":
            info = unicore_client.get_properties(base_url, auth)['client']['xlogin']['UID'] # , proxies=proxies)['client']['xlogin']['UID']
            UIDs = unicore_client.get_properties(base_url, auth)['client']['xlogin']['availableUIDs'] # , proxies=proxies)['client']['xlogin']['availableUIDs']
            if username in UIDs and username[0:3] == "vsk":
                resp = {"response": "OK", "message": "Successful authentication"}
            
        return resp

    @classmethod
    def run_unicore_opt(cls, hpc="", filename="", joblaunchname="", token=None, core_num=4, jobname="UNICORE_Job",
                        node_num=2, runtime=4, username="", foldname="", project=None):  # , proxies={}):

        basename = os.path.basename(filename)

        # read file to be moved to remote
        with open(filename, 'rb') as f:
            content = f.read()
        f.close()
        modpy = content
        mod = {'To': basename, 'Data': modpy}

        # create inputs array
        inputs = [mod]
        
        # define exec string depending on hpc system
        if hpc == "DAINT-CSCS":
            exec_str = "; chmod +rx *.sbatch; ./ipyparallel.sbatch"
            hpc_sub = "DAINT-CSCS"

            # create job to be submitted
            job = {}
            job = {
                "Executable": "unzip " + basename + "; cd " + foldname + exec_str,
                "Name": jobname,
                "Resources": {
                    "Nodes": str(node_num),
                    "CPUsPerNode": str(core_num),
                    "Runtime": runtime,
                    "NodeConstraints": "mc",
                    "Project": project
                },
                "Tags": [
                    "hhnb"
                ]
            }
            print(job)

            auth = unicore_client.get_oidc_auth(token=token)
            # auth['X-UNICORE-User-Preferences'] = 'uid:'+ username 
            base_url = unicore_client.get_sites()[hpc_sub]['url']

        elif hpc == "SA-CSCS":
            exec_str = "; chmod +rx *.sbatch; ./ipyparallel.sbatch"
            command = "unzip "+basename+"; cd " + foldname + exec_str
            payload = {
                'command': command, 
                'node_number': str(node_num),
                'core_number': str(core_num),
                'runtime': str(runtime),
            }
            job_file = {'file': open(filename, 'rb')}
            auth = unicore_client.get_oidc_auth(token=token)
            auth.update({'Content-Disposition': 'attachment;filename=' + basename})
            auth.update({'payload': json.dumps(payload)})

        elif hpc == "jureca":
            exec_str = "; chmod +rx *.sh; chmod +rx *.sbatch; sh " + joblaunchname + ";",
            hpc_sub = "jureca"
        try:
            if hpc == "SA-CSCS":
                SUBMIT_URL = 'https://bspsa.cineca.it/jobs/pizdaint/'
                r = requests.post(url=SUBMIT_URL, headers=auth, files=job_file)
                job = r.json()
                jobname = job['job_id']
                job_url = 'https://bspsa.cineca.it/jobs/pizdaint/bsp_pizdaint_01/' + jobname + '/'
            else:
                job_url = unicore_client.submit(base_url + '/jobs', job, auth, inputs)  # , proxies=proxies)
                # print('job_url: %s' % job_url)
                # print('jobname: %s' % job_url.split('/')[-1])
                jobname = job_url.split('/')[-1]

            resp = {
                'response': 'OK',
                'joburl': job_url,
                'jobname': jobname,
                'job_id': jobname,
                'message': 'Job submitted with success',
                'status_code': 200
            }
            print(resp)
        except Exception as e:
            print('this is the error')
            print(e)
            resp = {'response': 'KO', 'message': 'Operation not completed'}

        return resp
      
    @classmethod
    def fetch_job_list(cls, hpc, token, proxies={}):
        """
        Retrieve job list from Unicore systems
        """
        # tr = new_unicore_client.Transport(token.split('Bearer ')[1])

        job_list_dict = collections.OrderedDict()

        auth = unicore_client.get_oidc_auth(token="Bearer " + token)
        base_url = unicore_client.get_sites()[hpc]['url']

        if hpc == "DAINT-CSCS":
            # listofjobs = unicore_client.get_properties(base_url + '/jobs', auth, proxies=proxies)
            # jobs = listofjobs['jobs']
            # for i in jobs:
            #     job_title = i.split('/')[-1]
            #     job_list_dict[job_title] = collections.OrderedDict()
            #     job_list_dict[job_title]['url'] = i
            # daint_client = new_unicore_client.Client(tr, "https://brissago.cscs.ch:8080/DAINT-CSCS/rest/core")
            # daint_client = UnicoreClient(token=token).get_daint_client()
            # print(daint_client)
            # jobs = daint_client.get_jobs(tags=['hhnb'])

            daint_client = UnicoreClient().get_instance(token).get_daint_client()
            print(daint_client)
            jobs = daint_client.get_jobs(tags=['hhnb'])

            for j in jobs:
                job_title = j.job_id
                job_list_dict[job_title] = collections.OrderedDict()
                job_list_dict[job_title]['url'] = j.links['self']

        elif hpc == "SA-CSCS":
            listofjobs = unicore_client.get_properties(base_url + '/jobs/pizdaint/bsp_pizdaint_01/', auth, proxies=proxies)
            jobs = listofjobs
            for i in jobs:
                job_title = i["job_id"]
                job_list_dict[job_title] = collections.OrderedDict()
                job_list_dict[job_title]['url'] = base_url + '/jobs/pizdaint/bsp_pizdaint_01/' + job_title 

        return job_list_dict

    @classmethod
    def fetch_job_details(cls, hpc="", job_url="", job_id="", token="", proxies={}):
        # base_url = unicore_client.get_sites()[hpc]['url']
        auth = unicore_client.get_oidc_auth(token=token)

        # mapping for DAINT-CSCS and SA-CSCS fields
        mapfield = {    
            "job_date_submitted": {
                "DAINT-CSCS": 'submissionTime',
                "SA-CSCS": "init_date"
            },
            "job_stage": {
                "DAINT-CSCS": 'status',
                "SA-CSCS": "stage"
            },
            "job_res_url": {
                "DAINT-CSCS": job_url,
                "SA-CSCS": "https://bspsa.cineca.it/files/pizdaint/bsp_pizdaint_01/" + job_url
            },
            "job_name": {
                "DAINT-CSCS": 'name',
                "SA-CSCS": "title"
            },
            "status_message": {
                "DAINT-CSCS": 'statusMessage',
                "SA-CSCS": "stage"
            }
        } 

        job_details = unicore_client.get_properties(job_url, auth, proxies=proxies)
        job_info_dict = collections.OrderedDict()
        job_info_dict["job_date_submitted"] = job_details[mapfield["job_date_submitted"][hpc]]
        job_info_dict["job_stage"] = job_details[mapfield["job_stage"][hpc]]
        job_info_dict["job_id"] = job_id
        job_info_dict["job_res_url"] = job_url
        job_info_dict["job_name"] = job_details[mapfield["job_name"][hpc]]
        job_info_dict["status_message"] = job_details[mapfield["status_message"][hpc]]
        return job_info_dict

    @classmethod
    def fetch_job_results(cls, hpc="", job_url="", token="", dest_dir="", proxies={}, wf_id=""):
        # create destination dir if not existing
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)
        auth = unicore_client.get_oidc_auth(token=token)

        # print('Getting JOB info')
        # job = new_unicore_client.Job(tr, job_url)
        # print(job.properties)

        # r = unicore_client.get_properties(job_url, auth, proxies=proxies)

        # job retrieving from SA-CSCS
        if hpc == "SA-CSCS":
            r = requests.get(url=job_url, headers=auth)
            if r.status_code == 200:
                job = r.json()
                job_id = job_url.split("/")[-1]
                job_files_url = cls.SA_CSCS_FILES_URL + job_id + "/"
                r = requests.get(url=job_files_url, headers=auth)
                if r.status_code == 200:
                    files_list = r.json()
                    for f in files_list:
                        if f == '/stderr' or f == '/stdout' or f == '/output.zip':
                            filename = f[1:]
                            fname, extension = os.path.splitext(filename)
                            crr_file_url = job_files_url + filename + '/'
                            r = requests.get(url=crr_file_url, headers=auth)
                            if r.status_code == 200:
                                with open(os.path.join(dest_dir, filename), 'w') as local_file:
                                    local_file.write(str(r.content))
            
        elif hpc == "DAINT-CSCS":
            daint_client = UnicoreClient().get_instance(token).get_daint_client()

            for storage in daint_client.get_storages():
                if storage.storage_url.endswith(job_url.split('/')[-1] + '-uspace'):
                    job_storage = storage
            print(job_storage)

            # if (r['status'] == 'SUCCESSFUL') or (r['status'] == 'FAILED'):
            #     wd = unicore_client.get_working_directory(job_url, auth, proxies=proxies)
            #     output_files = unicore_client.list_files(wd, auth, proxies=proxies)
            #     for file_path in output_files:
            #         _, f = os.path.split(file_path)
            #         if (f == 'stderr') or (f == "stdout") or (f == "output.zip"):
            #             content = unicore_client.get_file_content(wd + "/files" + file_path, auth, MAX_SIZE=cls.MAX_SIZE, proxies=proxies)
            #             with open(os.path.join(dest_dir, f), "w") as local_file:
            #                 local_file.write(content)
            #             local_file.close()

            results_list = job_storage.listdir('.')
            for f in results_list:
                if f == 'stderr' or f == 'stdout' or f == 'output.zip':
                    remote_file = job_storage.stat(f)
                    remote_file.download(os.path.join(dest_dir, f))
                    print('downloaded %s' % os.path.join(dest_dir, f))

        OptFolderManager.create_opt_res_zip(fin_folder=dest_dir, filetype="optres", wf_id=wf_id)

        return ""

    
# TODO: to be check by Luca
class OptResultManager:
    """
    Manage common operations related to creation and modification of file 
    and/or performing of analysis concerning optimization results.
    """
    
    @classmethod
    def create_analysis_files(cls, opt_res_folder, opt_res_file):
        print('create_analysis_files() called.')
        """
        """
        print(opt_res_file)
        print('os_res_folder content: %s' % os.listdir(opt_res_folder))
        if opt_res_file.endswith(".tar.gz"):
            tar = tarfile.open(os.path.join(opt_res_folder, opt_res_file))
            tar.extractall(path=opt_res_folder)
            tar.close()
        elif opt_res_file.endswith(".zip"):
            zip_ref = zipfile.ZipFile(os.path.join(opt_res_folder, opt_res_file), 'r')
            zip_ref.extractall(path=opt_res_folder)
            zip_ref.close()
        print('os_res_folder content: %s' % os.listdir(opt_res_folder))

        analysis_file_list = []
        print('analysis_file_list=%s' % analysis_file_list)

        for (dirpath, dirnames, filenames) in os.walk(opt_res_folder):
            for filename in filenames:
                if filename == "analysis.py":
                    analysis_file_list.append(os.path.join(dirpath, filename))

        print('analysis_file_list=%s' % analysis_file_list)

        if len(analysis_file_list) != 1:
            msg = "No (or multiple) analysis.py file(s) found. \
                Check the .zip file submitted for the optimization."
            resp = {"Status": "ERROR", "response": "KO", "message": msg}
            return resp
        else:
            full_file_path = analysis_file_list[0]
            file_path = os.path.split(full_file_path)[0]
            up_folder = os.path.split(file_path)[0]

            # modify analysis.py file
            # f = open(full_file_path, 'r')
            #
            # lines = f.readlines()
            # lines[228]='    traces=[]\n'
            # lines[238]='        traces.append(response.keys()[0])\n'
            # lines[242]='\n    stimord={} \n    for i in range(len(traces)): \n        stimord[i]=float(traces[i][traces[i].find(\'_\')+1:traces[i].find(\'.soma\')]) \n    import operator \n    sorted_stimord = sorted(stimord.items(), key=operator.itemgetter(1)) \n    traces2=[] \n    for i in range(len(sorted_stimord)): \n        traces2.append(traces[sorted_stimord[i][0]]) \n    traces=traces2 \n'
            # lines[243]='    plot_multiple_responses([responses], cp_filename, fig=model_fig, traces=traces)\n'
            # lines[366]="def plot_multiple_responses(responses, cp_filename, fig, traces):\n"
            # lines[369] = "\n"
            # lines[370] = "\n"
            # lines[371] = "\n" # n is the line number you want to edit; subtract 1 as indexing of list starts from 0
            # f.close()   # close the file and reopen in write mode to enable writing to file; you can also open in append mode and use "seek", but you will have some unwanted old data if the new data is shorter in length.
            # f = open(full_file_path, 'w')
            # f.writelines(lines)
            # f.close()

            # modify evaluator.py if present
            if not os.path.exists(os.path.join(file_path, 'evaluator.py')):
                msg = "No evaluator.py file found. \
                    Check the .zip file submitted for the optimization."
                resp = {"Status":"ERROR", "response":"KO", "message": msg}
                return resp
            else:
                pass
            #     f = open(os.path.join(file_path, 'evaluator.py'), 'r')    # pass an appropriate path of the required file
            #     lines = f.readlines()
            #     lines[167]='    #print param_names\n'
            #     f.close()   # close the file and reopen in write mode to enable writing to file; you can also open in append mode and use "seek", but you will have some unwanted old data if the new data is shorter in length.
            #     f = open(os.path.join(file_path, 'evaluator.py'), 'w')    # pass an appropriate path of the required file
            #     f.writelines(lines)
            #     f.close()

            if up_folder not in sys.path:
                sys.path.append(up_folder)

            fig_folder = os.path.join(up_folder, 'figures')

        if os.path.exists(fig_folder):
            shutil.rmtree(fig_folder)
        os.makedirs(fig_folder)

        checkpoints_folder = os.path.join(up_folder, 'checkpoints')

        try:
            if 'checkpoint.pkl' not in os.listdir(checkpoints_folder):
                for files in os.listdir(checkpoints_folder):
                    if files.endswith('pkl'):
                        shutil.copy(os.path.join(checkpoints_folder, files), os.path.join(checkpoints_folder, 'checkpoint.pkl'))
                        os.remove(os.path.join(up_folder, 'checkpoints', files))

                f = open(os.path.join(up_folder, 'opt_neuron.py'), 'r')
                lines = f.readlines()

                new_line = ["import matplotlib \n"]
                new_line.append("matplotlib.use('Agg') \n")
                for i in lines:
                    new_line.append(i)
                f.close()
                f = open(os.path.join(up_folder, 'opt_neuron.py'), 'w')
                f.writelines(new_line)
                f.close()

                r_0_fold = os.path.join(up_folder, 'r_0')
                if os.path.isdir(r_0_fold):
                    shutil.rmtree(r_0_fold)
                os.mkdir(r_0_fold)

        except Exception as e:
            msg = traceback.format_exception(*sys.exc_info())
            resp = {"response": "KO", "msg": msg}

        return {"response": "OK", "up_folder": up_folder}


class OptFolderManager:

    @classmethod
    def create_opt_res_zip(cls, fin_folder="", filetype="", wf_id=""):
        """
        Create a to-be-downloaded zip in results folder
        """

        # if a zip file is already present do nothing
        listdir = os.listdir(fin_folder) 
        archive_to = os.path.join(fin_folder, "..", wf_id + "_opt_res")
        
        if len(listdir) > 0:
            parent_folder = os.path.dirname(fin_folder)
            opt_fold = os.path.basename(fin_folder)
            zfFileName = wf_id + "_opt_res"
            zfName = os.path.join(parent_folder, zfFileName + ".zip")
            zipf = zipfile.ZipFile(zfName, 'w', zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(fin_folder):
                for f in files:
                    f_wrt = os.path.join(root, f)
                    f_wrt_fin = f_wrt.replace(fin_folder, os.path.join(parent_folder, zfFileName))
                    zipf.write(f_wrt, f_wrt_fin.replace(parent_folder, '', 1))
            return True
        return False

    @classmethod
    def createzip(cls, fin_opt_folder, source_opt_zip, opt_name, source_feat, gennum, offsize, zfName, hpc, execname="", joblaunchname=""):
        """
        Create zip file to be submitted to HPC systems
        """

        # folder named as the optimization
        if not os.path.exists(fin_opt_folder):
            os.makedirs(fin_opt_folder)
        else:
            shutil.rmtree(fin_opt_folder)
            os.makedirs(fin_opt_folder)

        # unzip source optimization file 
        z = zipfile.ZipFile(source_opt_zip, 'r')
        z.extractall(path=fin_opt_folder)
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
            morph_json = json.load(morph_file, object_pairs_hook=collections.OrderedDict)
            morph_file.close()
        with open(fin_feat_path, 'r') as feat_file:
            feat_json = json.load(feat_file, object_pairs_hook=collections.OrderedDict)
            feat_file.close()
        with open(fin_prot_path, 'r') as prot_file:
            prot_json = json.load(prot_file, object_pairs_hook=collections.OrderedDict)
            prot_file.close()

        os.remove(fin_feat_path)
        os.remove(fin_prot_path)

        fin_key = list(morph_json.keys())[0]
        feat_key = list(feat_json.keys())[0]
        prot_key = list(prot_json.keys())[0]

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

        if hpc == "NSG":
            OptFolderManager.remove_files_from_opt_folder(fin_dest_dir=fin_dest_dir, hpc=hpc)
            OptFolderManager.add_exec_file(hpc=hpc, fin_dest_dir=fin_dest_dir, execname=execname, gennum=gennum, offsize=offsize, mod_path="")
        elif hpc == "JURECA":
            OptFolderManager.remove_files_from_opt_folder(fin_dest_dir=fin_dest_dir, hpc=hpc)
            OptFolderManager.add_exec_file(hpc, fin_dest_dir=fin_dest_dir, execname=execname, gennum=gennum, offsize=offsize, mod_path="", joblaunchname=joblaunchname)
        elif hpc == "DAINT-CSCS" or hpc == "SA-CSCS":
            OptFolderManager.remove_files_from_opt_folder(fin_dest_dir=fin_dest_dir, hpc=hpc)
            exc_name, job = OptFolderManager.add_exec_file(hpc, fin_dest_dir=fin_dest_dir, execname=execname, gennum=gennum, offsize=offsize, mod_path="", joblaunchname=joblaunchname, foldernameOPTstring=opt_name)
            print('================= FILES ==================')
            print(exc_name, job)

        # build optimization folder name
        crr_dir_opt = os.path.join(fin_opt_folder, opt_name)

        foo = zipfile.ZipFile(zfName, 'w')

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
        
        # full_execname = os.path.join(fin_dest_dir, execname)
        # full_joblaunchname = os.path.join(fin_dest_dir, joblaunchname)

        # if os.path.exists(full_execname):
        #     foo.write(full_execname, full_execname.replace(fin_opt_folder, '', 1))
        # if os.path.exists(full_joblaunchname):
        #     foo.write(full_joblaunchname, full_joblaunchname.replace(fin_opt_folder, '', 1))

        for root, dirs, files in os.walk(fin_opt_folder):
            if (root == os.path.join(crr_dir_opt, 'morphology')) or \
                (root == os.path.join(crr_dir_opt, 'config')) or \
                (root == os.path.join(crr_dir_opt, 'mechanisms')) or \
                    (root == os.path.join(crr_dir_opt, 'model')):

                for f in files:
                    final_zip_fname = os.path.join(root, f)
                    foo.write(final_zip_fname, final_zip_fname.replace(fin_opt_folder, '', 1))

            if root == os.path.join(crr_dir_opt, 'checkpoints') or (root == os.path.join(crr_dir_opt, 'figures')):
                        final_zip_fold_name = os.path.join(root)
                        foo.write(final_zip_fold_name, final_zip_fold_name.replace(fin_opt_folder, '', 1))

            if root == crr_dir_opt:
                for f in files:
                    print(f)
                    if f.endswith('.py') or (f.endswith('.sbatch') and (hpc == "DAINT-CSCS" or hpc == "SA-CSCS")):
                        final_zip_fname = os.path.join(root, f)
                        foo.write(final_zip_fname, final_zip_fname.replace(fin_opt_folder, '', 1))
        foo.close()
        
    @classmethod
    def remove_files_from_opt_folder(cls, fin_dest_dir, hpc):
        """
        Remove unwanted files from the folder to be zipped
        """
        # 'NSG'
        if hpc == "NSG":
            for item in os.listdir(fin_dest_dir):
                if item.startswith('init') or item.endswith('.zip') or item.startswith('__MACOSX'):
                    os.remove(os.path.join(fin_dest_dir, item))
        # 'DAINT-CSCS'
        elif hpc == "DAINT-CSCS" or hpc == "SA-CSCS":
            for item in os.listdir(fin_dest_dir):
                if item.startswith("ipyparallel.sbatch") or item.startswith("zipfolder.py") or \
                        item.startswith("__init__.py") or item.startswith('__MACOSX'):
                    os.remove(os.path.join(fin_dest_dir, item))

    @classmethod
    def add_exec_file(cls, hpc, fin_dest_dir="./", execname="fn", gennum=24, offsize=12, mod_path="", joblaunchname="jln", foldernameOPTstring = ""):

        # Neuro Science Gateway
        if hpc == "NSG":
            with open(os.path.join(fin_dest_dir, execname), 'w') as f:
                f.write('import os')
                f.write('\n')
                f.write('os.system(\'python opt_neuron.py --max_ngen=' + str(gennum) +
                        ' --offspring_size=' + str(offsize) + ' --start --checkpoint ./checkpoints/checkpoint.pkl\')')
                f.write('\n')
            f.close()
            return execname

        # Juelich Jureca
        elif hpc == "JURECA":
            with open(os.path.join(fin_dest_dir, execname), 'w') as f:
                # TODO: compress f.write calls with single call
                f.write("#!/bin/bash -x")
                f.write('\n')
                f.write('\n')
                f.write("set -e")
                f.write('\n')
                f.write("set -x")
                f.write('\n')
                f.write('\n')
                f.write("module purge all")
                f.write('\n')
                f.write("export  MODULEPATH=/homec/vsk25/vsk2501/local/jureca_booster-20180226142237/share/modules:$MODULEPATH")
                f.write('\n')
                f.write("module load bpopt")
                f.write('\n')
                f.write("export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}")
                f.write('\n')
                f.write('\n')
                f.write("OFFSPRING_SIZE=" + str(gennum))
                f.write('\n')
                f.write("MAX_NGEN=" + str(offsize))
                f.write('\n')
                f.write('\n')
                f.write("export USEIPYP=1")
                f.write('\n')
                f.write("export IPYTHONDIR=\"`pwd`/.ipython\"")
                f.write('\n')
                f.write("export IPYTHON_PROFILE=ipyparallel.${SLURM_JOBID}")
                f.write('\n')
                f.write("ipcontroller --init --sqlitedb --ip='*' --profile=${IPYTHON_PROFILE} &")
                f.write('\n')
                f.write("sleep 30")
                f.write('\n')
                f.write("srun ipengine --profile=${IPYTHON_PROFILE} &")
                f.write('\n')
                f.write('\n')
                f.write("CHECKPOINTS_DIR=\"checkpoints/run.${SLURM_JOBID}\"")
                f.write('\n')
                f.write("mkdir -p ${CHECKPOINTS_DIR}")
                f.write('\n')
                f.write('\n')
                f.write("pids=\"\"")
                f.write('\n')
                f.write("for seed in `seq 3 3`")
                f.write('\n')
                f.write("do")
                f.write('\n')
                f.write("    BLUEPYOPT_SEED=${seed} python opt_neuron.py --offspring_size=${OFFSPRING_SIZE} --max_ngen=${MAX_NGEN} --start --checkpoint \"${CHECKPOINTS_DIR}/seed${seed}.pkl\" &")
                f.write('\n')
                f.write("    pids=\"${pids} $!\"")
                f.write('\n')
                f.write("done")
                f.write('\n')
                f.write('\n')
                f.write("wait $pids")
                f.write('\n')

            # create sh for launching
            with open(os.path.join(fin_dest_dir, joblaunchname), 'w') as f:
                f.write("module purge all")
                f.write('\n')
                f.write("export MODULEPATH=" + mod_path + ":$MODULEPATH")
                f.write('\n')
                f.write("module load bpopt")
                f.write('\n')
                f.write("nrnivmodl ./mechanisms")
                f.write('\n')
                f.write("sbatch " + execname)

            return [execname, joblaunchname]

        # CSCS Pizdaint
        elif hpc == "DAINT-CSCS" or hpc == "SA-CSCS":
            # with open(os.path.join(fin_dest_dir, execname),'w') as f:
            #     f.write('import os\n')
            #     f.write('import zipfile\n')
            #     f.write('retval = os.getcwd()\n')
            #     f.write('print "Current working directory %s" % retval\n')
            #     f.write('os.chdir(\'..\')\n')
            #     f.write('retval = os.getcwd()\n')
            #     f.write('print "Current working directory %s" % retval\n')
            #     f.write('def zipdir(path, ziph):\n')
            #     f.write('    for root, dirs, files in os.walk(path):\n')
            #     f.write('        for file in files:\n')
            #     f.write('            ziph.write(os.path.join(root, file))\n')
            #     f.write('zipf = zipfile.ZipFile(\'output.zip\', \'w\')\n')
            #     f.write('zipdir(\''+foldernameOPTstring+'/\', zipf)\n')
            #
            # # create file for launching job
            # with open(os.path.join(fin_dest_dir, joblaunchname), 'w') as f:
            #     f.write('#!/bin/bash -l\n')
            #     f.write('\n')
            #     f.write('mkdir logs\n')
            #     f.write('#SBATCH --job-name=bluepyopt_ipyparallel\n')
            #     f.write('#SBATCH --error=logs/ipyparallel_%j.log\n')
            #     f.write('#SBATCH --output=logs/ipyparallel_%j.log\n')
            #     f.write('#SBATCH --partition=normal\n')
            #     f.write('#SBATCH --constraint=mc\n')
            #     # f.write('#SBATCH --mem=10GB\n')
            #     f.write('\n')
            #     f.write('export PMI_NO_FORK=1\n')
            #     f.write('export PMI_NO_PREINITIALIZE=1\n')
            #     f.write('export PMI_MMAP_SYNC_WAIT_TIME=300\n')
            #     f.write('\n')
            #     f.write('set -e\n')
            #     f.write('set -x\n')
            #     f.write('\n')
            #     f.write('export MODULEPATH=/users/bp000178/ich002/software/daint/' +
            #             'local-20191129103029/share/modules:$MODULEPATH;module load bpopt\n')
            #     f.write('\n')
            #     f.write('export USEIPYP=1\n')
            #     f.write('export IPYTHONDIR="`pwd`/.ipython"\n')
            #     f.write('export IPYTHON_PROFILE=ipyparallel.${SLURM_JOBID}\n')
            #     f.write('ipcontroller --init --sqlitedb --ip=\'*\' --profile=${IPYTHON_PROFILE} &\n')
            #     f.write('sleep 30\n')
            #     f.write('srun ipengine --profile=${IPYTHON_PROFILE} &\n')
            #     f.write('CHECKPOINTS_DIR="checkpoints"\n')
            #     f.write('nrnivmodl mechanisms\n')
            #     f.write('python opt_neuron.py --offspring_size='+ offsize +
            #             ' --max_ngen=' + gennum + ' --start --checkpoint "${CHECKPOINTS_DIR}/checkpoint.pkl"\n')
            #     f.write('python zipfolder.py')
            #     f.write('\n')
            # f.close()

            # with open(os.path.join(fin_dest_dir, execname),'w') as f:
            #     f.write('import os\n')
            #     f.write('import zipfile\n')
            #     f.write('retval = os.getcwd()\n')
            #     f.write('print("Current working directory %s" % retval)\n')
            #     f.write('os.chdir(\'..\')\n')
            #     f.write('retval = os.getcwd()\n')
            #     f.write('print("Current working directory %s" % retval)\n')
            #     f.write('def zipdir(path, ziph):\n')
            #     f.write('    for root, dirs, files in os.walk(path):\n')
            #     f.write('        for file in files:\n')
            #     f.write('            ziph.write(os.path.join(root, file))\n')
            #     f.write('zipf = zipfile.ZipFile(\'output.zip\', \'w\')\n')
            #     f.write('zipdir(\'' + foldernameOPTstring + '/\', zipf)\n')
            # f.close()
            # with open(os.path.join(fin_dest_dir, joblaunchname), 'w') as f:
            #     f.write('#!/bin/bash -l\n')
            #     f.write('\n')
            #     f.write('mkdir logs\n')
            #     f.write('#SBATCH --job-name=bluepyopt_ipyparallel\n')
            #     f.write('#SBATCH --error=logs/ipyparallel_%j.log\n')
            #     f.write('#SBATCH --output=logs/ipyparallel_%j.log\n')
            #     f.write('#SBATCH --partition=normal\n')
            #     f.write('#SBATCH --constraint=mc\n')
            #     f.write('\n')
            #     f.write('export PMI_NO_FORK=1\n')
            #     f.write('export PMI_NO_PREINITIALIZE=1\n')
            #     f.write('export PMI_MMAP_SYNC_WAIT_TIME=300 \n')
            #     f.write('set -e\n')
            #     f.write('set -x\n')
            #     f.write('\n')
            #     f.write('module load daint-mc cray-python/3.8.2.1 PyExtensions/python3-CrayGNU-20.08\n')
            #     f.write(
            #         'module use /apps/hbp/ich002/hbp-spack-deployments/softwares/15-09-2020/install/modules/tcl/cray-cnl7-haswell\n')
            #     f.write('module load neuron/7.8.0c\n')
            #     f.write('module load py-bluepyopt\n')
            #     f.write('nrnivmodl mechanisms\n')
            #     f.write('\n')
            #     f.write('export USEIPYP=1\n')
            #     f.write('export IPYTHONDIR="`pwd`/.ipython"\n')
            #     f.write('export IPYTHON_PROFILE=ipyparallel.${SLURM_JOBID}\n')
            #     f.write('ipcontroller --init --sqlitedb --ip=\'*\' --profile=${IPYTHON_PROFILE} &\n')
            #     f.write('sleep 30\n')
            #     f.write('srun ipengine --profile=${IPYTHON_PROFILE} &\n')
            #     f.write('CHECKPOINTS_DIR="checkpoints"\n')
            #     f.write('python opt_neuron.py --offspring_size=' + offsize +
            #             ' --max_ngen=' + gennum + ' --start --checkpoint "${CHECKPOINTS_DIR}/checkpoint.pkl"\n')
            #     f.write('python zipfolder.py')
            #     f.write('\n')
            # f.close()

            with open(os.path.join(fin_dest_dir, execname), 'w') as f:
                f.write('import os\n')
                f.write('import zipfile\n')
                f.write('retval = os.getcwd()\n')
                f.write('print("Current working directory %s" % retval)\n')
                f.write('os.chdir(\'..\')\n')
                f.write('retval = os.getcwd()\n')
                f.write('print("Current working directory %s" % retval)\n')
                f.write('def zipdir(path, ziph):\n')
                f.write('    for root, dirs, files in os.walk(path):\n')
                f.write('        for file in files:\n')
                f.write('            ziph.write(os.path.join(root, file))\n')
                f.write('zipf = zipfile.ZipFile(\'output.zip\', \'w\')\n')
                f.write('zipdir(\'' + foldernameOPTstring + '/\', zipf)\n')
            f.close()
            # create file for launching job
            with open(os.path.join(fin_dest_dir, joblaunchname), 'w') as f:
                f.write('#!/bin/bash -l\n')
                f.write('\n')
                f.write('mkdir logs\n')
                f.write('#SBATCH --job-name=bluepyopt_ipyparallel\n')
                f.write('#SBATCH --error=logs/ipyparallel_%j.log\n')
                f.write('#SBATCH --output=logs/ipyparallel_%j.log\n')
                f.write('#SBATCH --partition=normal\n')
                f.write('#SBATCH --constraint=mc\n')
                f.write('\n')
                f.write('export PMI_NO_FORK=1\n')
                f.write('export PMI_NO_PREINITIALIZE=1\n')
                f.write('export PMI_MMAP_SYNC_WAIT_TIME=300 \n')
                f.write('set -e\n')
                f.write('set -x\n')
                f.write('\n')
                f.write('module load daint-mc cray-python/3.8.2.1 PyExtensions/python3-CrayGNU-20.08\n')
                f.write(
                    'module use /apps/hbp/ich002/hbp-spack-deployments/softwares/15-09-2020/install/modules/tcl/cray-cnl7-haswell\n')
                f.write('module load neuron/7.8.0c\n')
                f.write('module load py-bluepyopt\n')
                f.write('nrnivmodl mechanisms\n')
                f.write('\n')
                f.write('export USEIPYP=1\n')
                f.write('export IPYTHONDIR="`pwd`/.ipython"\n')
                f.write('export IPYTHON_PROFILE=ipyparallel.${SLURM_JOBID}\n')
                f.write('ipcontroller --init --sqlitedb --ip=\'*\' --profile=${IPYTHON_PROFILE} &\n')
                f.write('sleep 30\n')
                f.write('srun ipengine --profile=${IPYTHON_PROFILE} &\n')
                f.write('CHECKPOINTS_DIR="checkpoints"\n')
                f.write('python opt_neuron.py --offspring_size=' + str(offsize) +
                        ' --max_ngen=' + str(gennum) + ' --start --checkpoint "${CHECKPOINTS_DIR}/checkpoint.pkl"\n')
                f.write('python zipfolder.py')
                f.write('\n')
            f.close()

            print(os.listdir())
            print(os.getcwd())

            return [execname, joblaunchname]


class OptSettings:

    params_default = {
        'wf_id': "",
        'gennum': 2,
        'offsize': 10,
        'nodenum': "",
        'corenum': "",
        'runtime': "",
        'hpc_sys':  "",
        'opt_sub_param_file': "",
        "job_title": ""
    }

    @classmethod
    def get_params_default(cls):
        params = {
            'wf_id': cls.params_default["wf_id"],
            'number_of_cores': cls.params_default["corenum"],
            'number_of_nodes': cls.params_default["nodenum"],
            'runtime': cls.params_default["runtime"],
            'number_of_generations': cls.params_default["gennum"],
            'offspring_size': cls.params_default["offsize"],
            'hpc_sys': cls.params_default["hpc_sys"],
            'job_title': cls.params_default["job_title"]
        }

        return params

    @classmethod
    def print_opt_params(cls, **kwargs):

        if 'wf_id' in kwargs:
            wf_id = kwargs['wf_id']
        else:
            wf_id = cls.params_default['wf_id']

        if 'gennum' in kwargs:
            gennum = kwargs['gennum']
        else:
            gennum = cls.params_default['gennum']

        if 'offsize' in kwargs:
            offsize = kwargs['offsize']
        else:
            offsize = cls.params_default['offsize']

        if 'nodenum' in kwargs:
            nodenum = kwargs['nodenum']
        else:
            nodenum = cls.params_default['nodenum']

        if 'corenum' in kwargs:
            corenum = kwargs['corenum']
        else:
            corenum = cls.params_default['corenum']

        if 'runtime' in kwargs:
            runtime = kwargs['runtime']
        else:
            runtime = cls.params_default['runtime']

        if 'hpc_sys' in kwargs:
            hpc_sys = kwargs['hpc_sys']
        else:
            hpc_sys = cls.params_default['hpc_sys']

        if 'opt_sub_param_file' in kwargs:
            opt_sub_param_file = kwargs['opt_sub_param_file']
        else:
            opt_sub_param_file = cls.params_default['opt_sub_param_file']

        if 'job_title' in kwargs:
            job_title = kwargs['job_title']
        else:
            job_title = cls.params_default['job_title']

        params = {
            'wf_id': wf_id,
            'number_of_cores': corenum,
            'number_of_nodes': nodenum,
            'runtime': runtime,
            'number_of_generations': gennum,
            'offspring_size': offsize,
            "hpc_sys": hpc_sys,
            "job_title": job_title
        }

        if 'project' in kwargs:
            params.update({'project': kwargs['project']})

        with open(opt_sub_param_file, 'w') as pf:
            json.dump(params, pf)

