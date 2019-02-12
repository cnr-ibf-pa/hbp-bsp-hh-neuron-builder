import os
import pprint
from tools import hpc_job_manager
import xml.etree.ElementTree

username = "lbologna"
password = "1u2n3o4@5N6O7V8E9"
username_fetch = "lbologna"
password_fetch = "1u2n3o4@5N6O7V8E9"
username_submit = "lbologna"
password_submit = "1u2n3o4@5N6O7V8E9"
core_num = 1 
node_num = 1
runtime = 0.3
gennum = 1
offsize = 4
dest_dir = "/home/lbologna/temp"
out_dir = "/home/lbologna/temp_out"
source_opt_zip = "/home/lbologna/CA1_int_bAC_011017HP2_20170510120000.zip"
opt_name = "my_modified_opt"
source_feat = "/home/lbologna/temp_feat"
opt_res_dir = "/home/lbologna/opt_res_dir"
zfName = os.path.join(dest_dir, opt_name + '.zip') 

hpc_job_manager.Nsg.createzip(fin_opt_folder=dest_dir, \
           source_opt_zip=source_opt_zip, opt_name=opt_name, \
           source_feat=source_feat, gennum=gennum, offsize=offsize, \
           zfName=zfName)

resp = hpc_job_manager.Nsg.runNSG(username_submit=username_submit, \
           password_submit=password_submit, core_num=core_num, \
           node_num=node_num, runtime=runtime, zfName=zfName)

pprint.pprint(resp)

#res = nsg_obj.runNSG()
job_list = hpc_job_manager.Nsg.fetch_job_list(username_fetch=username_fetch, \
                password_fetch=password_fetch)

pprint.pprint(job_list)

#for jobid in resp:
#    print jobid
#    resp = hpc_job_manager.Nsg.fetch_job_details( \
#                job_id = jobid, username_fetch=username_fetch, \
#                password_fetch=password_fetch) 

#for job_id in job_list:
#    resp_job_details = hpc_job_manager.Nsg.fetch_job_details( \
#        job_id = job_id, username_fetch=username_fetch, \
#        password_fetch=password_fetch) 
#    job_res_url = resp_job_details['job_res_url']

    #resp = hpc_job_manager.Nsg.fetch_job_results(job_res_url, \
    #            username_fetch=username_fetch, \
    #            password_fetch=password_fetch, opt_res_dir=opt_res_dir, \
    #            wf_id=wf_id)


#    print(job_id)
