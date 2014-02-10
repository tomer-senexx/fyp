import sys, shlex, os, getopt, uuid
from collections import OrderedDict

from os.path import normpath, isfile, isdir
from uuid import uuid4

from Extractors.DeceptionFeatureExtractor import DeceptionFeatureExtractor
from Extractors.HTMLScraper.items import HTMLScraperItem

from Utilities.PreProcessor import PreProcessor
from Utilities.ExtractorSelector import ExtractorSelector
from Utilities.Utils import readFromFile, listFilesInDirWithExtension, unpickleObject, unpickleHTMLScraperItem, listFilesInDir
from Utilities.listen import startFakeSMTPServer

from Parsers.HTMLParser_ import HTMLParser
from Parsers.TextParser import TextParser
from Utilities.Utils import downloadNLTKData

from Classifiers.GaussianSVM import GaussianSVM
from Classifiers.DecisionTree.DTree import DTree

class Detector(object):
        """docstring for Detector"""
        def __init__(self, *args):
                ###Defaults###

                self.categoryList = ['text', 'html']

                self.indicatorDictionary = {'text':['From:', 'Date:', 'Message-ID', 'In-Reply-To:'],\
                              'html':['http://', 'www', '.com', '.co.uk']}

                self.extractorList = [DeceptionFeatureExtractor(), DeceptionFeatureExtractor()]

                self.documentPaths = []
                self.extractorSelector = None

                self.matrixDict = OrderedDict()
                self.svms = None
                self.dTrees = None

                ###Dependency checks###
                downloadedP = downloadNLTKData('punkt')
                downloadedC = downloadNLTKData('cmudict')

                if not (downloadedP and downloadedC):
                        raise RuntimeError("\n\nCould not download the required nltk dependencies\n('punkt' or 'cmudict' dictionaries).\n")                

                ###User arguments###
                #Text must be delimited by semi-colon, in 
                #each file passed into the program
                options, extras = getopt.getopt(args, 'd:c:i:', ['documentlist=', 'categorylist=' 'indicatorlist='])
                
                for opt, arg in options:
                        path = normpath(arg)
                
                        if opt in ('-d', '--documentlist'):
                                documentListString = readFromFile(path)
                                self.documentPaths = self._getDocumentPaths(documentListString)

                        if opt in ('-c', '--categorylist'):
                                categoryListString = readFromFile(path)
                                self.categoryList = categoryListString.split(';')

                                print self.categoryList

                        if opt in ('-i', '--indicatorlist'):
                                indicatorListString = readFromFile(path)
                                #For separating indicator to groups - one for each category
                                indicatorGroupsList = indicatorListString.split(';')

                                #For separating indicator words/phrases
                                if len(categoryList) == len(indicatorGroupsList):
                                        self.indicatorDictionary = {categoryList[x] : indicatorGroupsList[x].split(',') \
                                                               for x in len(range(categoryList))}
                                else:
                                        raise RuntimeError("\nTotal number of categories, is not equal to the number of indicator groups.\n")     

                                print self.indicatorList
        
                self.extractorSelector = self._createExtractor(self.categoryList, self.indicatorDictionary, self.extractorList)

        def _getDocumentPaths(self, documentListString):
                documentPaths = []
                try:
                        documentFilePaths = documentListString.split(';')[:-1]
                        documentClassAndPaths = [pair.split(',') for pair in documentFilePaths]
                except AttributeError, IndexError:
                        sys.stderr.write("\nYour document list has been formatted incorrectly.\n"\
                                         +"Follow this format:\n[class integer],[directory path];\n"\
                                         +"----------------------------\nYou can enter in as many of these lines, as you'd like.\n")
                        sys.exit(1)
                for label, path in documentClassAndPaths:
                        if isdir(path):
                                documentPaths.extend([(int(label), os.path.join(path, document)) for document in listFilesInDir(path)])
                        elif isfile(path):
                                documentPaths.append((int(label), path))
                print "\n-------------------------\nPaths: ", documentFilePaths
                print "Documents: ", documentPaths if len(documentPaths) <= 20 else "More than 20 documents.", "\n-------------------------\n"

                return documentPaths

        def _createExtractor(self, categoryList, indicatorDictionary, extractorList):
                extractorSelector = ExtractorSelector(categoryList, extractorList)
                for category in categoryList:
                        extractorSelector.addExtractorIdentifierSet(category, indicatorDictionary[category])
                return extractorSelector

        def _selectExtractorAndProcess(self, processedText,\
                              documentClass, email_ID=None, emailPayload=None):
                featureSetList = []
                selectedExtractorTuple = self.extractorSelector.\
                                         determineBestExtractor(processedText.split())
                extractorCategory = selectedExtractorTuple[0]

                if extractorCategory is None:
                        documentName = "DEFAULT"
                        documentCategory = 'Text'
                else:
                        documentName = "%s - %s" % (extractorCategory.upper(), str(uuid4()))
                        documentCategory = extractorCategory

                if email_ID is None or emailPayload is None:
                        textString = processedText
                else:
                        documentName = email_ID
                        textString = emailPayload

                #Start parsing using the chosen extractor(s)
                extractorTuple = selectedExtractorTuple[1]
                for extractor in extractorTuple:
                        urlList = HTMLParser().getEmailURLs(textString) #Get all urls in email
                        if urlList != list(): #Get first url, if one exists in email (list is not empty)
                                extractor.scrapeWebsiteFromURL(urlList[0], documentName=None)
                        
                        featureSet = extractor.getFeatureSet(\
                                documentName+": "+documentCategory,\
                                extractor.__class__.__name__, textString, documentClass)

                        featureSetList.append(featureSet)
                return featureSetList

        def _extractFromDocument(self, filepath, documentClass, index=None):    
                documentString = readFromFile(filepath)
                print "---\n", documentString, "\n---"

                preProcessor = PreProcessor()
                processedDocument = preProcessor.removeEscapeChars(documentString)

                parser = TextParser(os.getcwd()+"/Parsers")
                email, isMultipart = parser.getEmailFromString(documentString)
                payload = email.get_payload()

                if index is not None:
                        print "Email no. "+str(index)+": "

                        print "---"
                        for header in email.keys():
                                print "\n"+header+": "+email.get(header)
                        print "\nPayload: "+payload
                        print "---"

                if index is not None:
                        processedPayload = preProcessor.removeEscapeChars(payload)
                        return self._selectExtractorAndProcess(processedDocument,\
                                                               documentClass,\
                                                               email.get("Message-Id"),\
                                                               processedPayload)
                else:
                        return self._selectExtractorAndProcess(processedDocument,\
                                                               documentClass)
                        
                    
        def extractFromEmails(self, documentClass):
                featureSetList = []
                filepathPrefix = "./Emails/"
        
                i=0
                for filepath in listFilesInDirWithExtension(filepathPrefix, ".eml"):
                        featureSetList.extend(self._extractFromDocument(filepathPrefix+filepath,\
                                                                        documentClass,\
                                                                        index=i))
                i+=1
                
                return featureSetList

        def extractAllDocuments(self):
                featureMatrix = []
                if self.documentPaths:  #List is not empty
                        [featureMatrix.extend(self._extractFromDocument(filepath=document, documentClass=label)) for label, document in self.documentPaths]
                else:                   #No documents found
                        sys.stderr.write("Could not find any documents.\nPlease try again, or enter another file, or directory path.\n")
                        return
                
                for featureSet in featureMatrix:
                        category = featureSet.documentCategory

                        if category not in self.matrixDict:
                                self.matrixDict[category] = [[],[]]

                        self.matrixDict[category][0].append(featureSet.getClass())
                        self.matrixDict[category][1].append(featureSet.getVector())
                
                print "---"
                for k in self.matrixDict:
                        print k
                        print self.matrixDict[k] 
                        print "---"

        def trainClassifiers(self):
                mkeys = self.matrixDict.keys()
                mdict = self.matrixDict
                
                self.svms = {category: GaussianSVM(mdict[category][0], mdict[category][1]) for category in mkeys}
                self.dTrees = {category: DTree(mdict[category][0], mdict[category][1], documentGroupName=category) for category in mkeys}


        def classifyDocument(self, classifierName, label, dictVector):
                return(self.svms[classifierName].classifyDocument(label, dictVector),
                       self.dTrees[classifierName].classifyDocument(dictVector))

        def startMainMenu(self):
                while True:
                        option = -1
                        documentClass = -1
                        documentPath = None
                        print "\n-------------------------\nSET Deception Detector:\n-------------------------\n"
                        print "Press a number associated with the following options."
                        print "1) Classify document\n2) Train program with documents\n3) Exit"
                        
                        while not isinstance(option, (int))\
                                   or (option < 1 or option > 3):
                                option = int(raw_input("Please choose a valid option.\n"))
                                
                        if option is 1:

                                while not isinstance(documentClass, (int))\
                                       or documentClass < 1:
                                        documentClass = int(raw_input("Please enter a class integer, equal to or greater than 1.\n"))
                                documentPath = normpath(raw_input("Now enter the filepath of the document to classify.\n"))
                                
                                while not isfile(documentPath):
                                        documentPath = normpath(raw_input("Please enter a valid filepath.\n"))
                                #Must change default classifier group name - imitation, obfuscation etc.
                                self.classifyDocument('ImitationFeatureExtractor', documentClass,\
                                	self._extractFromDocument(documentPath, documentClass))
                                
                        elif option is 2:

                                documentPaths = None
                                path = None
                                if len(sys.argv) is 1: #No arguments passed
                                        message = "\nNow enter the directory path or filepath of the document(s) "\
                                                  +"to classify, using the following format:\n[class integer],[directory path];\n"\
                                         +"----------------------------\nYou can enter in as many of these lines, as you'd like.\n"
                                        
                                        while not isinstance(path, basestring) or not (isfile(path) or isdir(path)):
                                                documentPaths = normpath(raw_input(message))
                                                try:
                                                        path = documentPaths.split(',')[1].split(';')[0]
                                                except IndexError:
                                                        path = None
                                        self.documentPaths = self._getDocumentPaths(documentPaths) #If entering in the document list, on the fly...
                                detector.extractAllDocuments()		
                                detector.trainClassifiers()
                                
                        elif option is 3:
                                sys.exit(0)
                
if __name__ == "__main__":
        detector = Detector(*sys.argv[1:])
        detector.startMainMenu()

        
