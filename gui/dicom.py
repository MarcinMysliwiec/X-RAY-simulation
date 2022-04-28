from datetime import datetime
from typing import Dict

import PySide2.QtWidgets as QtWidgets
import numpy as np
import pydicom as pd
import pydicom.uid
import pydicom._storage_sopclass_uids


class DicomSaveDialog(QtWidgets.QDialog):
    """
    Class for save patient informations to DICOM file.
    """

    def __init__(self, img: np.ndarray, date_time: datetime, name_input: str, id_input: str, comments_input: str):
        """
        :param img: image to save
        :param date_time: ct operation start datetime
        """
        super().__init__(None)
        self.setWindowTitle('Zapisz w formacie DICOM')
        self.img = img
        self.date_time = date_time

        self.name_input = name_input
        self.id_input = id_input
        self.comments_input = comments_input

        print("contruct", self.name_input, self.id_input, self.comments_input)

    def validate_input(self) -> bool:
        mb = QtWidgets.QErrorMessage()
        mb.setModal(True)
        if self.id_input == '':
            mb.showMessage('ID pacjenta nie może być puste!')
            mb.exec_()
            return False
        elif self.name_input == '':
            mb.showMessage('Imie pacjenta nie może być puste.')
            mb.exec_()
            return False

        return True


    def save(self) -> None:
        """
        Save input data into DICOM file.
        :return: None
        """
        if not self.validate_input():
            return
        else:
            filename = QtWidgets.QFileDialog.getSaveFileName(self, "Zapisz DICOM", "./results/DICOM", "*.dcm")[0]
            if filename == '':
                return
            else:
                meta = pd.Dataset()

                # CT Image Storage
                meta.MediaStorageSOPClassUID = pd._storage_sopclass_uids.CTImageStorage
                meta.MediaStorageSOPInstanceUID = pd.uid.generate_uid()
                meta.TransferSyntaxUID = pd.uid.ExplicitVRLittleEndian

                ds = pd.FileDataset(None, {}, preamble=b"\0" * 128)
                ds.file_meta = meta

                ds.is_little_endian = True
                ds.is_implicit_VR = False

                # CT Image Storage
                ds.SOPClassUID = pd._storage_sopclass_uids.CTImageStorage
                ds.SOPInstanceUID = pd.uid.generate_uid()

                ds.ContentDate = f"{self.date_time.year:04}{self.date_time.month:02}{self.date_time.day:02}"
                ds.ContentTime = f"{self.date_time.hour:02}{self.date_time.minute:02}{self.date_time.second:02}"

                ds.PatientID = self.id_input
                ds.PatientName = self.name_input
                ds.ImageComments = self.comments_input

                ds.Modality = "CT"
                ds.SeriesInstanceUID = pd.uid.generate_uid()
                ds.StudyInstanceUID = pd.uid.generate_uid()
                ds.FrameOfReferenceUID = pd.uid.generate_uid()

                ds.BitsStored = 8
                ds.BitsAllocated = 8
                ds.SamplesPerPixel = 1
                ds.HighBit = 7

                ds.ImagesInAcquisition = 1
                ds.InstanceNumber = 1

                ds.Rows, ds.Columns = self.img.shape

                ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"

                ds.PhotometricInterpretation = "MONOCHROME2"
                ds.PixelRepresentation = 0

                pd.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)

                ds.PixelData = self.img.astype(np.uint8).tobytes()

                ds.save_as(f"{filename}", write_like_original=False)
                self.close()
