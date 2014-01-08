import os, sys, re
sys.path.append("..")

from Extractors.HTMLScraper.items import HTMLScraperItem
from Utilities.Utils import unpickleObject

class HTMLParser:
        parsedText = {}
        
        def __init__(self):
        	pass

        #Source: StackOverflow - http://stackoverflow.com/questions/4436008/how-to-get-html-tags
        def getTagsFromString(self, textString):
        	return re.findall('<.*?>', textString)

        def getTagsFromPickledObject(self, filePath):
        	item = unpickleObject(filePath)
		print filePath
		print item

		if isinstance(item, dict):
			unicodeBody = item['response']['body']
			responseBody = ''.join([x.encode('utf8') for x in unicodeBody])
			responseAll = item['response']['tags']
			return [x.encode('utf8') for x in responseAll]
	
		if isinstance(item, basestring):
			return getTagsFromString(item)
                
