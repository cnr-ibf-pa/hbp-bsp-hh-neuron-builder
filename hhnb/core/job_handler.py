from hh_neuron_builder.settings import NSG_KEY
from hhnb.core.response import ResponseUtil
from hhnb.utils import messages

from collections import OrderedDict

import pyunicore.client as unicore_client
import xml.etree.ElementTree
import requests
import os
import json
import re
import datetime

import logging
logger = logging.getLogger(__name__)

LOG_ACTION = 'User: {}\tAction: {}'


def str_to_datetime(datetime_string, format=None):
    """
    Convert data string to datetime object.

    Parameters
    ----------
    datetime_string : str
        string to be converted.
    format : _type_, optional
        datetime format to convert the string. Can be
        "%Y-%m-%dT%H:%M:%S%z" or "%Y-%m-%dT%H:%M:%SZ".

    Returns
    -------
    datetime.datetime
        The string converted in datetime object.
    """

    date_re = '\d{4}(-\d{2}){2}'
    time_re = '(\d{2}:){2}\d{2}'
    
    match = re.match(date_re + 'T' + time_re + '\+\d{4}', datetime_string)
    if match and match.end() == len(datetime_string):
        format = '%Y-%m-%dT%H:%M:%S%z'
    
    match = re.match(date_re + 'T' + time_re + 'Z', datetime_string)
    if match and match.end() == len(datetime_string):
        format = '%Y-%m-%dT%H:%M:%SZ'

    return datetime.datetime.strptime(datetime_string, format).replace(tzinfo=None)


def get_expiration_time():
    """ Returns the expiration time calculated from now to thirty days."""
    return\
        datetime.datetime.strftime(
            datetime.datetime.now() + datetime.timedelta(days=30),
            '%Y-%m-%dT%H:%M:%S%z'
        )


def is_job_expired(job_details):
    """ Return true if the job is expired or false otherwise. """
    job_init_date = job_details['date']
    if job_init_date + datetime.timedelta(days=30) <\
        datetime.datetime.now().replace(microsecond=0):
        return True
    return False


class JobHandler:
    """
    Useful class to handle easly job on the HPC system.
    """

    class UnicoreClientException(Exception):
        pass

    class ServiceAccountException(Exception):
        pass

    class JobsFilesNotFound(Exception):
        pass

    class HPCException(Exception):
        pass

    def __init__(self):
        self._SA_ROOT_URL = 'https://bspsa.cineca.it/'
        self._SA_DAINT_JOB_URL = self._SA_ROOT_URL + 'jobs/pizdaint/hhnb_daint_cscs/'
        self._SA_DAINT_FILES_URL = self._SA_ROOT_URL + 'files/pizdaint/hhnb_daint_cscs/'
        self._SA_NSG_JOB_URL = self._SA_ROOT_URL + 'jobs/nsg/hhnb_nsg/'
        self._SA_NSG_FILES_URL = self._SA_ROOT_URL + 'files/nsg/hhnb_nsg/'
        self._NSG_URL = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'
        self._DAINT_URL = 'https://brissago.cscs.ch:8080/DAINT-CSCS/rest/core'
        
        self._DAINT_CSCS = 'DAINT-CSCS'
        self._SA_CSCS = 'SA-CSCS'
        self._NSG = 'NSG'
        self._SA_NSG = 'SA-NSG'
        self._NSG_TOOL = 'BLUEPYOPT_EXPANSE'
        self._TAGS = ['hhnb']

    def _get_nsg_headers(self):
        """ Returns NSG headers. """
        return {
            'cipres-appkey': NSG_KEY
        }

    def _get_nsg_payload(self, job_name, core_num, node_num, runtime):
        """
        Returns NSG payload.

        Parameters
        ----------
        job_name : str
            set the job id
        core_num : int
            set the HPC core number
        node_num : int
            set the HPC node number
        runtime : float
            set the job maximum runtime

        Returns
        -------
        payload
            returns the job descriptor as payload.
        """
        
        payload = {
            'tool': self._NSG_TOOL,
            'metadata.statusEmail': 'false',
            'metadata.clientJobId': job_name,
            'vparam.number_cores_': core_num,
            'vparam.number_nodes_': node_num,
            'vparam.runtime_': runtime,
            'vparam.filename_': 'init.py'
        } 
        logger.debug(f'NSG payload: {payload}')
        return payload

    def _submit_on_nsg(self, username, password, zip_file, settings):
        """
        Submitg the job on NSG system.

        Parameters
        ----------
        username : str
            username.
        password : str
            password.
        zip_file : str
            zip file path.
        settings : dict
            job settings

        Returns
        -------
        ResponseUtil
            returns a ResponseUtil object as result of the HPC response.
        """
        zip_name = os.path.split(zip_file)[1]
        payload = self._get_nsg_payload(job_name=zip_name.split('.')[0],
                                        core_num=settings['core-num'],
                                        node_num=settings['node-num'],
                                        runtime=settings['runtime'])

        headers = self._get_nsg_headers()

        files = {'input.infile_': open(zip_file, 'rb')}
        r = requests.post(url=f'{self._NSG_URL}/job/{username}', 
                          auth=(username, password),
                          data=payload,
                          headers=headers,
                          files=files,
                          verify=False)
        if r.status_code == 200:
            logger.info(f'CODE: {r.status_code}, CONTENT: {r.content}')
            root = xml.etree.ElementTree.fromstring(r.text)

            # extract job selfuri and resulturi
            outputuri = root.find('resultsUri').find('url').text
            selfuri = root.find('selfUri').find('url').text

            # extract job handle
            r = requests.get(url=selfuri,
                             auth=(username, password),
                             headers=headers)
            root = xml.etree.ElementTree.fromstring(r.text)
            if not r.status_code == 200:
                return ResponseUtil.ko_response(r.text)

            return ResponseUtil.ok_response(messages.JOB_SUBMITTED.format('NSG'))            

        return ResponseUtil.ko_response(r.text)

    def _get_nsg_jobs(self, username, password):
        """
        Returns a list of all jobs.

        Parameters
        ----------
        username : str
            username.
        password : str
            password.

        Returns
        -------
        dict
            a dictionaire of all submitted jobs. 

        Raises
        ------
        self.HPCException
            if something happens on the HPC side.
        """
        r = requests.get(url=f'{self._NSG_URL}/job/{username}',
                         auth=(username, password),
                         headers=self._get_nsg_headers())
        logger.debug(f'requests: {r.url} with headers: {r.headers}')
        if r.status_code != 200:
            root = xml.etree.ElementTree.fromstring(r.text)
            message = '<b>' + root.find('displayMessage').text + '</b><br><br>'\
                    + root.find('message').text
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            raise self.HPCException(message)
        
        jobs = {}
        root = xml.etree.ElementTree.fromstring(r.text)
        job_list = root.find('jobs')

        for job in job_list.findall('jobstatus'):
            job_title = job.find('selfUri').find('title').text
            job_url = job.find('selfUri').find('url').text

            r_job = requests.get(url=job_url,
                                 auth=(username, password),
                                 headers=self._get_nsg_headers())
            logger.debug(f'requests: {r.url} with headers: {r.headers}')
            if r_job.status_code != 200:
                logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')    
                raise self.HPCException(messages.JOB_FETCH_ERROR.format('NSG'))

            root_job = xml.etree.ElementTree.fromstring(r_job.text)
            
            job_date_submitted = ''
            job_stage = ''
            job_terminal_stage = ''
            job_failed = ''
            job_client_id = ''

            for child in root_job:
                if child.tag == 'dateSubmitted':
                    job_date_submitted = child.text
                if child.tag == 'jobStage':
                    job_stage = child.text
                if child.tag == 'terminalStage':
                    job_terminal_stage = True if child.text == 'true' else False
                if child.tag == 'failed':
                    job_failed = True if child.text == 'true' else False
                if child.tag == 'metadata':
                    for entry in child.findall('entry'):
                        if entry.find('key').text == 'clientJobId':
                            job_client_id = entry.find('value').text
            
            if job_terminal_stage and job_failed:
                job_stage = 'FAILED'

            jobs.update({
                job_title: {
                    'workflow_id': job_client_id,
                    'status': job_stage,
                    'title': job_client_id,
                    'date': job_date_submitted
                }
            })
            
        return jobs

    def _get_nsg_job_results(self, username, password, job_id):
        """
        Returns a file 

        Parameters
        ----------
        username : _type_
            _description_
        password : _type_
            _description_
        job_id : _type_
            _description_

        Returns
        -------
        _type_
            _description_

        Raises
        ------
        self.HPCException
            _description_
        """
        r = requests.get(url=f'{self._NSG_URL}/job/{username}/{job_id}/output',
                         auth=(username, password),
                         headers=self._get_nsg_headers())
        logger.debug(f'requests: {r.url} with headers: {r.headers}')
        if r.status_code != 200:
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            raise self.HPCException(messages.JOB_RESULTS_FETCH_ERRROR)
        
        file_list = {}
        root = xml.etree.ElementTree.fromstring(r.text)
        for child in root.find('jobfiles').findall('jobfile'):
            job_file = child.find('downloadUri')
            file_list.update({
                job_file.find('title').text: job_file.find('url').text
            })

        return file_list

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
        if hpc == self._DAINT_CSCS:
            client = unicore_client.Client(transport, self._DAINT_URL)
        else:
            try:
                hpc_url = unicore_client.get_sites(transport)[hpc]
            except KeyError:
                logger.error(f'KeyError when looking for {hpc} on unicore_client.')
                raise self.HPCException(messages.HPC_NOT_AVAILABLE.format(hpc))
            client = unicore_client.Client(transport, hpc_url)
        logger.info(f'UNICORE Client initialized for {hpc}')
        logger.debug(f'UNICORE Client access info {client.access_info()}')
        if client.access_info()['role']['selected'] == 'anonymous':
            logger.error('UNICORE Client initialization failed... User not recognized')
            raise self.UnicoreClientException(messages.USER_LOGIN_ERROR)
        return client

    def _submit_on_unicore(self, hpc, token, zip_file, settings):
        zip_name = os.path.split(zip_file)[1]
        job_description = self._get_unicore_job_description(
            command=self._get_unicore_command(zip_name),
            job_name=zip_name.split('.')[0],
            node_num=settings['node-num'],
            core_num=settings['core-num'],
            runtime=settings['runtime'],
            project=settings['project'],
        )
        client = self._initialize_unicore_client(hpc, token)        
        job = client.new_job(job_description=job_description, inputs=[zip_file])
        logger.info(f'job submitted on UNICORE Client: {job}')
        return ResponseUtil.ok_response(messages.JOB_SUBMITTED.format(hpc))

    def _get_unicore_jobs(self, hpc, token):
        client = self._initialize_unicore_client(hpc, token)
        return client.get_jobs(tags=self._TAGS)

    def _get_unicore_job_results(self, hpc, token, job_id):
        client = self._initialize_unicore_client(hpc, token)
        job_url = client.links['jobs'] + '/' + job_id
        job = unicore_client.Job(client.transport, job_url)
        storage = job.working_dir
        return storage.listdir()

    def _get_service_account_payload(self, node_num, core_num, runtime, title, command=None, tool=None):
        payload = {
            'node_number': node_num,
            'core_number': core_num,
            'runtime': runtime,
            'title': title,
            'expiration_time': get_expiration_time()
        }
        if command:
            payload.update({'command': command})
        elif tool:
            payload.update({'tool': tool, 'init_file': 'init.py'})
        
        logger.debug(f'Service Account payload: {str(payload)}')
        return payload

    def _get_service_account_headers(self, token, zip_name=None, payload=None):
        headers = {'Authorization': 'Bearer ' + token}
        if zip_name:
            headers.update({'Content-Disposition': 'attachment;filename=' + zip_name})
        if payload:
            headers.update({'payload': json.dumps(payload)})
        return headers

    def _submit_on_service_account(self, hpc, token, zip_file, settings):
        zip_name = os.path.split(zip_file)[1]
        payload = self._get_service_account_payload(
            command=self._get_unicore_command(zip_name) if hpc=='SA-CSCS' else None,
            tool=self._NSG_TOOL if hpc=='SA-NSG' else None,
            node_num=settings['node-num'],
            core_num=settings['core-num'],
            runtime=settings['runtime'],
            title=zip_name.split('.')[0]
        ) 

        headers = self._get_service_account_headers(token, zip_name, payload)
        job_file = {'file': open(zip_file, 'rb')}
        
        if hpc == self._SA_CSCS:
            sa_endpoint = self._SA_DAINT_JOB_URL
        elif hpc == self._SA_NSG:
            sa_endpoint =self._SA_NSG_JOB_URL
        r = requests.post(url=sa_endpoint, headers=headers, files=job_file)
        logger.debug(f'requests: {r.url} with headers: {r.headers} and files: {job_file}')
        if r.status_code >= 400:
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            return ResponseUtil.ko_response(r.text)

        message = 'Job submitted'
        if hpc == self._SA_CSCS:
            message = messages.JOB_SUBMITTED.format('SA-CSCS')
        elif hpc == self._SA_NSG:
            message = messages.JOB_SUBMITTED.format('SA-NSG') 
        return ResponseUtil.ok_response(message)

    def _get_service_account_jobs(self, hpc, token):
        headers = self._get_service_account_headers(token)
        if hpc == self._SA_CSCS:
            sa_endpoint = self._SA_DAINT_JOB_URL
        elif hpc == self._SA_NSG:
            sa_endpoint = self._SA_NSG_JOB_URL
        r = requests.get(url=sa_endpoint, headers=headers)
        logger.debug(f'requests: {r.url} with headers: {r.headers}')
        if r.status_code != 200:
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            raise self.ServiceAccountException(r.content, r.status_code)
        return r.json()

    def _get_service_account_job_results(self, hpc, token, job_id):
        headers = self._get_service_account_headers(token)
        
        if hpc == self._SA_CSCS:
            sa_endpoint = self._SA_DAINT_FILES_URL + job_id + '/'
        elif hpc == self._SA_NSG:
            sa_endpoint = self._SA_NSG_FILES_URL + job_id + '/'
        
        r = requests.get(url=sa_endpoint, headers=headers)

        logger.debug(f'requests: {r.url} with headers: {r.headers}')
        if r.status_code >= 400:
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            raise self.JobsFilesNotFound(messages.JOB_EXPIRED.format(job_id))
        if r.status_code != 200:
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            raise self.ServiceAccountException(r.content, r.status_code)
        
        file_list = []
        for f in r.json():
            if hpc == self._SA_CSCS:
                file_list.append({'id': f, 'name': f})
            elif hpc == self._SA_NSG:
                file_list.append({'id': f['fileid'], 'name': f['filename']})
        return file_list
          

    @classmethod
    def submit_job(cls, user, zip_file, settings):
        logger.info(LOG_ACTION.format(user, 'submitting job with settings: %s' % settings))
        job_handler = cls()
        if settings['hpc'] == job_handler._NSG:
            return job_handler._submit_on_nsg(user.get_nsg_user().get_username(),
                                              user.get_nsg_user().get_password(),
                                              zip_file, settings)
        elif settings['hpc'] == job_handler._DAINT_CSCS:
            return job_handler._submit_on_unicore(job_handler._DAINT_CSCS, user.get_token(),
                                                  zip_file, settings)
        elif settings['hpc'] == job_handler._SA_CSCS or settings['hpc'] == job_handler._SA_NSG:
            return job_handler._submit_on_service_account(settings['hpc'], user.get_token(),
                                                          zip_file, settings)
        return ResponseUtil.ko_response(messages.GENERAL_ERROR)
       
    @classmethod
    def fetch_jobs_list(cls, hpc, user):
        logger.info(LOG_ACTION.format(user, 'fetch %s jobs list' % hpc))
        job_handler = cls()
        jobs = {}

        if hpc == job_handler._NSG:
            jobs = job_handler._get_nsg_jobs(user.get_nsg_user().get_username(),
                                             user.get_nsg_user().get_password())

        elif hpc == job_handler._DAINT_CSCS:
            raw_jobs = job_handler._get_unicore_jobs(hpc, user.get_token())
            for raw_job in raw_jobs:
                props = raw_job.properties
                job = { raw_job.job_id: {
                        'workflow_id': props['name'],
                        'status': props['status'],
                        'date': str_to_datetime(props['submissionTime'])
                    }
                }
                jobs.update(job)

        elif hpc == job_handler._SA_CSCS or hpc == job_handler._SA_NSG:
            raw_jobs = job_handler._get_service_account_jobs(hpc, user.get_token())
            for raw_job in raw_jobs:
                job = {raw_job['job_id']: {
                    'workflow_id': raw_job['title'],
                    'status': raw_job['stage'],
                    'date': str_to_datetime(raw_job['init_date'])
                }}
                if not is_job_expired(job[raw_job['job_id']]):
                    jobs.update(job)
        
        # sort jobs from last to first
        ordered_jobs = OrderedDict(sorted(jobs.items(),
                                          key=lambda x: x[1]['date'],
                                          reverse=True))
        logger.info(LOG_ACTION.format(user, 'jobs list: %s' % ordered_jobs))
        return {'jobs': ordered_jobs}


    @classmethod
    def fetch_job_files(cls, hpc, job_id, user):
        logger.info(LOG_ACTION.format(user, 'fetch files of job: %s in %s' % (job_id, hpc)))
        job_handler = cls()
        if hpc == job_handler._NSG:
            raw_file_list = job_handler._get_nsg_job_results(user.get_nsg_user().get_username(),
                                                             user.get_nsg_user().get_password(),
                                                             job_id)
            file_list = {
                'root_url': 'nsg', 
                'file_list': raw_file_list,
                'headers': job_handler._get_nsg_headers(),
                'username': user.get_nsg_user().get_username(),
                'password': user.get_nsg_user().get_password()
            }
        
        if hpc == job_handler._DAINT_CSCS:
            raw_file_list = job_handler._get_unicore_job_results(hpc, user.get_token(), job_id)
            file_list = {
                'root_url': 'unicore', 
                'file_list': raw_file_list
            }
        
        if hpc == job_handler._SA_CSCS or hpc == job_handler._SA_NSG:
            raw_file_list = job_handler._get_service_account_job_results(hpc, user.get_token(), job_id)
            if hpc == job_handler._SA_CSCS:
                root_url = job_handler._SA_DAINT_FILES_URL + job_id
            elif hpc == job_handler._SA_NSG:
                root_url = job_handler._SA_NSG_FILES_URL + job_id + '/'
            file_list = {
                'root_url': root_url, 
                'file_list': raw_file_list,
                'headers': {'Authorization': 'Bearer ' + user.get_token()}
            }
        return file_list
