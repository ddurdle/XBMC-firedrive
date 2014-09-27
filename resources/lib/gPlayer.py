
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

import xbmc, xbmcaddon, xbmcgui, xbmcplugin

addon = xbmcaddon.Addon(id='plugin.video.firedrive')

def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), xbmc.LOGERROR)
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), xbmc.LOGDEBUG)


class gPlayer(xbmc.Player):

    try:

        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    except :
        pass

    def __init__( self, *args, **kwargs ):
        xbmc.Player.__init__( self )
        self.isExit = 0

    def setContent(self, episodes):
        self.content = episodes
        self.current = 0

    def next(self):

                self.play(self.content[self.current])

                if self.current < len(self.content)-1:
                    self.current += 1
                else:
                    self.current = 0


    def PlayStream(self, url):
        self.play(url)

    def onPlayBackStarted(self):
        print "PLAYBACK STARTED"
        print self.getPlayingFile()

    def onPlayBackEnded(self):
        print "PLAYBACK ENDED"
        self.next()

    def onQueueNextItem(self):
        print "PLAYBACK ENDED"
        self.next()

    def onPlayBackStopped(self):
        print "PLAYBACK STOPPED"
        self.isExit = 1
        if self.isExit == 0:
            print "don't exit"

    def onPlayBackPaused(self):
        print "PLAYBACK Paused"

