#!/usr/bin/python
'''
Tool to find the debian package for filename X
'''

import sys
from io import StringIO

import requests
from lxml import etree

URL = 'https://packages.debian.org/search?searchon=contents&keywords={}&mode=path&suite=stable&arch=any'

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Missing file argument")

    filename = sys.argv[1]

    r = requests.get(URL.format(filename))

    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(r.content.decode('utf-8')), parser)

    root = tree.getroot()

    pkgs = [a for a in root.xpath('//td/a//text()')]
    # td + span
    files = [td.text + td.getchildren()[0].text for td in root.xpath("//td[@class='file']")]

    for entry in zip(files, pkgs):
        print("{} - {}".format(entry[0], entry[1]))
