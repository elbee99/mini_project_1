import numpy as np
import pandas as pd
from refellips.dataSE import DataSE
import os
from nanofilm.ndimage import imread
import time
import matplotlib.pyplot as plt
import pickle

import refellips
from refellips.reflect_modelSE import ReflectModelSE
from refellips.objectiveSE import ObjectiveSE
import refnx
from refnx.analysis import CurveFitter
from refnx.reflect import Slab
from refellips.dispersion import RI, Cauchy, load_material
from refellips.dataSE import open_EP4file

from multiprocessing import Manager, Pool


def get_im_width(image_path : str):
    image_array = imread(image_path)
    return np.shape(image_array)[1]

def get_im_height(image_path : str):
    image_array = imread(image_path)
    return np.shape(image_array)[0]

def openEP4ImageData(fname : str):
    """
    Opens an EP4 image data file, returning np.ndarray
    corresponding to the lambda, AOI, Delta and Psi values
    for each of the png files
    Args:
        fname (str): filename (full path preferrably) to the 
        .dat file which contains the image data

    Returns:
        4 x np.ndarray: these correspond to the lambda, AOI,
        Delta and Psi data. The shape is (N_measurements,png_width,png_height)
        where N_measurements is the number of measurements taken e.g. number of 
        different wavelengths, and png_width/height is width and height in number of pixels
    """
    df = pd.read_csv(fname,sep='\t', skiprows=[1])
    df = df.drop(['Bandwidth','ExposureTime','AcquisitionFrameRate','Zone','Time','X_pos','Y_pos'],axis=1) #drop irrelevant data
    dir = os.path.dirname(fname)
    delta_array = [] #initialise list for 3D array of png data
    for path in df['Delta']:
        path = os.path.join(dir,path) #create full path
        delta_array.append(imread(path))
    delta_array = np.stack(delta_array) #stack list into 3D numpy array
    # print(delta_array)

    psi_array = []
    for path in df['Psi']:
        path = os.path.join(dir,path) #create full path
        psi_array.append(imread(path))
    psi_array = np.stack(psi_array)

    lambda_array = np.array([df['#Lambda'].values]*delta_array.shape[1])
    #transposition in order to get shape to match that required to line up
    #with stack of png arrays
    lambda_array = np.array(delta_array.shape[2]*[lambda_array]).transpose()

    #duplicate #Lambda and AOI columns into a (20,350,407) shape
    aoi_array = np.array([df['AOI'].values]*delta_array.shape[1])
    #transposition in order to get shape to match that required to line up
    #with stack of png arrays
    aoi_array = np.array(delta_array.shape[2]*[aoi_array]).transpose()

    return lambda_array,aoi_array,psi_array,delta_array

 
def get_image_dimensions(fname : str):
    """Generates the width and height of an image in pixels

    Args:
        fname (str): file path of .dat file containing imaging data

    Returns:
        tuple: (int,int) = (width,height)
    """
    df = pd.read_csv(fname,sep='\t', skiprows=[1])
    dat_dir = os.path.dirname(fname)
    path = df['Delta'][1] #taking a sample path
    print(path) 
    path = os.path.join(dat_dir,path) #create full path
    return get_im_width(path),get_im_height(path)



def fit_data(args):
    i, j, lambda_arr, aoi_arr, psi_arr, delta_arr,model,cuo_layer = args
    data = (lambda_arr[:,i:i+1,j:j+1].flatten(),
            aoi_arr[:,i:i+1,j:j+1].flatten(),
            psi_arr[:,i:i+1,j:j+1].flatten(),
            delta_arr[:,i:i+1,j:j+1].flatten())
    data = pd.DataFrame(data).dropna(axis=1,how='any')
    data = data.values

    try:
        objective = ObjectiveSE(model,data)
        fitter = CurveFitter(objective)
        fitter.fit('differential_evolution')
        return cuo_layer.thick.value, cuo_layer.thick.stderr
    except Exception:
        return 0,0
    
def data_arr_to_2D(value_arr : list,im_width,im_height):
    return np.reshape(value_arr,[im_height,im_width])

    

if __name__ == '__main__':

    start = time.time()
    fname = r"/rds/user/lb958/hpc-work/mini_1_data/2023_01_09_Cu_after_2weeks/maps/Cu_Tile_longbreak_run01_20230109-171343.ds.dat"

    times = [i*30 for i in range(13)]
    for time in times:
        fname = r"C:\Users\lb958\Data\2023_01_25_Cu_120C\maps\split_maps\measurement_{}min_115C\Cu_Tile_115C_map_sample2_20230125-202556.ds.dat".format{time}

        refellips_path = os.path.dirname(refellips.__file__)
        air = RI(os.path.join(refellips_path,'materials/air.csv'))
        cu = RI(os.path.join(refellips_path,'materials/cu_disp.csv'))
        cuo = RI(os.path.join(refellips_path,'materials/cuo_disp.csv'))

        cuo_layer = cuo(50) #this sets the thickness to 50 Ang to begin with

        cuo_layer.name = 'CuO'
        #vary thickness between 0-1000 Ang
        cuo_layer.thick.setp(vary=True,bounds=(0,1000))
        cuo_layer.vfsolv.setp(vary=False,value=0) #we have no solvent 

        #build the structure
        cu = cu()
        air = air()
        structure = air | cuo_layer | cu

        model = ReflectModelSE(structure)
        im_width,im_height = get_image_dimensions(fname)
        print(type(im_width))
        lambda_arr,aoi_arr,psi_arr,delta_arr = openEP4ImageData(fname)
        with Manager() as manager:
            shared_model = manager.Namespace()
            shared_cuo = manager.Namespace()
            shared_model.model = model
            shared_cuo.cuo_layer = cuo_layer
        with Pool() as p:
            data = [(i, j, lambda_arr, aoi_arr, psi_arr, delta_arr,model,cuo_layer) for i in range(im_height) for j in range(im_width)]
            results = p.map(fit_data, data)

        thickness_arr, stderr_arr = zip(*results)
        # print(thickness_arr[0:5],stderr_arr[0:5])
        print("Time taken for {} fits using {} CPU cores= {}".format(im_width*im_height,os.cpu_count(),time.time()-start))
        thickness_png_array = data_arr_to_2D(thickness_arr,im_width=im_width,im_height=im_height)
        stderr_png_array = data_arr_to_2D(stderr_arr,im_width=im_width,im_height=im_height)
        with open("thickness_arr_{}min.pkl".format{time},'wb') as f:
            pickle.dump(thickness_arr,f) 

        with open("thickness_arr_png_{}min.pkl".format{time},'wb') as f:
            pickle.dump(thickness_png_array,f) 

        with open("stderr_arr.pkl_{}min".format{time},'wb') as f:
            pickle.dump(stderr_arr,f) 
        with open("stderr_arr_png_{}min.pkl".format{time},'wb') as f:
            pickle.dump(stderr_png_array,f) 




    # start = time.time()
    # fname = r"/rds/user/lb958/hpc-work/mini_1_data/2023_01_09_Cu_after_2weeks/maps/Cu_Tile_longbreak_run01_20230109-171343.ds.dat"

    # refellips_path = os.path.dirname(refellips.__file__)
    # air = RI(os.path.join(refellips_path,'materials/air.csv'))
    # cu = RI(os.path.join(refellips_path,'materials/cu_disp.csv'))
    # cuo = RI(os.path.join(refellips_path,'materials/cuo_disp.csv'))

    # cuo_layer = cuo(50) #this sets the thickness to 50 Ang to begin with

    # cuo_layer.name = 'CuO'
    # #vary thickness between 0-1000 Ang
    # cuo_layer.thick.setp(vary=True,bounds=(0,1000))
    # cuo_layer.vfsolv.setp(vary=False,value=0) #we have no solvent 

    # #build the structure
    # cu = cu()
    # air = air()
    # structure = air | cuo_layer | cu

    # model = ReflectModelSE(structure)
    # im_width,im_height = get_image_dimensions(fname)
    # print(type(im_width))
    # lambda_arr,aoi_arr,psi_arr,delta_arr = openEP4ImageData(fname)
    # with Manager() as manager:
    #     shared_model = manager.Namespace()
    #     shared_cuo = manager.Namespace()
    #     shared_model.model = model
    #     shared_cuo.cuo_layer = cuo_layer
    # with Pool() as p:
    #     data = [(i, j, lambda_arr, aoi_arr, psi_arr, delta_arr,model,cuo_layer) for i in range(im_height) for j in range(im_width)]
    #     results = p.map(fit_data, data)

    # thickness_arr, stderr_arr = zip(*results)
    # # print(thickness_arr[0:5],stderr_arr[0:5])
    # print("Time taken for {} fits using {} CPU cores= {}".format(im_width*im_height,os.cpu_count(),time.time()-start))
    # thickness_png_array = data_arr_to_2D(thickness_arr,im_width=im_width,im_height=im_height)
    # stderr_png_array = data_arr_to_2D(stderr_arr,im_width=im_width,im_height=im_height)
    # with open("thickness_arr.pkl",'wb') as f:
    #     pickle.dump(thickness_arr,f) 

    # with open("thickness_arr_png.pkl",'wb') as f:
    #     pickle.dump(thickness_png_array,f) 

    # with open("stderr_arr.pkl",'wb') as f:
    #     pickle.dump(stderr_arr,f) 
    # with open("stderr_arr_png.pkl",'wb') as f:
    #     pickle.dump(stderr_png_array,f) 

    # plt.imsave('fitted_thickness.png',thickness_png_array)
    # plt.imsave('fitted_stderr.png',stderr_png_array)

# thickness_arr = []
# for i in range(lambda_arr.shape[2]): #along image height
#     for j in range(lambda_arr.shape[1]): #along image width
#         try:
#             data = (np.nan_to_num(lambda_arr[:,i:i+1,j:j+1].flatten()),
#                     np.nan_to_num(aoi_arr[:,i:i+1,j:j+1].flatten()),
#                     np.nan_to_num(psi_arr[:,i:i+1,j:j+1].flatten()),
#                     np.nan_to_num(delta_arr[:,i:i+1,j:j+1].flatten()))
#             objective = ObjectiveSE(model,data)
#             fitter = CurveFitter(objective)
#             fitter.fit()
#             # print(objective.model.paramters[3])
#         except RuntimeError:
#             print('runtime error would have happened')
#             pass
    
