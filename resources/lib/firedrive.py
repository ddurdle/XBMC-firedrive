'''
    firedrive XBMC Plugin
    Copyright (C) 2013-2014 ddurdle

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''

import os
import re
import urllib, urllib2
from resources.lib import authorization
from cloudservice import cloudservice
from resources.lib import folder
from resources.lib import file
from resources.lib import mediaurl





import xbmc, xbmcaddon, xbmcgui, xbmcplugin



#
#
#
class firedrive(cloudservice):

    AUDIO = 1
    VIDEO = 2

    CACHE_TYPE_ORIGINAL = 0

    CACHE_TYPE_STREAM = 2
    CACHE_TYPE_STREAM_SD = 3
    CACHE_TYPE_STREAM_HD = 4
    FILE_URL = 'http://www.firedrive.com/file/'
    DOWNLOAD_LINK = 'http://dl.firedrive.com/?alias='

    ##
    # initialize (save addon, instance name, user agent)
    ##
    def __init__(self, PLUGIN_URL, addon, instanceName, user_agent):
        self.PLUGIN_URL = PLUGIN_URL
        self.addon = addon
        self.instanceName = instanceName

        try:
            username = self.addon.getSetting(self.instanceName+'_username')
        except:
            username = ''
        self.authorization = authorization.authorization(username)


        try:
            auth = self.addon.getSetting(self.instanceName+'_auth_token')
            cookie = self.addon.getSetting(self.instanceName+'_auth_cookie')
        except:
            auth = ''
            cookie = ''

        self.authorization.setToken('auth_token',auth)
        self.authorization.setToken('auth_cookie',cookie)
        self.user_agent = user_agent

        #public playback only -- no authentication
        if self.authorization.username == '':
            return

        # if we have an authorization token set, try to use it
        if auth != '':
          xbmc.log(self.addon.getAddonInfo('name') + ': ' + 'using token', xbmc.LOGDEBUG)
          return
        else:
          xbmc.log(self.addon.getAddonInfo('name') + ': ' + 'no token - logging in', xbmc.LOGDEBUG)
          self.login();
          return



    ##
    # perform login
    ##
    def login(self):

        header = { 'User-Agent' : self.user_agent}


        url = 'http://auth.firedrive.com/'

        values = {
                  'pass' : self.addon.getSetting(self.instanceName+'_password'),
                  'user' : self.authorization.username,
                  'remember' : 1,
                  'json' : 1,
                  'user_token' : '',
        }

        xbmc.log(self.addon.getAddonInfo('name') + ': ' + 'logging in', xbmc.LOGDEBUG)
        req = urllib2.Request(url, urllib.urlencode(values), header)

        # try login
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403:
                #login denied
                xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30017))
            xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
            return
        response_header = response.info().getheader('Set-Cookie')
        response_data = response.read()

        authCookie = 0
        for r in re.finditer(' (auth)\=([^\;]+)\;',
                             response_header, re.DOTALL):
            setCookie,authCookie = r.groups()

        if (authCookie != 0):
            self.authorization.setToken('auth_cookie',authCookie)
            header = { 'User-Agent' : self.user_agent, 'Cookie' : 'auth='+authCookie+'; exp=1' }


        statusResult = 0
        #validate successful login
        for r in re.finditer('"(status)":(\d+),',
                             response_data, re.DOTALL):
            statusType,statusResult = r.groups()

        if (statusResult == 0):
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30017))
            xbmc.log(self.addon.getAddonInfo('name') + ': ' + 'login failed', xbmc.LOGERROR)

            return

        url = 'http://www.firedrive.com/myfiles'

        req = urllib2.Request(url, None, header)

        # if action fails, validate login
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
            return

        response_data = response.read()

        userID = 0
        # retrieve authorization token
        for r in re.finditer('var_Array\[\'(user_token)\'\]\s+\=\s+\"([^\"]+)\"\;',
                             response_data, re.DOTALL):
            id,userID = r.groups()

        if userID == 0 :
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.ddon.getLocalizedString(30017))
            xbmc.log(self.addon.getAddonInfo('name') + ': ' + 'login failed', xbmc.LOGERROR)
            return

        # save authorization token
        self.authorization.setToken('auth_token',userID)
        return


    ##
    # return the appropriate "headers" for FireDrive requests that include 1) user agent, 2) authorization cookie
    #   returns: list containing the header
    ##
    def getHeadersList(self):
        cookie = self.authorization.getToken('auth_cookie')
        if (cookie != '' and cookie != 0):
            return { 'User-Agent' : self.user_agent, 'Cookie' : 'auth='+cookie+'; exp=1' }
        else:
            return { 'User-Agent' : self.user_agent }


    ##
    # retrieve a list of media files
    #   parameters: prompt for video quality (optional), cache type (optional)
    #   returns: array of media file objects
    ##
    def getMediaList(self, folderID=0, cacheType=0):

        # retrieve all documents
        params = urllib.urlencode({'getFiles': folderID, 'format': 'large', 'term': '', 'group':0, 'limit':1, 'user_token': self.authorization.getToken('auth_token'), '_': 1394486104901})

        url = 'http://www.firedrive.com/action/?'+ params

        mediaFiles = []
        if True:
            req = urllib2.Request(url, None, self.getHeadersList())

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)

                  return
              else:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return

            response_data = response.read()

            #if authorization cookie is broken, response will be empty, so log in again
            if response_data == '':
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  return
                response_data = response.read()

            # video-entry
            for r in re.finditer('"gal_thumb":"([^\"]+)"\,.*?type\=\'video\'.*?"file_filename":"([^\"]+)","al_title":"([^\"]+)".*?alias\=([^\"]+)"' ,response_data, re.DOTALL):
                img,filename,title,fileID = r.groups()
                img = re.sub('\\\\', '', img)
                img = 'http://static.firedrive.com/'+img


                mediaFiles.append(file.file(fileID, title, title, self.VIDEO, '', img))

            for r in re.finditer('"gal_thumb":"([^\"]+)"\,.*?type\=\'audio\'.*?"file_filename":"([^\"]+)","al_title":"([^\"]+)".*?alias\=([^\"]+)"' ,response_data, re.DOTALL):
                img,filename,title,fileID = r.groups()
                img = re.sub('\\\\', '', img)
                img = 'http://static.firedrive.com/'+img

#                videos[title] = {'url': self.PLUGIN_URL+'?mode=playAudio&instance='+self.instanceName+'&filename=' + fileID+'&title=' + title, 'thumbnail' : img}
                mediaFiles.append(file.file(fileID, title, title, self.AUDIO, '', img))

            for r in re.finditer('"gal_thumb":"([^\"]+)"\,.*?type\=\'other\'.*?"file_filename":"([^\"]+)","al_title":"([^\"]+)".*?alias\=([^\"]+)"' ,response_data, re.DOTALL):
                img,filename,title,fileID = r.groups()
                img = re.sub('\\\\', '', img)
                img = 'http://static.firedrive.com/'+img

#                videos[title] = {'url': self.PLUGIN_URL+'?mode=playVideo&instance='+self.instanceName+'&filename=' + fileID+'&title=' + title, 'thumbnail' : img}
                mediaFiles.append(file.file(fileID, title, title, self.VIDEO, '', img))

            response.close()

        return mediaFiles

    ##
    # retrieve a playback url
    #   returns: url
    ##
    def getPlaybackCall(self, file):
        if file.type == self.VIDEO:
            return self.PLUGIN_URL+'?mode=play&instance='+self.instanceName+'&filename=' + file.id+'&title=' + file.title
        else:
            return self.PLUGIN_URL+'?mode=streamaudio&instance='+self.instanceName+'&filename=' + file.id+'&title=' + file.title
    ##
    # retrieve a directory url
    #   returns: url
    ##
    def getDirectoryCall(self, folder):
        return self.PLUGIN_URL+'?mode=folder&instance='+self.instanceName+'&folderID=' + folder.id


    ##
    # retrieve a list of folders
    #   parameters: folder is the current folderID
    #   returns: array of folder objects
    ##
    def getFolderList(self, folderID=0):

        # retrieve all documents
        params = urllib.urlencode({'getFolders': folderID, 'format': 'large', 'term': '', 'group':0, 'user_token': self.authorization.getToken('auth_token'), '_': 1394486104901})

        url = 'http://www.firedrive.com/action/?'+ params

        folders = []
        if True:
            req = urllib2.Request(url, None, self.getHeadersList())

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  return
              else:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return

            response_data = response.read()

            #if authorization cookie is broken, response will be empty, so log in again
            if response_data == '':
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  return
                response_data = response.read()

            # parsing page for folders
            for r in re.finditer('"f_id":"([^\"]+)".*?"f_fullname":"([^\"]+)"' ,response_data, re.DOTALL):
                folderID, folderName = r.groups()

                folders.append(folder.folder(folderID,folderName))
#                folders[folderName] = self.PLUGIN_URL+'?mode=folder&instance='+self.instanceName+'&folderID=' + folderID

            response.close()

        return folders



    ##
    # retrieve a audio playback URL
    #   parameters: filename of audio
    #   returns: list of media URLs
    ##
    def getAudioURL(self,filename):



        url = 'http://www.firedrive.com/file/'+filename

        req = urllib2.Request(url, None, self.getHeadersList())


        # if action fails, validate login
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              req = urllib2.Request(url, None, self.getHeadersList())
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return
            else:
              xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
              return

        response_data = response.read()

        #if authorization cookie is broken, response will be empty, so log in again
        if response_data == '':
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  return
                response_data = response.read()


        mediaURLs = []
#        playbackURL = self.DOWNLOAD_LINK+filename+'&stream' + '|'+self.getHeadersEncoded()
        mediaURLs.append(mediaurl.mediaurl(self.DOWNLOAD_LINK+filename+'&stream', 'Transcode Stream SD', self.CACHE_TYPE_STREAM_SD, 2))
        mediaURLs.append(mediaurl.mediaurl(self.DOWNLOAD_LINK+filename, 'Original (non-Transcode Stream)', self.CACHE_TYPE_ORIGINAL, 3))

        # fetch video title, download URL and docid for stream link
        for r in re.finditer('(label)\: \"([^\"]+)\"' ,response_data, re.DOTALL):
             streamLabel,streamType = r.groups()
             if streamType == 'HD':
#                 playbackURL = self.DOWNLOAD_LINK+filename+'&hd' + '|'+self.getHeadersEncoded()
                 urls.append(mediaurl.mediaurl(filename,self.DOWNLOAD_LINK+filename+'&hd', 'Transcode Stream HD', self.CACHE_TYPE_STREAM_HD, 1))

        response.close()

        mediaURLs = []
        mediaURLs.append(mediaurl.mediaurl('https://dl.firedrive.com/?alias='+filename+'&key', 'Audio Stream', self.CACHE_TYPE_STREAM, 2))
        mediaURLs.append(mediaurl.mediaurl('https://dl.firedrive.com/?alias='+filename, 'Original (non-Stream)', self.CACHE_TYPE_ORIGINAL, 3))

        return mediaURLs


    ##
    # retrieve a video playback URL
    #   parameters: filename of video
    #   returns: list of media URLs
    ##
    def getVideoURL(self,filename):

#        #user requested SD quality
#        if cacheType == self.CACHE_TYPE_STREAM and videoQuality == True:
#            return self.DOWNLOAD_LINK+filename+'&stream' + '|'+self.getHeadersEncoded()
#        elif cacheType != self.CACHE_TYPE_STREAM:
#            return self.DOWNLOAD_LINK+filename+ '|'+self.getHeadersEncoded()


        url = 'http://www.firedrive.com/file/'+filename

        req = urllib2.Request(url, None, self.getHeadersList())


        # if action fails, validate login
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              req = urllib2.Request(url, None, self.getHeadersList())
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return
            else:
              xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
              return

        response_data = response.read()

        #if authorization cookie is broken, response will be empty, so log in again
        if response_data == '':
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  return
                response_data = response.read()


        mediaURLs = []
#        playbackURL = self.DOWNLOAD_LINK+filename+'&stream' + '|'+self.getHeadersEncoded()
        mediaURLs.append(mediaurl.mediaurl(self.DOWNLOAD_LINK+filename+'&stream', 'Transcode Stream SD', self.CACHE_TYPE_STREAM_SD, 2))
        mediaURLs.append(mediaurl.mediaurl(self.DOWNLOAD_LINK+filename, 'Original (non-Transcode Stream)', self.CACHE_TYPE_ORIGINAL, 3))

        # fetch video title, download URL and docid for stream link
        for r in re.finditer('(label)\: \"([^\"]+)\"' ,response_data, re.DOTALL):
             streamLabel,streamType = r.groups()
             if streamType == 'HD':
#                 playbackURL = self.DOWNLOAD_LINK+filename+'&hd' + '|'+self.getHeadersEncoded()
                 urls.append(mediaurl.mediaurl(filename,self.DOWNLOAD_LINK+filename+'&hd', 'Transcode Stream HD', self.CACHE_TYPE_STREAM_HD, 1))

        response.close()

        return mediaURLs


    ##
    # retrieve a media file
    #   parameters: title of video, whether to prompt for quality/format (optional), cache type (optional)
    ##
    def getDownload(self,filename,cacheType=0,videoQuality=False):


        url = self.DOWNLOAD_LINK+filename

        req = urllib2.Request(url, None, self.getHeadersList())

        CHUNK = 16 * 1024
        count = 0
        path = xbmcgui.Dialog().browse(0,self.addon.getLocalizedString(30026), 'files','',False,False,'')

        # if action fails, validate login
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              req = urllib2.Request(url, None, self.getHeadersList())
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return
            else:
              xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
              return

        progress = xbmcgui.DialogProgress()
        progress.create(addon.getLocalizedString(30000),addon.getLocalizedString(30035),filename,'\n')
#        (0,self.addon.getLocalizedString(30026), addon.getLocalizedString(30034),'',False,False,'')

        with open(path + 'test.mp4', 'wb') as fp:
            while True:
                progress.update(count,addon.getLocalizedString(30035),filename,'\n')
                chunk = response.read(CHUNK)
                if not chunk: break
                fp.write(chunk)
                count = count + 1



    ##
    # retrieve a video link
    #   parameters: title of video, whether to prompt for quality/format (optional), cache type (optional)
    #   returns: list of URLs for the video or single URL of video (if not prompting for quality)
    ##
    def getPublicLink(self,url,cacheType=0):


        req = urllib2.Request(url, None, self.getHeadersList())


        # if action fails, validate login
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              req = urllib2.Request(url, None, self.getHeadersList())
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return
            else:
              xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
              return

        response_data = response.read()

        #if authorization cookie is broken, response will be empty, so log in again
        if response_data == '':
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  return
                response_data = response.read()

        confirmID = 0
        # fetch video title, download URL and docid for stream link
        for r in re.finditer('name\=\"(confirm)\" value\=\"([^\"]+)"\/\>' ,response_data, re.DOTALL):
             confirmType,confirmID = r.groups()

        response.close()

        #if we need to confirm (sometimes not necessary if logged in)
        if confirmID != 0:

            values = {
                  'confirm' : confirmID,
                  }

            req = urllib2.Request(url, urllib.urlencode(values), self.getHeadersList())


            # if action fails, validate login
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                        self.login()
                        req = urllib2.Request(url,  urllib.urlencode(values), self.getHeadersList())
                        try:
                            response = urllib2.urlopen(req)
                        except urllib2.URLError, e:
                            xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                            return
              else:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
              return

            response_data = response.read()

        streamURL = 0
        # fetch video title, download URL
        for r in re.finditer('(file)\: loadURL\(\'([^\']+)' ,response_data, re.DOTALL):
             streamType,streamURL = r.groups()

        # fetch audio title, download URL
        for r in re.finditer('(mp3)\:\"([^\"]+)' ,response_data, re.DOTALL):
             streamType,streamURL = r.groups()

        # fetch title
        for r in re.finditer('\<b\>(Name\:)\<\/b\> ([^\<]+)\<br\>' ,response_data, re.DOTALL):
             nameType,title = r.groups()

        response.close()


        return (title,streamURL + '|'+self.getHeadersEncoded())


    ##
    # retrieve a list of videos, using playback type stream
    #   parameters: prompt for video quality (optional), cache type (optional)
    #   returns: list of videos
    ##
    def buildSTRM(self, path, folderID=0,savePublic=True):

        import xbmcvfs
        xbmcvfs.mkdir(path)

        # retrieve all documents
        params = urllib.urlencode({'getFiles': folderID, 'format': 'large', 'term': '', 'group':0, 'limit':1, 'user_token': self.authorization.getToken('auth_token'), '_': 1394486104901})

        url = 'http://www.firedrive.com/action/?'+ params

        videos = {}
        if True:
            req = urllib2.Request(url, None, self.getHeadersList())

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  return
              else:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return

            response_data = response.read()

            #if authorization cookie is broken, response will be empty, so log in again
            if response_data == '':
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  return
                response_data = response.read()

            # parsing page for videos
            # video-entry
            for r in re.finditer('"gal_thumb":"([^\"]+)"\,.*?type\=\'video\'.*?"file_filename":"([^\"]+)","al_title":"([^\"]+)".*?alias\=([^\"]+)"' ,response_data, re.DOTALL):
                img,filename,title,fileID = r.groups()
                img = re.sub('\\\\', '', img)
                img = 'http://static.firedrive.com/'+img


                filename = xbmc.translatePath(os.path.join(path, title+'.strm'))
                strmFile = open(filename, "w")

#                if cacheType == self.CACHE_TYPE_STREAM:
                  # streaming
#                  strmFile.write('plugin://plugin.video.firedrive?mode=streamVideo&instance='+self.instanceName+'&filename=' + fileID+'&title=' + title+'\n')
#                else:

                strmFile.write(self.PLUGIN_URL+'?mode=streamURL&url=' + self.FILE_URL+ fileID+'\n')

                strmFile.close()


            for r in re.finditer('"gal_thumb":"([^\"]+)"\,.*?type\=\'audio\'.*?"file_filename":"([^\"]+)","al_title":"([^\"]+)".*?alias\=([^\"]+)"' ,response_data, re.DOTALL):
                img,filename,title,fileID = r.groups()
                img = re.sub('\\\\', '', img)
                img = 'http://static.firedrive.com/'+img

                filename = xbmc.translatePath(os.path.join(path, title+'.strm'))
                strmFile = open(filename, "w")

                strmFile.write(self.PLUGIN_URL+'?mode=streamURL&url=' + self.FILE_URL+ fileID+'\n')
                strmFile.close()


            for r in re.finditer('"gal_thumb":"([^\"]+)"\,.*?type\=\'other\'.*?"file_filename":"([^\"]+)","al_title":"([^\"]+)".*?alias\=([^\"]+)"' ,response_data, re.DOTALL):
                img,filename,title,fileID = r.groups()
                img = re.sub('\\\\', '', img)
                img = 'http://static.firedrive.com/'+img

                filename = xbmc.translatePath(os.path.join(path, title+'.strm'))
                strmFile = open(filename, "w")

                strmFile.write(self.PLUGIN_URL+'?mode=streamURL&url=' + self.FILE_URL+ fileID+'\n')
                strmFile.close()

            response.close()

