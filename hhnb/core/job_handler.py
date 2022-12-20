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
    Useful class to easily handle jobs, and the relative files, 
    on the selected HPC system. This class is intended
    to be used by calling its static methods and for this
    it is not recommended to instantiate a JobHandler object
    and call its private methods. 
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
        self._SA_JOBS_URL = self._SA_ROOT_URL + 'jobs/{}/{}/'
        self._SA_FILES_URL = self._SA_ROOT_URL + 'files/{}/{}/'
        self._NSG_URL = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'
        self._DAINT_URL = 'https://brissago.cscs.ch:8080/DAINT-CSCS/rest/core'
        
        self._DAINT_CSCS = 'DAINT-CSCS'
        self._SA = 'SA'
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
        Returns the configuration payload with all settings to
        submit/run the job on the HPC system.  

        Parameters
        ----------
        job_name : str
            set the job name
        core_num : int
            set the HPC core number
        node_num : int
            set the HPC node number
        runtime : float
            set the job maximum runtime

        Returns
        -------
        dict
            returns the job payload.
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
        Submit the job on NSG system. Once the job is submitted,
        a ResponseUtil object is returned according to the
        submission result. 

        Parameters
        ----------
        username : str
            nsg username.
        password : str
            nsg password.
        zip_file : str
            zip file path.
        settings : dict
            job settings

        Returns
        -------
        hhnb.core.response.ResponseUtil
            the result of the submission.
        """
        payload = self._get_nsg_payload(job_name=settings['job_name'],
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

            return ResponseUtil.ok_response(messages.JOB_SUBMITTED.format('<b>NSG</b>'))            

        return ResponseUtil.ko_response(r.text)

    def _get_nsg_jobs(self, username, password):
        """
        Returns a list of all jobs.

        Parameters
        ----------
        username : str
            nsg username.
        password : str
            nsg password.

        Returns
        -------
        dict
            a dictionary of all submitted jobs. 

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
        Returns the results of the job as a list of files.

        Parameters
        ----------
        username : str
            nsg username.
        password : str
            nsg password.
        job_id : str
            job id.

        Returns
        -------
        dict
            list of files.

        Raises
        ------
        self.HPCException
            if something happens on the HPC side.
        """
        r = requests.get(url=f'{self._NSG_URL}/job/{username}/{job_id}/output',
                         auth=(username, password),
                         headers=self._get_nsg_headers())
        logger.debug(f'requests: {r.url} with headers: {r.headers}')
        if r.status_code != 200:
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            raise self.HPCException(messages.JOB_RESULTS_FETCH_ERROR)
        
        file_list = {}
        root = xml.etree.ElementTree.fromstring(r.text)
        for child in root.find('jobfiles').findall('jobfile'):
            job_file = child.find('downloadUri')
            file_list.update({
                job_file.find('title').text: job_file.find('url').text
            })

        return file_list

    def _get_unicore_command(self, zip_name):
        """
        Returns the UNICORE command to run the job.

        Parameters
        ----------
        zip_name : str
            zip file name of the job.

        Returns
        -------
        str
            UNICORE command.
        """
        command = 'unzip ' + zip_name + '; cd ' + zip_name.split('.zip')[0] \
                + '; chmod +rx *.sbatch; ./ipyparallel.sbatch'
        return command

    def _get_unicore_job_description(self, command, job_name, node_num, 
                                     core_num, runtime, project):
        """
        Returns the UNICORE job description.
        The job description is a payload that is formed by the command
        to run, the name of the job, and the resources list to 
        reserve for the job that are subtracted from the project.

        Parameters
        ----------
        command : str
            UNICORE command to run the job.
        job_name : str
            the job name
        node_num : int
            set the HPC node number
        core_num : int
            set the HPC core number
        runtime : int
            maximum job runtime
        project : str
            the project from where the resources are reserved to run the job

        Returns
        -------
        dict
            the job description.
        """
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
        """
        Initialize the UNICORE client using the user token
        (to identify him) and the HPC system.

        Parameters
        ----------
        hpc : str
            the HPC system
        token : str
            user barer token

        Returns
        -------
        pyunicore.client.Client
            UNICORE client instance.

        Raises
        ------
        self.HPCException
            if something happens on the HPC side.
        self.UnicoreClientException
            if something happens during the client initialization.
        """
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
        """
        Submit the job on UNICORE system. 
        To submit a job, first a UNICORE client is created using
        the user token and the relative HPC in which the user want
        to submit the job, and then will be passed the zip file 
        containing the job and the settings to run the job.
        Then a ResponseUtil is returned as the job submission result. 

        Parameters
        ----------
        hpc : str
            select which HPC to use.
        token : str
            user barer token.
        zip_file : str
            job input file as zip file path
        settings : dict
            job settings

        Returns
        -------
        hhnb.core.response.ResponseUtil
            the result of the submission as ResponseUtil object. 
        """
        zip_name = os.path.split(zip_file)[1]
        job_description = self._get_unicore_job_description(
            command=self._get_unicore_command(zip_name),
            job_name=settings['job_name'],
            node_num=settings['node-num'],
            core_num=settings['core-num'],
            runtime=settings['runtime'],
            project=settings['project'],
        )
        client = self._initialize_unicore_client(hpc, token)        
        job = client.new_job(job_description=job_description, inputs=[zip_file])
        logger.info(f'job submitted on UNICORE Client: {job}')
        return ResponseUtil.ok_response(messages.JOB_SUBMITTED.format('<b>' + hpc + '</b>'))

    def _reoptimize_model_on_unicore(self, job_id, job_name, hpc, max_gen,
                                     node_num, core_num, runtime, token):
        """
        Submit job to reoptimize model on unicore. The job executes a dedicated script on 
        CSCS-PizDAINT that make a copy of the output of the previous optimization and then
        resume the optimization starting from its checkpoint.  

        Args:
            job_id : str
                the job id.
            job_name : str
                the job name.
            hpc : str
                the HPC in which submit the job.
            max_gen : int
                the new generation parameter for the optimization.
            node_num : int
                the node number allocated for the optimization.
            core_num : int
                the core number allocated for the optimization.
            runtime : str
                the maximum amount of time for the job to be completed.
            token : str
                the EBRAINS user token.

        Returns:
            Response : (status_code, content)
                the response of the submission request. 
        """
        job_description = {
            'User precommand': f'cp -r /scratch/snx3000/unicore/FILESPACE/{job_id}/{job_name}/ .',
            'Executable': f'/apps/hbp/ich002/cnr-software-utils/hhnb/reoptimize_model.sh {job_name} {max_gen}',
            'User postcommand': f'mv {job_name} reopt_{job_name}; cd reopt_{job_name}; ' + \
                                f'sed -i "s/{job_name}/reopt_{job_name}/" zipfolder.py; ' + \
                                f'python ./zipfolder.py',
            'Name': 'reopt_' + job_name,
            'Resources': {
                'Nodes': node_num,
                'CPUsPerNode': core_num,
                'Runtime': runtime,
                'NodeConstraints': 'mc',
                'Project': 'ich002'
            },
            'Tags': self._TAGS,
            "haveClientStageIn": "false",
        }
        client = self._initialize_unicore_client(hpc, token)
        job = client.new_job(job_description=job_description)
        job.start
        logger.info(f'reoptimize model job {job_id} submitted on UNICORE Client')
        return ResponseUtil.ok_response(messages.JOB_SUBMITTED.format('<b>' + hpc + '</b>'))


    def _get_unicore_jobs(self, hpc, token):
        """
        Returns a list of submitted jobs by the user (identified by
        its token) and the relative HPC system in which the user 
        wants to fetch its jobs.
        The result is a list of a Job object.

        Parameters
        ----------
        hpc : str
            from where the jobs are fetched.
        token : str
            user barer token.

        Returns
        -------
        list[Job]
            list of all jobs submitted
        """
        client = self._initialize_unicore_client(hpc, token)
        return client.get_jobs(tags=self._TAGS)

    def _get_unicore_job_results(self, hpc, token, job_id):
        """
        Returns the output of the job as a list of files and directories.

        Parameters
        ----------
        hpc : str
            the HPC system
        token : str
            user barer token.
        job_id : str
            the job identifier

        Returns
        -------
        list
            a list of a files and directories.
        """
        client = self._initialize_unicore_client(hpc, token)
        job_url = client.links['jobs'] + '/' + job_id
        job = unicore_client.Job(client.transport, job_url)
        storage = job.working_dir
        return storage.listdir()

    def _get_service_account_payload(self, node_num, core_num, runtime, title, command=None, tool=None):
        """
        Returns the payload for the Service Account. 
        It is formed by the node and core number the HPC can use to 
        processes the job, the maximum runtime for the job, the 
        job title, and optionally the command (only for UNICORE system)
        or the tool (only for NSG system).

        Parameters
        ----------
        node_num : int
            the HPC node number 
        core_num : int
            the HPC core number
        runtime : float
            the maximum job runtime
        title : str
            the job name
        command : str, optional
            to be set only for UNICORE command, by default None
        tool : str, optional
            to be set only for NSG system, by default None

        Returns
        -------
        dict
            the job payload for the Service Account service.
        """
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
        """
        Returns the Service Account headers to pass in the requests
        object. This is formed by the user token, the input zip file
        and the job payload. 

        Parameters
        ----------
        token : str
            user barer token
        zip_name : str, optional
            the input zip file name if the job needs it, by default None
        payload : dict, optional
            the job payload for the Service Account, by default None

        Returns
        -------
        dict
            a dict object to pass to the request as header
        """
        headers = {'Authorization': 'Bearer ' + token}
        if zip_name:
            headers.update({'Content-Disposition': 'attachment;filename=' + zip_name})
        if payload:
            headers.update({'payload': json.dumps(payload)})
        return headers

    def _submit_on_service_account(self, hpc, project, token, zip_file, settings):
        """
        Submit a job behind the Service Account in the selected HPC 
        system. To submit a job, an available HPC system must be choose
        from the list of HPC linked to the Service Account, the user
        token must be provide to identify the user, and finally 
        the input zip file and the job configuration can be set.  
        Once the job is submitted a ResponseUtil object will be 
        returned with the result of the submission.

        Parameters
        ----------
        hpc : str
            the HPC where the user wants to submit the job
        token : str
            the user barer token
        zip_file : str
            the job input zip file
        settings : dict
            the job payload that contains the job settings

        Returns
        -------
        hhnb.core.response.ResponseUtil
            the result of the submitted job
        """
        zip_name = os.path.split(zip_file)[1]
        payload = self._get_service_account_payload(
            command=self._get_unicore_command(zip_name) if hpc=='pizdaint' else None,
            tool=self._NSG_TOOL if hpc=='nsg' else None,
            node_num=settings['node-num'],
            core_num=settings['core-num'],
            runtime=settings['runtime'],
            title=settings['job_name']
        ) 

        headers = self._get_service_account_headers(token, zip_name, payload)
        job_file = {'file': open(zip_file, 'rb')}
        
        sa_endpoint = self._SA_JOBS_URL.format(hpc, project)

        r = requests.post(url=sa_endpoint, headers=headers, files=job_file)
        logger.debug(f'requests: {r.url} with headers: {r.headers} and files: {job_file}')
        print(f"SERVICE ACCOUNT RESPONSE: {r.status_code}, {r.content}")
        if r.status_code >= 400:
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            if r.status_code == 500:
                raise self.ServiceAccountException(r.content, r.status_code)
            return ResponseUtil.ko_response(r.text)

        message = messages.JOB_SUBMITTED.format(
            '<b>' + hpc.upper() + '</b> using the Service Account project <b>' + project + '</b>')
        return ResponseUtil.ok_response(message)

    def _get_service_account_jobs(self, hpc, project, token):
        """
        Returns a list of all jobs submitted using the Service Account
        by the user to the selected HPC system.

        Parameters
        ----------
        hpc : str
            the hpc system
        token : str
            the user barer token

        Returns
        -------
        dict
            a dict object  

        Raises
        ------
        self.ServiceAccountException
            if something happens on the Service Account side
        """
        headers = self._get_service_account_headers(token)
        sa_endpoint = self._SA_JOBS_URL.format(hpc, project)
        r = requests.get(url=sa_endpoint, headers=headers)
        logger.debug(f'requests: {r.url} with headers: {r.headers}')
        if r.status_code != 200:
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            raise self.ServiceAccountException(r.content, r.status_code)
        return r.json()

    def _get_service_account_job_results(self, hpc, project, token, job_id):
        """
        Returns a list of the files once the job ends.
        The list is formed by a json object per file 
        composed by the "id" and the "name" keys.
        
        Parameters
        ----------
        hpc : str
            the hpc system
        token : str
            the user barer token
        job_id : str
            the job id

        Returns
        -------
        list
            a list of json objects that represent the job's files

        Raises
        ------
        self.JobsFilesNotFound
            if the job is not found for the selected HPC system.
        self.ServiceAccountException
            if something happens on the Service Account side or
            if it is down.
        """
        headers = self._get_service_account_headers(token)
        
        sa_endpoint = self._SA_FILES_URL.format(hpc, project)
        
        r = requests.get(url=sa_endpoint + job_id + '/', headers=headers)

        logger.debug(f'requests: {r.url} with headers: {r.headers}')
        if r.status_code >= 400:
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            raise self.JobsFilesNotFound(messages.JOB_EXPIRED.format(job_id))
        if r.status_code != 200:
            logger.error(f'CODE: {r.status_code}, CONTENT: {r.content}')
            raise self.ServiceAccountException(r.content, r.status_code)
        
        file_list = []
        for f in r.json():
            if hpc == 'pizdaint':
                file_list.append({'id': f, 'name': f})
            elif hpc == 'nsg':
                file_list.append({'id': f['fileid'], 'name': f['filename']})
        return file_list
          

    @classmethod
    def submit_job(cls, user, zip_file, settings):
        """
        A static method to easily submit a job in the HPC system.
        A settings dictionary must be provided with the "hpc" key
        that indicate in which HPC system the job should be submitted.
        A ResponseUtil object will be returned.

        Parameters
        ----------
        user : hhnb.core.user.HhnbUser
            the user object that want to submit the job
        zip_file : str
            the input zip file
        settings : dict
            the job configuration

        Returns
        -------
        hhnb.core.response.ResponseUtil
            the job submission result
        """
        logger.info(LOG_ACTION.format(user, 'submitting job with settings: %s' % settings))
        job_handler = cls()
        if settings['hpc'] == job_handler._NSG:
            return job_handler._submit_on_nsg(user.get_nsg_user().get_username(),
                                              user.get_nsg_user().get_password(),
                                              zip_file, settings)
        elif settings['hpc'] == job_handler._DAINT_CSCS:
            return job_handler._submit_on_unicore(job_handler._DAINT_CSCS, user.get_token(),
                                                  zip_file, settings)
        elif settings['hpc'] == job_handler._SA:
            return job_handler._submit_on_service_account(settings['sa-hpc'], settings['sa-project'],
                                                          user.get_token(), zip_file, settings)
        return ResponseUtil.ko_response(messages.GENERAL_ERROR)
       
    @classmethod
    def fetch_jobs_list(cls, hpc, user, sa_hpc=None, sa_project=None):
        """
        A static method to easily fetch the jobs list from the selected HPC system.
        
        Parameters
        ----------
        hpc : str
            the HPC system according to the available ones
        user : hhnb.core.user.HhnbUser
            the user who wants to fetch the jobs
        sa_hpc : str, optional
            select which HPC will be used behind the Service Account. Only works
            with the "hpc" parameter set to "SA"
        sa_project : str, optional
            select which Service Account project will be used to fetch jobs. Only
            works with the "hpc" parameter set to "SA"
            
        Returns
        -------
        dict
            a dictionary containing the list of job
            ordered by the date from the most recent 
        """
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

        elif hpc == job_handler._SA:
            raw_jobs = job_handler._get_service_account_jobs(sa_hpc, sa_project, user.get_token())
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
    def fetch_job_files(cls, hpc, job_id, user, sa_hpc=None, sa_project=None):
        """
        A static method to easily fetch the job's files that are produced
        once the HPC ends to process the job. To fetch the list a 
        the parameters that must be passed are the HPC in which the job
        was submitted, the job id to identify the correct job, and the 
        user as owner of the job. The result will be a dictionary 
        containing the "root_url" that is required to download the files,
        the list of files and, optionally, an header that must be passed
        in the download request to correctly identify user when the HPC
        selected is the Service Account.

        Parameters
        ----------
        hpc : str
            the HPC system
        job_id : str
            the job id
        user : hhnb.core.user.HhnbUser
            the owner of the job
        sa_hpc : str, optional
            select which HPC will be used behind the Service Account. Only
            works with the "hpc" parameter set to "SA"
        sa_project : str, optional
            select the job'project where the job was submitted. Only works
            with the "hpc" parameter set to "SA"

        Returns
        -------
        dict
            a dictionary containing all required information to download the files
        """
        logger.info(LOG_ACTION.format(user, 'fetch files of job: %s in %s' % (job_id, hpc)))
        job_handler = cls()
        file_list = None
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
        
        elif hpc == job_handler._DAINT_CSCS:
            raw_file_list = job_handler._get_unicore_job_results(hpc, user.get_token(), job_id)
            file_list = {
                'root_url': 'unicore', 
                'file_list': raw_file_list
            }
        
        elif hpc == job_handler._SA:
            raw_file_list = job_handler._get_service_account_job_results(sa_hpc, sa_project, user.get_token(), job_id)
            root_url = job_handler._SA_FILES_URL.format(sa_hpc, sa_project) + job_id
            if sa_hpc == 'nsg':
                root_url += '/'
            file_list = {
                'root_url': root_url, 
                'file_list': raw_file_list,
                'headers': {'Authorization': 'Bearer ' + user.get_token()}
            }
        
        return file_list
