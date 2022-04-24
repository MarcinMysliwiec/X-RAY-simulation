from os import path
from threading import Thread
from typing import Any, List, Union, Tuple, Callable

from PySide2.QtCore import SIGNAL, QObject
from PySide2.QtGui import QPixmap
from skimage import io

from ct import ComputerTomography
from gui.dicom import *


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.resize(1500, 800)
        self.ct_start_datetime: Union[None or datetime] = None
        self.debug = True

        self.inputs = {
            "img": None,
            "sinogram": None,
            "result": None,
            "fast_mode": False,
            "alpha_angle": 1,
            "theta_angle": 90,
            "detectors_amount": 180,
            "animation_img_frames": None,
            "animation_sinogram_frames": None,
            "animation_result_frames": None,
            "animation_sinogram_actual_frame": None,
            "animation_img_actual_frame": None,
            "animation_result_actual_frame": None
        }

        # First layout level
        self.plots_layout = {
            "object": QtWidgets.QGridLayout(),
            "items": {
                "img_fig": {
                    "object": QtWidgets.QLabel(self),
                    "position": (1, 1)
                },
                "radon_fig": {
                    "object": QtWidgets.QLabel(self),
                    "position": (1, 2)
                },
                "iradon_fig": {
                    "object": QtWidgets.QLabel(self),
                    "position": (1, 3),
                },
                "animation_slider": {
                    "object": QtWidgets.QSlider(Qt.Horizontal),
                    "position": (2, 1),
                    "signal": "valueChanged(int)",
                    "slot": lambda x: self.setInputValue("animation_img_actual_frame", x / 100 if x < 99 else 1)
                                      or self.setInputValue("animation_sinogram_actual_frame", x / 100 if x < 99 else 1)
                                      or self.setInputValue("animation_result_actual_frame", x / 100 if x < 99 else 1)
                                      or self.changeFrame("radon_fig")
                                      or self.changeFrame("iradon_fig")
                },
                "fast_mode": {
                    "object": QtWidgets.QCheckBox("Tryb szybki"),
                    "position": (2, 3),
                    "signal": "stateChanged(int)",
                    "slot": lambda x: self.setInputValue("fast_mode", False if not x else True)
                    # in the linux, for Qt, 2 means True
                }
            }
        }
        self.buttons_layout = {
            "object": QtWidgets.QVBoxLayout(),
            "items": {
                "load": {
                    "object": QtWidgets.QPushButton("Załaduj obrazek"),
                    "position": 1,
                    "signal": "clicked()",
                    "slot": self.loadImg
                },
                "run": {
                    "object": QtWidgets.QPushButton("Uruchom"),
                    "position": 2,
                    "signal": "clicked()",
                    "slot": self.startComputerTomography
                },
                "save_dicom": {
                    "object": QtWidgets.QPushButton("Zapisz DICOM"),
                    "position": 3,
                    "signal": "clicked()",
                    "slot": self.saveDicom
                },
                "show_dicom": {
                    "object": QtWidgets.QPushButton("Pokaż DICOM"),
                    "position": 4,
                    "signal": "clicked()",
                    "slot": self.showDicom
                }
            }
        }
        self.inputs_layout = {
            "object": QtWidgets.QGridLayout(),
            "items": {
                "alpha_angle_label": {
                    "object": QtWidgets.QLabel("Kąt obrotu"),
                    "position": (1, 1)
                },
                "alpha_angle": {
                    "object": QtWidgets.QSpinBox(),
                    "position": (1, 2),
                    "signal": "valueChanged(int)",
                    "slot": lambda x: self.setInputValue("alpha_angle", x)
                },
                "theta_label": {
                    "object": QtWidgets.QLabel("Kąt początkowy"),
                    "position": (2, 1)
                },
                "theta_angle": {
                    "object": QtWidgets.QSpinBox(),
                    "position": (2, 2),
                    "signal": "valueChanged(int)",
                    "slot": lambda x: self.setInputValue("theta_angle", x)
                },
                "detectors_num_label": {
                    "object": QtWidgets.QLabel("Ilość czujników"),
                    "position": (3, 1)
                },
                "detectors_num": {
                    "object": QtWidgets.QSpinBox(),
                    "position": (3, 2),
                    "signal": "valueChanged(int)",
                    "slot": lambda x: self.setInputValue("detectors_amount", x)
                },
            }
        }

        # Second layout level
        self.aggregated_layouts = {
            "object": QtWidgets.QVBoxLayout(),
            "items": {
                "first": {
                    "reference": self.plots_layout,
                    "position": 1
                },
                "second": {
                    "object": QtWidgets.QGridLayout(),
                    "position": 2,
                    "items": {
                        "left": {
                            "reference": self.inputs_layout,
                            "position": (1, 1)
                        },
                        "empty": {
                            "object": QtWidgets.QWidget(),
                            "position": (1, 2)
                        },
                        "right": {
                            "reference": self.buttons_layout,
                            "position": (1, 3)
                        }
                    }
                }
            }
        }

        self.plots_layout["items"]["img_fig"]["object"].setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                                                      QtWidgets.QSizePolicy.Ignored)
        self.plots_layout["items"]["img_fig"]["object"].setScaledContents(True)
        self.plots_layout["items"]["img_fig"]["object"].setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Plain)
        self.plots_layout["items"]["img_fig"]["object"].setLineWidth(1)

        self.plots_layout["items"]["radon_fig"]["object"].setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                                                        QtWidgets.QSizePolicy.Ignored)
        self.plots_layout["items"]["radon_fig"]["object"].setScaledContents(True)
        self.plots_layout["items"]["radon_fig"]["object"].setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Plain)
        self.plots_layout["items"]["radon_fig"]["object"].setLineWidth(1)

        self.plots_layout["items"]["iradon_fig"]["object"].setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                                                         QtWidgets.QSizePolicy.Ignored)
        self.plots_layout["items"]["iradon_fig"]["object"].setScaledContents(True)
        self.plots_layout["items"]["iradon_fig"]["object"].setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Plain)
        self.plots_layout["items"]["iradon_fig"]["object"].setLineWidth(1)

        self.plots_layout["items"]["animation_slider"]["object"].setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                                                               QtWidgets.QSizePolicy.Preferred)
        self.plots_layout["items"]["animation_slider"]["object"].setDisabled(True)

        self.inputs_layout["items"]["theta_angle"]["object"].setMinimum(0)
        self.inputs_layout["items"]["theta_angle"]["object"].setMaximum(360)
        self.inputs_layout["items"]["theta_angle"]["object"].setValue(self.inputs["theta_angle"])

        self.inputs_layout["items"]["alpha_angle"]["object"].setMinimum(1)
        self.inputs_layout["items"]["alpha_angle"]["object"].setMaximum(179)
        self.inputs_layout["items"]["alpha_angle"]["object"].setValue(self.inputs["alpha_angle"])

        self.inputs_layout["items"]["detectors_num"]["object"].setMinimum(2)
        self.inputs_layout["items"]["detectors_num"]["object"].setMaximum(1000)
        self.inputs_layout["items"]["detectors_num"]["object"].setValue(self.inputs["detectors_amount"])

        self.buttons_layout["items"]["run"]["object"].setDisabled(True)
        self.buttons_layout["items"]["save_dicom"]["object"].setDisabled(True)

        self.createLayout(self.aggregated_layouts)
        self.setLayout(self.aggregated_layouts["object"])

    def createLayout(self, layout: Any) -> None:
        """
        Create layout via recursion.
        :param layout: layout object to create
        :return: None
        """

        def addIf(operation: Callable, widget_dict: dict, widget_object, position: Tuple[int]):
            if "position" in widget_dict:
                try:
                    operation(widget_object, *position)
                except:
                    operation(widget_object, position)
            else:
                operation(widget_object)

        # Python checks function argument, cannot pass undefined or unnecessary args ...
        for widget in layout["items"].values():
            if "items" in widget:
                self.createLayout(widget)
                addIf(layout["object"].addLayout, widget, widget["object"], widget["position"])
            elif "reference" in widget:
                self.createLayout(widget["reference"])
                addIf(layout["object"].addLayout, widget, widget["reference"]["object"], widget["position"])
            else:  # widget
                addIf(layout["object"].addWidget, widget, widget["object"], widget["position"])
                if "signal" and "slot" in widget:
                    QObject.connect(widget["object"], SIGNAL(widget["signal"]), widget["slot"])

    def loadImg(self) -> None:
        """
        Load image to process by CT.
        :return: None
        """
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Otwórz plik", "./img",
                                                         "Otwórz plik (*.png *.jpg *.bmp)")

        print(filename)
        if filename[0] == '':
            return
        else:
            # RGB image
            img = io.imread(path.expanduser(filename[0]))
            fig = self.plots_layout["items"]["img_fig"]["object"]
            fig.setPixmap(Conversion().array2qpixmap(img))

            # save rgb image as greyscale
            self.inputs["img"] = Conversion().rgb2greyscale(img)
            self.buttons_layout["items"]["run"]["object"].setEnabled(True)

            self.plots_layout["items"]["animation_slider"]["object"].setDisabled(True)

    def startComputerTomography(self) -> None:
        runStatus = self.buttons_layout["items"]["run"]["object"].isEnabled()
        loadStauts = self.buttons_layout["items"]["load"]["object"].isEnabled()

        self.buttons_layout["items"]["run"]["object"].setEnabled(False)
        self.buttons_layout["items"]["load"]["object"].setEnabled(False)
        self.buttons_layout["items"]["save_dicom"]["object"].setEnabled(False)

        # parallel task
        def task():
            try:
                ct = ComputerTomography(self.debug, self.inputs["fast_mode"], self.inputs["img"],
                                        self.inputs["alpha_angle"], self.inputs["theta_angle"],
                                        self.inputs["detectors_amount"])

                self.ct_start_datetime = datetime.now()

                self.inputs["sinogram"], self.inputs["result"] = ct.run()
                if self.debug:
                    print('Normalizing sinogram.')
                self.normalizeImg(self.inputs["sinogram"])

                if not self.inputs["fast_mode"]:
                    frames = ct.get_frames()
                    self.inputs["animation_sinogram_frames"], self.inputs["animation_result_frames"] = frames
                    if self.debug:
                        print('Preparing sinogram frames.')
                    self.inputs["animation_sinogram_frames"].append(self.inputs["sinogram"])
                    if self.debug:
                        print('Preparing result frames.')
                    self.inputs["animation_result_frames"].append(self.inputs["result"])
                    self.preprocessFrames(self.inputs["animation_sinogram_frames"])
                    self.preprocessFrames(self.inputs["animation_result_frames"])
                    self.plots_layout["items"]["animation_slider"]["object"].setEnabled(True)
                    self.plots_layout["items"]["animation_slider"]["object"].setValue(100)

                else:
                    self.plots_layout["items"]["animation_slider"]["object"].setDisabled(True)

                self.plots_layout["items"]["radon_fig"]["object"].setPixmap(
                    self.preprocessFrame(self.inputs["sinogram"]))
                self.plots_layout["items"]["iradon_fig"]["object"].setPixmap(
                    self.preprocessFrame(self.inputs["result"]))

            except Exception as msg:
                QtWidgets.QErrorMessage().showMessage(str(msg))
            finally:
                self.buttons_layout["items"]["run"]["object"].setEnabled(runStatus)
                self.buttons_layout["items"]["load"]["object"].setEnabled(loadStauts)
                self.buttons_layout["items"]["save_dicom"]["object"].setEnabled(True)

        thread = Thread(target=task)
        thread.start()

    @staticmethod
    def preprocessFrames(frames: List[np.ndarray]) -> None:
        """
        Convert greyscale frames into rgb QPixmap.
        :param frames: numpy greyscale ndarray list
        :return: None
        """
        conv = Conversion(frames[0].shape)
        for index, img in enumerate(frames):
            frames[index] = conv.array2qpixmap(conv.greyscale2rgb(img))

    @staticmethod
    def preprocessFrame(frame: np.ndarray) -> QPixmap:
        """
        Convert greyscale frame into rgb QPixmap.
        :param frame: numpy greyscale ndarray
        :return: QPixmap
        """
        conv = Conversion()
        return conv.array2qpixmap(conv.greyscale2rgb(frame))

    @staticmethod
    def normalizeImg(img: np.ndarray) -> None:
        """
        Extends image pixel value range from [0-1] to [0-255].
        :param img: image to normalize
        :return: None
        """
        img *= 255

    def setInputValue(self, key: str, value: Any) -> None:
        self.inputs[key] = value

    def changeFrame(self, label_type: str) -> None:
        """
        Load image from frames list into selected label.
        :param label_type: selected label
        :return: None
        """
        if label_type == "radon_fig":
            frame_id = self.inputs["animation_sinogram_actual_frame"] * (
                    len(self.inputs["animation_sinogram_frames"]) - 1)
            frame_id = round(frame_id)
            frame = self.inputs["animation_sinogram_frames"][frame_id]

            fig = self.plots_layout["items"]["radon_fig"]["object"]
            fig.setPixmap(frame)
        elif label_type == "iradon_fig":
            frame_id = self.inputs["animation_result_actual_frame"] * (len(self.inputs["animation_result_frames"]) - 1)
            frame_id = round(frame_id)
            frame = self.inputs["animation_result_frames"][frame_id]

            fig = self.plots_layout["items"]["iradon_fig"]["object"]
            fig.setPixmap(frame)

    def showDicom(self) -> None:
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Otwórz DICOM", "./results/DICOM", "Plik DICOM (*.dcm)")[
            0]
        if filename == '':
            self.close()
            return False
        else:
            ds = pydicom.dcmread(filename)
            ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
            fig = self.plots_layout["items"]["img_fig"]["object"]
            fig.setPixmap(Conversion().array2qpixmap(ds.pixel_array))

            # save rgb image as greyscale
            self.inputs["img"] = Conversion().rgb2greyscale(ds.pixel_array)
            self.buttons_layout["items"]["run"]["object"].setEnabled(True)
            self.plots_layout["items"]["animation_slider"]["object"].setDisabled(True)

    def saveDicom(self) -> None:
        DicomSaveDialog(self.inputs["img"], self.ct_start_datetime).exec_()
