import os
import os.path

# we require numpy, opencv, and matplotlib
import numpy as np
import cv2
import matplotlib

# this disables GUI windows from popping up
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# set working directory to location of script:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
print(dname)
os.chdir(dname)

def init_accumulated_exposures():
    acc_exp = None
    return acc_exp


def input_seconds_per_frame(spf):
    sec_per_frame = spf
    return sec_per_frame


def open_file(file_name):
    file = open(file_name, "r")
    return file


def read_lines(file_name):
    lines = file_name.readlines()
    return lines


def parse_line(line):
    # format of a line is space delineated in the following format
    #
    # image_file_path number_of_labels x1 y1 x2 y2 x3 y3 x4 y4 x1 y1 x2 y2 x3 y3 x4 y4 ... etc
    #
    # Note: We use 4 x,y coordinates to denote a detection label
    # since Orpix logo detection outputs a quadrilateral as opposed to a rectangle
    toks = line.split(' ')

    frame_path = toks[0]
    label_count = int(toks[1])

    # getting points only, casting to int
    pts = toks[2:]
    pts = [int(x) for x in pts]

    labels = []
    for i in range(label_count):

        # get the 8 points for the current label
        label_pts = pts[i * 8:i * 8 + 8]

        # reshape to array of 4 tuples
        pt_pairs = []
        for ptind in range(0, 8, 2):
            pt_pairs.append([label_pts[ptind], label_pts[ptind + 1]])

            # add this label to the list of labels we return
        pt_pairs = np.array(pt_pairs)
        labels.append(pt_pairs)

    return frame_path, np.array(labels)


def load_image(frame_path):
    frame = cv2.imread(frame_path)
    return frame


def create_higlighted_image_folder(folder_name):
    if not os.path.exists(folder_name):
        os.mkdir('output')
        print('successfully created output folder to save highlighted images')


def get_accumulated_exposures(frame):
    accumulated_exposures = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.float)
    return accumulated_exposures


def mask(accumulated_exposures):
    masking = np.zeros(accumulated_exposures.shape, dtype=np.float)
    return masking


def fill_convex_poly(masking, label, seconds_per_frame):
    cv2.fillConvexPoly(masking, label, (seconds_per_frame))


def highlight_labels(img, labels, masking=None):
    # create a copy of the image so we can draw on it
    imgcpy = img.copy()

    # draw a quadrilateral for each label in red
    cv2.polylines(imgcpy, labels, True, (0, 0, 255), thickness=2)

    # a mask needs to be created from the labels so we can properly highlight.
    # if the mask isn't passed in, we create it
    if type(masking) == type(None):
        masking = np.zeros(imgcpy.shape, dtype=np.float)
        for label in labels:
            # this sets all pixels inside the label to 1
            cv2.fillConvexPoly(masking, label, (1))

            # create a rgb version of the mask by setting each channel to the mask we created
    masking = (masking > 0).astype(np.uint8)
    maskrgb = np.zeros(imgcpy.shape, np.uint8)
    maskrgb[:, :, 0] = masking
    maskrgb[:, :, 1] = masking
    maskrgb[:, :, 2] = masking

    # interpolate image with white using a weighted sum
    bgimg = .5 * 255 * np.ones(imgcpy.shape, np.float) + .5 * imgcpy.astype(np.float)
    # mask out the background
    bgimg = (1 - maskrgb) * bgimg
    # cast to uint8 image
    bgimg = np.round(bgimg).astype(np.uint8)

    # get foreground unchanged
    fgimg = maskrgb * imgcpy

    # add white tinted background with unchanged foreground
    imgcpy = bgimg + fgimg.astype(np.uint8)

    return imgcpy


def save_highlighted_images(frame_path, highlighted_image):
    cv2.imwrite('output/%s' % os.path.basename(frame_path), highlighted_image)


def sum_accumulated_exposures(accumulated_exposures, masking):
    a = accumulated_exposures + masking
    return a


def create_save_heatmap(accumulated_exposures):
    data = np.array(accumulated_exposures)
    # create the figure
    fig, axis = plt.subplots()
    # set the colormap
    # we will use cm.jet
    hm = axis.pcolor(data, cmap=plt.cm.jet)
    # set axis ranges
    axis.set(xlim=[0, data.shape[1]], ylim=[0, data.shape[0]], aspect=1)
    # need to invert coordinate for images
    axis.invert_yaxis()
    # remove the ticks
    axis.set_xticks([])
    axis.set_yticks([])

    # fit the colorbar to the height
    shrink_scale = 1.0
    aspect = data.shape[0] / float(data.shape[1])
    if aspect < 1.0:
        shrink_scale = aspect
    clb = plt.colorbar(hm, shrink=shrink_scale)
    # set title
    clb.ax.set_title('Exposure (seconds)', fontsize=10)
    # saves image to same directory that the script is located in (our working directory)
    plt.savefig('heatmap.png', bbox_inches='tight')
    # close objects
    plt.close('all')


def main():
    # keeps track of exposure time per pixel.  Accumulates for each image
    accumulated_exposures = init_accumulated_exposures()
    print('type of accumulated_exposures - ', type(accumulated_exposures))

    # frames were sampled at one 0.1 second per frame.  If you sampled frames from a video at a different rate, change this value
    seconds_per_frame = input_seconds_per_frame(0.1)
    print('seconds_per_frame - ', seconds_per_frame)

    # we open the labels file and will iterate through each line.
    # each line contains a reference to the image and the corresponding polygon lables (4 points per label)
    # each frame in the labels file was extracted from one video
    f = open_file('labels.txt')

    lines = read_lines(f)

    for line in lines:

        # parse the line using helper function
        frame_path, labels = parse_line(line)

        print("processing ", frame_path)

        # load the image
        frame = load_image(frame_path)

        # this is where the highlighted images will go
        create_higlighted_image_folder('output')

        # if the heatmap is None we create it with same size as frame, single channel
        if type(accumulated_exposures) == type(None):
            accumulated_exposures = get_accumulated_exposures(frame)
            print("accumulated_exposures type ", type(accumulated_exposures))

        # we create a mask where all pixels inside each label are set to number of seconds per frame that the video was sampled at
        # so as we accumulate the exposure heatmap counts, each pixel contained inside a label contributes the seconds_per_frame
        # to the overall accumulated exposure values
        masking = mask(accumulated_exposures)

        # masking = np.zeros(accumulated_exposures.shape, dtype=np.float)

        for label in labels:
            fill_convex_poly(masking, label, seconds_per_frame)

        # highlight the labels on the image and save.
        # comment out the 2 lines below if you only want to compute the heatmap
        highlighted_image = highlight_labels(frame, labels, masking)
        save_highlighted_images(frame_path, highlighted_image)

        # accumulate the heatmap object exposure time
        accumulated_exposures = sum_accumulated_exposures(accumulated_exposures, masking)
        print("HERE %s" % type(accumulated_exposures))

    #
    # create final heatmap using matplotlib
    #

    create_save_heatmap(accumulated_exposures)



if __name__ == '__main__':
    main()