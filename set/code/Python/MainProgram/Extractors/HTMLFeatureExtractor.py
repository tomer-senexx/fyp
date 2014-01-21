import sys, importlib

from twisted.internet import reactor
from twisted.internet.error import ConnectionRefusedError

from scrapy import log, signals
from scrapy.crawler import Crawler
from scrapy.settings import CrawlerSettings

sys.path.append("..")

from Utilities.Utils import downloadNLTKData
from BaseExtractor import BaseExtractor
from HTMLScraper.spiders.SETSpider import SETSpider
from Extractors.HTMLScraper.items import HTMLScraperItem
from Parsers.HTMLParser_ import HTMLParser

#Use scrapy code here - items, spiders etc.
#Source - Stack Overflow: http://stackoverflow.com/questions/14777910/scrapy-crawl-from-script-always-blocks-script-execution-after-scraping/19060485
class HTMLFeatureExtractor(BaseExtractor):

        def __init__(self, startScrapyScan=False, domainList=["localhost"],\
                     urlList=["http://127.0.0.1/"]):
                BaseExtractor.__init__(self)
                self.domainList = domainList
                self.urlList = urlList
                self.hparser = HTMLParser()
                
                if startScrapyScan is True:
                        self._createCrawler(self._stopReactor, signals.spider_closed)

			
	def _stopReactor(self):
		reactor.stop()
        

        def _createCrawler(self, stopReactorFunction, signalFunction):
		spider = SETSpider(self.domainList, self.urlList)
		settings_module = importlib.import_module('Extractors.HTMLScraper.settings')
		settings = CrawlerSettings(settings_module)
		crawler = Crawler(settings)
		crawler.configure()
		crawler.signals.connect(stopReactorFunction, signal=signalFunction)
		crawler.crawl(spider)
		crawler.start()
		log.start()
		reactor.run() # the script will block here until the spider_closed signal was sent

   


    #Define private methods as utilities for actual text parsing, instance methods, which will produce features, via inherited 'getFeatureSet' function

    #source: StackOverflow - http://stackoverflow.com/questions/106179/regular-expression-to-match-hostname-or-ip-address?lq=1 
        def findIPAddressesInEmail(self, textString):
		countExp = re.compile(r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
		return re.findall(countExp, textString)


