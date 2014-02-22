from io import StringIO
from lxml.html import HtmlElement
import lxml.html as lh
sys.path.append("..")

from Parsers.HTMLParser_ import HTMLParser
from DeceptionFeatureExtractor import DeceptionFeatureExtractor

class DeceptionFeatureExtractor(BaseExtractor):
        def __init__(self, documentName="currentWebsite"):
                DeceptionFeatureExtractor.__init__(self, documentName)

        def numOfTagsInString(self, textString):
                return len(self.htmlParser.getTagsFromString(textString))

        def _getHREFAndURLTextPairsInString(self, textString):
                tree = lh.fromstring(textString)
                if isinstance(tree, HtmlElement):
                    return [(tree.get("href"), tree.text)]
                urls = tree.xpath("//a/@href")
                textStrings = tree.xpath("//a/@href/text()")
                return zip(urls, textStrings)

        def proportionOfNonMatchingHRefPairs(self, textString):
                pairs = self._getHREFAndURLTextPairsInString(textString)
                if len(pairs) == 1 and (pairs[0][0] == None\
                                        and pairs[0][1] == None): #List/tuple is empty
                    return 0
                return float(sum([0 if pair[0] == pair[1] else 1\
                                  for pair in pairs]))/len(pairs)

        
                
                
