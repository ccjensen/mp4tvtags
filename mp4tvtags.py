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
dbr/Ben - http://github.com/dbr - for python help, tvdb_api and tvnamer.py
Rodney - http://kerstetter.net - for AtomicParsley help
"""
 
__author__ = "ccjensen/Chris"
__version__ = "0.3"
 
import os
import sys
import re
import glob

from optparse import OptionParser
 
from tvdb_api import (tvdb_error, tvdb_shownotfound, tvdb_seasonnotfound,
    tvdb_episodenotfound, tvdb_episodenotfound, tvdb_attributenotfound, tvdb_userabort)
from tvdb_api import Tvdb

class Program:
	"""docstring for Program"""
	def __init__(self, opts, dirPath):
		if opts.verbose:
			print "Connecting to the TVDB... "
		#end if verbose
		from tvdb_api import Tvdb
		self.tvdb = Tvdb(debug = opts.debug, interactive = opts.interactive)
		self.atomicParsley = os.path.dirname(__file__) + "/AtomicParsley32"
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
		
		self.contentRating = getShowSpecificInfo(verbose, program.tvdb, self.seriesName, 'contentrating')
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
	def __init__(self, verbose, program, series, fileName):
		self.fileName = fileName
		
		pattern = re.compile('[\D]+')
		#Parse the file name for information: 1x01 - Pilot.mp4
		(fileBaseName, self.fileExtension) = os.path.splitext(fileName)
		(seasonNumberEpisode, episodeNumber, tail) = pattern.split(fileBaseName,2)
		
		#check if filename was of correct format, else set it to an incorrect value
		if len(seasonNumberEpisode) > 0:
			self.seasonNumberEpisode = int(seasonNumberEpisode)
		else:
			self.seasonNumberEpisode = 9999
		#end if len(seasonNumberEpisode)
		
		self.episodeNumber = int(episodeNumber)
		
		#get other episode specific meta data
		self.episodeName = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumber, 'episodename')
		self.firstAired = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumber, 'firstaired') + "T09:00:00Z"
		
		self.guestStarsUnsplit = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumber, 'gueststars')
		self.guestStars = self.guestStarsUnsplit.split('|')
		
		self.directorsUnsplit = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumber, 'director')
		self.directors = self.directorsUnsplit.split('|')
		
		self.writersUnsplit = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumber, 'writer')
		self.writers = self.writersUnsplit.split('|')
		
		self.productionCode = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumber, 'productioncode')
		self.overview = getEpisodeSpecificInfo(verbose, program, series, self.episodeNumber, 'overview')
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

def correctFileName(verbose, program, series, episode):
	"""docstring for correctFilename"""
	#Correct file name if incorrect
	if episode.fileName != "%02dx%02d - %s%s" % (series.seasonNumber, episode.episodeNumber, episode.episodeName.encode("utf-8").replace('/', "-"), episode.fileExtension):
		newFileName = "%02dx%02d - %s%s" % (series.seasonNumber, episode.episodeNumber, episode.episodeName.encode("utf-8").replace('/', "-"), episode.fileExtension)
		renameCmd = "mv -n \"%s/%s\" \"%s/%s\"" % (program.dirPath, episode.fileName, program.dirPath, newFileName)
		os.popen(renameCmd)
		if verbose:
			print "Filename corrected from \"%s\" to \"%s\"" % (episode.fileName, newFileName)
		#end if verbose
		episode.fileName = newFileName
	else:
		if verbose:
			print "Filename \"%s\" already correct" % episode.fileName
		#end if verbose
	#end if fileName
#end correctFileName

def tagFile(opts, program, series, episode, additionalParameters):
	"""docstring for tagFile"""
	if not forcetagging:
		#check if file has already been tagged
		cmd = "\"" + program.atomicParsley + "\" \"" + program.dirPath + "/" + episode.fileName + "\"" + " -t"
		existingTagsUnsplit = os.popen(cmd).read()
		existingTags = existingTagsUnsplit.split('\r')
		for line in existingTags:
			if line.count("tagged by mp4tvtags"):
				if opts.verbose:
					print episode.fileName + " already tagged"
				#end if verbose
				return
			#end if line.count
		#end for line
	#end if opts.forcetagging
	#setup tags for the AtomicParsley function
	addArtwork = " --artwork \"%s\"" % series.artworkFileName #the file we downloaded earlier
	addStik = " --stik value=\"10\"" #set type to TV Show
	addArtist = " --artist \"%s\"" % series.seriesName
	addTitle =  " --title \"%s\"" % episode.episodeName
	addAlbum = " --album \"%s - Season %s\"" % (series.seriesName, series.seasonNumber)
	addGenre = " --genre \"%s\"" % series.genres[1] #cause first one is an empty string, and genre can only have one entry
	addAlbumArtist = " --albumArtist \"%s\"" % series.seriesName
	addDescription = " --description \"%s\"" % episode.overview
	addLongDescription = " --longDescription \"%s\"" % episode.overview
	addTVNetwork = " --TVNetwork \"%s\"" % series.network
	addTVShowName = " --TVShowName \"%s\"" % series.seriesName
	addTVEpisode = " --TVEpisode \"%s\"" % episode.productionCode
	addTVSeasonNum = " --TVSeasonNum \"%i\"" % series.seasonNumber
	addTVEpisodeNum = " --TVEpisodeNum \"%i\"" % episode.episodeNumber
	addDisk = " --disk \"%i\"" % series.seasonNumber
	addTracknum = " --tracknum \"%i\"" % episode.episodeNumber
	addContentRating = " --contentRating \"%s\"" % series.contentRating
	addYear = " --year \"%s\"" % episode.firstAired
	addSortOrderName = " --sortOrder name \"%s\"" % episode.episodeName
	addSortOrderArtist = " --sortOrder artist \"%s\"" % series.seriesName
	addSortOrderAlbumArtist = " --sortOrder albumartist \"%s\"" % series.seriesName
	addSortOrderAlbum = " --sortOrder album \"%s - Season %s\"" % (series.seriesName, series.seasonNumber)
	addSortOrderShow = " --sortOrder show \"%s\"" % series.seriesName
	addComment = " --comment \"tagged by mp4tvtags\""
	
	#concatunate actors and guest stars
	#actors = series.actors + episode.guestStars #usually makes a ridicously long list
	#create rDNSatom
	castDNS = ""
	directorsDNS = ""
	screenwritersDNS = ""
	if len(series.actors) > 0:
		castDNS = createrdnsatom("cast", series.actors)
	#end if len	
	if len(episode.directors) > 0:
		directorsDNS = createrdnsatom("directors", episode.directors)
	#end if len
	if len(episode.writers) > 0:
		screenwritersDNS = createrdnsatom("screenwriters", episode.writers)
	#end if len
	
	#create the rDNSatom string
	addrDNSatom = " --rDNSatom \"<?xml version=\'1.0\' encoding=\'UTF-8\'?><plist version=\'1.0\'><dict>%s%s%s</dict></plist>\" name=iTunMOVI domain=com.apple.iTunes" % (castDNS, directorsDNS, screenwritersDNS)
	
	#Create the command line string
	tagCmd = "\"" + program.atomicParsley + "\" \"" + program.dirPath + "/" + episode.fileName + "\"" \
	+ addArtwork + addStik + addArtist + addTitle + addAlbum + addGenre + addAlbumArtist + addDescription \
	+ addTVNetwork + addTVShowName + addTVEpisode + addTVSeasonNum + addTVEpisodeNum + addDisk + addTracknum \
	+ addSortOrderName + addSortOrderArtist + addSortOrderAlbumArtist + addSortOrderAlbum + addSortOrderShow \
	+ addContentRating  + addYear + addComment + addrDNSatom + addLongDescription + additionalParameters
	
	#run AtomicParsley using the arguments we have created
	if opts.debug:
		print tagCmd
	#end if debug
	
	os.popen(tagCmd.encode("utf-8"))
	
	if opts.overwrite:
		lockCmd = "chflags uchg \"" + program.dirPath + "/" + episode.fileName + "\""
	
		os.popen(lockCmd.encode("utf-8"))
		if opts.verbose:
			print "Tagged and locked: " + episode.fileName
		#end if verbose
	else:
		if opts.verbose:
			print "Tagged: " + episode.fileName
		#end if verbose
	#end if overwrite
#end tagFile
	

def artwork(verbose, interactive, program, series):
	potentialArtworkFileName = series.seriesName + " Season " + str(series.seasonNumber)
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
	
	artworkFileName = series.seriesName + " Season " + str(series.seasonNumber) + artworkUrl_fileNameExtension
	
	if verbose:
		os.popen("curl -o \"%s\" \"%s\"" % (artworkFileName, artworkUrl))
		print "Downloaded Artwork: " + artworkFileName
	else:
		os.popen("curl -o \"%s\" \"%s\"" % (artworkFileName, artworkUrl))
	#end if verbose
	series.artworkFileName = artworkFileName
#end artwork

def getShowSpecificInfo(verbose, tvdb, seriesName, attribute):
	"""docstring for getEpisodeSpecificInfo"""
	try:
		value = tvdb[seriesName][attribute]		
		#clean up string
		value =  value.replace('&quot;', "\\\"")
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
		#clean up string
		value =  value.replace('&quot;', "\\\"")
		return value
	except tvdb_episodenotfound:
		# The episode was not found wasn't found
		sys.stderr.write("!!!! Critical Episode Error: Episode name not found for %s - %02dx%02d\n" % (series.seriesName, series.seasonNumber, episodeNumber))
		sys.exit(2)
	except tvdb_error, errormsg:
		# Error communicating with thetvdb.com
		sys.stderr.write("!!!! Critical Episode Error: Error contacting www.thetvdb.com:\n%s\n" % (errormsg))
		sys.exit(2)
	except tvdb_attributenotfound:
		# The attribute wasn't found, not critical
		if verbose:
			sys.stderr.write("!! Non-Critical Episode Error: %s not found for %02dx%02d\n" % (attribute, series.seasonNumber, episodeNumber))
		#end if verbose
		return ""
#end getEpisodeSpecificInfo

def createrdnsatom(key, array):
	"""docstring for createrdnsatom"""
	dns = "<key>" + key + "</key><array>"
	for item in array:
		if len(array) > 0:
			if len(item) > 0:
				dns += "<dict><key>name</key><string>%s</string></dict>" % item
			#end if len
		#end if len
	#end for actor
	dns += "</array>"
	return dns
#end createrdnsatom


def main():
	parser = OptionParser(usage="%prog [options] <full path directory>\n%prog -h for full list of options")
	
	parser.add_option(  "-b", "--batch", action="store_false", dest="interactive",
	                    help="selects first search result, requires no human intervention once launched")
	parser.add_option(  "-i", "--interactive", action="store_true", dest="interactive",
	                    help="interactivly select correct show from search results [default]")
	parser.add_option(  "-c", "--cautious", action="store_false", dest="overwrite", 
	                    help="Writes everything to new files. Nothing is deleted (will make a mess!)")
	parser.add_option(  "-d", "--debug", action="store_true", dest="debug", 
	                    help="shows all debugging info")
	parser.add_option(  "-v", "--verbose", action="store_true", dest="verbose",
	                    help="Will provide some feedback [default]")
	parser.add_option(  "-q", "--quiet", action="store_false", dest="verbose",
	                    help="For ninja-like processing")
	parser.add_option(  "-f", "--force-tagging", action="store_true", dest="forcetagging",
	                    help="Tags all valid files, even previously tagged ones")
	parser.add_option(  "-r", "--remove-artwork", action="store_true", dest="removeartwork",
	                    help="removes previously embeded artwork")
	parser.add_option(  "-n", "--no-renaming", action="store_false", dest="rename",
	                    help="disables renaming")
	parser.add_option(  "-t", "--no-tagging", action="store_false", dest="tagging",
	                    help="disables tagging")
	parser.set_defaults( interactive=True, overwrite=True, debug=False, verbose=True, forcetagging=False,
	 						removeartwork=False, rename=True, tagging=True )
	
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
		
		try:
			# directory structure should be of syntax: /.../.../The X Files/Season 1
			(head, seasonFull) = os.path.split(dirPath)
			(head, series) = os.path.split(head)
			(season, seasonNumber) = seasonFull.split(" ",1)
		except ValueError:
			sys.stderr.write("!!!! Critical Path Error: Path structure \"%s\" is of incorrect format\nExample of structure: .../The X Files/Season 1\n" % (dirPath))
			sys.exit(2)		
	else:
		raise Exception("%s is not a valid directory") % args[0]
	#end if os.path.isdir
	
	program = Program(opts, dirPath)
	
	series = Series(opts.verbose, program, series, seasonNumber)
	
	if opts.overwrite:
		additionalParameters = " --overWrite"
	else:
		additionalParameters = ""
	#end if opts.overwrite
	
	#request user to select artwork
	artworkFileName = artwork(opts.verbose, opts.interactive, program, series)
	
	# loop over all file names in the current directory
	for fileName in glob.glob("*.mp4") + glob.glob("*.m4v"):		
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
		episode = Episode(opts.verbose, program, series, fileName)
		
		#check that file was of correct format
		if episode.seasonNumberEpisode != series.seasonNumber:
			sys.stderr.write("!!!! Critical File Name Error: File \"%s\" is of incorrect format\nExample of structure: 01x01 - Pilot.mp4\n" % (fileName))
			continue
		#end if seasonNumber !=
		
		if opts.rename:
			#fix the filename
			correctFileName(opts.verbose, program, series, episode)
		#end if opts.rename
		
		if opts.removeartwork:
			#remove any pre-existing embeded artwork
			os.popen("\"" + program.atomicParsley + "\" \"" + program.dirPath + "/" + episode.fileName + "\" --artwork REMOVE_ALL" + additionalParameters)
			if opts.verbose:
				print "Removed any pre-existing embeded artwork from %s" % episode.fileName
			#end if opts.verbose
		#end if opts.removeartwork
		
		#embed information in file using AtomicParsley
		if opts.tagging:
			tagFile(opts, program, series, episode, additionalParameters)
		#end if opts.tagging
	#end for fileName
	
	if opts.overwrite:
		#remove any temporary artwork files created by AtomicParsley
		(imageFile, imageExtension) = os.path.splitext(series.artworkFileName)
		if series.artworkFileName.count("-resized-"):
			os.remove(series.artworkFileName)
			if opts.verbose:
				print "Deleted temporary artwork file created by AtomicParsley"
			#end if opts.verbose
		else:
			#if only one file was tagged, we need to check again if a temporary artwork file was created
			for imageFileName in glob.glob("*" + imageExtension):
				if imageFileName.count("-resized-"):
					os.remove(imageFileName)
					if opts.verbose:
						print "Deleted temporary artwork file created by AtomicParsley"
					#end if opts.verbose
				#end if imageFileName.count
			#end for imageFileName
		#end if artworkFileName.count
	#end if opts.overwrite
	
	if opts.verbose:
		print "============ mp4tvtags Completed ============"
	#end if verbose
#end main

if __name__ == '__main__':
		sys.exit(main())
#end if __name__