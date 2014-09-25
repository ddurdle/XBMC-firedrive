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

from resources.lib import firedrive
from resources.lib import gPlayer
from resources.lib import tvWindow

import sys
import urllib
import cgi
import re

import xbmc, xbmcgui, xbmcplugin, xbmcaddon


#helper methods
def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGERROR)
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGDEBUG)

def parse_query(query):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q

def addVideo(url, infolabels, label, img='', fanart='', total_items=0,
                   cm=[], cm_replace=False):
    infolabels = decode_dict(infolabels)
    log('adding video: %s - %s' % (infolabels['title'], url))
    listitem = xbmcgui.ListItem(label, iconImage=img,
                                thumbnailImage=img)
    listitem.setInfo('video', infolabels)
    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('fanart_image', fanart)
    cm=[]
    cleanURL = re.sub('---', '', url)
    cleanURL = re.sub('&', '---', cleanURL)
    cm.append(( addon.getLocalizedString(30042), 'XBMC.RunPlugin(plugin://plugin.video.firedrive?mode=buildstrm&title='+infolabels['title']+'&streamurl='+cleanURL+')', ))
#    listitem.addContextMenuItems( commands )
    if cm:
        listitem.addContextMenuItems(cm, cm_replace)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=total_items)

def addDirectory(url, title, img='', fanart='', total_items=0, folderID='', instanceName=''):
    log('adding dir: %s - %s' % (title, url))
    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
    if not fanart:
        fanart = addon.getAddonInfo('path') + '/fanart.jpg'

    if folderID != '' and 0:
        cm=[]
        cm.append(( addon.getLocalizedString(30042), 'XBMC.RunPlugin(plugin://plugin.video.firedrive?mode=buildstrm&title='+title+'&instanceName='+str(instanceName)+'&folderID='+str(folderID)+')', ))
        listitem.addContextMenuItems(cm, False)

    listitem.setProperty('fanart_image', fanart)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=True, totalItems=total_items)

#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

def decode(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def decode_dict(data):
    for k, v in data.items():
        if type(v) is str or type(v) is unicode:
            data[k] = decode(v)
    return data


def numberOfAccounts(accountType):

    count = 1
    max_count = int(addon.getSetting(accountType+'_numaccounts'))
    actualCount = 0
    while True:
        try:
            if addon.getSetting(accountType+str(count)+'_username') != '':
                actualCount = actualCount + 1
        except:
            break
        if count == max_count:
            break
        count = count + 1
    return actualCount


#global variables
PLUGIN_URL = sys.argv[0]
plugin_handle = int(sys.argv[1])
plugin_queries = parse_query(sys.argv[2][1:])

addon = xbmcaddon.Addon(id='plugin.video.firedrive')

#debugging
try:

    remote_debugger = addon.getSetting('remote_debugger')
    remote_debugger_host = addon.getSetting('remote_debugger_host')

    # append pydev remote debugger
    if remote_debugger == 'true':
        # Make pydev debugger works for auto reload.
        # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace(remote_debugger_host, stdoutToServer=True, stderrToServer=True)
except ImportError:
    log(addon.getLocalizedString(30016), True)
    sys.exit(1)
except :
    pass


# retrieve settings
user_agent = addon.getSetting('user_agent')



mode = plugin_queries['mode']

# make mode case-insensitive
mode = mode.lower()


log('plugin url: ' + PLUGIN_URL)
log('plugin queries: ' + str(plugin_queries))
log('plugin handle: ' + str(plugin_handle))

if mode == 'main':
    addDirectory(PLUGIN_URL+'?mode=options','<<'+addon.getLocalizedString(30043)+'>>')

#dump a list of videos available to play
if mode == 'main' or mode == 'folder':
    log(mode)

    folderID=0
    if (mode == 'folder'):
        folderID = plugin_queries['folderID']


    try:
      cacheType = (int)(addon.getSetting('playback_type'))
    except:
      cacheType = 0


    instanceName = ''
    try:
        instanceName = plugin_queries['instance']
    except:
        pass

    numberOfAccounts = numberOfAccounts('firedrive')

    # show list of services
    if numberOfAccounts > 1 and instanceName == '':
        count = 1
        max_count = int(addon.getSetting('firedrive_numaccounts'))
        while True:
            instanceName = 'firedrive'+str(count)
            try:
                username = addon.getSetting(instanceName+'_username')
                if username != '':
                    addDirectory('plugin://plugin.video.firedrive?mode=main&instance='+instanceName,username)
            except:
                break
            if count == max_count:
                break
            count = count + 1

    else:
        # show index of accounts
        if instanceName == '' and numberOfAccounts == 1:

                count = 1
                max_count = int(addon.getSetting('firedrive_numaccounts'))
                while True:
                    instanceName = 'firedrive'+str(count)
                    try:
                        username = addon.getSetting(instanceName+'_username')
                        if username != '':
                            password  = addon.getSetting(instanceName+'_password')
                            auth_token = addon.getSetting(instanceName+'_auth_token')
                            auth_cookie = addon.getSetting(instanceName+'_auth_cookie')

                            # you need to have at least a username&password set or an authorization token
                            if ((username == '' or password == '') and auth_token == ''):
                                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                                log(addon.getLocalizedString(30015), True)
                                xbmcplugin.endOfDirectory(plugin_handle)

                            #let's log in
                            firedrive = firedrive.firedrive(PLUGIN_URL,instanceName, username, password, auth_token, auth_cookie, user_agent)

                    except:
                        break

                    if count == max_count:
                        break
                    count = count + 1

        # no accounts defined
        elif numberOfAccounts == 0:

            #legacy account conversion
            try:
                username = addon.getSetting('username')
                if username != '':
                    password  = addon.getSetting('password')
                    auth_token = addon.getSetting('auth_token')
                    auth_cookie = addon.getSetting('auth_cookie')
                    addon.setSetting('firedrive1_username', username)
                    addon.setSetting('firedrive1_password', password)
                    addon.setSetting('firedrive1_auth_token', auth_token)
                    addon.setSetting('firedrive1_auth_cookie', auth_cookie)
                else:
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                    log(addon.getLocalizedString(30015), True)
                    xbmcplugin.endOfDirectory(plugin_handle)
            except :
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                    log(addon.getLocalizedString(30015), True)
                    xbmcplugin.endOfDirectory(plugin_handle)
            #let's log in
            firedrive = firedrive.firedrive(PLUGIN_URL,instanceName, username, password, auth_token, auth_cookie, user_agent)


        # show entries of a single account (such as folder)
        elif instanceName != '':

                    username = addon.getSetting(instanceName+'_username')
                    password  = addon.getSetting(instanceName+'_password')
                    auth_token = addon.getSetting(instanceName+'_auth_token')
                    auth_cookie = addon.getSetting(instanceName+'_auth_cookie')

                    # you need to have at least a username&password set or an authorization token
                    if ((username == '' or password == '') and auth_token == ''):
                        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                        log(addon.getLocalizedString(30015), True)
                        xbmcplugin.endOfDirectory(plugin_handle)

                    #let's log in
                    firedrive = firedrive.firedrive(PLUGIN_URL,instanceName, username, password, auth_token, auth_cookie, user_agent)



        videos = firedrive.getVideosList(folderID,cacheType)

        folders = firedrive.getFolderList(folderID)
        if folders:
            for title in sorted(folders.iterkeys()):
                addDirectory(folders[title],title,folderID=folderID,instanceName=firedrive.instanceName)

#        videos = firedrive.getVideosList(folderID)
        if videos:
            for title in sorted(videos.iterkeys()):
                addVideo(videos[title]['url'],
                             { 'title' : title , 'plot' : title }, title,
                             img=videos[title]['thumbnail'])

        firedrive.updateAuthorization(addon)

#play a URL that is passed in (presumely requires authorizated session)
elif mode == 'play2':
    try:
      url = plugin_queries['url']
    except:
      url = 0

    try:
      instanceName = plugin_queries['instance']
    except:
      instanceName = 'firedrive1'

    try:
            username = addon.getSetting(instanceName+'_username')
            password = addon.getSetting(instanceName+'_password')
            auth_token = addon.getSetting(instanceName+'_auth_token')
            auth_cookie = addon.getSetting(instanceName+'_auth_cookie')

            firedrive = firedrive.firedrive(PLUGIN_URL,instanceName, username, password, auth_token, auth_cookie, user_agent)

    except :
            pass


    episodes = []
    # immediately play resulting (is a video)
    (title,videoURL) = firedrive.getPublicLink(url)
    episodes.append(videoURL)
    player = gPlayer.gPlayer()
    player.setContent(episodes)

    #item = xbmcgui.ListItem(path=videoURL)
    #log('play url: ' + videoURL)
    #item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
    #xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

    while 1:
        player.next()
        xbmc.sleep(1000)

#    w = tvWindow.tvWindow("tvWindow.xml",addon.getAddonInfo('path'),"Default")
#    w.setPlayer(player)
#    w.doModal()

#    item = xbmcgui.ListItem(path=videoURL)
#    log('play url: ' + videoURL)
#    item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
#    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
#    player.PlayStream(videoURL)

#    player.next()



    firedrive.updateAuthorization(addon)




#play a URL that is passed in (presumely requires authorizated session)
elif mode == 'play':
    url = plugin_queries['url']

    item = xbmcgui.ListItem(path=url)
    log('play url: ' + url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

#play a video given its exact-title
elif mode == 'playvideo':
    filename = plugin_queries['filename']

    # no need to select stream type

    try:
      title = plugin_queries['title']
    except:
      title = filename


    try:
      instanceName = plugin_queries['instance']
    except:
      instanceName = 'firedrive1'

    try:
            username = addon.getSetting(instanceName+'_username')
            password = addon.getSetting(instanceName+'_password')
            auth_token = addon.getSetting(instanceName+'_auth_token')
            auth_cookie = addon.getSetting(instanceName+'_auth_cookie')

            # you need to have at least a username&password set or an authorization token
            if ((not mode == 'streamurl') and ((username == '' or password == '') and auth_token == '')):
                        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                        log(addon.getLocalizedString(30015), True)
                        xbmcplugin.endOfDirectory(plugin_handle)


            firedrive = firedrive.firedrive(PLUGIN_URL,instanceName, username, password, auth_token, auth_cookie, user_agent)

    except :
            pass

    videoURL = firedrive.getVideoLink(filename,0,False)

    item = xbmcgui.ListItem(path=videoURL)
    log('play url: ' + videoURL)
    item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

    firedrive.updateAuthorization(addon)



#force stream - play a video given its exact-title
elif mode == 'streamvideo':
    try:
      filename = plugin_queries['filename']
    except:
      filename = ''

    try:
      title = plugin_queries['title']
    except:
      title = filename


    force_sd = addon.getSetting('force_sd')

    if force_sd == 'true':
        force_sd = True
    else:
        force_sd = False

    try:
        quality = plugin_queries['quality']
        if (quality == 'SD'):
            force_sd = True
    except :
        pass

    try:
      instanceName = plugin_queries['instance']
    except:
      instanceName = 'firedrive1'

    try:
            username = addon.getSetting(instanceName+'_username')
            password = addon.getSetting(instanceName+'_password')
            auth_token = addon.getSetting(instanceName+'_auth_token')
            auth_cookie = addon.getSetting(instanceName+'_auth_cookie')

            # you need to have at least a username&password set or an authorization token
            if ((not mode == 'streamurl') and ((username == '' or password == '') and auth_token == '')):
                        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                        log(addon.getLocalizedString(30015), True)
                        xbmcplugin.endOfDirectory(plugin_handle)


            firedrive = firedrive.firedrive(PLUGIN_URL,instanceName, username, password, auth_token, auth_cookie, user_agent)

    except :
            pass

    # immediately play resulting (is a video)
    videoURL = firedrive.getVideoLink(filename, firedrive.CACHE_TYPE_STREAM, force_sd)
    item = xbmcgui.ListItem(path=videoURL)
    log('play url: ' + videoURL)
    item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


    firedrive.updateAuthorization(addon)




#force stream - play a video given its exact-title
elif mode == 'streamaudio' or mode == 'playaudio':
    try:
      filename = plugin_queries['filename']
    except:
      filename = ''

    try:
      title = plugin_queries['title']
    except:
      title = filename


    try:
      instanceName = plugin_queries['instance']
    except:
      instanceName = 'firedrive1'

    try:
            username = addon.getSetting(instanceName+'_username')
            password = addon.getSetting(instanceName+'_password')
            auth_token = addon.getSetting(instanceName+'_auth_token')
            auth_cookie = addon.getSetting(instanceName+'_auth_cookie')

            # you need to have at least a username&password set or an authorization token
            if ((username == '' or password == '') and auth_token == ''):
                        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                        log(addon.getLocalizedString(30015), True)
                        xbmcplugin.endOfDirectory(plugin_handle)


            firedrive = firedrive.firedrive(PLUGIN_URL,instanceName, username, password, auth_token, auth_cookie, user_agent)

    except :
            pass

    # immediately play resulting (is a video)
    videoURL = firedrive.getAudioLink(filename)
    item = xbmcgui.ListItem(path=videoURL)
    log('play url: ' + videoURL)
    item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


    firedrive.updateAuthorization(addon)





elif mode == 'streamurl':
    try:
      url = plugin_queries['url']
    except:
      url = 0

    try:
      instanceName = plugin_queries['instance']
    except:
      instanceName = 'firedrive1'

    try:
            username = addon.getSetting(instanceName+'_username')
            password = addon.getSetting(instanceName+'_password')
            auth_token = addon.getSetting(instanceName+'_auth_token')
            auth_cookie = addon.getSetting(instanceName+'_auth_cookie')

            firedrive = firedrive.firedrive(PLUGIN_URL,instanceName, username, password, auth_token, auth_cookie, user_agent)

    except :
            pass

    # immediately play resulting (is a video)
    (title,videoURL) = firedrive.getPublicLink(url)
    item = xbmcgui.ListItem(path=videoURL)
    log('play url: ' + videoURL)
    item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


    firedrive.updateAuthorization(addon)



#create strm files
elif mode == 'buildstrm':


    try:
        path = addon.getSetting('path')
    except:
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')

    if path == '':
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')

    if path != '':
        returnPrompt = xbmcgui.Dialog().yesno(addon.getLocalizedString(30000), addon.getLocalizedString(30027) + '\n'+path +  '?')


    if path != '' and returnPrompt:

        try:
            url = plugin_queries['streamurl']
            title = plugin_queries['title']
            url = re.sub('---', '&', url)
        except:
            url=''

        if url != '':

                import os

                filename = xbmc.translatePath(os.path.join(path, title+'.strm'))
                strmFile = open(filename, "w")

                strmFile.write(url+'\n')
                strmFile.close()

        else:

            try:
                folderID = plugin_queries['folderID']
                title = plugin_queries['title']
                instanceName = plugin_queries['instanceName']
            except:
                folderID = ''



            if folderID != '':

                    try:
                        username = addon.getSetting(instanceName+'_username')
                        if username != '':

                            try:
                                username = addon.getSetting(instanceName+'_username')
                                password = addon.getSetting(instanceName+'_password')
                                auth_token = addon.getSetting(instanceName+'_auth_token')
                                auth_cookie = addon.getSetting(instanceName+'_auth_cookie')

                                firedrive = firedrive.firedrive(PLUGIN_URL,instanceName, username, password, auth_token, auth_cookie, user_agent)
                            except :
                                pass

                            savePublic = True
                            firedrive.buildSTRM(path+'/'+title + '/',folderID,savePublic)

                    except:
                        pass

            else:

                numberOfAccounts = numberOfAccounts('firedrive')

                count = 1
                max_count = int(addon.getSetting('firedrive_numaccounts'))
                while True:
                    instanceName = 'firedrive'+str(count)
                    try:
                        username = addon.getSetting(instanceName+'_username')
                        if username != '':

                            try:
                                username = addon.getSetting(instanceName+'_username')
                                password = addon.getSetting(instanceName+'_password')
                                auth_token = addon.getSetting(instanceName+'_auth_token')
                                auth_cookie = addon.getSetting(instanceName+'_auth_cookie')

                                firedrive = firedrive.firedrive(PLUGIN_URL,instanceName, username, password, auth_token, auth_cookie, user_agent)
                            except :
                                pass

                            savePublic = True
                            firedrive.buildSTRM(path+username,0,savePublic)

                            folders = firedrive.getFolderIDList(0)
                            if folders:
                                for title in folders.iterkeys():
                                    firedrive.buildSTRM(path+username+'/'+title + '/',folders[title],savePublic)

                    except:
                        break
                    if count == max_count:
                        break
                    count = count + 1


        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30028))


#clear the authorization token
elif mode == 'clearauth':

    instanceName = ''
    try:
        instanceName = plugin_queries['instance']
    except:
        pass

    numberOfAccounts = numberOfAccounts('firedrive')

    # clear all accounts
    if numberOfAccounts >= 1 and instanceName == '':
        count = 1
        max_count = int(addon.getSetting('firedrive_numaccounts'))
        while True:
            instanceName = 'firedrive'+str(count)
            try:
                addon.setSetting(instanceName + '_auth_token', '')
                addon.setSetting(instanceName + '_auth_cookie', '')
            except:
                break
            if count == max_count:
                break
            count = count + 1

    elif instanceName != '':

            try:
                addon.setSetting(instanceName + '_auth_token', '')
                addon.setSetting(instanceName + '_auth_cookie', '')
            except:
                pass

    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30023))

if mode == 'options' or mode == 'buildstrm' or mode == 'clearauth':
    addDirectory('plugin://plugin.video.firedrive?mode=clearauth','<<'+addon.getLocalizedString(30018)+'>>')
    addDirectory('plugin://plugin.video.firedrive?mode=buildstrm','<<'+addon.getLocalizedString(30025)+'>>')



xbmcplugin.endOfDirectory(plugin_handle)

