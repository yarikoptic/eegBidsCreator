############################################################################# 
## Event is a package that defines common interface to treat events
############################################################################# 
## Copyright (c) 2018-2019, University of Liège
## Author: Nikita Beliy
## Owner: Liege University https://www.uliege.be
## Version: 0.74
## Maintainer: Nikita Beliy
## Email: Nikita.Beliy@uliege.be
## Status: developpement
############################################################################# 
## This file is part of eegBidsCreator                                     
## eegBidsCreator is free software: you can redistribute it and/or modify     
## it under the terms of the GNU General Public License as published by     
## the Free Software Foundation, either version 2 of the License, or     
## (at your option) any later version.      
## eegBidsCreator is distributed in the hope that it will be useful,     
## but WITHOUT ANY WARRANTY; without even the implied warranty of     
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     
## GNU General Public License for more details.      
## You should have received a copy of the GNU General Public License     
## along with eegBidsCreator.  If not, see <https://www.gnu.org/licenses/>.
############################################################################


from datetime import datetime
from DataStructure.BIDS.BIDS import BIDSfieldLibrary


def ReplaceInField(In_string, Void="", ToReplace=None):
    if not isinstance(In_string, str) or not isinstance(Void, str):
        raise TypeError("ReplaceInField: In_string and Void must be a string")
    if ToReplace is not None:
        if not isinstance(ToReplace, tuple)\
           or len(ToReplace) != 2\
           or not isinstance(ToReplace[0], str)\
           or not isinstance(ToReplace[1], str):
            raise TypeError("ReplaceInField: "
                            "ToReplace must be either None or (str,str)")
    if In_string == "" :
        return Void
    if ToReplace is not None:
        return In_string.replace(ToReplace[0], ToReplace[1])
    return In_string


class GenEvent(object):
    """An intendent virtual class serving as parent to other,
    format specific event classes"""
    __base_slots__ = [
            "_name", "_time", "_duration", 
            "_channels", "_baseEvent",
            "BIDSvalues"]

    BIDSfields = BIDSfieldLibrary()

    __slots__ = __base_slots__

    def __copy__(self, source):
        if not isinstance(source, GenEvent):
            raise TypeError("Source object must be a daughter of " 
                            + self.__class__.__name__)
        for f in self.__base_slots__:
            setattr(self, f, getattr(source, f))
        self._baseEvent = source

    def __init__(self, Name="", Time=datetime.min, Duration=0):
        super(GenEvent, self).__init__()
        self._name = Name
        self._time = Time
        self._duration = Duration
        self._channels = []
        self._baseEvent = self
        self.BIDSvalues = dict()

    def SetName(self, Name):
        if not isinstance(Name, str):
            raise TypeError("Name must be a string")
        self._name = Name

    def SetTime(self, Time=None, Duration=None):
        if Time is None:
            Time = self._time
        if Duration is None:
            Duration = self._duration
        if not (isinstance(Duration, int) or isinstance(Duration, float)):
            raise TypeError("Duration must be a number")
        if not isinstance(Time, datetime):
            raise TypeError("Time must be a datetime object")
        self._time = Time
        self._duration = Duration

    def GetName(self, Void="", ToReplace=None):
        return ReplaceInField(self._name, Void, ToReplace)

    def GetTime(self):
        return self._time

    def GetDuration(self):
        return self._duration

    def GetOffset(self, Time):
        if not isinstance(Time, datetime):
            raise TypeError("Time must be a datetime object")
        return (self._time - Time).total_seconds()

    def AddChannel(self, Id):
        if isinstance(Id, list):
            for ref in Id:
                self.AddChannel(ref)
        elif Id not in self._channels:
            self._channels.append(Id)

    def GetChannels(self):
        return self._channels

    def GetChannelsSize(self):
        return len(self._channels)

    def RemoveChannel(self, Id=None):
        if Id is None:
            self._channels = []
        if isinstance(Id, list):
            for ref in Id:
                self.RemoveChannel(ref)
        elif Id in self._channels:
            self._channels.remove(ref)

    def __eq__(self, other):
        if type(other) != type(self):
            raise TypeError("Comparaison arguments must be of the same class")
        if self._time == other._time\
           and self._name == other._name\
           and self._duration == other._duration : 
            return True
        else:
            return False

    def __lt__(self, other):
        if type(other) != type(self):
            raise TypeError("Comparaison arguments must be of the same class")
        if self._time != other._time:
            return self._time < other._time
        if self._name != other._name:
            return self._name < other._name
        if self._duration != other._duration:
            return self._duration < other._duration
        return False

    def __gt__(self, other):
        if type(other) != type(self):
            raise TypeError("Comparaison arguments must be of the same class")
        if self._time != other._time:
            return self._time > other._time
        if self._name != other._name:
            return self._name > other._name
        if self._duration != other._duration:
            return self._duration > other._duration
        return False

    def __ge__(self, other):
        return (self > other or self == other)

    def __le__(self, other):
        return (self < other or self == other)
