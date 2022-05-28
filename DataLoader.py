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
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
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
#            self.iface.removePluginVectorMenu(
#                self.tr(u'Load spectral data'),
#                action)
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
            self.dlg.pbLoadData.setEnabled(False)
            self.dlg.cbMapLayer.currentIndexChanged.connect(self.enablesave)
        # show the dialog
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
        dose for detector 1, floating point number
        dose for detector 2, floating point number
        spectre for detector 1, string consiting of a comma separated list of integers 
        spectre for detector 2, string consiting of a comma separated list of integers
        height above ground, floating point number
        pressure, floating point number
        temperature, floating point number
        line number, integer e.g. to show when the measurements should be used

        The values can all be strings in the call to insertpoints, but they need to be parseable as the above mentioned
        data types.
        
        Unknown data kan be represented by an empty string or None. These will both be stored as NULL.

        For each datapoint, call self.insertpoint(lat,lon, array)
        
        lat and lon is assumed to be be in WGS84. The point will be reprojected to whatever CRS is used in the layer it is being stored to
        
        The function should set self.read to the number of lines that have been read successfully and self.readfailure to the number of lines that have had problems
        
        The reader function can throw an execption that will stop the reading and will print
        to the python console. Any data that have been read successfully befor the expection will stay stored.
        """
    
        
        self.mission=self.dlg.leMission.text()
        self.vl=self.dlg.cbMapLayer.currentLayer()
        layer=self.iface.activeLayer()
        idx=layer.fields().indexFromName('id')
        self.maxid=max(0,layer.maximumValue(idx))
        print(self.maxid)
        self.pr = self.vl.dataProvider()
        self.filename=self.dlg.FileWidget.filePath()
        self.database="MEM"
        self.autoid=False
        # May be set to PG to use postgresql's native array storage 
        fromCRS=QgsCoordinateReferenceSystem("EPSG:4326")
        # The coordinate system the data to be imported are stored in
        #TODO: User selectable source CRS 
        toCRS= self.vl.crs()
        print(fromCRS)
        print(toCRS)
        self.transformation = QgsCoordinateTransform(fromCRS, toCRS, QgsProject.instance())
        try:
            self.read=0
            self.readfailure=0
            #TODO: Other file reading functions - eg. based on file name
            # To import other type of files, define some logic to recognice them here and 
            # write a reader function that calls self.insertpoints as defined above
            if self.filename.endswith('.csv'):
                self.readRSI(self.filename)
            elif self.filename.endswith('.spe'):
                self.readspe(self.filename)
            else:
                raise unknownFileType()
            # Refreshes canvas and clears dialog to make it clear that the data have been imported
            self.iface.mapCanvas().refreshAllLayers()
            self.dlg.leMission.clear()
            self.dlg.FileWidget.setFilePath("")
            if self.readfailure==0:
                message="{} points from file imported sucessfully to '{}'".format(self.read,self.vl.name())
                level=Qgis.Success   
            else:
                message="Problem reading {} points - ({} read successfully)".format(self.readfailure,self.read)
                level=Qgis.Warning
            self.iface.messageBar().pushMessage("Data Loader", message, level=level)
        except unknownFileType as e:
            self.iface.messageBar().pushMessage("Data Loader", "Unknown file type '{}'".format(self.filename), level=Qgis.Critical)
        except Exception as e:
            print(e)
            self.iface.messageBar().pushMessage("Data Loader", "Problem when importing '{}'".format(self.filename), level=Qgis.Critical)
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
        
    def readspe(self,filename):
        """
        Reads a directory with spe-files
        Select one file within the directory - all will be read
        """
        directory=os.path.split(filename)[0]
        files=os.listdir(directory)
        spefiles=list(filter(lambda x: x.endswith('.spe'), files))
        spefiles.sort()
        print(spefiles)
        readspec=False
        readGPS=False
        
        for filename in spefiles:
            spectre=[]
            gpsdata=dict()
            dose = 0
            temperature = 0
            encoding = self.checkencoding(directory+'/'+filename)
            #encoding = 'utf-16'
            if encoding is None:
                encoding = 'latin-1'
            print(encoding)
            with open(directory+'/'+filename, "r",encoding=encoding) as f:
                print(f"reading {filename}")
                for line in f:
                    if readspec:
                        if not line.startswith('$'):
                            spectre.append(line.strip())
                            continue
                        else:
                            readspec=False
                            spectre=self.lst2arr(spectre)
                    if readGPS:
                        # print('Reading GPS')
                        if not line.startswith('$'):
                            parts=line.split('=')
                            gpsdata[parts[0]]=parts[1].strip()
                            continue
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
            try:
                insdata=[float(gpsdata['Alt']),date,float(dose),'',spectre,'',2,'', float(temperature), '']
                #print(f"insdata;{insdata}")
                self.insertpoint(float(gpsdata['Lat']),float(gpsdata['Lon']),insdata)
                print(f'{filename} OK')
            except:
                print(f'No valid data found in {filename}!')
            
    def readRSI(self,filename):
        """
        Reads a csv file exported from RSI's radassist. The file has a two line header.
        It is assumed 1024ch spectra
        """
        chnum=1024
        fs={'lat':9,
            'lon':8,
            'gpsalt':10,
            'acqtime':1,
            'dose1':14,
            'dose2':28,
            'laseralt':24,
            'radaralt':23,
            'press':22,
            'temp':21,
            'line':11}
        fs['alt']=fs['laseralt']
        #TODO: User selectable field mapping
        header=True
        idxs=[]
        with open(self.filename, "r",encoding='latin-1') as f:
            for idx,line in enumerate(f):
                data=(line.split(',')) 
                if(header):
                    # RSI export CSV has a two line header. Need to fetch some information from it to be able to 
                    # read the spectre in a sensible way
                    if idx ==1:
                        matching = [s for s in data if "Spectrum VD" in s]
                        print(matching)
                        get_indexes = lambda x, xs: [i for (y, i) in zip(xs, range(len(xs))) if x in y]
                        idxs=get_indexes("Spectrum VD",data)
                    header = idx<2
                else:
                    vd1=self.lst2arr(data[idxs[0]:idxs[0]+chnum])
                    vd2=self.lst2arr(data[idxs[1]:idxs[1]+chnum])
                    # TODO: Make a timestamp from the epoch number
                    
                    insdata=[data[10],data[1],data[14],data[28],vd1,vd2,data[24],data[22],data[21],data[11]]
                    #print(insdata)
                    self.insertpoint(data[fs['lat']],data[fs['lon']],insdata)
                
    def insertpoint(self,lat,lon,insdata):
        """
        Inserts a newly defined point into the selected layer
        """
        # print(insdata)
        try:
            floats=[0,2,3,6,7,8]
            for f in floats:
                if insdata[f] == '' or insdata[f] is None:
                    insdata[f] = None
                else:
                    insdata[f] = float(insdata[f])
            ints=[9]
            for i in ints:
                if insdata[i] == '' or insdata[f]==None:
                    insdata[i]==None
                else:
                    insdata[i]=int(insdata[i])
                
            insdata.append(self.filename)
            insdata.append(self.mission)
            
            fet = QgsFeature()
            point=QgsPointXY(float(lon),float(lat))
            prpoint=self.transformation.transform(point)
            geom=QgsGeometry.fromPointXY(prpoint)
            fet.setGeometry(geom)
            self.maxid+=1
            insdata.insert(0,self.maxid)
            insdata=[x if x !='' else None for x in insdata]
            fet.setAttributes(insdata)
            self.pr.addFeatures( [ fet ] )
            self.read+=1
        except Exception as e:
            self.readfailure+=1
            print(e)

    def createlayer(self):
        """
        Creates a new layer designed for storage of imported data
        
        """
        layername="Spectral data"
        mission=self.dlg.leMission.text()
        if mission > '':
            layername="{} ({})".format(layername,mission)
        # Uses the project to set a crs for the layer
        # TODO: Show a reminder if project == EPSG3246, that this may not be what one wants
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
                        QgsField("acqtime",  QVariant.String),
                        QgsField("dose1", QVariant.Double),
                        QgsField("dose2", QVariant.Double),
                        QgsField("spectre1", QVariant.String),
                        QgsField("spectre2", QVariant.String),
                        QgsField("altitude", QVariant.Double),
                        QgsField("pressure", QVariant.Double),
                        QgsField("temperature", QVariant.Double),
                        QgsField("linenumber", QVariant.Int),
                        QgsField("filename", QVariant.String),
                        QgsField("mission", QVariant.String)] )

        # Commit changes - is this needed?
        vl.commitChanges()
        # To display the new layer in the project
        QgsProject.instance().addMapLayer(vl)
        # Set the new layer as the default layer to import data into
        self.dlg.cbMapLayer.setLayer(vl)
