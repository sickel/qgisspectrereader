# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DataLoader
                                 A QGIS plugin
 Loads spectral data
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-02-02
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Morten Sickel
        email                : morten@sickel.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .DataLoader_dialog import DataLoaderDialog
import os.path

from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject, QgsMapLayerProxyModel, QgsCoordinateTransform, QgsCoordinateReferenceSystem

from qgis.core import Qgis

from qgis.gui import QgsFileWidget

from PyQt5.QtCore import *
#from PyQt.QtGui import QFileDialog
from qgis.core import QgsExpression
from datetime import date,time,datetime

import xml.etree.ElementTree as ET

class unknownFileType(Exception):
    pass


class DataLoader:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DataLoader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Spectral data')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DataLoader', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag = True,
        add_to_menu = True,
        add_to_toolbar = True,
        status_tip = None,
        whats_this = None,
        parent = None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/DataLoader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Load spectral data'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True
        from .lowportion import lowportion

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'Spectral data'),
                action)
            self.iface.removeToolBarIcon(action)
        QgsExpression.unregisterFunction("$lowportion")

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = DataLoaderDialog(parent=self.iface.mainWindow())
            # This makes the dialog modal
            self.dlg.pbLoadData.clicked.connect(self.selectfile)
            self.dlg.pbNewLayer.clicked.connect(self.createlayer)
            self.dlg.pbClose.clicked.connect(self.closedlg)
            self.dlg.cbMapLayer.setFilters(QgsMapLayerProxyModel.PointLayer)
            self.dlg.cbMapLayer.setShowCrs(True)
            self.dlg.cbMapLayer.currentIndexChanged.connect(self.enablesave)
            
        # show the dialog
        if self.dlg.cbMapLayer.currentLayer() == None:
            self.dlg.pbLoadData.setEnabled(False)
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
        
    def enablesave(self):
        self.dlg.pbLoadData.setEnabled(True)
            
    def closedlg(self):
        self.dlg.hide()

    
    def lst2arr(self,alist):
        """ Makes a comma separated string. If postgres is used, the string is formatted to be inserted as
        a native array"""
        ret=','.join(alist)
        if self.database=="PG":
            ret='{' + ret + '}'
        return(ret)

    def selectfile(self):
                        
        """
        Selects and stores data from a file or set of files
        
        
        To write a parser for another file format: The parser should read the file or files to be imported, 
        then for each measurement populate an array with the following data:
        
        altitude, floating point number (above sea level, e.g. gps altitude) - 
        sampling time, string (any format, but it should preferably be consistent)
        height above ground1, floating point number, e.g. radar or laster altitude
        height above ground2, floating point number, e.g. radar or laster altitude
        pressure, floating point number
        temperature, floating point number
        line number, integer e.g. line number in a flight pattern
        utcdate: Date for data collection
        detcount1: Numbers of detector elements in detector 1, integer
        livetime1: Livetime for detector 1, float
        dose for detector 1, floating point number
        detcount2: Numbers of detector elements in detector 2, integer
        livetime2: Livetime for detector 2, float
        dose for detector 2, floating point number
        spectre for detector 1, string consiting of a comma separated list of integers 
        spectre for detector 2, string consiting of a comma separated list of integers
        timestamp: timestamp, string
        
        The values can all be strings in the call to insertpoints, but they need to be parseable as the above mentioned data types.
        
        Unknown data kan be represented by an empty string or None. These will both be stored as NULL.

        For each datapoint, call self.insertpoint(lat,lon, array,[filename])
        
        lat and lon is assumed to be be in WGS84. The point will be reprojected to whatever CRS is used in the layer it is being stored to
        
        The filename is by default the selected filename. For data types where each spectre is stored in a separate file, the filename for each file can be given.
        The function should set self.read to the number of lines that have been read successfully and self.readfailure to the number of lines that have had problems
        
        The reader function can throw an execption that will stop the reading and will print
        to the python console. Any data that have been read successfully befor the expection will stay stored.
        """
    
        
        self.mission=self.dlg.leMission.text()
        self.vl=self.dlg.cbMapLayer.currentLayer()
        layer=self.iface.activeLayer()
        idx=layer.fields().indexFromName('id')
        try:
            self.maxid=max(0,layer.maximumValue(idx))
        except TypeError:
            self.maxid = 0
        # print(self.maxid)
        self.pr = self.vl.dataProvider()
        self.filename=self.dlg.FileWidget.filePath()
        self.database="MEM"
        # May be set to PG to use postgresql's native array storage 
        self.autoid=False
        fromCRS=QgsCoordinateReferenceSystem("EPSG:4326")
        # The coordinate system the data to be imported are stored in
        #TODO: User selectable source CRS 
        # Is it possible with a dropdown with known CRSs?
        # or to call QGIS CRS selection dialog?
        toCRS= self.vl.crs()
        # The CRS of the vl is set to the same as the project when the vl is created
        
        self.transformation = QgsCoordinateTransform(fromCRS, toCRS, QgsProject.instance())
        try:
            self.read=0
            self.readfailure=0
            #TODO: Other file reading functions - eg. based on file name
            # TODO: Hourglass cursor while reading data.
            # Progressbar? QprogressBar
            # https://gis.stackexchange.com/questions/110524/qgis-processing-progress
            # To import other type of files, define some logic to recognice them here and 
            # write a reader function that calls self.insertpoints as defined above
            if self.filename.endswith('.csv'):
                self.readRSI(self.filename)
            elif self.filename.endswith('.spe'):
                self.readspe(self.filename)
            elif self.filename.endswith('.n42') or self.filename.endswith('.xml'):
                self.readn42(self.filename)
            else:
                raise unknownFileType()
            # Refreshes canvas and clears dialog to make it clear that the data have been imported
            self.iface.mapCanvas().refreshAllLayers()
            self.dlg.leMission.clear()
            self.dlg.FileWidget.setFilePath("")
            if self.readfailure==0:
                message=f"{self.read} points from file imported sucessfully to '{self.vl.name()}'"
                level=Qgis.Success   
            else:
                message=f"Problem reading {self.readfailure} points - ({self.read} read successfully)"
                level=Qgis.Warning
            self.iface.messageBar().pushMessage("Data Loader", message, level=level)
        except unknownFileType as e:
            self.iface.messageBar().pushMessage("Data Loader", f"Unknown file type '{self.filename}'", level=Qgis.Critical)
        except Exception as e:
            print(e)
            self.iface.messageBar().pushMessage("Data Loader", f"Problem when importing '{self.filename}'", level=Qgis.Critical)
            raise(e)
    
    def checkencoding(self,filename):
        with open(filename, "rb") as file:
            beginning = file.read(4)
            # The order of these if-statements is important
            # otherwise UTF32 LE may be detected as UTF16 LE as well
            if beginning == b'\x00\x00\xfe\xff':
                encoding="utf-32 be"
            elif beginning == b'\xff\xfe\x00\x00':
                encoding="utf-32 le"
            elif beginning[0:3] == b'\xef\xbb\xbf':
                encoding="utf-8"
            elif beginning[0:2] == b'\xff\xfe':
                encoding="utf-16"
            elif beginning[0:2] == b'\xfe\xff':
                encoding="uft-16 be"
            else:
                encoding=None
        return(encoding)
    
    def readn42(self,filename):
        base = '{http://physics.nist.gov/N42/2011/N42}'
        tree = ET.parse(filename)
        root = tree.getroot()
        print("parsed OK")
        for measurement in root.findall(f'{base}RadMeasurement'):
        #for measurement in root:
            spectrum = None 
            print("New measurement")
            print(measurement.tag , measurement.attrib, measurement.text)
            for detail in measurement:
                if detail.tag.endswith('Spectrum'):
                    for specdet in detail:
                        print(specdet.tag, specdet.attrib)
                        if specdet.tag.endswith('Channeldata'):
                            print('Found spec!!!')
                            spectrum = specdet.text
                print(detail.tag, detail.attrib, detail.text)
            print(spectrum)
        print("Finished")

        
    def readspe(self,filename):
        """
        Reads a directory with spe-files
        Select one file within the directory - all will be read
        
        DONE: Important - rewrite to insert in new data format
        DONE: Test with new data format
        
        """
        directory=os.path.split(filename)[0]
        files=os.listdir(directory)
        spefiles=list(filter(lambda x: x.endswith('.spe'), files))
        spefiles.sort()
        print(spefiles)
        
        for filename in spefiles:
            try:
                insdata,gpsdata = self.parsespefile(filename,directory)
                # print(f"insdata;{insdata}")
                self.insertpoint(float(gpsdata['Lat']),float(gpsdata['Lon']),insdata,directory+'/'+filename)
                # print(f'{filename} OK')
            except Exception as e:
                print(e) 
                print(f'Problems reading {filename}!')

    def parsespefile(self, filename,directory):
        spectre=[]
        gpsdata=dict()
        dose = 0
        temperature = 0
        encoding = self.checkencoding(directory+'/'+filename)
        #encoding = 'utf-16'
        if encoding is None:
            encoding = 'latin-1'
        # print(encoding)
        readspec=False
        readGPS=False
        with open(directory+'/'+filename, "r",encoding=encoding) as f:
            # print(f"reading {filename}")
            for line in f:
                line = line.strip()
                if readspec:
                    if not line.startswith('$'):
                        spectre.append(line)
                        continue
                    else:
                        readspec=False
                        spectre=self.lst2arr(spectre)
                if readGPS:
                    print('Reading GPS')
                    print(line)
                    if not line.startswith('$'):
                        parts=line.split('=')
                        print(parts)
                        print(gpsdata)
                        gpsdata[parts[0]]=parts[1].strip()
                        continue
                    else:
                        readGPS = False
                readGPS = line.startswith('$GPS:')
                if line.startswith('$DATE_MEA:'):
                    date=f.readline()
                    continue
                if line.startswith('$DATA'):
                    readspec=True
                    #print(line)
                    nlines=f.readline()
                    #print(nlines)
                    nlines=nlines.split()[1].strip()
                if line.startswith('$DOSE_RATE:'):
                    dose=f.readline().strip()
                if line.startswith('$TEMPERATURE:'):
                    temperature=f.readline().strip()
        insdata=[float(gpsdata['Alt']), date, 2, 2, None, float(temperature), None, date, 1, None, dose, None, None, None, spectre, None, date]
        return insdata,gpsdata
    
    
    def readRSI(self,filename):
        """
        Reads a csv file exported from RSI's radassist. The file has a three line header.
        It is assumed 1024ch spectra
        """
        chnum=1024
        # TODO: Calculate chnum from the header.
        # Maximum number of detectors to read in
        maxdets = 2
        # General info to look for
        colnames = ['Lat', 'Long', 'Alt[m]', 'UtcTime', 'Laser_Alt [M]', 'RAD_ALT [M]', 'Pres', 'Temp', 'LineNum','UtcDate']
        # Detector specific data:
        perdetector = ['DetCount','LiveTime','Doserate'] # ,'PPT_PRES','PPT_TEMP']
        #TODO: User selectable field mapping - will it still be needed?
        header = True
        fields = {}
        vdidxs = []
        roiidxs = []
        timestampwarned = False
        self.readfailure = 0
        useUTCtime = self.dlg.cBUTC.isChecked()
        with open(self.filename, "r",encoding='latin-1') as f:
            for idx,line in enumerate(f):
                data=(line.split(',')) 
                if(header):
                    # RSI exported CSV has a three line header. 
                    # Need to fetch some information from it to find fields
                    if idx == 0:
                        # First line is always empty
                        pass
                    if idx == 1:
                        header1 = data
                        get_indexes = lambda x, xs: [i for (y, i) in zip(xs, range(len(xs))) if x in y]
                        #Must find data for each detector
                        # Looking for where VD spectra start
                        vdidxs=get_indexes("Spectrum VD",data)
                        # Looking for where ROIdata starts
                        # Roidata contains per detector information 
                        # such as livetime, detector count and dose rate
                        roiidxs = get_indexes("ROI for Virtual Detector",data)
                    if idx == 2:
                        # May need this later on, or maybe not?
                        header2 = data
                        # 2nd line, some general data, some are repeated per VD
                        # Find columns for general data
                        for col in colnames:
                            if col in data:
                                fields[col] = data.index(col)
                            else:
                                fields[col] = None
                        # Looking through the data for each ROI
                        for ridx,roi in enumerate(roiidxs):
                            col = roi
                            while data[col] != '':
                                if data[col] in perdetector and ridx < maxdets:
                                    fields[f"{data[col]}{ridx+1}"]=col
                                col+= 1
                        # Pressure and temperature may be stored as per detector data
                        if fields['Pres'] is None and 'PPT_PRES [mbar]' in data:
                            fields['Pres'] = data.index('PPT_PRES [mbar]')
                        if fields['Temp'] is None and 'PPT_TEMP [°C]' in data:
                            fields['Temp'] = data.index('PPT_TEMP [°C]')
                        print(f'fields:{fields}')
                        lonfield = fields.pop('Long')
                        latfield = fields.pop('Lat')
                    # To go on with real data after the three lines of header
                    header = idx<2
                    # Lat and lon are treated differently than the other fields
                    
                else:
                    lat = data[latfield]
                    lon = data[lonfield]
                    if lat == 0 and lon == 0:
                        # Assumes no gpsdata, bad luck if someone is collecting data at this point...
                        self.readfailure+=1
                        continue
                    # Reading in one or two spectra
                    # The RSI file may contain more spectra, the are ignored for the time being
                    # TODO: Look into reading more spectra from RSI-file
                    # Possible solution: Make a file with data from one detector, mark detector number
                    # per line, filter on detector number. On the other hand, this will make a mess if 
                    # the data are not correctly filtered.
                    # Another solution: make separate data sets for the different detectors
                    vd1 = self.lst2arr(data[vdidxs[0]:vdidxs[0]+chnum])
                    if len(vdidxs) > 1:
                        vd2 = self.lst2arr(data[vdidxs[1]:vdidxs[1]+chnum])
                    else:
                        vd2 = None
                    try:
                        epoch = int(data[fields['UtcTime']])
                        if useUTCtime:
                            timestamp = datetime.utcfromtimestamp( epoch ).isoformat()
                        else:
                            timestamp = datetime.fromtimestamp( epoch ).isoformat()
                        # Timestamp may either be epoch is secounds or hh:mnm:ss ...
                    except ValueError:
                        # The utctime is not a number. Probably h:m:s
                        if not timestampwarned:
                            message = "Timestamp not as epoch time, assuming today UTC"
                            level = Qgis.Warning
                            self.iface.messageBar().pushMessage("Data Loader", message, level=level)
                            timestampwarned = True
                        (h,m,s) = data[fields['UtcTime']].split(':')
                        epoch = int(datetime.combine(date.today(),time(int(h),int(m),int(s))).timestamp())
                        timestamp = data[fields['UtcTime']]
                        data[fields['UtcTime']] = epoch
                        if not fields['UtcDate'] is None:
                            timestamp = f"{data[fields['UtcDate']]}T{timestamp}"
                    # position data need some special treatment and shall not end up in fields
                    insdata = []
                    for field in fields:
                        if fields[field] is None or data[fields[field]] == '':
                            insdata.append(None)
                        else:
                            insdata.append(data[fields[field]])
                    # Adds on the spectra       
                    insdata.append(vd1)
                    insdata.append(vd2)
                    insdata.append(timestamp)
                    try:
                        self.insertpoint(lat,lon,insdata)
                    except Exception as e:
                        self.readfailure+=1
                        print(e)
                        print(insdata)
                        # This will abort the import after the first failure.
                        # TODO: Make this user selectable
                        # TODO: Log errors to file
                        return()
                
    def insertpoint(self,lat,lon,insdata,filename = None):
        """
        Inserts a newly defined point into the selected layer. 
        
        Filename may be set . Makes most sense for data types where each spectrum is in a separate file.
        
        Exceptions here should be handled by the caller
        """
        if filename is None:
            filename = self.filename
        # Functions to use to convert the data before inserting
        # The keys are the variant typeNames in the table
        # TODO: Go back and check if things still works with postgres backend
        converts = {'integer': int, 'double': float,'string':str}
        # Putting in the last data:
        self.maxid+=1
        insdata.insert(0,self.maxid)    
        insdata.append(filename)
        insdata.append(self.mission)
        # Setting the right data type:
        insdata=[x if x !='' else None for x in insdata]
        for i in range(0,len(insdata)):
            if insdata[i] is None:
                continue
                # Leave Nones as they are
            insdata[i] = converts[self.pr.fields()[i].typeName()](insdata[i])
            # Data are coming in as strings.
            # TODO: Make a custom exception so it is possible to fail out with more information
        feature = QgsFeature()
        point=QgsPointXY(float(lon),float(lat))
        # TODO: Could / should this be a 3d point?
        # Transforms the point to the right CRS
        prpoint=self.transformation.transform(point)
        geom=QgsGeometry.fromPointXY(prpoint)
        feature.setGeometry(geom)
        # Any empty string should be null value
        feature.setAttributes(insdata)
        # The feature to be added is set up, time to add it to the data set
        self.pr.addFeatures( [ feature ] )
        self.read+=1


    def createlayer(self):
        """
        Creates a new layer designed for storage of imported data
        
        """
        layername = "Spectral data"
        mission = self.dlg.leMission.text()
        if mission > '':
            layername = f"{layername} ({mission})"
        # Uses the project to set a crs for the layer
        # TODO: Show a reminder if project == EPSG3246, that this may not be what one wants
        # TODO: Drop down to select CRS
        CRS= QgsProject.instance().crs()
        vl = QgsVectorLayer("Point", layername, "memory",crs=CRS)
        pr = vl.dataProvider()
        # Enter editing mode
        vl.startEditing()
        # is this needed?
        # add fields
        pr.addAttributes( [
                    QgsField("id",QVariant.Int),
                    QgsField("gpsaltitude", QVariant.Double),
                    QgsField("utctime",  QVariant.String),
                    QgsField("laseraltitude", QVariant.Double),
                    QgsField("radaraltitude", QVariant.Double), 
                    QgsField("pressure", QVariant.Double),
                    QgsField("temperature", QVariant.Double),
                    QgsField("linenumber", QVariant.Int),
                    QgsField("utcdate", QVariant.String),
                    QgsField("detcount1",QVariant.Int),
                    QgsField("livetime1",QVariant.Double),
                    QgsField("doserate1", QVariant.Double),
                    QgsField("detcount2",QVariant.Int),
                    QgsField("livetime2",QVariant.Double),
                    QgsField("doserate2", QVariant.Double),
                    QgsField("spectre1", QVariant.String),
                    QgsField("spectre2", QVariant.String),
                    QgsField("timestamp", QVariant.String),
                    QgsField("filename", QVariant.String),
                    QgsField("mission", QVariant.String)
                    ])
        # filename and mission should be kept as the two last fields 
        # as they will be added on later
        # when the data is collected
        # Commit changes - is this needed?
        vl.commitChanges()
        # To display the new layer in the project
        QgsProject.instance().addMapLayer(vl)
        # Set the new layer as the default layer to import data into
        self.dlg.cbMapLayer.setLayer(vl)
