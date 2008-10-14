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
dbr/Ben - http://github.com/dbr - for python and tvdb_api
Rodney - http://kerstetter.net - for AtomicParsley help
Coordt - http://www.djangosnippets.org/users/coordt/ - for unicode to ascii
"""
 
__author__ = "ccjensen/Chris"
__version__ = "0.1"
 
import os
import sys
import re
import glob

from optparse import OptionParser
 
from tvdb_api import (tvdb_error, tvdb_shownotfound, tvdb_seasonnotfound,
    tvdb_episodenotfound, tvdb_episodenotfound, tvdb_attributenotfound, tvdb_userabort)
from tvdb_api import Tvdb

def openurl(urls):
	for url in urls:
		if len(url) > 0:
			os.popen("open \"%s\"" % url)
		#end if len
	#end for url
	return
#end openurl

def artwork(db, dirPath, seriesName, seasonNumber):
	potentialArtworkFileName = seriesName + " Season " + str(seasonNumber)
	for fileName in glob.glob("*.jpg"):
		(fileBaseName, fileExtension) = os.path.splitext(fileName)
		if fileBaseName == potentialArtworkFileName:
			print "Using Previously Downloaded Artwork: " + fileName
			return fileName
		#end if fileBaseName
	#end for fileName
	sid = db._nameToSid(seriesName)
	artworks = db._getSeasonSpecificArtwork(sid, seasonNumber)
	
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
	artworkUrl = artworks[artworkChoice]
	
	(artworkUrl_base, artworkUrl_fileName) = os.path.split(artworkUrl)
	(artworkUrl_baseFileName, artworkUrl_fileNameExtension)=os.path.splitext(artworkUrl_fileName)
	
	artworkFileName = seriesName + " Season " + str(seasonNumber) + artworkUrl_fileNameExtension
	
	os.popen("curl -o %s %s" % ("\"" + artworkFileName + "\"", artworkUrl))
	print "Downloaded Artwork: " + artworkFileName
	return artworkFileName
#end artwork

def getShowSpecificInfo(tvdb, series, attribute):
	"""docstring for getEpisodeSpecificInfo"""
	try:
		value = tvdb[series][attribute]		
		return value
	except tvdb_error, errormsg:
		# Error communicating with thetvdb.com
		sys.stderr.write("!!!! Critical Show Error: Error contacting www.thetvdb.com:\n%s\n" % (errormsg))
		sys.exit(2)
	except tvdb_shownotfound:
		# No such series found.
		sys.stderr.write("!!!! Critical Show Error: Show %s not found\n" % (series))
		sys.exit(2)
	except tvdb_seasonnotfound, errormsg:
		# Either the season wasn't found, or a bit of data we requested about the show is missing
		sys.stderr.write("!! Non-Critical Show Error: %s for %s\n" % (errormsg, series))
	except tvdb_attributenotfound, errormsg:
		# The attribute wasn't found, not critical
		sys.stderr.write("!! Non-Critical Show Error: %s for %s\n" % (errormsg, series))
#end getEpisodeSpecificInfo

def getEpisodeSpecificInfo(tvdb, series, seasonNumber, episodeNumber, attribute):
	"""docstring for getEpisodeSpecificInfo"""
	try:
		value = tvdb[series][seasonNumber][episodeNumber][attribute]
		#clean up string
		value =  value.replace('&quot;', "\\\"")
		
		#convert any unicode to ascii
		from unaccented_map import unicode_to_ascii
		value = unicode_to_ascii(value)
		
		return value
	except tvdb_episodenotfound:
		# The episode was not found wasn't found
		sys.stderr.write("!!!! Critical Episode Error: Episode name not found for %s %sx%s\n" % (series, seasonNumber, episodeNumber))
		sys.exit(2)
	except tvdb_error, errormsg:
		# Error communicating with thetvdb.com
		sys.stderr.write("!!!! Critical Episode Error: Error contacting www.thetvdb.com:\n%s\n" % (errormsg))
		sys.exit(2)
	except tvdb_attributenotfound, errormsg:
		# The attribute wasn't found, not critical
		sys.stderr.write("!! Non-Critical Episode Error: %s for %sx%s\n" % (errormsg, seasonNumber, episodeNumber))
		return ""
#end getEpisodeSpecificInfo

def createrdnsatom(key, array):
	"""docstring for createrdnsatom"""
	dns = "<key>" + key + "</key><array>"
	for item in array:
		if len(array) > 0:
			dns += "<dict><key>name</key><string>%s</string></dict>" % item
		#end if len
	#end for actor
	dns += "</array>"
	return dns
#end createrdnsatom

def main():
	print "Connecting to the TVDB... "
	"""docstring for run"""
	from tvdb_api import Tvdb
	db = Tvdb()
	
	atomicParsley = os.path.dirname(__file__) + "/AtomicParsley32"
	additionalParameters = " --overWrite"
	dirPath = os.getcwd()
	# ex: /.../.../The X Files/Season 1
	(head, seasonFull) = os.path.split(dirPath)
	(head, series) = os.path.split(head)
	(season, seasonNumber) = seasonFull.split(" ",1)
	
	#get show specific meta data
	print "Retrieving Show Information... "
	seriesName = getShowSpecificInfo(db, series, 'seriesname')
	
	#check if we actually found seriesName
	if len(seriesName) == 0:
		return 2
	#end if len
	
	actorsUnsplit = getShowSpecificInfo(db, series, 'actors')
	actors = actorsUnsplit.split('|')
	
	contentRating = getShowSpecificInfo(db, series, 'contentrating')
	firstaired  = getShowSpecificInfo(db, series, 'firstaired')
	
	genresUnsplit  = getShowSpecificInfo(db, series, 'genre')
	genres = genresUnsplit.split('|')

	network  = getShowSpecificInfo(db, series, 'network')
	#seriesOverview  = getShowSpecificInfo(db, series, 'overview') #currently not used for anything
	
	seasonNumber = int(seasonNumber)
	
	#request user to select artwork
	artworkFileName = artwork(db, dirPath, seriesName, seasonNumber)
	
	pattern = re.compile('[\D]+')
	# loop over all file names in the current directory
	for fileName in glob.glob("*.mp4"):
		#reset variables
		alreadyTagged = False
		
		#check if file has already been tagged
		cmd = "\"" + atomicParsley + "\" \"" + dirPath + "/" + fileName + "\"" \
		+ " -t"
		existingTagsUnsplit = os.popen(cmd).read()
		existingTags = existingTagsUnsplit.split('\r')
		for line in existingTags:
			if line.count("tagged by mp4tvtags"):
				alreadyTagged = True
				break
			#end if line.count
		#end for line
		if alreadyTagged:
			print fileName + " already tagged"
			continue
		#end if alreadyTagged	
		
		#check if the image we have needed resizing/dpi changed, so now we should use this new temp file that was created
		(imageFile, imageExtension) = os.path.splitext(artworkFileName)
		if artworkFileName.count("-resized-") == 0:
			for imageFileName in glob.glob("*" + imageExtension):
				if imageFileName.count("-resized-"):
					artworkFileName = imageFileName
					break
				#end if imageFileName.count
			#end for imageFileName
		#end if artworkFileName.count
		
		#Parse the file name for information: 1x01 - Pilot.mp4
		(fileBaseName, fileExtension) = os.path.splitext(fileName)
		(seasonNumber2, episodeNumber, tail) = pattern.split(fileBaseName,2)
		episodeNumber = int(episodeNumber)
		
		#get episode specific meta data			
		episodeName = getEpisodeSpecificInfo(db, series, seasonNumber, episodeNumber, 'episodename')
		firstAired = getEpisodeSpecificInfo(db, series, seasonNumber, episodeNumber, 'firstaired') + "T09:00:00Z"
		
		guestStarsUnsplit = getEpisodeSpecificInfo(db, series, seasonNumber, episodeNumber, 'gueststars')
		guestStars = guestStarsUnsplit.split('|')
		
		directorsUnsplit = getEpisodeSpecificInfo(db, series, seasonNumber, episodeNumber, 'director')
		directors = directorsUnsplit.split('|')
		
		writersUnsplit = getEpisodeSpecificInfo(db, series, seasonNumber, episodeNumber, 'writer')
		writers = writersUnsplit.split('|')
		
		productionCode = getEpisodeSpecificInfo(db, series, seasonNumber, episodeNumber, 'productioncode')
		overview = getEpisodeSpecificInfo(db, series, seasonNumber, episodeNumber, 'overview')
		
		#setup tags for the AtomicParsley function
		addArtwork = " --artwork \"%s\"" % artworkFileName #the file we downloaded earlier
		addStik = " --stik value=\"10\"" #set type to TV Show
		addArtist = " --artist \"%s\"" % seriesName
		addTitle =  " --title \"%s\"" % episodeName
		addAlbum = " --album \"%s\"" % seriesName
		addGenre = " --genre \"%s\"" % genres[1] #cause first one is an empty string, and genre can only have one entry
		addAlbumArtist = " --albumArtist \"%s\"" % seriesName
		addDescription = " --description \"%s\"" % overview
		addLongDescription = " --longDescription \"%s\"" % overview
		addTVNetwork = " --TVNetwork \"%s\"" % network
		addTVShowName = " --TVShowName \"%s\"" % seriesName
		addTVEpisode = " --TVEpisode \"%s\"" % productionCode
		addTVSeasonNum = " --TVSeasonNum \"%i\"" % seasonNumber
		addTVEpisodeNum = " --TVEpisodeNum \"%i\"" % episodeNumber
		addDisk = " --disk \"%i\"" % seasonNumber
		addTracknum = " --tracknum \"%i\"" % episodeNumber
		addContentRating = " --contentRating \"%s\"" % contentRating
		addYear = " --year \"%s\"" % firstAired
		addComment = " --comment \"tagged by mp4tvtags\""
		
		#create rDNSatom
		if len(actors) > 0:
			castDNS = createrdnsatom("cast", actors)
		#end if len	
		if len(directors) > 0:
			directorsDNS = createrdnsatom("directors", directors)
		#end if len
		if len(writers) > 0:
			screenwritersDNS = createrdnsatom("screenwriters", writers)
		#end if len
		
		#create the rDNSatom string
		addrDNSatom = " --rDNSatom \"<?xml version=\'1.0\' encoding=\'UTF-8\'?><plist version=\'1.0\'><dict>%s%s%s</dict></plist>\" name=iTunMOVI domain=com.apple.iTunes" % (castDNS, directorsDNS, screenwritersDNS)
		
		#Create the command line string
		tagCmd = "\"" + atomicParsley + "\" \"" + dirPath + "/" + fileName + "\"" \
		+ addArtwork + addStik + addArtist + addTitle + addAlbum + addGenre + addAlbumArtist + addDescription \
		+ addTVNetwork + addTVShowName + addTVEpisode + addTVSeasonNum + addTVEpisodeNum + addDisk + addTracknum \
		+ addContentRating  + addYear + addComment + addrDNSatom + addLongDescription + additionalParameters
		
		#run AtomicParsley using the arguments we have created
		os.popen(tagCmd)
		print "Tagged: " + fileName
		#print tagCmd
	#end for fileName
	
	#remove any temporary artwork files created by AtomicParsley
	(imageFile, imageExtension) = os.path.splitext(artworkFileName)
	if artworkFileName.count("-resized-"):
		os.remove(artworkFileName)
		print "Deleted temporary artwork file created by AtomicParsley"
	else:
		#if only one file was tagged, we need to check again if a temporary artwork file was created
		for imageFileName in glob.glob("*" + imageExtension):
			if imageFileName.count("-resized-"):
				os.remove(imageFileName)
				print "Deleted temporary artwork file created by AtomicParsley"
			#end if imageFileName.count
		#end for imageFileName
	#end if artworkFileName.count
#end main

if __name__ == '__main__':
		sys.exit(main())
#end if __name__