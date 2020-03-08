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
