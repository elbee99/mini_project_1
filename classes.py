import numpy as np
import matplotlib.colorbar as colorbar
import matplotlib.pyplot as plt
import nanofilm
from nanofilm.ndimage import imread


class ImageData():
    """
    This is a class which utilises the image data exported by a 
    Accurion DataStudio fit of ellipsometry data in a more 
    convenient format
    """
    def __init__(self,image_path : str,time : int):
        """
        This is the constructer of the ImageData object

        Args:
            image_path (str): a path to the PNG image data given by a
            fit to ellipsometry data
            min (float): the minimum thickness value measured
            max (float): the maximum thickness value measured
            time (int): the time into the measurement this image was taken
            e.g. if the image was taken after 30 mins of measurement make this
            30 NOTE: this may be changed in the future to work with seconds 
            rather than minutes if required
        """
        self.image_path = image_path
        self.min = min
        self.max = max
        self.time = time
        # temp_image = Image.open(image_path)
        self.array = imread(image_path) # A NumPy array of the data PNG
        # temp_image.close() # if I don't close it again it will never let me construct another of these objects
        # below uses the provided min and max values for thickness and scales the image array to these values
        #self.real_array = self.raw_array*(self.max/np.amax(self.raw_array))

    def plot(self,title : str = ""):
        """
        Plots a basic thickness map of the data
        Args:
            title (str, optional): Plot title. Defaults to "".
        """
        fig, ax = plt.subplots()
        pos = ax.imshow(self.array,cmap='afmhot')
        fig.colorbar(pos)
        if title == "":
            title = "Thickness plot after time = {} units".format(self.time)
        ax.set_title(title)

    def return_image(self,ax):
        """
        This is for when plotting an animated graph we need to return an
        image object of the type im = ax.imshow() from matplotlib
        Args:
            ax (ax): This is a matplotlib.axes.Axes object e.g. as returned when doing
            fig, ax = plt.subplots()
        """
        im = ax.imshow(self.array,animated = True)
        return im