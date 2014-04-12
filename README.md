sift
====

Simple Image Fix-it Tool

sift is a python script used to shrinkticate images to a reasonable size and
upload them to a wordpress site.

Currently, works (barely).

Todo:
- Add support for creating image directory
- Add support for creating a configuration file if it doesn't exist

Requirements:
- Python 3.3 (or greater)
- pillow
- wordpress-xmlrpc

Theory of operation:
- Select the directory containing the images to install.
- The script will reduce images to a defined width (if the images width is
  greater) using Pillow
- Upload the images to the wordpress site using wordpress-xmlrpc

