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
import mimetypes
import os
import subprocess
from PIL import Image

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts

def parse_configuration(logfile,DEBUG=False):
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.sift.cfg'))
    # We should do something if the config file is not found

    logfile.write("Images to be processed:\n")
    for f in args.files:
        logfile.write(" - " + f)
    logfile.write('\n')
    return config

def parse_arguments():
    parser = argparse.ArgumentParser(
        description = "Formats and uploads images to a wordpress site",
        epilog = "BrokenLogo internet Production (BLiP)\n" 
            + "Kevin Somervill copyright 2014"
        )
    parser.add_argument("files", metavar="filename", type=str, nargs="+",
            help="image files to be processed and uploaded")

    parser.add_argument("-v", "--verbose", action='store_true',
            help="print/log verbose output")
    args = parser.parse_args()
    return args

def process_images(image_ary, max_width, out_dir, logfile=None):
    dest_ary = []
    #autorot_cmd = "jhead --autorot"
    #resize_cmd = "convert -scale " + str(max_width) + "\\>"

    for filename in image_ary:
        img = Image.open(filename)
        xpix, ypix = img.size
        print("processing image: " + filename
                + " (" + str(xpix) + "x" + str(ypix) + ")" )

        dest = os.path.join(out_dir, os.path.basename(filename))
        if max_width > 0 and max_width < xpix:
            scale = float(max_width)/float(xpix)
            ydim  = int(scale*ypix)
            print("Resizing image to (" +str(max_width) + "x" + str(ydim) +")")
            img = img.resize((max_width, ydim))
        
        img.save(dest)
        xdim, ydim = img.size
        if logfile:
            logfile.write("saved updated image to " + dest 
                    + " (" + str(xdim) + "x" + str(ydim) + ")\n")

        dest_ary.append(dest)
        
    return dest_ary

def upload_images(client, image_ary, logfile=None):
    data = {}
    for filename in image_ary:
        data['name'] = os.path.basename(filename)
        base, ext = os.path.splitext(data['name'])
        if ext.lower() == ".jpg":
            data['type'] = "image/jpg"
        elif ext.lower() == ".png":
            data['type'] = "image/png"
        elif ext.lower() == ".gif":
            data['type'] = "image/gif"
        else:
            print("Unknown image type for extension '" + ext + "'")
            continue

        if logfile:
            logfile.write("Uploading " + data['name'] + " (" 
                    + data['type'] + ")\n")
        
        with open(filename, 'rb') as img:
            data['bits'] = xmlrpc_client.Binary(img.read())


        response = client.call(media.UploadFile(data))
        # response == { 'id': 6, 'file': 'picture.jpg'
        #       'url': 'http://.../picture.jpg', 'type': 'image/jpg' }
        if logfile:
            logfile.write("id: " + response['id'] + "\n")
            logfile.write("url: " + response['url'] + "\n")

if __name__ == "__main__":
    # Open a log file
    logfile = open('sift.log', 'w')
    args = parse_arguments()
    
    config = parse_configuration(logfile)
    try:
        url = config.get('wordpress', 'url') + "/xmlrpc.php"
        user = config.get('wordpress', 'user') 
        passwd = config.get('wordpress', 'password')
        upload = config.getboolean('wordpress', 'upload', fallback=True)
    except (configparser.NoSectionError, configparser.NoOptionError):
        print("Not uploading. Missing or incomplete wordpress configuration.")
        upload = False
    else:
        logfile.write("URL: " + url + '\n')
        logfile.write("User: " + user + '\n')

    if upload == False:
        logfile.write("Not uploading images.\n")

    max_width = config.getint('image', 'max_width', fallback=0)
    out_dir = config.get('image', 'out_dir', fallback=".")
        
    logfile.write("Image width: " + str(max_width) + '\n')
    logfile.write("Image output directory: " + out_dir + '\n')

    if os.path.isdir(out_dir) == False:
        print("Creating directory for images...")

    image_ary = process_images(args.files, max_width, out_dir, logfile)

    
    if upload:
        print ("Connecting to wordpress site...")
        client = Client(url, user, passwd)

        print("Uploading images...")
        upload_images(client, image_ary, logfile)

