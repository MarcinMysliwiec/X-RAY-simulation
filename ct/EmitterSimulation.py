from math import pi, cos, sin

import skimage


def calc_alpha_angles(alpha_angle):
    list_of_angles = [i * alpha_angle for i in range(int(pi / alpha_angle))]
    return [- angle + pi / 2. for angle in list_of_angles]


def calc_radius(image):
    return (min(image.shape) - 1) / 2.


def find_emitter_coords(radius, alpha_angle, theta_angle, detectors_number):
    x = lambda i: radius * cos(alpha_angle - theta_angle / 2. + i * theta_angle / (detectors_number - 1))
    y = lambda i: radius * sin(alpha_angle - theta_angle / 2. + i * theta_angle / (detectors_number - 1))
    return tuple((x(i), y(i)) for i in reversed(range(detectors_number)))


def find_detector_coords(radius, alpha_angle, theta_angle, detectors_number):
    x = lambda i: radius * cos(alpha_angle + pi - theta_angle / 2. + i * theta_angle / (detectors_number - 1))
    y = lambda i: radius * sin(alpha_angle + pi - theta_angle / 2. + i * theta_angle / (detectors_number - 1))
    return tuple((x(i), y(i)) for i in reversed(range(detectors_number)))


def coords_formula_to_image(coords, image_size):
    r = (image_size[0] - 1) / 2. - coords[1]
    c = (image_size[1] - 1) / 2. + coords[0]
    return r, c


def simple_resenham_algorithm(image, theta_angle, detectors_number, alpha_angle):
    radius = calc_radius(image)
    emitter_coords = find_emitter_coords(radius, alpha_angle, theta_angle, detectors_number)
    detector_coords = find_detector_coords(radius, alpha_angle, theta_angle, detectors_number)

    for j, end_coords in enumerate(zip(emitter_coords, reversed(detector_coords))):
        i_coords = tuple(coords_formula_to_image(c, image.shape) for c in end_coords)
        line = skimage.draw.line_nd(*i_coords, endpoint=True)
        yield line
