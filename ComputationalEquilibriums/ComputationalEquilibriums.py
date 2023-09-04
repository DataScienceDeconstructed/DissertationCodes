
# Reference Distribution keeps track of how many np are in the polymer brush.

class ReferenceDistribution():

    #Type = None
    #ReferenceValue = None
    #Distribution = None # distribution [# np in brush, # np in solvent]
    
    def __init__(self, _type="Binary", _reference=0.0, _dist=[0,0]):
        #sets values to defaults. All distributions are Binary right now (np either in the brush or not), references
        # start at 0, and will be updated on first update_reference, distribution starts are 0,0 because we don't yet 
        # know where the NPs are. 
        self.Type = _type # type of distribution
        self.ReferenceValue = _reference # height of the polymer brush
        self.Distribution = _dist # distribution [# np in brush, # np in solvent]

    def update_reference(self, _val):
        # update the brush height
        self.ReferenceValue = _val

    def update_distribution(self, _val):
        #look at the passed z value and determine if it is below the brush height (in the brush) or above the brush 
        # height in the solvent
        if _val <= self.ReferenceValue:
            self.Distribution[0] += 1
        else:
            self.Distribution[1] += 1



