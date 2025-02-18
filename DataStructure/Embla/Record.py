############################################################################# 
## Record contains all nessesary routines to read Embla meta-data
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


from DataStructure.Generic.Record import Record
import olefile
import glob
import logging
import xml.etree.ElementTree as ElementTree
from datetime import datetime

from Parcel.parcel import Parcel
from DataStructure.Generic.Event import GenEvent
from DataStructure.Embla.Channel import EmbChannel

Logger = logging.getLogger(__name__)


class EmbRecord(Record):

    def __init__(self):
        super(EmbRecord, self).__init__()
        self._extList = [".ebm",".ead",".esedb",".ewp",".esrc",".esev"]

    def _loadMetadata(self):
        """
        ovveride function
        loads metadata from imput files and performs preliminary checks. 
        Input path must be defined

        Raises
        ------
        FileNotFoundError
            if file Recording.esrc not found
        ValueError
            if input path is not defined
        """
        if len(glob.glob(self.GetInputPath('Recording.esrc'))) != 1:
            raise FileNotFoundError("Couldn't find Recording.escr file, "
                                    "needed for recording proprieties")
        if len(glob.glob(self.GetInputPath('*.esedb'))) == 0:
            Logger.warning("No .esedb files containing events found. "
                           "Event list will be empty.")

        # Reading metadata
        esrc = olefile.OleFileIO(self.GetInputPath('Recording.esrc'))\
            .openstream('RecordingXML')
        xml = esrc.read().decode("utf_16_le")[2:-1]
        metadata = self.ParceRecording(xml)

        birth = datetime.min
        if "DateOfBirth" in metadata["PatientInfo"]:
            birth = metadata["PatientInfo"]["DateOfBirth"]
        self.SetSubject(id=metadata["PatientInfo"]["ID"],
                        name="",
                        birth=birth,
                        gender=metadata["PatientInfo"]["Gender"],
                        notes=metadata["PatientInfo"]["Notes"],
                        height=metadata["PatientInfo"]["Height"],
                        weight=metadata["PatientInfo"]["Weight"])
        self.SetId(subject=metadata["PatientInfo"]["ID"])
        self.SetDevice(type=metadata["Device"]["DeviceTypeID"],
                       id=metadata["Device"]["DeviceID"],
                       name=metadata["Device"]["DeviceName"],
                       manufactor="RemLogic")
        self.SetStartTime(metadata["RecordingInfo"]["StartTime"],
                          metadata["RecordingInfo"]["StopTime"])
        esrc.close()

    def _readChannels(self, name=None):
        if name is None:
            name = "*"
        return [EmbChannel(c) for c in 
                glob.glob(self.GetInputPath(name + ".ebm"))]

    def _readEvents(self):
        events = list()
        for evfile in glob.glob(self.GetInputPath("*.esedb")):
            esedb = olefile.OleFileIO(evfile)\
                    .openstream('Event Store/Events')
            root = Parcel(esedb)
            evs = root.get("Events")
            aux_l = root.getlist("Aux Data")[0]
            grp_l = root.getlist("Event Types")[0].getlist()
            times = root.getlist("EventsStartTimes")[0]
            locat = root.get("Locations", 0)

            for ev,time in zip(evs, times):
                ch_id = locat.getlist("Location")[ev.LocationIdx]\
                        .get("Signaltype").get("MainType")
                ch_id += "_" + locat.getlist("Location")[ev.LocationIdx]\
                         .get("Signaltype").get("SubType")

                try:
                    name = grp_l[ev.GroupTypeIdx]
                except LookupError:
                    try:
                        name = aux_l.get("Aux", ev.AuxDataID)\
                               .get("Sub Classification History")\
                               .get("1").get("type")
                    except Exception:
                        Logger.warning(
                                "Can't get event name for index {}"
                                .format(ev.AuxDataID))
                        name = ""
                evnt = GenEvent(Name=name, Time=time, Duration=ev.TimeSpan)
                evnt.AddChannel(ch_id)
                events.append(evnt)
        return events

    @staticmethod
    def _isValidInput(inputPath):
        """
        an ovveride function thats checks if a folder in inputPath is
        a valid input for a subclass

        Parameters
        ----------
        inputPath : str
            path to input folder

        Returns
        -------
        bool
            true if input is valid for given subclass
        """
        ebm = len(glob.glob(inputPath + '/*.ebm'))
        if ebm > 0:
            Logger.info("Detected Embla format")
            return True
        else:
            return False

    @staticmethod
    def ParceRecording(xml):
        root = ElementTree.fromstring(xml)
        return EmbRecord.addDict(root)

    @staticmethod
    def addDict(parent):
        d = dict()
        for child in parent:
            data = child.get('{urn:schemas-microsoft-com:datatypes}dt', None)
            if data is not None :
                del child.attrib['{urn:schemas-microsoft-com:datatypes}dt']
                try:
                    if child.text is None:
                        d[child.tag] = None
                    else:
                        if data == 'string':
                            d[child.tag] = child.text
                        elif data == 'datetime':
                            d[child.tag] = datetime.strptime(
                                    child.text, 
                                    "%Y-%m-%dT%H:%M:%S.%f")
                        elif data == 'r8':
                            d[child.tag] = float(child.text)
                        elif data == 'i2' or data == 'i4':
                            d[child.tag] = int(child.text)
                        else :
                            raise Exception("Unown type {}".format(data))
                except Exception as e:
                    print(e)
                    d[child.tag] = child.text
                d.update(parent.attrib)
            else : 
                d[child.tag] = EmbRecord.addDict(child)
        d.update(parent.attrib)
        return d
