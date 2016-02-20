sift
====

Simple Image Fix-it Tool

sift is a python script used to shrinkticate images to a reasonable size and
upload them to a wordpress site.

Current status (August 18, 2014):
- Works (mostly).

Todo:
- Add support for creating image directory
- Add support for creating a configuration file if it doesn't exist

Requirements:
- Python 3.3 (or greater)
- pillow
- wordpress-xmlrpc

Theory of operation:
- Select the directory containing the images to install
- The script will reduce images to a defined width (if the images width is
  greater) using Pillow
- Upload the images to the wordpress site using wordpress-xmlrpc

Usage Overview:

    usage: sift.py [-h] [-v] [-V] [-D] [-C [CONFIG]] filename [filename ...]
    
    Formats and uploads images to a wordpress site
    
    positional arguments:
      filename              image files to be processed and uploaded
    
    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         print/log verbose output
      -V, --version         show program's version number and exit
      -D, --debug           print debug output
      -C [CONFIG], --config [CONFIG]
                            set config file
    
    BrokenLogo internet Production (BLiP) Kevin Somervill copyright 2016


I wrote this for my wife. She abhors commandline tools so I created a desktop
launcher that she can drag her images onto.

For xfce, this is what I've put on the desktop (named SIFT.desktop)

    [Desktop Entry]
    Version=1.0
    Type=Application
    Name=SIFT
    Comment= Simple Image Fix-it Tool
    Exec=/path/to/sift/sift.py -v %F
    Icon=
    Path=/path/to/working/directory
    Terminal=true
    StartupNotify=false

