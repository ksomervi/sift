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
import os
import subprocess
from PIL import Image

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts

def parse_configuration(logfile,DEBUG=False):
    logfile.write("parsing configuration file\n")
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.sift.cfg'))
    # We should do something if the config file is not found

    logfile.write("configuration file parsed\n")
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

def process_images(image_ary, max_width, out_dir, verbose=None):
    dest_ary = []
    for img in image_ary:
        if verbose:
            print("processing image: " + img)

        dest = os.path.basename(img)

        im = Image.open(img)
        xpix, ypix = im.size
        print("filename: " + dest 
                + " (" + str(xpix) + "x" + str(ypix) + ")" )
        if max_width < xpix:
            scale = float(max_width)/float(xpix)
            ydim  = int(scale*ypix)
            print("Resizing image to (" +str(max_width) + "x" + str(ydim) +")")
            im = im.resize((max_width, ydim))
        
        im.save(dest)
        dest_ary.append(dest)

def upload_images(client, image_ary, logfile=None):
    for image in image_ary:
        data = {'name' : dest, 'type' : 'image/jpg' }
        #data['type'] = mimetypes.read_mime_types(filename)
        #or mimetypes.guess_type(filename)[0]
        
        with open(dest, 'rb') as m:
            data['bits'] = xmlrpc_client.Binary(m.read())
        print ("Uploading the image")
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
    
    logfile.write("Images to be processed:\n")
    for f in args.files:
        logfile.write(" - " + f)
    logfile.write('\n')
    
    config = parse_configuration(logfile)
    url = config.get('wordpress', 'url') + "/xmlrpc.php"
    user = config.get('wordpress', 'user') 
    passwd = config.get('wordpress', 'password')
    max_width = config.getint('image', 'max_width')
    out_dir = config.get('image', 'out_dir')
    upload = config.getboolean('wordpress', 'upload')

    if os.path.isdir(out_dir) == False:
        print("Creating directory for images...")

    logfile.write("URL: " + url + '\n')
    logfile.write("User: " + user + '\n')
    logfile.write("Image width: " + str(max_width) + '\n')

    autorot_cmd = "jhead --autorot"
    resize_cmd = "convert -scale " + str(max_width) + "\\>"

    image_ary = process_images(args.files, max_width, out_dir)
    
    if upload:
        print ("Connecting to wordpress site...")
        client = Client(url, user, passwd)

        print("Uploading images")
        #upload_images(client, image_ary)

