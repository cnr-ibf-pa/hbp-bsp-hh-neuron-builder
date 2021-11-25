from hh_neuron_builder.settings import NSG_KEY
from hhnb.core.response import ResponseUtil
from collections import OrderedDict

from hhnb.core.security import Cypher

import pyunicore.client as unicore_client
import xml.etree.ElementTree
import requests
import os
import json
import re
import datetime


def str_to_datetime(datetime_string, format=None):

    date_re = '\d{4}(-\d{2}){2}'
    time_re = '(\d{2}:){2}\d{2}'
    
    match = re.match(date_re + 'T' + time_re + '\+\d{4}', datetime_string)
    if match and match.end() == len(datetime_string):
        format = '%Y-%m-%dT%H:%M:%S%z'
    
    match = re.match(date_re + 'T' + time_re + 'Z', datetime_string)
    if match and match.end() == len(datetime_string):
        format = '%Y-%m-%dT%H:%M:%SZ'
    
    return datetime.datetime.strptime(datetime_string, format).replace(tzinfo=None)


def verify_uploaded_archive(arch_file):
    print(arch_file) 



class JobHandler:

    class UnicoreClientException(Exception):
        pass

    class ServiceAccountException(Exception):
        pass

    class JobsFilesNotFound(Exception):
        pass


    def __init__(self):
        self._SA_DAINT_JOB_URL = 'https://bspsa.cineca.it/jobs/pizdaint/hhnb_daint_cscs/'
        self._SA_DAINT_FILES_URL = 'https://bspsa.cineca.it/files/pizdaint/hhnb_daint_cscs/'
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
            'tool': 'BLUEPYOPT_EXPANSE',
            'metadata.statusEmail': 'false',
            'vparam.number_cores_': core_num,
            'vparam.number_nodes_': node_num,
            'vparam.runtime_': runtime,
            'vparam.filename_': 'init.py'
        } 

    def _submit_on_nsg(self, user, zip_file, settings):
        payload = self._get_nsg_payload(core_num=settings['core-num'],
                                        node_num=settings['node-num'],
                                        runtime=settings['runtime'])

        headers = self._get_nsg_headers()

        files = {'input.infile_': open(zip_file, 'rb')}
        r = requests.post(url=f'{self._NSG_URL}/job/{user.get_username()}', 
                          auth=(user.get_username(), user.get_password()),
                          data=payload,
                          headers=headers,
                          files=files,
                          verify=False)
        
        print(r.status_code, r.content)
        
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

    def _get_nsg_job_list(self, user):
        r = requests.get(url=f'{self._NSG_URL}/job/{user.get_username()}',
                         auth=(user.get_username(), user.get_password()),
                         headers=self._get_nsg_headers())
        print(r.status_code, r.text)
        jobs = {}
        if r.status_code == 200:
            root = xml.etree.ElementTree.fromstring(r.text)
            job_list = root.find('jobs')
            
            for job in job_list.findall('jobstatus'):
                job_title = job.find('selfUri').find('title').text
                job_url = job.find('selfUri').find('url').text

        return None        

    def _get_unicore_command(self, zip_name):
        command = 'unzip ' + zip_name + '; cd ' + zip_name.split('.zip')[0] \
                + '; chmod +rx *.sbatch; ./ipyparallel.sbatch'
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
            'Tags': self._TAGS
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
            job_name=zip_name.split('.')[0],
            node_num=settings['node-num'],
            core_num=settings['core-num'],
            runtime=settings['runtime'],
            project=settings['project']
        )

        client = self._initialize_unicore_client(hpc, token)        
        job = client.new_job(job_description=job_description, inputs=[zip_file])
        return ResponseUtil.ok_response('Job submitted correctly on DAINT-CSCS')

    def _get_jobs_on_unicore(self, hpc, token):
        client = self._initialize_unicore_client(hpc, token)
        return client.get_jobs(tags=self._TAGS)

    def _get_job_results_on_unicore(self, hpc, token, job_id):
        client = self._initialize_unicore_client(hpc, token)
        print(client.access_info())
        job_url = client.links['jobs'] + '/' + job_id
        job = unicore_client.Job(client.transport, job_url)
        storage = job.working_dir
        return {'root_url': 'unicore', 'file_list': storage.listdir()}

    def _get_service_account_payload(self, command, node_num, core_num, runtime, title):
        return {
            'command': command,
            'node_number': node_num,
            'core_number': core_num,
            'runtime': runtime,
            'title': title,
        }

    def _get_service_account_headers(self, token, zip_name=None, payload=None):
        headers = {'Authorization': 'Bearer ' + token}
        if zip_name:
            headers.update({'Content-Disposition': 'attachment;filename=' + zip_name + '.zip'})
        if payload:
            headers.update({'payload': json.dumps(payload)})
        return headers

    def _submit_on_service_account(self, token, zip_file, settings):
        zip_name = os.path.split(zip_file)[1]
        payload = self._get_service_account_payload(
            command=self._get_unicore_command(zip_name),
            node_num=settings['node-num'],
            core_num=settings['core-num'],
            runtime=settings['runtime'],
            title=zip_name.split('.')[0]
        )
        headers = self._get_service_account_headers(token, zip_name, payload)
        job_file = {'file': open(zip_file, 'rb')}

        r = requests.post(url=self._SA_DAINT_JOB_URL, headers=headers, files=job_file)
        if r.status_code == 400:
            
            return ResponseUtil.ko_response(r.text)
        
        return ResponseUtil.ok_response('Job submitted correctly on SA-CSCS')

    def _get_jobs_on_service_account(self, token):
        headers = self._get_service_account_headers(token)
        r = requests.get(url=self._SA_DAINT_JOB_URL, headers=headers)
        if r.status_code != 200:
            raise self.ServiceAccountException(r.content, r.status_code)
        return r.json()

    def _get_job_results_on_service_account(self, token, job_id):
        headers = self._get_service_account_headers(token)
        r = requests.get(url=self._SA_DAINT_FILES_URL + job_id + '/', headers=headers)
        if r.status_code == 404:
            raise self.JobsFilesNotFound('Job "%s" has expired and no one files is present' % job_id)
        if r.status_code != 200:
            raise self.ServiceAccountException(r.content, r.status_code)
        return {'root_url': self._SA_DAINT_FILES_URL + job_id, 'file_list': r.json()}
          

    @classmethod
    def submit_job(cls, user, zip_file, settings):
        
        job_handler = cls()
        if settings['hpc'] == job_handler._NSG:
            return job_handler._submit_on_nsg(user.get_nsg_user(), zip_file, settings)
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
        jobs = {}

        if hpc == job_handler._NSG:
            raw_jobs = job_handler._get_nsg_job_list(user.get_nsg_user())

        elif hpc == job_handler._DAINT_CSCS:
            raw_jobs = job_handler._get_jobs_on_unicore(hpc, user.get_token())
            for raw_job in raw_jobs:
                props = raw_job.properties
                job = { raw_job.job_id: {
                        'workflow_id': props['name'],
                        'status': props['status'],
                        'date': str_to_datetime(props['submissionTime'])
                    }
                }
                jobs.update(job)

        elif hpc == job_handler._SA_CSCS:
            raw_jobs = job_handler._get_jobs_on_service_account(user.get_token())
            for raw_job in raw_jobs:
                job = {raw_job['job_id']: {
                    'workflow_id': raw_job['title'],
                    'status': raw_job['stage'],
                    'date': str_to_datetime(raw_job['init_date'])
                }}
                jobs.update(job)

        # sort jobs from last to first
        ordered_jobs = OrderedDict(sorted(jobs.items(),
                                          key=lambda x: x[1]['date'],
                                          reverse=True))
        return {'jobs': ordered_jobs}


    @classmethod
    def fetch_job_files(cls, hpc, job_id, user):

        job_handler = cls()
        if hpc == job_handler._DAINT_CSCS:
            file_list = job_handler._get_job_results_on_unicore(hpc=hpc, 
                                                                token=user.get_token(),
                                                                job_id=job_id)
        if hpc == job_handler._SA_CSCS:
            file_list = job_handler._get_job_results_on_service_account(token=user.get_token(),
                                                                        job_id=job_id)
        return file_list
