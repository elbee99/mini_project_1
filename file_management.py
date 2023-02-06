import shutil
import os

#absolute path to the base folder containing all the data
# base_folder = r"C:\Users\lb958\Data\2022_12_16_Cu_in_air_run_02\maps" 
# base_folder = r"C:\Users\lb958\Code\test\maps"
base_folder = r"C:\Users\lb958\Data\2023_01_30_Cu-Gr_Sample2\maps"
#the folder within the base folder which will hold the subfolders for each measurement
destination_root_folder = "split_maps" 
#creating an absolute path from the above
destination_root_folder = os.path.join(base_folder,destination_root_folder)
if not os.path.exists(destination_root_folder):
   os.mkdir(destination_root_folder)
print(destination_root_folder)


for i in range(13): #number of measurements is 50
    measurement_time = i*30 #time of measurement in minutes
    #path to which the maps at a given time will be move to
    split_folder = "measurement_{}min_115C".format(measurement_time)
    #creating absolute path
    split_folder = os.path.join(destination_root_folder,split_folder)
    if not os.path.exists(split_folder):
        os.mkdir(split_folder)

    for j in range(1,41): #as there are 40 files per measurement
        file_number = (i*40)+j
        if file_number <= 9:
            file_name = "Cu-Gr_115C_sample2_20230130-171219_00{}.png".format(file_number)
        elif file_number <= 99:
            file_name = "Cu-Gr_115C_sample2_20230130-171219_0{}.png".format(file_number)
        else:
            file_name = "Cu-Gr_115C_sample2_20230130-171219_{}.png".format(file_number)
        old_file_path = os.path.join(base_folder,file_name)
        destination_file_path = os.path.join(split_folder,file_name)
        shutil.copy(old_file_path,destination_file_path)
