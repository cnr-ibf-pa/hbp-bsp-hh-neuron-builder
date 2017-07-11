import io
import json
import os
import requests
import xml.etree.ElementTree
import time
import sys
import zipfile
import shutil
import pprint
def runNSG(username, password, core_num, node_num, runtime, zfName, dest_dir):
    os.chdir(dest_dir)
    #global CRA_USER, PASSWORD, KEY, URL, TOOL
    CRA_USER = username
    PASSWORD = password
    KEY = 'Application_Fitting-DA5A3D2F8B9B4A5D964D4D2285A49C57'
    URL = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'
    TOOL = 'BLUEPYOPT_TG'
    
    os.popen('pwd').read()
    os.popen('ls -ltr').read()
    headers = {'cipres-appkey' : KEY}
    #payload = {'tool' : TOOL, 'metadata.statusEmail' : 'false', 'vparam.number_cores_' : NCORES.value, 'vparam.number_nodes_' : NNODES.value, 'vparam.runtime_' : RT.value, 'vparam.filename_': 'init.py'}
    payload = {'tool' : TOOL, 'metadata.statusEmail' : 'false', 'vparam.number_cores_' : core_num, 'vparam.number_nodes_' : node_num, 'vparam.runtime_' : runtime, 'vparam.filename_': 'init.py'}
    files = {'input.infile_' : open(zfName,'rb')}

    r = requests.post('{}/job/{}'.format(URL, CRA_USER), auth=(CRA_USER, PASSWORD), data=payload, headers=headers, files=files)
    
    root = xml.etree.ElementTree.fromstring(r.text)
    # status dopo avere lanciato il job
    global outputuri, selfuri
    for child in root:
        if child.tag == 'resultsUri':
            for urlchild in child:
                if urlchild.tag == 'url':
                    outputuri = urlchild.text
        if child.tag == 'selfUri':
            for urlchild in child:
                if urlchild.tag == 'url':
                    selfuri = urlchild.text

    return str(r.status_code)


def createzip(foldernameOPTstring, utils_dir, gennum, offsize, optimization_name):
    os.chdir(foldernameOPTstring)

    #shutil.copytree(os.path.join(utils_dir,'model'), '.'+os.path.sep+ optimization_name +os.path.sep+'model')

    #shutil.copy(os.path.join(utils_dir,'analysis.py'), '.'+os.path.sep+ optimization_name +os.path.sep+'analysis.py')


    #shutil.copy(os.path.join(utils_dir,'evaluator.py'), '.'+os.path.sep+ optimization_name +os.path.sep+'evaluator.py')


    #shutil.copy(os.path.join(utils_dir,'opt_neuron.py'), '.'+os.path.sep+ optimization_name +os.path.sep+'opt_neuron.py')


    #shutil.copy(os.path.join(utils_dir,'template.py'), '.'+os.path.sep+ optimization_name+os.path.sep+'template.py')


    dirloc=os.getcwd()
    for file in os.listdir(dirloc):
        if file.startswith('init') or file.endswith('.zip'):
            os.remove(file)
    with open('init.py','w') as f:
        f.write('import os')
        f.write('\n')
        f.write('os.system(\'python opt_neuron.py --max_ngen='+str(gennum)+' --offspring_size='+str(offsize)+' --start --checkpoint ./checkpoints/checkpoint.pkl\')')
        f.write('\n')
    f.close()
    os.chdir(optimization_name)

    print(foldernameOPTstring)
    print(foldernameOPTstring)
    dirloc=os.getcwd()
    for file in os.listdir(dirloc):
        if file.startswith('init'):
            os.remove(file)
    os.chdir('..')
    shutil.copy('init.py','.'+os.path.sep+ optimization_name +os.path.sep+'init.py')
    zfName = optimization_name + '.zip'
    foo = zipfile.ZipFile(zfName, 'w')
    for root, dirs, files in os.walk('.'+ os.path.sep + optimization_name):
        if (root=='.'+ os.path.sep+optimization_name + os.path.sep+'morphology') or \
        (root=='.'+ os.path.sep+optimization_name +os.path.sep+'config') or \
        (root=='.'+ os.path.sep+optimization_name +os.path.sep+'mechanisms') or \
        (root=='.' + os.path.sep+optimization_name +os.path.sep+'model'):
            for f in files:
                foo.write(os.path.join(root, f))
        if (root=='.'+os.path.sep + optimization_name + os.path.sep+'checkpoints') or \
        (root=='.'+os.path.sep+ optimization_name + os.path.sep+'figures'):
            foo.write(os.path.join(root))
        if (root=='.'+os.path.sep + optimization_name):
            for f in files:
                if f.endswith('.py'):
                    foo.write(os.path.join(root, f))                    
    foo.close()


def replace_feat_files(source_dir, dest_dir):
    feat_source_name = os.path.join(source_dir, "features.json")
    feat_dest_name = os.path.join(dest_dir, "features.json")
    prot_source_name = os.path.join(source_dir, "protocols.json")
    prot_dest_name = os.path.join(dest_dir, "protocols.json")
    
    if os.path.isfile(feat_dest_name):
        os.remove(feat_dest_name)
        shutil.copy(feat_source_name, feat_dest_name)

    if os.path.isfile(prot_dest_name):
        os.remove(prot_dest_name)
        shutil.copy(prot_source_name, prot_dest_name)

def change_exp_name():
    pass



def unzip_opt(opt_folder, crr_dest_folder):
    pass

def copy_orig_opt_folder(opt_folder,dest_folder):
    if not os.path.exists(dest_folder):
        shutil.copytree(opt_folder, dest_folder)
    for files in os.listdir(dest_folder):
        if files.endswith('.zip'):
            os.chdir(dest_folder)
            zip_ref = zipfile.ZipFile(files, 'r')
            zip_ref.extractall()
            zip_ref.close()   








