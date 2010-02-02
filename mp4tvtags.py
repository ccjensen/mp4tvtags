#!/usr/bin/env python
#encoding:utf-8
#author:ccjensen/Chris
#project:mp4tvtagger
#repository:http://github.com/ccjensen/mp4tvtags/
#license:Creative Commons GNU GPL v2
# (http://creativecommons.org/licenses/GPL/2.0/)
 
"""
mp4tvtags.py
Automatic TV episode tagger.
Uses data from www.thetvdb.com via tvdb_api, 

thanks goes to:
the MP4v2 team (http://code.google.com/p/mp4v2/) for their excellent mp4 container editing library
the Subler team (http://code.google.com/p/subler/), their project was used as a template for MP4Tagger (source code soon to be released)
dbr/Ben - http://github.com/dbr - for python help, tvdb_api and tvnamer.py
"""
 
__author__ = "ccjensen/Chris"
__version__ = "0.4"

import sys
# This script does not work well with the current default python path SabNZBD sets
# Set it to the same python path as OS X defaults
osx_python_path = [
	sys.path[0],
	"/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python26.zip",
	"/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6",
	"/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/plat-darwin",
	"/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/plat-mac",
	"/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/plat-mac/lib-scriptpackages",
	"/System/Library/Frameworks/Python.framework/Versions/2.6/Extras/lib/python",
	"/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/lib-tk",
	"/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/lib-old",
	"/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/lib-dynload",
	"/Library/Python/2.6/site-packages",
	"/System/Library/Frameworks/Python.framework/Versions/2.6/Extras/lib/python/PyObjC",
	"/System/Library/Frameworks/Python.framework/Versions/2.6/Extras/lib/python/wx-2.8-mac-unicode"
]

sys.path = osx_python_path

#import sys
import os
import re
import glob
import unicodedata

from optparse import OptionParser
 
from tvdb_api import Tvdb
#from tvdb_ui import BaseUI, ConsoleUI
from tvdb_exceptions import (tvdb_error, tvdb_userabort, tvdb_shownotfound,
    tvdb_seasonnotfound, tvdb_episodenotfound, tvdb_attributenotfound)

class Program:
    """docstring for Program"""
    def __init__(self, opts, dirPath):
        if opts.verbose:
            print "Connecting to the TVDB... "
        #end if verbose
        self.tvdb = Tvdb(debug = opts.debug, interactive = opts.interactive, banners = True)
        self.mp4tagger = os.path.dirname(__file__) + "/MP4Tagger"
        self.dirPath = dirPath
    #end def __init__
#end class Program      


class Series:
    """docstring for Series"""
    artworkFileName = ""
    
    def __init__(self, verbose, program, series, seasonNumber):         
        #get show specific meta data
        if verbose:
            print "Retrieving Show Information... "
        #end if verbose
        self.seriesName = getShowSpecificInfo(verbose, program.tvdb, series, 'seriesname')
        
        self.actorsUnsplit = getShowSpecificInfo(verbose, program.tvdb, self.seriesName, 'actors')
        self.actors = self.actorsUnsplit.split('|')
        
        #thetvdb is using wrong name for the rating
        self.rating = getShowSpecificInfo(verbose, program.tvdb, self.seriesName, 'contentrating')
        #self.firstaired  = getShowSpecificInfo(verbose, program.tvdb, self.seriesName, 'firstaired') #currently not used for anything
        
        self.genresUnsplit  = getShowSpecificInfo(verbose, program.tvdb, self.seriesName, 'genre')
        self.genres = self.genresUnsplit.split('|')
        
        self.network  = getShowSpecificInfo(verbose, program.tvdb, self.seriesName, 'network')
        #seriesOverview  = getShowSpecificInfo(verbose, program.tvdb, self.seriesName, 'overview') #currently not used for anything
        
        self.seasonNumber = int(seasonNumber)
    #end def __init__
#end class Series


class Episode:
    """docstring for Episode""" 
    def __init__(self, verbose, program, series, episodeNumbers, fileName):
        self.fileName = fileName
        self.seasonNumberEpisode = series.seasonNumber
        self.episodeNumbers = episodeNumbers
        self.singleEpisode = len(episodeNumbers) == 1
        
        if(self.singleEpisode):
            #get other episode specific meta data
            self.episodeName = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumbers[0], 'episodename').replace(":", ";")
            
            self.firstAired = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumbers[0], 'firstaired') + "T09:00:00Z"
            self.productionCode = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumbers[0], 'productioncode')
            
            self.overview = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumbers[0], 'overview')
            self.longOverview = self.overview
            
            directorsUnsplit = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumbers[0], 'director')
            self.directors = directorsUnsplit.split('|')
        
            writersUnsplit = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumbers[0], 'writer')
            self.writers = writersUnsplit.split('|')
        else:
            #get information for only first episode in multiepisode listing
            self.firstAired = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumbers[0], 'firstaired') + "T09:00:00Z"
            self.productionCode = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumbers[0], 'productioncode')
            self.overview = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumbers[0], 'overview')
            
            self.episodeName = ""
            self.directors = []
            self.writers = []
            self.longOverview = ""
            
            for i in range(0, len(self.episodeNumbers)):
                episodeNumber = self.episodeNumbers[i]
                if len(self.episodeName) > 0:
                    epName = getEpisodeSpecificInfo(verbose, program, series, episodeNumber, 'episodename').replace(":", ";")
                    self.episodeName = "%s : %s" % (self.episodeName, epName)
                else:
                    self.episodeName = getEpisodeSpecificInfo(verbose, program, series, episodeNumber, 'episodename').replace(":", ";")
                #end if len episodeName                
        
                directorsUnsplit = getEpisodeSpecificInfo(verbose, program, series, episodeNumber, 'director')
                directorsSplit = directorsUnsplit.split('|')
                for director in directorsSplit:
                    if director not in self.directors:
                        self.directors.append(director)
                    #end if director not in
                #end for director
        
                writersUnsplit = getEpisodeSpecificInfo(verbose, program, series, episodeNumber, 'writer')
                writersSplit = writersUnsplit.split('|')
                for writer in writersSplit:
                    if writer not in self.writers:
                        self.writers.append(writer)
                    #end if director not in
                #end for director
                if len(self.longOverview) > 0:
                    self.longOverview = "%s\n\nPart %d: %s" % (self.longOverview, i+1, getEpisodeSpecificInfo(verbose, program, series, episodeNumber, 'overview'))
                else:
                    self.longOverview = "Part %d: %s" % (i+1, self.overview)
                #end if len longOverview
            #end for episodeNumber
        #end if self.singleEpisode
    #end def __init__
#end class Episode


def openurl(urls):
    for url in urls:
        if len(url) > 0:
            os.popen("open \"%s\"" % url)
        #end if len
    #end for url
    return
#end openurl


def correctFileName(opts, program, series, episode):
    """docstring for correctFilename"""
    (fileNameWithoutExtension, fileExtension) = os.path.splitext(episode.fileName)
    
    seriesName = series.seriesName.replace('/', "-")
    seriesName = seriesName.encode("utf-8")
    episodeName = episode.episodeName.replace('/', "-")
    episodeName = episodeName.encode("utf-8")
    
    #expand episode numbers
    if episode.singleEpisode:
        suggestedNewFileName = "%s - S%02dE%02d - %s%s" % (seriesName, series.seasonNumber, episode.episodeNumbers[0], episodeName, fileExtension)
    else:
        episodeNumbers = ""
        for episodeNumber in episode.episodeNumbers:
            episodeNumbers = "%sE%02d" % (episodeNumbers, episodeNumber)
        #end for episodeNumber
        suggestedNewFileName = "%s - S%02d%s - %s%s" % (seriesName, series.seasonNumber, episodeNumbers, episodeName, fileExtension)
    #end if episode singleEpisode
    
    #Correct file name if incorrect
    if episode.fileName != suggestedNewFileName:
        renameCmd = "mv -n \"%s/%s\" \"%s/%s\"" % (program.dirPath, episode.fileName, program.dirPath, suggestedNewFileName)
        if opts.debug:
            print "!!Rename command: %s" % renameCmd
        #end if debug
        os.popen(renameCmd)
        if opts.verbose:
            print "  Filename corrected from \"%s\" to \"%s\"" % (episode.fileName, suggestedNewFileName)
        #end if verbose
        episode.fileName = suggestedNewFileName
    else:
        if opts.verbose:
            print "  Filename \"%s\" already correct" % episode.fileName
        #end if verbose
    #end if fileName
#end correctFileName


def tagFile(opts, program, series, episode):
    """docstring for tagFile"""
    if not opts.forcetagging:
        #check if file has already been tagged
        alreadyTaggedCmd = "\"%s\" -i \"%s/%s\" -t" % (program.mp4tagger, program.dirPath, episode.fileName)
        #cmd = "\"" + program.mp4tagger + "\" -i \"" + program.dirPath + "/" + episode.fileName.encode("utf-8") + "\"" + " -t"
        if opts.debug:
            print "!!AlreadyTagged command: %s" % alreadyTaggedCmd
        #end if debug
        existingTagsUnsplit = os.popen(alreadyTaggedCmd).read()
        existingTags = existingTagsUnsplit.split('\r')
        for line in existingTags:
            if line.count("tagged by mp4tvtags"):
                if opts.verbose:
                    print "  %s already tagged" % episode.fileName
                #end if verbose
                return
            #end if line.count
        #end for line
    #end if opts.forcetagging
    #setup tags for the MP4Tagger function
    if series.artworkFileName != "":
        addArtwork = " --artwork \"%s/%s\"" % (program.dirPath, series.artworkFileName) #the file we downloaded earlier
    else:
        addArtwork = ""
    #end if series.artworkFileName != ""
    if series.rating != "":
        addRating = " --rating \"%s\"" % series.rating
    else:
        addRating = ""
    #end if series.rating != "":
    
    addMediaKind = " --media_kind \"TV Show\"" #set type to TV Show
    addArtist = " --artist \"%s\"" % series.seriesName
    addName =  " --name \"%s\"" % episode.episodeName
    addAlbum = " --album \"%s - Season %s\"" % (series.seriesName, series.seasonNumber)
    addGenre = " --genre \"%s\"" % series.genres[1] #cause first one is an empty string, and genre can only have one entry
    addAlbumArtist = " --album_artist \"%s\"" % series.seriesName
    addDescription = " --description \"%s\"" % episode.overview
    addLongDescription = " --long_description \"%s\"" % episode.longOverview
    addTVNetwork = " --tv_network \"%s\"" % series.network
    addTVShowName = " --tv_show \"%s\"" % series.seriesName
    addTVEpisode = " --tv_episode_id \"%s\"" % episode.productionCode
    addTVSeasonNum = " --tv_season \"%i\"" % series.seasonNumber
    
    #kept for clarity as it same decision is made
    if episode.singleEpisode:
        addTVEpisodeNum = " --tv_episode_n \"%i\"" % episode.episodeNumbers[0]
        addTracknum = " --track_n \"%i\"" % episode.episodeNumbers[0]
    else:
        addTVEpisodeNum = " --tv_episode_n \"%i\"" % episode.episodeNumbers[0]
        addTracknum = " --track_n \"%i\"" % episode.episodeNumbers[0]    
    #end if episode.singleEpisode
    
    addDisk = " --disk_n \"%i\"" % series.seasonNumber
    addReleaseDate = " --release_date \"%s\"" % episode.firstAired
    #addSortOrderName = " --sortOrder name \"%s\"" % episode.episodeName
    #addSortOrderArtist = " --sortOrder artist \"%s\"" % series.seriesName
    #addSortOrderAlbumArtist = " --sortOrder albumartist \"%s\"" % series.seriesName
    #addSortOrderAlbum = " --sortOrder album \"%s - Season %s\"" % (series.seriesName, series.seasonNumber)
    #addSortOrderShow = " --sortOrder show \"%s\"" % series.seriesName
    addComment = " --comment \"tagged by mp4tvtags\""
    
    addCast = ""
    addDirectors = ""
    addScreenwriters = ""
    
    if len(series.actors) > 0:
        actors = createCommaSeperatedStringFromArray(series.actors)
        addCast = " --cast \"%s\"" % actors
    #end if len 
    if len(episode.directors) > 0:
        directors = createCommaSeperatedStringFromArray(episode.directors)
        addDirectors = " --director \"%s\"" % directors
    #end if len
    if len(episode.writers) > 0:
        screenwriters = createCommaSeperatedStringFromArray(episode.writers)
        addScreenwriters = " --screenwriters \"%s\"" % screenwriters
    #end if len
    
    #Create the command line string
    tagCmd = "\"%s\" -i \"%s/%s\" %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s" % \
    (program.mp4tagger, program.dirPath, episode.fileName, addArtwork.encode("utf-8"), addMediaKind.encode("utf-8"), \
    addArtist.encode("utf-8"), addName.encode("utf-8"), addAlbum.encode("utf-8"), addGenre.encode("utf-8"), \
    addAlbumArtist.encode("utf-8"), addDescription.encode("utf-8"), addTVNetwork.encode("utf-8"), addTVShowName.encode("utf-8"), \
    addTVEpisode.encode("utf-8"), addTVSeasonNum.encode("utf-8"), addTVEpisodeNum.encode("utf-8"), addDisk.encode("utf-8"), \
    addTracknum.encode("utf-8"), addRating.encode("utf-8"), addReleaseDate.encode("utf-8"), addComment.encode("utf-8"), \
    addLongDescription.encode("utf-8"), addCast.encode("utf-8"), addDirectors.encode("utf-8"), addScreenwriters.encode("utf-8"))
    
    #run MP4Tagger using the arguments we have created
    if opts.debug:
        print "!!Tag command: %s" % tagCmd
    #end if debug
    
    result = os.popen(tagCmd).read()
    if result.count("Program aborted") or result.count("Error"):
        print "** ERROR: %s" % result
        sys.exit(1)
    
    lockCmd = "chflags uchg \"" + program.dirPath + "/" + episode.fileName + "\""
    
    os.popen(lockCmd)
    if opts.verbose:
        print "  Tagged and locked: " + episode.fileName
    #end if verbose
    #end if overwrite
#end tagFile
    


def artwork(verbose, interactive, program, series):
    try:
        potentialArtworkFileName = "%s - S%02d" % (series.seriesName, series.seasonNumber)
        for fileName in glob.glob("*.jpg"):
            (fileBaseName, fileExtension) = os.path.splitext(fileName)
            if fileBaseName == potentialArtworkFileName:
                if verbose:
                    print "Using Previously Downloaded Artwork: " + fileName
                #end if verbose
                series.artworkFileName = fileName
                return
            #end if fileBaseName
        #end for fileName
    
        tvdb = program.tvdb
    
        if 'season' in tvdb[series.seriesName]['_banners']:
            if 'season' in tvdb[series.seriesName]['_banners']['season']:
                artworks = []
                for banner_id, banner_info in tvdb[series.seriesName]['_banners']['season']['season'].items():
                    if banner_info['season'] == str(series.seasonNumber):
                        artworks.append(banner_info['_bannerpath'])
    
        #check if we didn't find any artwork, if so do not continue
        if len(artworks) == 0:
            raise tvdb_attributenotfound
        #end if len(artworks) == 0
    
        if interactive:
            artworkCounter = 0
            print "\nList of available artwork"
            for artwork in artworks:
                print "%s. %s" % (artworkCounter, artwork)
                artworkCounter += 1
            #end for artwork
    
            #allow user to preview images
            print "Example of listing: 0 2 4"
            artworkPreviewRequestNumbers = raw_input("List Images to Preview: ")
            artworkPreviewRequests = artworkPreviewRequestNumbers.split()
            
            artworkPreviewUrls = []
            for artworkPreviewRequest in artworkPreviewRequests:
                artworkPreviewUrls.append(artworks[int(artworkPreviewRequest)])
            #end for artworkPreviewRequest
            openurl(artworkPreviewUrls)
    
            #ask user what artwork he wants to use
            artworkChoice = int(raw_input("Artwork to use: "))
        else:
            artworkChoice = 0
        #end if interactive
    
        artworkUrl = artworks[artworkChoice]
    
        (artworkUrl_base, artworkUrl_fileName) = os.path.split(artworkUrl)
        (artworkUrl_baseFileName, artworkUrl_fileNameExtension)=os.path.splitext(artworkUrl_fileName)
    
        artworkFileName = "%s - S%02d%s" % (series.seriesName, series.seasonNumber, artworkUrl_fileNameExtension)
    
        if verbose:
            os.popen("curl -o \"%s\" \"%s\"" % (artworkFileName, artworkUrl))
            print "Downloaded Artwork: " + artworkFileName
        else:
            os.popen("curl -o \"%s\" \"%s\"" % (artworkFileName, artworkUrl))
        #end if verbose
        series.artworkFileName = artworkFileName
    except tvdb_attributenotfound:
        # The attribute wasn't found, not critical
        if verbose:
            sys.stderr.write("!! Non-Critical Show Error: %s not found for %s\n" % ("artwork", series.seriesName))
        #end if verbose
#end artwork


def getShowSpecificInfo(verbose, tvdb, seriesName, attribute):
    """docstring for getEpisodeSpecificInfo"""
    try:
        value = tvdb[seriesName][attribute]     
        if not value:
            return ""
        #clean up string
        value = value.replace('"', "\\\"")
        value = value.replace('&quot;', "\\\"")
        value = value.replace("'", "\'")
        return value
    except tvdb_error, errormsg:
        # Error communicating with thetvdb.com
        sys.stderr.write("!!!! Critical Show Error: Error contacting www.thetvdb.com:\n%s\n" % (errormsg))
        sys.exit(2)
    except tvdb_shownotfound:
        # No such series found.
        sys.stderr.write("!!!! Critical Show Error: Show %s not found\n" % (seriesName))
        sys.exit(2)
    except tvdb_seasonnotfound, errormsg:
        #the season name could not be found
        sys.stderr.write("!! Critical Show Error: The series name was not found for %s\n" % (seriesName))
        return 2
    except tvdb_attributenotfound, errormsg:
        # The attribute wasn't found, not critical
        if verbose:
            sys.stderr.write("!! Non-Critical Show Error: %s not found for %s\n" % (attribute, seriesName))
        #end if verbose
#end getEpisodeSpecificInfo


def getEpisodeSpecificInfo(verbose, program, series, episodeNumber, attribute):
    """docstring for getEpisodeSpecificInfo"""
    try:
        value = program.tvdb[series.seriesName][series.seasonNumber][episodeNumber][attribute]
        if not value:
            return ""
        #clean up string
        value = value.replace('"', "\\\"")
        value = value.replace('&quot;', "\\\"")
        value = value.replace("'", "\'")
        value = value.replace('`', "\'")
        return value
    except tvdb_episodenotfound:
        # The episode was not found wasn't found
        sys.stderr.write("!!!! Critical Episode Error: Episode name not found for %s - S%02dE%02d\n" % (series.seriesName, series.seasonNumber, episodeNumber))
        sys.exit(2)
    except tvdb_error, errormsg:
        # Error communicating with thetvdb.com
        sys.stderr.write("!!!! Critical Episode Error: Error contacting www.thetvdb.com:\n%s\n" % (errormsg))
        sys.exit(2)
    except tvdb_attributenotfound:
        # The attribute wasn't found, not critical
        if verbose:
            sys.stderr.write("!! Non-Critical Episode Error: %s not found for S%02dE%02d\n" % (attribute, series.seasonNumber, episodeNumber))
        #end if verbose
        return ""
#end getEpisodeSpecificInfo


def createCommaSeperatedStringFromArray(array):
    """docstring for createCommaSeperatedStringFromArray"""
    result = ""
    for item in array:
        if len(item) > 0:
            if result == "":
                result = "%s" % item
            else:
                result = "%s, %s" % (result, item)
        #end if len
    #end for item
    return result
#end createrdnsatom


def main():
    parser = OptionParser(usage="%prog [options] <full path directory>\n%prog -h for full list of options")
    
    parser.add_option(  "-b", "--batch", action="store_false", dest="interactive",
                        help="selects first search result, requires no human intervention once launched")
    parser.add_option(  "-i", "--interactive", action="store_true", dest="interactive",
                        help="interactivly select correct show from search results [default]")
    parser.add_option(  "-d", "--debug", action="store_true", dest="debug", 
                        help="shows all debugging info")
    parser.add_option(  "-v", "--verbose", action="store_true", dest="verbose",
                        help="Will provide some feedback [default]")
    parser.add_option(  "-q", "--quiet", action="store_false", dest="verbose",
                        help="For ninja-like processing")
    parser.add_option(  "-f", "--force-tagging", action="store_true", dest="forcetagging",
                        help="Tags all valid files, even previously tagged ones")
    parser.add_option(  "-r", "--remove-tags", action="store_true", dest="removetags",
                        help="Removes all tags")
    parser.add_option(  "-n", "--no-renaming", action="store_false", dest="rename",
                        help="disables renaming")
    parser.add_option(  "-t", "--no-tagging", action="store_false", dest="tagging",
                        help="disables tagging")
    parser.set_defaults( interactive=True, debug=False, verbose=True, forcetagging=False,
                            removetags=False, rename=True, tagging=True )
    
    opts, args = parser.parse_args()
    
    if len(args) == 0:
        parser.error("No directory supplied")
    #end if len(args)
    
    if len(args) > 1:
        parser.error("Provide single directory")
    #end if len(args)
    
    if opts.verbose:
        print "============ mp4tvtags Started ============"
    #end if verbose
    
    if os.path.isdir(args[0]):
        if args[0] == ".": #current directory
            dirPath = os.environ['PWD']
        else:
            dirPath = args[0]
        #end if args[0]
        os.chdir(dirPath)
        
    program = Program(opts, dirPath)
    informationHeldInFilename = re.compile("^(?P<series>(.*?)) - S(?P<seasonNumber>([0-9]+))(?P<episodeNumbers>((E[0-9]+)+)).*")
    
    # loop over all file names in the current directory
    for fileName in glob.glob("*.mp4") + glob.glob("*.m4v"):
        #filename syntax should be "showname - SXXEXX (ignored)"
        result = informationHeldInFilename.match(fileName)
        if not result:
            sys.stderr.write("!!!! Critical File Name Error: File \"%s\" is of incorrect format\nExample of structure: Showname - S01E01 - Pilot.mp4\n" % (fileName))
            continue
        #end if not result
        
        series = str(result.group("series"))
        seasonNumber = result.group("seasonNumber")
        
        episodeNumbersString = result.group("episodeNumbers")
        episodeNumbersAsStrings = episodeNumbersString.split('E')
        del episodeNumbersAsStrings[0] #first item will always be empty
        #convert all episode numbers to int
        episodeNumbers = [] 
        for episodeNumberAsString in episodeNumbersAsStrings:
            episodeNumbers.append(int(episodeNumberAsString))
        
        series = Series(opts.verbose, program, series, seasonNumber)
    
        #request user to select artwork
        artworkFileName = artwork(opts.verbose, opts.interactive, program, series)
        
        #check if the image we have needed resizing/dpi changed -> use this new temp file that was created for all the other episodes
        (imageFile, imageExtension) = os.path.splitext(series.artworkFileName)
        if series.artworkFileName.count("-resized-") == 0:
            for imageFileName in glob.glob("*" + imageExtension):
                if imageFileName.count("-resized-"):
                    series.artworkFileName = imageFileName
                    if opts.verbose:
                        print "Using resized artwork file \"%s\"" % imageFileName
                    #end if opts.verbose
                    break
                #end if imageFileName.count
            #end for imageFileName
        #end if series.artworkFileName.count
        
        #create an episode which will populate it's fields using data from thetvdb
        episode = Episode(opts.verbose, program, series, episodeNumbers, fileName)
        
        if opts.rename:
            #fix the filename
            correctFileName(opts, program, series, episode)
        #end if opts.rename
        
        if opts.removetags:
            if opts.verbose:
                print "  Removed any pre-existing tags from %s" % episode.fileName
            removeTagsCmd = "\"" + program.mp4tagger + "\" -i \"" + program.dirPath + "/" + episode.fileName + "\" -r -o"
            if opts.debug:
                print "!!Remove tags command: %s" % removeTagsCmd
            #remove any pre-existing embeded artwork
            result = os.popen(removeTagsCmd).read()
            if result.count("Program aborted") or result.count("Error"):
                print "** ERROR: %s" % result
                return sys.exit(1)
            #end if opts.verbose
        #end if opts.removeartwork
        
        #embed information in file using MP4Tagger
        if opts.tagging:
            tagFile(opts, program, series, episode)
        #end if opts.tagging
    #end for fileName
    
    if opts.verbose:
        print "============ mp4tvtags Completed ============"
    #end if verbose
#end main


if __name__ == '__main__':
        sys.exit(main())
#end if __name__