from proveit.expression import Expression, Literal, LATEX, Operation
from proveit.multiExpression import Etcetera, ExpressionList
from proveit.common import a, b
from proveit.basiclogic import Forall, In, NotEquals, AssociativeOperation

pkg = __package__

Z   = Literal(pkg,'Z',{LATEX:r'\mathbb{Z}'})
Zp  = Literal(pkg,'Z^+',{LATEX:r'\mathbb{Z}^+'})
R   = Literal(pkg,'R',{LATEX:r'\mathbb{R}'})
zeroToOne = Literal(pkg,'zeroToOne',{LATEX:r'[0,1]'})

Reals = Literal(pkg,'Reals',{LATEX:r'\mathbb{R}'})
RealsPos = Literal(pkg,'RealsPos',{LATEX:r'\mathbb{R}^+'})
Integers = Literal(pkg,'Integers',{LATEX:r'\mathbb{Z}'})
Naturals = Literal(pkg,'Naturals',{LATEX:r'\mathbb{N}'})
Complexes = Literal(pkg,'Complexes',{LATEX:r'\mathbb{C}'})

class NumberOp:
    def __init__(self):
        pass

    def _closureTheorem(self, numberSet):
        pass # implemented by derived class

    def _notEqZeroTheorem(self):
        pass # implemented by derived class
    
    def deduceInIntegers(self, assumptions=frozenset()):
        return deduceInNumberSet(self, Integers, assumptions)

    def deduceInNaturals(self, assumptions=frozenset()):
        return deduceInNumberSet(self, Naturals, assumptions)
        
    def deduceInReals(self, assumptions=frozenset()):
        return deduceInNumberSet(self, Reals, assumptions)

    def deduceInComplexes(self, assumptions=frozenset()):
        return deduceInNumberSet(self, Complexes, assumptions)

    def deduceNotZero(self, assumptions=frozenset()):
        return deduceNotZero(self, assumptions)

def deduceInNumberSet(exprOrList, numberSet, assumptions=frozenset(), ruledOutSets=frozenset()):
    '''
    For each given expression, attempt to derive that it is in the specified numberSet
    under the given assumptions.  If ruledOutSets is provided, don't attempt to
    derive it from being in a subset in ruledOutSets.
    If successful, returns the deduced statement, otherwise raises an Exception.   
    '''
    from proveit.number.common import ComplexesSansZero
    import integer.theorems
    import natural.theorems
    import real.theorems
    import complex.theorems
    if not isinstance(exprOrList, Expression) or isinstance(exprOrList, ExpressionList):
        # If it isn't an Expression, assume it's iterable and deduce each
        return [deduceInNumberSet(expr, numberSet=numberSet, assumptions=assumptions) for expr in exprOrList]
    # A single Expression:
    expr = exprOrList
    try:
        return In(expr, numberSet).checked(assumptions)
    except:
        pass # not so simple, keep trying (below)
        
    if Naturals not in ruledOutSets and (numberSet == Complexes or 
                                         numberSet == Reals or numberSet == Integers):
        try:
            # try deducing in the Naturals as a subset of the desired numberSet
            deduceInNumberSet(expr, Naturals, assumptions=assumptions, ruledOutSets=ruledOutSets)
            if numberSet == Complexes:
                natural.theorems.inComplexes.specialize({a:expr})
            elif numberSet == Reals:
                natural.theorems.inReals.specialize({a:expr})
            elif numberSet == Integers:
                natural.theorems.inIntegers.specialize({a:expr})
            return In(expr, numberSet).checked(assumptions)
        except:
            ruledOutSets = ruledOutSets | {Naturals} # ruled out Naturals
    if Integers not in ruledOutSets and (numberSet == Complexes or numberSet == Reals):
        try:
            # try deducing in the Integers as a subset of the desired numberSet
            deduceInNumberSet(expr, Integers, assumptions=assumptions, ruledOutSets=ruledOutSets)
            if numberSet == Complexes:
                integer.theorems.inComplexes.specialize({a:expr})
            elif numberSet == Reals:
                integer.theorems.inReals.specialize({a:expr})
            return In(expr, numberSet).checked(assumptions)
        except:
            ruledOutSets = ruledOutSets | {Integers} # ruled out Integers
    if Reals not in ruledOutSets and numberSet == Complexes:
        try:
            # try deducing in the Reals as a subset of the desired numberSet
            deduceInNumberSet(expr, Reals, assumptions=assumptions, ruledOutSets=ruledOutSets)
            if numberSet == Complexes:
                real.theorems.inComplexes.specialize({a:expr})
            return In(expr, numberSet).checked(assumptions)
        except:
            ruledOutSets = ruledOutSets | {Integers} # ruled out Reals
    
    # Couldn't deduce in a subset.  Try using a closure theorem.
    if numberSet == ComplexesSansZero:
        # special case for numberSet = Complexes - {0}
        closureThm = complex.theorems.inComplexesSansZero
        closureSpec = closureThm.specialize({a:expr})        
    else:
        if not isinstance(expr, NumberOp):
            # See of the Expression class has deduceIn[numberSet] method (as a last resort):
            if numberSet == Naturals and hasattr(expr, 'deduceInNaturals'):
                return expr.deduceInNaturals()
            elif numberSet == Integers and hasattr(expr, 'deduceInIntegers'):
                return expr.deduceInIntegers()
            elif numberSet == Reals and hasattr(expr, 'deduceInReals'):
                return expr.deduceInReals()
            elif numberSet == Complexes and hasattr(expr, 'deduceInComplexes'):
                return expr.deduceInComplexes()          
            # Ran out of options:  
            raise DeduceInNumberSetException(expr, numberSet, assumptions)
        closureThm = expr._closureTheorem(numberSet)
        if closureThm is None:
            raise DeduceInNumberSetException(expr, numberSet, assumptions)    
        # Apply the closure theorem
        assert isinstance(closureThm, Forall), 'Expecting closure theorem to be a Forall expression'
        iVars = closureThm.instanceVars
        # Specialize the closure theorem differently for AccociativeOperation compared with other cases
        if isinstance(expr, AssociativeOperation):
            assert len(iVars) == 1, 'Expecting one instance variable for the closure theorem of an AssociativeOperation'
            assert isinstance(iVars[0], Etcetera), 'Expecting the instance variables for the closure theorem of an AssociativeOperation to be an Etcetera Variable'
            closureSpec = closureThm.specialize({iVars[0]:expr.operands})
        else:
            assert len(iVars) == len(expr.operands), 'Expecting the number of instance variables for the closure theorem to be the same as the number of operands of the Expression'
            closureSpec = closureThm.specialize({iVar:operand for iVar, operand in zip(iVars, expr.operands)})
    # deduce any of the requirements for the notEqZeroThm application
    _deduceRequirements(closureThm, closureSpec, assumptions)
    try:
        return In(expr, numberSet).checked(assumptions)
    except:
        raise DeduceInNumberSetException(expr, numberSet, assumptions)

def deduceInNaturals(exprOrList, assumptions=frozenset()):
    '''
    For each given expression, attempt to derive that it is in the set of integers.
    Warnings/errors may be suppressed by setting suppressWarnings to True.
    '''
    return deduceInNumberSet(exprOrList, Naturals, assumptions=assumptions)

def deduceInIntegers(exprOrList, assumptions=frozenset()):
    '''
    For each given expression, attempt to derive that it is in the set of integers
    under the given assumptions.  If successful, returns the deduced statement,
    otherwise raises an Exception.
    '''
    return deduceInNumberSet(exprOrList, Integers, assumptions=assumptions)

def deduceInReals(exprOrList, assumptions=frozenset()):
    '''
    For each given expression, attempt to derive that it is in the set of reals
    under the given assumptions.  If successful, returns the deduced statement,
    otherwise raises an Exception.    
    '''
    return deduceInNumberSet(exprOrList, Reals, assumptions=assumptions)

def deduceInComplexes(exprOrList, assumptions=frozenset()):
    '''
    For each given expression, attempt to derive that it is in the set of complexes
    under the given assumptions.  If successful, returns the deduced statement,
    otherwise raises an Exception.  
    '''
    return deduceInNumberSet(exprOrList, Complexes, assumptions=assumptions)

def deduceNotZero(exprOrList, assumptions=frozenset()):
    '''
    For each given expression, attempt to derive that it is not equal to zero
    under the given assumptions.  If successful, returns the deduced statement,
    otherwise raises an Exception.  
    '''
    from proveit.number import num
    if not isinstance(exprOrList, Expression) or isinstance(exprOrList, ExpressionList):
        # If it isn't an Expression, assume it's iterable and deduce each
        return [deduceNotZero(expr, assumptions=assumptions) for expr in exprOrList]
    # A single Expression:
    expr = exprOrList
    try:
        return NotEquals(expr, num(0)).checked(assumptions)
    except:
        pass # not so simple

    # Try using notEqZeroTheorem
    if not isinstance(expr, NumberOp):
        # See of the Expression class has deduceNotZero method (as a last resort):
        if hasattr(expr, 'deduceNotZero'):
            return expr.deduceNotZero()
        print expr, expr.__class__
        raise DeduceNotZeroException(expr, assumptions)
    notEqZeroThm = expr._notEqZeroTheorem()
    if notEqZeroThm is None:
        raise DeduceNotZeroException(expr, assumptions)
    assert isinstance(notEqZeroThm, Forall), 'Expecting notEqZero theorem to be a Forall expression'
    iVars = notEqZeroThm.instanceVars
    # Specialize the closure theorem differently for AccociativeOperation compared with other cases
    if isinstance(expr, AssociativeOperation):
        assert len(iVars) == 1, 'Expecting one instance variables for the notEqZero theorem of an AssociativeOperation'
        assert isinstance(iVars[0], Etcetera), 'Expecting the instance variable for the notEqZero theorem of an AssociativeOperation to be an Etcetera Variable'
        notEqZeroSpec = notEqZeroThm.specialize({iVars[0]:expr.operands})
    else:
        if len(iVars) != len(expr.operands):
            raise Exception('Expecting the number of instance variables for the closure theorem to be the same as the number of operands of the Expression')
        notEqZeroSpec = notEqZeroThm.specialize({iVar:operand for iVar, operand in zip(iVars, expr.operands)})
    # deduce any of the requirements for the notEqZeroThm application
    _deduceRequirements(notEqZeroThm, notEqZeroSpec, assumptions)
    try:
        return NotEquals(expr, num(0)).checked(assumptions)
    except:
        raise DeduceNotZeroException(expr, assumptions)


def _deduceRequirements(theorem, specializedExpr, assumptions):
    # Grab the conditions for the specialized expression of the given theorem
    # and see if we need a further deductions for those requirements.
    from proveit.number import num
    for stmt, _, _, conditions in specializedExpr.statement._specializers:
        if stmt._expression == theorem:
            # check each condition and apply recursively if it is in some set                
            for condition in conditions:
                condition = condition._expression
                if isinstance(condition, In):
                    domain = condition.domain
                    elem = condition.element
                    deduceInNumberSet(elem, numberSet=domain, assumptions=assumptions)
                elif isinstance(condition, NotEquals) and condition.rhs == num(0):
                    deduceNotZero(condition.lhs, assumptions=assumptions)
    

class DeduceInNumberSetException(Exception):
    def __init__(self, expr, numberSet, assumptions):
        self.expr = expr
        self.numberSet = numberSet
        self.assumptions = assumptions
    def __str__(self):
        return 'Unable to prove ' + str(self.expr) + ' in ' + str(self.numberSet) + ' under assumptions: ' + str(self.assumptions)

class DeduceNotZeroException(Exception):
    def __init__(self, expr, assumptions):
        self.expr = expr
        self.assumptions = assumptions
    def __str__(self):
        return 'Unable to prove ' + str(self.expr) + ' not equal to zero under assumptions: ' + str(self.assumptions)
    