#!/usr/bin/python3
#
# General flow
# 1. Parse the configuration file
#    a. Get the wordpress URL and password
#    b. Get the image parameters (MAX_WIDTH)
# 2. Process the images
#    a. Fix rotation if required ('jhead -autorate')
#    b. Resize to max width of config['MAX_WIDTH']
# 3. Upload to wordpress site

import argparse
import configparser
from datetime import date
#import mimetypes
import os
#import subprocess
from PIL import Image #, ImageFile

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts

SIFT_VERSION = "1.05"

def parse_configuration(cfg_file, logfile, verbose=False):
    config = configparser.ConfigParser()
    if args.debug:
        print("reading config file " + cfg_file)

    if verbose:
        logfile.write("reading config file " + cfg_file)
    config.read(os.path.expanduser(cfg_file))
    # We should do something if the config file is not found

    return config


def parse_arguments():
    parser = argparse.ArgumentParser(
        description = "Formats and uploads images to a wordpress site",
        epilog = "BrokenLogo internet Production (BLiP)\n" 
            + "Kevin Somervill copyright 2016"
        )
    parser.add_argument("files", metavar="filename", type=str, nargs="+",
            help="image files to be processed and uploaded")

    parser.add_argument("-v", "--verbose", action='store_true',
            help="print/log verbose output")

    parser.add_argument('-V', '--version', action='version',
            version='%(prog)s ' + SIFT_VERSION)

    parser.add_argument("-D", "--debug", action='store_true',
            help="print debug output")

    parser.add_argument("-C", "--config", type=str, nargs="?",
            default="~/.sift.cfg",
            help="set config file")

    args = parser.parse_args()
    return args


# This part taken blatantly from Kyle Fox's fix_orientation patch. This will
# be integrated such that it's not a plain copy and paste.

# The EXIF tag that holds orientation data.
EXIF_ORIENTATION_TAG = 274

# Obviously the only ones to process are 3, 6 and 8.
# All are documented here for thoroughness.
ORIENTATIONS = {
    1: ("Normal", 0),
    2: ("Mirrored left-to-right", 0),
    3: ("Rotated 180 degrees", 180),
    4: ("Mirrored top-to-bottom", 0),
    5: ("Mirrored along top-left diagonal", 0),
    6: ("Rotated 90 degrees", -90),
    7: ("Mirrored along top-right diagonal", 0),
    8: ("Rotated 270 degrees", -270)
}

def process_images(image_ary, max_width, out_dir, verbose, logfile=None):
    if args.debug:
        print("Debug process_images()")

    dest_ary = []

    for filename in image_ary:
        img = Image.open(filename)
        if logfile:
            logfile.write("processing image: " + filename + "\n")

        xpix, ypix = img.size
        if args.debug and logfile:
            logfile.write("Image dimensions before rotation: "
                          + " (" + str(xpix) + "x" + str(ypix) + ")\n")

        if rotate_images and (img.format == 'JPEG'):
            if args.debug:
                print("Image format: " + img.format)
            try:
                # Check the image's orientation
                orientation = img._getexif()[EXIF_ORIENTATION_TAG]
            except (TypeError, AttributeError, KeyError):
                raise ValueError("Image file has no EXIF data.")

            print(filename + " orientation: (" + str(orientation) + ") "
                  + ORIENTATIONS[orientation][0])

            # Fix the orientation if not correct
            if orientation in [3, 6, 8]:
                degrees = ORIENTATIONS[orientation][1]
                print("rotating image " + str(degrees) + " degrees" )
                img = img.rotate(degrees, expand=True)

        xpix, ypix = img.size
        if args.debug and logfile:
            logfile.write("Image dimensions after rotation: "
                          + " (" + str(xpix) + "x" + str(ypix) + ")\n")

        # Resize the image
        if max_width > 0 and max_width < xpix:
            scale = float(max_width)/float(xpix)
            ydim = int(scale*ypix)
            if verbose and logfile:
                logfile.write("Resizing image to (" + str(max_width)
                              + "x" + str(ydim) +")\n")
            img = img.resize((max_width, ydim))

        # Add mark if requested
        dest = os.path.join(out_dir, os.path.basename(filename))
        img.save(dest)
        xdim, ydim = img.size
        if verbose and logfile:
            logfile.write("saved updated image to " + dest 
                          + " (" + str(xdim) + "x" + str(ydim) + ")\n")

        dest_ary.append(dest)
        
    return dest_ary


def upload_images(client, image_ary, verbose=False, logfile=None):
    data = {}
    for filename in image_ary:
        name = os.path.basename(filename)
        base, ext = os.path.splitext(name)
        data['name'] = name
        if ext.lower() == ".jpg":
            data['type'] = 'image/jpeg'
        elif ext.lower() == ".png":
            data['type'] = 'image/png'
        elif ext.lower() == ".gif":
            data['type'] = 'image/gif'
        else:
            print("Unknown image type for extension '" + ext + "'")
            if logfile:
                logfile.write("Unknown image type for extension '" + ext 
                        + "'\n")
                logfile.write("Skipping '" + filename + "'\n")
            continue

        if verbose:
            print("Uploading " + data['name'] + " (" + data['type'] + ")")

        if logfile:
            logfile.write("Uploading " + data['name'] + " (" 
                    + data['type'] + ")\n")
        
        with open(filename, 'rb') as img:
            data['bits'] = xmlrpc_client.Binary(img.read())

        response = client.call(media.UploadFile(data))
        # response == { 'id': 6, 'file': 'picture.jpg'
        #       'url': 'http://.../picture.jpg', 'type': 'image/jpeg' }
        if logfile:
            logfile.write("[id: " + response['id'] + "] ")
            logfile.write("mimetype: " + response['type'] + "\n")
            logfile.write("    url: " + response['url'] + "\n")


if __name__ == "__main__":
    # Open a log file
    logfile = open('sift.log', 'w')
    args = parse_arguments()
    if args.debug:
        print("Debug mode")
        print("Version " + SIFT_VERSION)

    config = parse_configuration(args.config, logfile)
    try:
        url = config.get('wordpress', 'url') + "/xmlrpc.php"
        user = config.get('wordpress', 'user') 
        passwd = config.get('wordpress', 'password')
        upload = config.getboolean('wordpress', 'upload', fallback=True)
    except (configparser.NoSectionError, configparser.NoOptionError):
        print("Not uploading. Missing or incomplete wordpress configuration.")
        upload = False
    else:
        if args.verbose:
            logfile.write("Verbose output\n")
            logfile.write("URL: " + url + '\n')
            logfile.write("User: " + user + '\n')

    if not upload:# == False:
        logfile.write("Not uploading images.\n")

    max_width = config.getint('image', 'max_width', fallback=0)
    out_dir = config.get('image', 'out_dir', fallback=".")
    rotate_images = config.getboolean('image', 'rotate', fallback=True) 

    out_dir = date.today().strftime(out_dir + "/%Y/%m")

    if args.verbose:
        logfile.write("Image width: " + str(max_width) + '\n')
        logfile.write("Image output directory: " + out_dir + '\n')
        logfile.write("Rotate image: " + str(rotate_images) + '\n')

    logfile.write("Images to be processed:\n")
    for f in args.files:
        logfile.write(" - " + f + "\n")

    if os.path.exists(out_dir) == False:
        logfile.write("Creating directory '" + out_dir + "' for images...\n")
        os.makedirs(out_dir)

    image_ary = process_images(args.files, max_width, out_dir, 
                                args.verbose, logfile)
    
    if upload:
        logfile.write("Connecting to wordpress site...\n")
        client = Client(url, user, passwd)

        if args.verbose:
            logfile.write("Uploading images...\n")

        upload_images(client, image_ary, args.verbose, logfile)

