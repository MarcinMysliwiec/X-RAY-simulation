import glob
import os
import time
from os import path

import skimage
from PIL import Image
from skimage import io

from helpers import Helpers
from ct import ComputerTomography

IMG_DIR = "./results/images/"


def generate_ct(
        sub_folder, sub_name, debug, fastMode, img,
        alpha_angle, theta_angle_default,
        detectors_amount):
    time.sleep(1)

    ct = ComputerTomography(debug, fastMode, img,
                            alpha_angle, theta_angle_default,
                            detectors_amount)
    dir = IMG_DIR + sub_folder
    if not os.path.exists(dir):
        os.makedirs(dir)

    sinogram, result = ct.run()
    timestr = time.strftime("%Y%m%d-%H%M%S")
    sub_name = str(sub_name)
    skimage.io.imsave(dir + "/sinogram-" + sub_name + "-" + ".jpg", sinogram)
    skimage.io.imsave(dir + "/result-" + sub_name + "-" + ".jpg", result)


def generate_gif(sub_folder):
    fp_in = IMG_DIR + sub_folder + "/sinogram-*.jpg"
    fp_out = IMG_DIR + sub_folder + ".gif"
    print(fp_in)

    imgs = (Image.open(f) for f in sorted(glob.glob(fp_in)))
    print(imgs)
    img = next(imgs)  # extract first image from iterator
    img.save(fp=fp_out, format='GIF', append_images=imgs,
             save_all=True, duration=200, loop=0)


if __name__ == '__main__':
    debug = True
    fastMode = True
    filename = './img/CT_ScoutView.jpg'


    def debug_log(*args):
        if debug:
            for arg in args:
                print(arg)


    # if os.path.exists(IMG_DIR):
    #     shutil.rmtree(IMG_DIR)

    detectors_default = 180
    detectors_start = 90
    detectors_stop = 720
    detectors_step = 90
    list_of_detectors = [detectors_start + (i * detectors_step) for i in range(int(detectors_stop / detectors_step))]

    alpha_angle_default = 1  # 180 degrees in radians is 1
    alpha_angle_start = 90
    alpha_angle_stop = 720
    alpha_angle_step = 90
    list_of_alpha_angles = [(alpha_angle_start + (i * alpha_angle_step)) / 180 for i in
                            range(int(alpha_angle_stop / alpha_angle_step))]

    theta_angle_default = 180
    theta_angle_start = 45
    theta_angle_stop = 270
    theta_angle_step = 45
    list_of_theta_angles = [theta_angle_start + (i * theta_angle_step) for i in
                            range(int(theta_angle_stop / theta_angle_step))]

    image = io.imread(path.expanduser(filename))
    img = Helpers().rgb2greyscale(image)

    debug_log("=== START EXPERIMENT WITH DIFFERENT DETECTORS ===")
    debug_log("List of detectors:", list_of_detectors)
    for i, detectors_amount in enumerate(list_of_detectors):
        debug_log("\n", i, detectors_amount)
        generate_ct('detectors', detectors_amount, debug, fastMode, img,
                    alpha_angle_default, theta_angle_default,
                    detectors_amount)

    debug_log("=== START EXPERIMENT WITH DIFFERENT ALPHA ANGLES ===")
    debug_log("List of alpha angles:", list_of_alpha_angles)
    for i, alpha_angle in enumerate(list_of_alpha_angles):
        debug_log("\n", i, alpha_angle)
        generate_ct('alpha', alpha_angle, debug, fastMode, img,
                    alpha_angle, theta_angle_default,
                    detectors_default)

    debug_log("=== START EXPERIMENT WITH DIFFERENT THETA ANGLES ===")
    debug_log("List of theta:", list_of_theta_angles)
    for i, theta_angle in enumerate(list_of_theta_angles):
        debug_log("\n", i, theta_angle)
        generate_ct('theta', theta_angle, debug, fastMode, img,
                    alpha_angle_default, theta_angle,
                    detectors_default)
