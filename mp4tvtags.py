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
dbr/Ben - http://github.com/dbr
Rodney - http://kerstetter.net
"""
 
__author__ = "ccjensen/Chris"
__version__ = "0.1"
 
import os, sys, re, glob
from optparse import OptionParser
 
from tvdb_api import (tvdb_error, tvdb_shownotfound, tvdb_seasonnotfound,
    tvdb_episodenotfound, tvdb_episodenotfound, tvdb_attributenotfound, tvdb_userabort)
from tvdb_api import Tvdb
 
config = {}

def _openUrl(urls):
	for url in urls:
		if len(url) > 0:
			os.popen("open \"%s\"" % url)
	return

def _artwork(db, dirPath, seriesName, seasonNumber):
	potentialArtworkFileName = seriesName + " Season " + str(seasonNumber)
	for fileName in glob.glob("*.jpg"):
		(fileBaseName, fileExtension) = os.path.splitext(fileName)
		if fileBaseName == potentialArtworkFileName:
			print "Using Previously Downloaded Artwork: " + fileName
			return fileName
	sid = db._nameToSid(seriesName)
	artworks = db._getSeasonSpecificArtwork(sid, seasonNumber)
	
	artworkCounter = 0
	for artwork in artworks:
		print "%s. %s" % (artworkCounter, artwork)
		artworkCounter += 1
	
	#allow user to preview images
	print "Example of listing: 1 2 4"
	artworkPreviewRequestNumbers = raw_input("List Images to Preview: ")
	artworkPreviewRequests = artworkPreviewRequestNumbers.split()
	
	artworkPreviewUrls = []
	for artworkPreviewRequest in artworkPreviewRequests:
		artworkPreviewUrls.append(artworks[int(artworkPreviewRequest)])
	_openUrl(artworkPreviewUrls)
	
	#ask user what artwork he wants to use
	artworkChoice = int(raw_input("Artwork to use: "))
	artworkUrl = artworks[artworkChoice]
	
	(artworkUrl_base, artworkUrl_fileName) = os.path.split(artworkUrl)
	(artworkUrl_baseFileName, artworkUrl_fileNameExtension)=os.path.splitext(artworkUrl_fileName)
	
	artworkFileName = seriesName + " Season " + str(seasonNumber) + artworkUrl_fileNameExtension
	
	os.popen("curl -o %s %s" % ("\"" + artworkFileName + "\"", artworkUrl))
	print "Downloaded Artwork: " + artworkFileName
	return artworkFileName

def main():
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
	
	try:
		#get show specific meta data
		seriesName  = db[series]['seriesname']
		
		actorsUnsplit = db[series]['actors']
		actors = actorsUnsplit.split('|')

		contentRating = db[series]['contentrating']
		firstaired  = db[series]['firstaired']

		genresUnsplit  = db[series]['genre']
		genres = genresUnsplit.split('|')

		network  = db[series]['network']
		seriesOverview  = db[series]['overview']

	except tvdb_shownotfound:
		# No such series found.
		sys.stderr.write("!!!! Critical Error: Show %s not found (in %s)\n" % (series, dirPath))
		return 2
	except tvdb_seasonnotfound:
		# The season wasn't found, but the show was.
		sys.stderr.write("!!!! Critical Error: Season number %s not found for %s (in %s)\n" % (seasonNumber, series, dirPath))
		return 2
	except tvdb_error, errormsg:
		# Error communicating with thetvdb.com
		sys.stderr.write("!!!! Critical Error: Error contacting www.thetvdb.com:\n%s\n" % (errormsg))
		return 2
	except tvdb_attributenotfound, errormsg:
		# The attribute wasn't found, not critical
		sys.stderr.write("!! Non-Critical Error: %s for %s (in %s)\n" % (errormsg, series, dirPath))
	
	seasonNumber = int(seasonNumber)
	
	artworkFileName = _artwork(db, dirPath, seriesName, seasonNumber)
	
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
		if alreadyTagged:
			print fileName + " already tagged"
			continue			
		
		#check if the image we have needed resizing/dpi changed, so now we should use this new temp file that was created
		(imageFile, imageExtension) = os.path.splitext(artworkFileName)
		if artworkFileName.count("-resized-") == 0:
			for imageFileName in glob.glob("*" + imageExtension):
				if imageFileName.count("-resized-"):
					artworkFileName = imageFileName
					break
		
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
		addLongDescription = " --longDescription \"%s\"" % seriesOverview
		addTVNetwork = " --TVNetwork \"%s\"" % network
		addTVShowName = " --TVShowName \"%s\"" % seriesName
		addTVEpisode = " --TVEpisode \"%s\"" % productionCode
		addTVSeasonNum = " --TVSeasonNum \"%i\"" % seasonNumber
		addTVEpisodeNum = " --TVEpisodeNum \"%i\"" % episodeNumber
		addContentRating = " --contentRating \"%s\"" % contentRating
		addYear = " --year \"%s\"" % firstAired
		addComment = " --comment \"tagged by mp4tvtags\""
		
		#create rDNSatom
		if len(actors) > 0:
			castDNS = "<key>cast</key><array>"
			for actor in actors:
				if len(actor) > 0:
					castDNS += "<dict><key>name</key><string>%s</string></dict>" % actor
			castDNS += "</array>"
		
		if len(directors) > 0:
			directorsDNS = "<key>directors</key><array>"
			for director in directors:
				if len(director) > 0:
					directorsDNS += "<dict><key>name</key><string>%s</string></dict>" % director
			directorsDNS += "</array>"
		
		if len(writers) > 0:
			screenwritersDNS = "<key>screenwriters</key><array>"
			for writer in writers:
				if len(writer) > 0:
					screenwritersDNS += "<dict><key>name</key><string>%s</string></dict>" % writer
			screenwritersDNS += "</array>"
		
		#create the rDNSatom string
		addrDNSatom = ' --rDNSatom \'<?xml version=\"1.0\" encoding=\"UTF-8\"?><plist version=\"1.0\"><dict>%s%s%s</dict></plist>\' name=iTunMOVI domain=com.apple.iTunes' % (castDNS, directorsDNS, screenwritersDNS)
		
		#Create the command line string
		tagCmd = "\"" + atomicParsley + "\" \"" + dirPath + "/" + fileName + "\"" \
		+ addArtwork + addStik + addArtist + addTitle + addAlbum + addGenre + addAlbumArtist + addDescription \
		+ addTVNetwork + addTVShowName + addTVEpisode + addTVSeasonNum + addTVEpisodeNum + addContentRating  \
		+ addYear + addComment + addrDNSatom + addLongDescription + additionalParameters
		
		#run AtomicParsley using the arguments we have created
		os.popen(tagCmd)
		print "Tagged: " + fileName
		#print tagCmd
	
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
		
def getEpisodeSpecificInfo(tvdb, series, seasonNumber, episodeNumber, attribute):
	"""docstring for getEpisodeSpecificInfo"""
	try:
		value = tvdb[series][seasonNumber][episodeNumber][attribute]
		#clean up string
		value =  value.replace('"', "&quot;")
		value = value.replace("'", "&#39;")
		return value
	except tvdb_episodenotfound:
		# The episode was not found wasn't found
		sys.stderr.write("!!!! Critical Error: Episode name not found for %s (in %s%s)\n" % (series, dirPath, fileName))
		sys.exit(2)
	except tvdb_error, errormsg:
		# Error communicating with thetvdb.com
		sys.stderr.write("!!!! Critical Error: Error contacting www.thetvdb.com:\n%s\n" % (errormsg))
		sys.exit(2)
	except tvdb_attributenotfound, errormsg:
		# The attribute wasn't found, not critical
		sys.stderr.write("!! Non-Critical Error: %s for %sx%s\n" % (errormsg, seasonNumber, episodeNumber))
		return ""

if __name__ == '__main__':
		sys.exit(main())