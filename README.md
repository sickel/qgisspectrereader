# qgisspectrereader
Loads spectral data into a layer. Possible to create a customised layer. To be used to import a set of geolocated spe files in a directory or csv-files exported from RSI radassist. The RSI csv files has a three line header and several fields that are to be collected for the spectre field, so it can not be imported using the normal csv-import function.
The plugin will read up to two spectra for each row in a RSI-file. 

The spectra can be displayed using the plugin Spectre Viewer.

Usage
The mission field can be left blank. The text will be used to name a new layer and will be added to the name of any new layer. 

The plugin will also install some new functions to do calculations on spectra for the field calculator. All these functions can be found in the group Gamma
