'''
    Copyright (C) 2014 ddurdle

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

#
#
#
class account:

    ##
    ##
    def __init__(self, instanceName, username, password):
        self.instanceName = instanceName
        self.username = username
        self.password = password


    ##
    # returns whether the account has credentials (username and password) provided
    ##
    def hasCredentials(self):
        if self.username != '' and self.password != '':
            return True
        else:
            return False

