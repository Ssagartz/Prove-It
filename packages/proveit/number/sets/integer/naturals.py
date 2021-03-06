from proveit import USE_DEFAULTS
from proveit.logic import Membership
from proveit.number.sets.number_set import NumberSet

class NaturalsSet(NumberSet):
    def __init__(self):
        NumberSet.__init__(self, 'Naturals', r'\mathbb{N}', context=__file__)
    
    def membershipObject(self, element):
        return NaturalsMembership(element)
    
    def deduceMemberLowerBound(self, member):
        from ._theorems_ import naturalsLowerBound
        return naturalsLowerBound.specialize({n:member})  

class NaturalsPosSet(NumberSet):
    def __init__(self):
        NumberSet.__init__(self, 'NaturalsPos', r'\mathbb{N}^+', context=__file__)
    
    def membershipObject(self, element):
        return NaturalsPosMembership(element)
    
    def deduceMemberLowerBound(self, member):
        from ._theorems_ import naturalsPosLowerBound
        return naturalsPosLowerBound.specialize({n:member})  

class NaturalsMembership(Membership):
    '''
    Defines methods that apply to membership in an enumerated set. 
    '''
    
    def __init__(self, element):
        Membership.__init__(self, element)

    def conclude(self, assumptions=USE_DEFAULTS):
        '''
        Attempt to conclude that the element is in the set of Naturals.
        '''   
        element = self.element
        if hasattr(element, 'deduceInNaturals'):
            return element.deduceInNaturals()

    def sideEffects(self, knownTruth):
        return
        yield

class NaturalsPosMembership(Membership):
    '''
    Defines methods that apply to membership in an enumerated set. 
    '''
    
    def __init__(self, element):
        Membership.__init__(self, element)

    def conclude(self, assumptions=USE_DEFAULTS):
        '''
        Attempt to conclude that the element is in the set of Naturals.
        '''   
        element = self.element
        if hasattr(element, 'deduceInNaturalsPos'):
            return element.deduceInNaturalsPos()

    def sideEffects(self, knownTruth):
        return
        yield

try:
    # Import some fundamental axioms and theorems without quantifiers.
    # Fails before running the _axioms_ and _theorems_ notebooks for the first time, but fine after that.
    from ._theorems_ import natsPosInNats, natsInInts, natsPosInInts
except:
    pass
