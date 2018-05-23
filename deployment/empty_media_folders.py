import datetime
import time
import os
import shutil

ibf_bspg_hhnb = "/app/media/hhnb/workflows/"
epfl_bspg_hhnb = "/apps/media/hhnb/workflows/"
ibf_bspg_efelg = "/app/media/efel_data/efel_gui/results/"
epfl_bspg_efelg = "/apps/media/efel_data/efel_gui/results/"

dir_list = [ibf_bspg_hhnb, epfl_bspg_hhnb, ibf_bspg_efelg, epfl_bspg_efelg]

# if directories exist
for i in dir_list:
    if os.path.exists(i):

        # change directory
	os.chdir(i)

        # extract path recursively
	folder_list = os.walk(".")                                                
 
	for root, folders, files in folder_list:                                            
    	    [path, crr_folder] = os.path.split(root)                                        
            # check folder name
            if path is not "." and len(crr_folder) >= 14 and crr_folder[:14].isdigit():          
                # get directory's last access time
                access_time_sec = os.path.getmtime(root)                                    
        	current_time = time.time()                                                  
        	time_diff = current_time - access_time_sec                                  

        	# if the folder last access is older then 7200s (i.e. 2h)
		# delete folder 
        	if time_diff > 7200:                                                        
                    print("removing: " + root)
                    shutil.rmtree(root)
