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
class authorization:

    ##
    ##
    def __init__(self):
        self.auth = {}
        self.isUpdated = False

    ##
    # Set the token of name with value provided.
    ##
    def setToken(self,name,value):
        if name in auth:
            self.isUpdated = True
        self.auth[name] = value


    ##
    # Get the token of name with value provided.
    # returns: str
    ##
    def getToken(self,name):
        return self.auth[name]

    ##
    # Get the count of authorization tokens
    # returns: int
    ##
    def getTokenCount(self):
        return len(self.auth)

