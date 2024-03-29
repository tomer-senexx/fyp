import sys, os
sys.path.append("..")

from Extractors.HTMLScraper.WebsiteScraper import WebsiteScraper
from Parsers.HTMLParser_ import HTMLParser
from TextFeatureExtractor import TextFeatureExtractor as tfe

class GeneralFeatureExtractor(tfe): #Text and HTML (via Scrapy)
        def __init__(self, documentName="currentWebsite", urlString=None,\
                     indicators=('http://', 'www', '.com', '.co.uk')):
                tfe.__init__(self, documentName, indicators)
                
                self.website = None
                self.scraper = WebsiteScraper(documentName=self.documentName, startScrapyScan=False)
                self.foundWebsite = False
                self.numOfURLs = None
                self.htmlResponse = None
                
                if urlString is not None:
                        self.scrapeWebsiteFromURL(urlString)
                        

        def scrapeWebsiteFromURL(self, urlString, documentName=None):
                domainList, urlList = self.htmlParser.getURLsWithDomains(urlString)

                if documentName is not None:
                        self.documentName = documentName           
                self.website = self.scraper.startCrawler(domainList,\
                        urlList, self.documentName)
                
                if self.website != None: #If website was found...
                        self.foundWebsite = True
                        self.numOfURLs = float(len(self.htmlParser.getWebsiteURLs(self.website)))
                        self.htmlResponse = self.htmlParser.getResponseAttribute(self.website, 'all')
                

        def lengthOfWebsiteBodyText(self, textString):
                if self.foundWebsite:
                        bodyLength = len(self.htmlParser.getResponseAttribute(self.website, 'body'))
                        responseLength = len(self.htmlResponse)
                        return float(bodyLength)/responseLength
                else:
                        return 0

        def numOfURLsInWebsite(self, textString):
                if self.foundWebsite:
                        maxURLCount = 30 #Unsure of how many URLs exist in the document, so not perfect
                        return self.numOfURLs/maxURLCount
                else:
                        return 0

        def proportionOfUniqueTagsInWebsite(self, textString):
                if self.foundWebsite:
                        maxTagCount = 100 #Unsure of how many HTML tags exist, so not perfect
                        return float(len(self.htmlParser.getTagCounter(self.website).keys()))/maxTagCount       
                else:
                        return 0

        def tagDiversity(self, textString):
                if self.foundWebsite:
                        numOfTags = len(self.htmlParser.getTagsFromItem(self.website))
                        return float(len(self.htmlParser.getTagCounter(self.website).keys()))/numOfTags       
                else:
                        return 0

        def containsFormTag(self, textString):
                if self.foundWebsite:
                        if len(self.htmlParser.getFormTags(self.htmlResponse)) > 0:
                                return 1
                return 0

        def containsJavascript(self, textString):
                if self.foundWebsite:
                        if (('function' and '(){') or\
                            '<script>' or '</script>') in self.htmlParser.getTagsFromItem(self.website):
                                return 1
                return 0

        def getNumberOfDomains(self, textString):
                if self.foundWebsite:
                        if self.numOfURLs == 0:
                                return 0
                        else:
                                return float(self.htmlParser.getNumberOfDomains(self.htmlResponse))/self.numOfURLs
                return 0

        def getNumberOfSubDomains(self, textString):
                if self.foundWebsite:
                        if self.numOfURLs == 0:
                                return 0
                        else:
                                return float(self.htmlParser.getNumberOfSubDomains(self.htmlResponse))/self.numOfURLs
                return 0
                
                        
