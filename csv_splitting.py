import os
import shutil 

# dat_folder = r"C:\Users\lb958\Code\test\maps"
# dat_folder = r"C:\Users\lb958\Data\2022_12_16_Cu_in_air_run_02\maps"
# dat_filename = r"Cu_Tile_run01_20221216-170029.ds.dat"
# png_filename = r"Cu_Tile_run01_20221216-170029.ds.png"
# xml_filename = r"Cu_Tile_run01_20221216-170029.dsinfo.xml"
# dat_folder = r"C:\Users\lb958\Data\2023_01_11_Cu_150C\maps"
# dat_filename = r"Cu_Tile_150Cmaps_20230111-102540.ds.dat"
# png_filename = r"Cu_Tile_150Cmaps_20230111-102540.ds.png"
# xml_filename = r"Cu_Tile_150Cmaps_20230111-102540.dsinfo.xml"

dat_folder = r"C:\Users\lb958\Data\2023_01_25_Cu_120C\maps"
dat_filename = r"Cu_Tile_120C_map_20230125-131101.ds.dat"
png_filename = r"Cu_Tile_120C_map_20230125-131101.ds.png"
xml_filename = r"Cu_Tile_120C_map_20230125-131101.dsinfo.xml"

dat_path = os.path.join(dat_folder,dat_filename)
png_path = os.path.join(dat_folder,png_filename)
xml_path = os.path.join(dat_folder,xml_filename)
destination_root_folder = "split_maps"
destination_root_folder = os.path.join(dat_folder,destination_root_folder)
if not os.path.exists(destination_root_folder):
    os.mkdir(destination_root_folder)

with open(dat_path,'r') as dat:
    dat_list = dat.readlines()
    header = dat_list[0:2]
    body = dat_list[2:]
    # 13 measurements taken
    for i in range(13):
        measurement_time = i*30 #time of measurement in minutes
        #path to which the maps at a given time will be move to
        split_folder = "measurement_{}min_120C".format(measurement_time)
        #creating absolute path
        split_folder = os.path.join(destination_root_folder,split_folder)
        if not os.path.exists(split_folder):
            os.mkdir(split_folder)
        destination_dat_file = os.path.join(split_folder,dat_filename)
        destination_png_file = os.path.join(split_folder,png_filename)
        shutil.copy(png_path,destination_png_file)
        destination_xml_file = os.path.join(split_folder,xml_filename)
        shutil.copy(xml_path,destination_xml_file)
        with open(destination_dat_file,'w') as cut_dat:
            # edited list for writing to new .dat file
            file_list = header + body[i*20:i*20+20]
            print(file_list)
            cut_dat.writelines(file_list)
    

