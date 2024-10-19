
# Reference Distribution keeps track of how many np are in the polymer brush.
import numpy as np

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

    def calculate_ball_Vol_percentage(self,radius, h):
        scale = 4.0/3.0* np.pi * radius * radius * radius
        volume = np.pi*h*h/3.0*(3.0*radius - h)
        return volume/scale

    def update_distribution(self, _val, radius):
        #look at the passed z value and determine if NP is in brush
        if _val <= self.ReferenceValue:
            #in the brush
            if _val < self.ReferenceValue - radius:
                #completely in brush
                self.Distribution[0] += 1
            else:
                #partially in brush
                #cap is in solvent
                h = _val + radius - self.ReferenceValue
                cap_vol = self.calculate_ball_Vol_percentage(radius, h)
                self.Distribution[1] += cap_vol
                self.Distribution[0] += 1 - cap_vol

        else:
            #in the solvent
            if _val > self.ReferenceValue + radius:
                #totally in the solvent
                self.Distribution[1] += 1
            else:
                #cap in brush
                h = radius - ( _val - self.ReferenceValue)
                cap_vol = self.calculate_ball_Vol_percentage(radius, h)
                self.Distribution[0] += cap_vol
                self.Distribution[1] += 1 - cap_vol



