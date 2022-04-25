from datetime import datetime
from typing import Dict

import PySide2.QtWidgets as QtWidgets
import numpy as np
import pydicom as pd
import pydicom._storage_sopclass_uids
import pydicom.uid


class DicomSaveDialog(QtWidgets.QDialog):
    """
    Class for save patient informations to DICOM file.
    """

    def __init__(self, img: np.ndarray, date_time: datetime):
        """
        :param img: image to save
        :param date_time: ct operation start datetime
        """
        super().__init__(None)
        self.setWindowTitle('Zapisz w formacie DICOM')
        self.img = img
        self.date_time = date_time

        self.input_data: Dict[str, None or str] = {
            'PatientID': None,
            'PatientName': None,
            'PatientSex': None,
            'ImageComments': None
        }

        self.name_input = None
        self.id_input = None
        self.sex_input = None
        self.comments_input = None

        self.createLayout()

    def createLayout(self) -> None:
        self.name_input = QtWidgets.QLineEdit()
        self.id_input = QtWidgets.QLineEdit()
        self.sex_input = QtWidgets.QComboBox()
        self.comments_input = QtWidgets.QPlainTextEdit()

        self.comments_input.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        self.sex_input.addItem('Mezczyzna')
        self.sex_input.addItem('Kobieta')

        cancel = QtWidgets.QPushButton('Anuluj')
        save = QtWidgets.QPushButton('Zapisz')

        cancel.clicked.connect(self.close)
        save.clicked.connect(self.save)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(cancel, 1, 1)
        grid.addWidget(save, 1, 2)

        form = QtWidgets.QFormLayout()
        form.addRow(QtWidgets.QLabel('ID pacjenta'), self.id_input)
        form.addRow(QtWidgets.QLabel('Imie'), self.name_input)
        form.addRow(QtWidgets.QLabel('Płec'), self.sex_input)
        form.addRow(QtWidgets.QLabel('Komentarze'), self.comments_input)
        form.addRow(grid)
        self.setLayout(form)

    def validateInput(self) -> bool:
        mb = QtWidgets.QErrorMessage()
        mb.setModal(True)
        if self.id_input.text() == '':
            mb.showMessage('ID pacjenta nie może być puste!')
            mb.exec_()
            return False
        elif self.name_input.text() == '':
            mb.showMessage('Imie pacjenta nie może być puste.')
            mb.exec_()
            return False

        return True

    def parseInput(self) -> bool:
        if not self.validateInput():
            return False
        else:
            self.input_data["PatientID"] = self.id_input.text()
            self.input_data["PatientName"] = self.name_input.text()
            self.input_data["PatientSex"] = 'M' if self.sex_input.currentText() == 'Male' else 'F'
            self.input_data["ImageComments"] = self.comments_input.toPlainText()

            return True

    def save(self) -> None:
        """
        Save input data into DICOM file.
        :return: None
        """
        if not self.parseInput():
            return
        else:
            filename = QtWidgets.QFileDialog.getSaveFileName(self, "Zapisz DICOM", "./results/DICOM", "*.dcm")[0]
            if filename == '':
                return
            else:
                meta = pd.Dataset()

                # CT Image Storage
                meta.MediaStorageSOPClassUID = pydicom._storage_sopclass_uids.CTImageStorage
                meta.MediaStorageSOPInstanceUID = pd.uid.generate_uid()
                meta.TransferSyntaxUID = pd.uid.ExplicitVRLittleEndian

                ds = pd.FileDataset(None, {}, preamble=b"\0" * 128)
                ds.file_meta = meta

                ds.is_little_endian = True
                ds.is_implicit_VR = False

                # CT Image Storage
                ds.SOPClassUID = pydicom._storage_sopclass_uids.CTImageStorage
                ds.SOPInstanceUID = pd.uid.generate_uid()

                ds.ContentDate = f"{self.date_time.year:04}{self.date_time.month:02}{self.date_time.day:02}"
                ds.ContentTime = f"{self.date_time.hour:02}{self.date_time.minute:02}{self.date_time.second:02}"

                ds.PatientName = self.input_data["PatientName"]
                ds.PatientID = self.input_data["PatientID"]
                ds.PatientSex = self.input_data["PatientSex"]
                ds.ImageComments = self.input_data["ImageComments"]

                ds.Modality = "CT"
                ds.SeriesInstanceUID = pydicom.uid.generate_uid()
                ds.StudyInstanceUID = pydicom.uid.generate_uid()
                ds.FrameOfReferenceUID = pydicom.uid.generate_uid()

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

                pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)

                ds.PixelData = self.img.astype(np.uint8).tobytes()

                ds.save_as(f"{filename}", write_like_original=False)
                self.close()

