#!/usr/bin/env python
from lxml import etree
from lxml.html import parse, tostring, fromstring
import urllib.request
import sys

# Downloads a webalbum of picasa in the current directory if the rss url is provided.
# Note that https doesn't work atm


if len(sys.argv) == 2:
    url = sys.argv[1]
    url = url + "&imgdl=1"

    parser = etree.XMLParser(ns_clean=True, recover=True)
    try:
        xml = etree.parse(url,parser)
        items = xml.findall('//item')

        # iterate over items
        for item in items:
            title = item.xpath('title')[0].text
            photo =  item.xpath("m:group/m:content/@url",namespaces={"m": "http://search.yahoo.com/mrss/"})
            photo = photo[0]
            f = urllib.request.urlopen(photo)
            locale_file = open(title,"wb")
            locale_file.write(f.read())
            locale_file.close()
    except IOError:
        print ("Couldn't parse source {0} ".format(url))
else:
    print ("Provide more url, note that https doesn't work atm")
