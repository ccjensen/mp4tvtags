#!/usr/bin/env python

import glob
import re
import sys, os

def _openUrl(urls):
	for url in urls:
		if len(url) > 0:
			os.popen("open \"%s\"" % url)
	return
	
def _artwork(db, seriesName, seasonNumber):
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
	return artworkFileName

def main():
	from tvdb_api import Tvdb
	db = Tvdb()
	
	dirPath = os.getcwd()
	# ex: /.../.../The X Files/Season 1
	(head, seasonFull) = os.path.split(dirPath)
	(head, show) = os.path.split(head)
	(season, seasonNumber) = seasonFull.split(" ",1)
	
	#get show specific meta data
	actorsUnsplit = db[show]['actors']
	actors = actorsUnsplit.split('|')
	
	contentRating = db[show]['contentrating']
	firstaired  = db[show]['firstaired']
	contentRating  = db[show]['contentrating']
	
	genresUnsplit  = db[show]['genre']
	genres = genresUnsplit.split('|')
	
	network  = db[show]['network']
	seriesOverview  = db[show]['overview']
	seriesName  = db[show]['seriesname']
	
	seasonNumber = int(seasonNumber)
	
	artworkFileName = _artwork(db, seriesName, seasonNumber)
	print artworkFileName
	
	pattern = re.compile('[\D]+')
	# loop over all file names in the current directory
	for fileName in glob.glob("*.mp4"):
		#Parse the file name for information: 1x01 - Pilot.mp4
		(fileBaseName, fileExtension) = os.path.splitext(fileName)
		(seasonNumber2, episodeNumber, tail) = pattern.split(fileBaseName,2)
		episodeNumber = int(episodeNumber)
		
		#get episode specific meta data
		episodeName = db[show][seasonNumber][episodeNumber]['episodename']
		firstAired = db[show][seasonNumber][episodeNumber]['firstaired'] + "T09:00:00Z"
		
		guestStarsUnsplit = db[show][seasonNumber][episodeNumber]['gueststars']
		guestStars = guestStarsUnsplit.split('|')
		
		directorsUnsplit = db[show][seasonNumber][episodeNumber]['director']
		directors = directorsUnsplit.split('|')
		
		writersUnsplit = db[show][seasonNumber][episodeNumber]['writer']
		writers = writersUnsplit.split('|')
		
		productionCode = db[show][seasonNumber][episodeNumber]['productioncode']
		overview = db[show][seasonNumber][episodeNumber]['overview']
		
		#setup tags for the AtomicParsley function
		addArtwork = " --artwork \"%s\"" % artworkFileName #the file we downloaded earlier
		addStik = " --stik 10" #set type to TV Show
		#addLongDescription = "testing \"%s\"" % seriesOverview
		addArtist = " --artist \"%s\"" % seriesName
		addTitle =  " --title \"%s\"" % episodeName
		addAlbum = " --album \"%s\"" % seriesName
		addGenre = " --genre \"%s\"" % genres[1] #cause first one is an empty string, and genre can only have one entry
		addAlbumArtist = " --albumArtist \"%s\"" % seriesName
		addDescription = " --description \"%s\"" % overview
		addTVNetwork = " --TVNetwork \"%s\"" % network
		addTVShowName = " --TVShowName \"%s\"" % seriesName
		addTVEpisode = " --TVEpisode \"%s\"" % productionCode
		addTVSeasonNum = " --TVSeasonNum \"%i\"" % seasonNumber
		addTVEpisodeNum = " --TVEpisodeNum \"%i\"" % episodeNumber
		addContentRating = " --contentRating \"%s\"" % contentRating
		addYear = " --year \"%s\"" % firstAired
		
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
		cmd = "/Applications/MetaX.app/Contents/Resources/AtomicParsley32 \"" + dirPath + "/" + fileName + "\"" \
		+ addStik + addArtist + addTitle + addAlbum + addGenre + addAlbumArtist + addDescription + addTVNetwork \
		+ addTVShowName + addTVEpisode + addTVSeasonNum + addTVEpisodeNum + addContentRating + addrDNSatom
		
		#run AtomicParsley using the arguments we have created
		result = os.popen(cmd)

if __name__ == '__main__':
	main()