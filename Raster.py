import os

import numpy as np
import rasterio
import xmltodict


class Raster:
    """
    Represents a raster image.

    Args:
        path (str): The path to the raster file.
        wavelength (float): The wavelength of the raster image.
        datacube (ndarray): The datacube of the raster image.
        metadata (dict): The metadata of the raster image.
        profile (rasterio.profiles.Profile): The profile of the raster image.
        name (str): The name of the raster image.

    Attributes:
        wavelength (float): The wavelength of the raster image.
        datacube (ndarray): The datacube of the raster image.
        metadata (dict): The metadata of the raster image.
        profile (rasterio.profiles.Profile): The profile of the raster image.
        name (str): The name of the raster image.
        path (str): The path to the raster file.

    """

    def __init__(
        self,
        path=None,
        wavelength=None,
        datacube=None,
        metadata=None,
        profile=None,
        name=None,
    ):
        if path is not None:
            self.load_from_file(path)
        else:
            self.wavelength = wavelength
            self._datacube = datacube
            self.metadata = metadata
            self.profile = profile
            self.name = name
            self.path = None

    def load_from_file(self, raster_path):
        """
        Load the raster image from a file.

        Args:
            raster_path (str): The path to the raster file.

        """
        with rasterio.open(raster_path) as src:
            self.profile = src.profile
            self._datacube = src.read()

        self.path = raster_path
        self.name = os.path.basename(raster_path)
        self.metadata = self.get_metadata()
        self.wavelength = self.get_wavelengths()

    def get_metadata(self):
        """
        Get the metadata of the raster image.

        Returns:
            dict: The metadata of the raster image.

        """
        xml_file_path = self.find_metadata_file()

        with open(xml_file_path, "r", encoding="utf-8") as file:
            my_xml = file.read()

        metadata_dict = xmltodict.parse(my_xml)

        return metadata_dict

    def get_wavelengths(self):
        """
        Get the wavelengths of the raster image.

        Returns:
            ndarray: The wavelengths of the raster image.

        """
        band_characterisation = self.metadata["level_X"]["specific"][
            "bandCharacterisation"
        ]
        band_ids = band_characterisation["bandID"]

        wavelengths = [band["wavelengthCenterOfBand"] for band in band_ids]

        return np.array(wavelengths, dtype=np.float32)

    def find_metadata_file(self):
        """
        Find the metadata file associated with the raster image.

        Returns:
            str: The path to the metadata file.

        Raises:
            FileNotFoundError: If the metadata file is not found.

        """
        tiff_file_path = self.path
        directory = os.path.dirname(tiff_file_path)

        xml_filename = os.path.basename(tiff_file_path).replace(
            "SPECTRAL_IMAGE.TIF", "METADATA.XML"
        )

        # Search for the XML file in the same directory
        for file in os.listdir(directory):
            if file == xml_filename:
                xml_file_path = os.path.join(directory, file)
                break
        else:
            raise FileNotFoundError("XML file not found.")

        return xml_file_path

    @property
    def datacube(self):
        """
        Get the datacube of the raster image.

        Returns:
            ndarray: The datacube of the raster image.

        """
        return self._datacube

    @datacube.setter
    def datacube(self, value):
        """
        Set the datacube of the raster image.

        Args:
            value (ndarray): The datacube of the raster image.

        """
        self._datacube = value

    def rescale(self: "Raster"):
        """
        Rescale the datacube of the raster image using gains and offsets.

        Returns:
            Raster: The rescaled raster image.

        """
        gains, offsets = self.get_gains_and_offsets()

        self.datacube = self.datacube * gains[:, None, None] + offsets[:, None, None]

        return self

    def get_gains_and_offsets(self: "Raster"):
        """
        Get the gains and offsets of the raster image.

        Returns:
            tuple: A tuple containing the gains and offsets of the raster image.

        """
        band_characterisation = self.metadata["level_X"]["specific"][
            "bandCharacterisation"
        ]

        band_ids = band_characterisation["bandID"]

        # Extracting gain values
        gains = [band["GainOfBand"] for band in band_ids]

        # Extracting offset values
        offsets = [band["OffsetOfBand"] for band in band_ids]

        return np.array(gains, dtype=np.float32), np.array(offsets, dtype=np.float32)
