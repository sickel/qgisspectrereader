from qgis.core import *
from qgis.gui import *


@qgsfunction(args='auto', group='Gamma')
def lowportion(arrayfield, splitch,feature, parent):
    """
    <h2>Description</h2>
    Calculates the portion of a spectre that is below a given channel
    
    lowportion=sum(spectre below splitchannel)/sum(total spectre)
    
    Since the last channel is used in RSI spectre to store the cosmic count, this channel 
    is removed from the spectra before calculation. 
    
    A split channel of 480 gives a typical MMGC in a 1024 ch spectra.
    
    <h2>Example usage:</h2>
    <ul>
      <li>lowpart(field,splitchannel) -> float</li>
    </ul>
    
    """
    spec=arrayfield
    if isinstance(spec, str):
        spec=spec.split(',')
    del spec[-1] # Cosmic in RSI-spectre
    spec = list(map(float, spec)) 
    low=sum(spec[0:splitch])
    high=sum(spec[splitch:])
    return low/(high+low)


@qgsfunction(args='auto', group='Gamma')
def extractchannels(arrayfield, fromch, toch, feature, parent):
    """
    <h2>Description</h2>
    Extracts a set of channels from a spectre
    
    extract=sum(spectre[fromch:toch])
    
    fromch needs to be less than toch
    
    Since the last channel is used in RSI spectre to store the cosmic count, this channel 
    is removed from the spectra before calculation. 
    
    
    
    <h2>Example usage:</h2>
    <ul>
      <li>extractchannels(field,fromch,toch) -> integer</li>
    </ul>
    
    """
    spec=arrayfield
    if isinstance(spec, str):
        spec=spec.split(',')
    del spec[-1] # Cosmic in RSI-spectre
    spec = list(map(float, spec)) # Converts in case
    extract = sum(spec[fromch:toch])
    return extract




@qgsfunction(args='auto', group='Gamma')
def extractpeak(arrayfield, fromch, toch, borderch, feature, parent):
    """
    <h2>Description</h2>
    Extracts a peak above background from a spectre
    
    extract=sum(spectre[fromch:toch])
    
    fromch needs to be less than toch
    
    Since the last channel is used in RSI spectre to store the cosmic count, this channel 
    is removed from the spectra before calculation. 
    
    Borderch is the number of channels on each side of the peak used to calculate the background, typically 5.
    
    <h2>Example usage:</h2>
    <ul>
      <li>extractpeak(field,fromch,toch,borderch) -> integer</li>
    </ul>
    
    """
    spec=arrayfield
    if isinstance(spec, str):
        spec=spec.split(',')
    del spec[-1] # Cosmic in RSI-spectre
    spec = list(map(float, spec)) # Converts in case
    leftside = sum(spec[fromch-borderch:fromch])/borderch
    rightside = sum(spec[toch:toch+borderch])/borderch
    peakwidth = toch - fromch
    deltach = (leftside - rightside) / peakwidth
    peak = spec[fromch:toch]
    for i in range(0,peakwidth):
        peak[i] = peak[i]*deltach*i+1
    return sum(peak)

@qgsfunction(args='auto', group='Gamma')
def gmm_total(arrayfield,feature,parent):
    """
    <h2>Description</h2>
    Calculates the sum of all channels for a spectre.
    <h2>Example usage:</h2>
    <ul>
    <li>gmm_total(<arrayfield>) -> integer</li>
    
    """
    removelast = 1
    spec=arrayfield
    if isinstance(spec, str):
        spec=spec.split(',')
    if removelast > 0:
        del spec[-1*removelast] # Cosmic in RSI-spectre
    spec = list(map(float, spec)) 
    return(sum(spec))