from math import pi, radians
from typing import Tuple, Callable

import numpy as np

from .EmitterSimulation import calc_alpha_angles, simple_resenham_algorithm


class ComputerTomography:
    """
    Simulates computer tomography via image reconstruction.
    """

    def __init__(self, debug: bool, fast_mode: bool, img: np.ndarray, alpha_angle: int, theta_angle: int,
                 detectors_number: int):
        """
        :param img: image to simulate radon transform
        :param alpha_angle: emiters and detectors_pos angle for next iteration in degrees
        :param theta_angle: angular diameter of detectors
        :param detectors_number: amount of detectors_pos
        """
        if alpha_angle <= 0:
            raise ArithmeticError("Rotate angle have to be greater than 0.")

        self.debug = debug
        self.fast_mode = fast_mode
        self.img = img
        self.alpha_angle = alpha_angle
        self.theta = theta_angle
        self.detectors_number = detectors_number

        self.sinogram_plots = []
        self.result_plots = []

    def run(self) -> Tuple[np.ndarray, np.ndarray]:
        if self.debug:
            print('Radon transform starting.')

        sinogram = self.radon_transform(self.img, self.alpha_angle, self.theta,
                                        self.detectors_number, self.save_radon_frame)
        if self.debug:
            print('Radon transform ended, inverse radon transform starting.')

        result = self.iradon_transform(self.img.shape, sinogram, self.alpha_angle, self.theta, self.detectors_number,
                                       self.save_iradon_frame)

        if self.debug:
            print('Inverse radon transform ended.')
            # timestr = time.strftime("%Y%m%d-%H%M%S")
            # skimage.io.imsave("./results/images/" + timestr + "-sinogram.jpg", sinogram)
            # skimage.io.imsave("./results/images/" + timestr + "-result.jpg", result)

        return sinogram, result

    def radon_transform(self, image: np.ndarray, alpha_angle: int, theta_angle: int, detectors_number: int,
                        animate_func: Callable[[np.ndarray], None] = None) -> np.ndarray:
        """
        Construct sinogram from image.
        :param image: numpy image
        :param alpha_angle: rotate angle in degree per iteration
        :param theta_angle: angular diameter of detectors
        :param detectors_number: amount of detectors
        :param animate_func: function for save sinogram frames
        :return: sinogram
        """
        alpha_angle = radians(alpha_angle)
        theta_angle = radians(theta_angle)

        list_of_alpha_angles = calc_alpha_angles(alpha_angle)
        sinogram = np.zeros((len(list_of_alpha_angles), detectors_number), dtype=np.float16)

        for i, alpha in enumerate(list_of_alpha_angles):
            for j, line in enumerate(simple_resenham_algorithm(image, theta_angle, detectors_number, alpha)):
                value = np.average(image[line])
                sinogram[i, j] = value
            if not self.fast_mode:
                animate_func(sinogram)

        self.filter_sinogram(sinogram)

        return sinogram

    def iradon_transform(self, image_shape: Tuple[int, int], sinogram: np.ndarray, alpha_angle: float,
                         theta_angle: float,
                         detectors_number: int,
                         animate_func: Callable[[np.ndarray, np.ndarray], None] = None) -> np.ndarray:
        """
        Construct sinogram from image.
        :param image_shape: original image shape
        :param alpha_angle: angle in degree to rotate every iteration
        :param theta_angle: angular diameter of detectors
        :param sinogram: sinogram of original image
        :param detectors_number: amount of detectors
        :param animate_func: function for save reconstructed image frames
        :return: reconstructed image
        """
        alpha_angle = radians(alpha_angle)
        theta_angle = radians(theta_angle)
        list_of_alpha_angles = calc_alpha_angles(alpha_angle)
        image = np.zeros(image_shape, dtype=np.float16)

        for i, alpha in enumerate(list_of_alpha_angles):
            for j, line in enumerate(simple_resenham_algorithm(image, theta_angle, detectors_number, alpha)):
                image[line] += sinogram[i, j]
            if not self.fast_mode:
                animate_func(image)

        return image

    def filter_sinogram(self, image):
        kernel = [1 if k == 0 else (0 if k % 2 == 0 else -4 / pi ** 2 / k ** 2)
                  for k in range(-10, 11)]
        for i in range(image.shape[0]):
            image[i, :] = np.convolve(image[i, :], kernel, mode='same')

    def get_frames(self) -> Tuple[list, list]:
        return self.sinogram_plots, self.result_plots

    def save_radon_frame(self, sinogram: np.ndarray) -> None:
        sinogram = np.array(sinogram, copy=True)
        # sinogram *= 255
        self.sinogram_plots.append(sinogram)

    def save_iradon_frame(self, img: np.ndarray) -> None:
        img_iradon = np.array(img, copy=True)
        self.result_plots.append(img_iradon)
