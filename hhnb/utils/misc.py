from hh_neuron_builder.settings import FERNET_KEY, NSG_KEY
from hhnb.core.response import ResponseUtil
from cryptography.fernet import Fernet

import pyunicore.client as unicore_client
import xml.etree.ElementTree
import requests
import os
import json


class Cypher:

    @staticmethod
    def encrypt(plain_text, at_time=None):
        if type(plain_text) == str:
            data = bytes(plain_text, 'utf-8')
        f = Fernet(FERNET_KEY)
        if at_time:
            token = f.encrypt_at_time(data, at_time)
        else:
            token = f.encrypt(data)
        cipher_text = token.decode('utf-8')
        return cipher_text

    @staticmethod
    def decrypt(cipher_text, at_time=None):
        if type(cipher_text) == str:
            token = bytes(cipher_text, 'utf-8')
        f = Fernet(FERNET_KEY)
        if at_time:
            plaint_text = f.decrypt_at_time(token, at_time)
        else:
            plaint_text = f.decrypt(token)
        return plaint_text


class JobHandler:

    class UnicoreClientException(Exception):
        pass


    def __init__(self):
        self._SA_DAINT_URL = 'https://bspsa.cineca.it/jobs/pizdaint/hhnb_daint_cscs/'
        self._NSG_URL = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'
        
        self._DAINT_CSCS = 'DAINT-CSCS'
        self._SA_CSCS = 'SA-CSCS'
        self._NSG = 'NSG'
        self._TAGS = ['hhnb']

    def _get_nsg_headers(self):
        return {
            'cipres-appkey': NSG_KEY
        }

    def _get_nsg_payload(self, core_num, node_num, runtime):
        return {
            'tool': 'BLUEPYOPT_TG',
            'metadata.statusEmail': 'false',
            'vparam.number_cores_': core_num,
            'vparam.number_nodes_': node_num,
            'vparam.runtime_': runtime,
            'vparam.filename_': 'init.py'
        } 

    def _submit_on_nsg(self, zip_file, settings):

        username = Cypher.decrypt(settings['username_submit'])
        password = Cypher.decrypt(settings['password_submit'])
                
        payload = self._get_nsg_payload(core_num=settings['core-num'],
                                        node_num=settings['node-num'],
                                        runtime=settings['runtime'])

        headers = self._get_nsg_headers()

        files = {'input.infile_': open(zip_file + '.zip', 'rb')}
        r = requests.post(url=f'{self._NSG_URL}/job/{username}', 
                          auth=(username, password),
                          data=payload,
                          headers=headers,
                          files=files)
        
        if r.status_code == 200:
            root = xml.etree.ElementTree.fromstring(r.text)

            # extract job selfuri and resulturi
            outputuri = root.find('resultsUri').find('url').text
            selfuri = root.find('selfUri').find('url').text

            # extract job handle
            r = requests.get(selfuri, auth=(username, password), headers=headers)
            root = xml.etree.ElementTree.fromstring(r.text)
            if not r.status_code == 200:
                return ResponseUtil.ko_response(r.text)

            return ResponseUtil.ok_response('Job submitted correctly on NSG')            

        return ResponseUtil.ko_response(r.text)

    def _get_nsg_job_list(self, nsg_user, username, password):
        r_all = requests.get(url=f)

        

    def _get_unicore_command(self, zip_name):
        command = 'unzip ' + zip_name + '; cd ' + zip_name.split('.zip')[0] \
                + ' chmod +rx *.sbatch; ./ipyparallel.sbatch'
        return command

    def _get_unicore_job_description(self, command, job_name, node_num, 
                                     core_num, runtime, project):
        return {
            'Executable': command,
            'Name': job_name,
            'Resources': {
                'Nodes': node_num,
                'CPUsPerNode': core_num,
                'Runtime': runtime,
                'NodeConstraints': 'mc',
                'Project': project
            },
            'Tags': [
                self._JOB_TAG,
            ]
        }

    def _initialize_unicore_client(self, hpc, token):
        transport = unicore_client.Transport(token)
        hpc_url = unicore_client.get_sites(transport)[hpc]
        client = unicore_client.Client(transport, hpc_url)
        if client.access_info()['role']['selected'] == 'anonymous':
            raise self.UnicoreClientException('Unable to login user')
        return client

    def _submit_on_unicore(self, hpc, token, zip_file, settings):

        zip_name = os.path.split(zip_file)[1]
        job_description = self._get_unicore_job_description(
            command=self._get_unicore_command(zip_name),
            job_name=zip_name,
            node_num=settings['node-num'],
            core_num=settings['core-num'],
            runtime=settings['runtime'],
            project=settings['project']
        )

        client = self._initialize_unicore_client()        
        job = client.new_job(job_description=job_description, inputs=[zip_file])
        print(job)

        return ResponseUtil.ok_response('Job submitted correctly on DAINT-CSCS')

    def _get_jobs_on_unicore(self, hpc, token):
        client = self._initialize_unicore_client(hpc, token)
        jobs_url = client.links['jobs'] + '?tags=hhnb' 
        jobs = client.transport.get(url=jobs_url)['jobs']
        return jobs

    def _get_jobs_properties_on_unicore(self, hpc, token):
        client = self._initialize_unicore_client(hpc, token)
        jobs = client.get_jobs(tags=self._TAGS)
        details = {}
        for job in jobs:
            props = job.properties
            details.update({job.job_id: {
                'status': props['status'],
                'name': props['name'],
                'submissionTime': props['submissionTime'],
                'terminationTime': props['terminationTime']
            }})
        return details

    def _get_job_results_on_unicore(self, hpc, token, job_id):
        client = self._initialize_unicore_client(hpc, token)
        job_url = client.links['jobs'] + '/' + job_id
        print(job_url)
        job = unicore_client.Job(client.transport, job_url)
        storage = job.working_dir
        return storage.listdir()

    def _get_service_account_payload(self, command, node_num, core_num, runtime, title):
        return {
            'command': command,
            'node_number': node_num,
            'core_number': core_num,
            'runtime': runtime,
            'title': title,
        }

    def _get_service_account_headers(self, token, zip_name, payload):
        return {
            'Authorization': 'Bearer ' + token,
            'Content-Disposition': 'attachment;filename=' + zip_name + '.zip',
            'payload': json.dumps(payload)
        }

    def _submit_on_service_account(self, token, zip_file, settings):
        
        zip_name = os.path.split(zip_file)[1]
        payload = self._get_service_account_payload(
            command=self._get_unicore_command(zip_name),
            node_num=settings['node-num'],
            core_num=settings['core-num'],
            runtime=settings['runtime'],
            title=zip_name
        )
        
        headers = self._get_service_account_headers(token, zip_name, payload)
        job_file = {'file': open(zip_file)}

        r = requests.post(url=self.SA_DAINT_URL, headers=headers, files=job_file)
        
        if r.status_code == 400:
            return ResponseUtil.ko_response(r.text)
        
        return ResponseUtil.ok_response('Job submitted correctly on SA-CSCS')

    @classmethod
    def submit_job(cls, user, zip_file, settings):
        
        job_handler = cls()
        if settings['hpc'] == job_handler._NSG:
            return job_handler._submit_on_nsg(zip_file, settings)
        elif settings['hpc'] == job_handler._DAINT_CSCS:
            return job_handler._submit_on_unicore(job_handler._DAINT_CSCS, user.get_token(),
                                                  zip_file, settings)
        elif settings['hpc'] == job_handler._SA_CSCS:
            return job_handler._submit_on_service_account(user.get_token(),
                                                          zip_file, settings)
        return ResponseUtil.ko_response('Something goes wrong.')
       
    @classmethod
    def fetch_jobs_list(cls, hpc, user):

        job_handler = cls()
        if hpc == job_handler._DAINT_CSCS:

            jobs = job_handler._get_jobs_on_unicore(hpc, user.get_token())

        return {'jobs': jobs}

    @classmethod
    def fetch_jobs_details(cls, hpc, user):

        job_handler = cls()
        if hpc == job_handler._DAINT_CSCS:

            details = job_handler._get_jobs_properties_on_unicore(hpc, user.get_token())
            


        return {'jobs': details}

    @classmethod
    def fetch_job_files(cls, hpc, job_id, user):

        job_handler = cls()
        if hpc == job_handler._DAINT_CSCS:

            file_list = job_handler._get_job_results_on_unicore(hpc, user.get_token(), job_id)

        return file_list