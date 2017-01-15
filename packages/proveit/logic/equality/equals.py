from proveit import BinaryOperation, USE_DEFAULTS, ProofFailure, tryDerivation
from proveit import Literal, Operation, Lambda
from proveit.common import A, P, X, f, x, y, z
from proveit.logic.transitivity_search import transitivitySearch
from irreducible_value import IrreducibleValue

pkg = __package__

EQUALS = Literal(pkg, '=')

class Equals(BinaryOperation):
    # map Expressions to sets of KnownTruths of equalities that involve the Expression
    # on the left hand or right hand side.
    knownEqualities = dict()

    # Subset of knownEqualities that have irreducible values on the right
    # hand side.
    evaluations = dict()
        
    def __init__(self, a, b):
        BinaryOperation.__init__(self, EQUALS, a, b)
        self.lhs = a
        self.rhs = b
        
    def deriveSideEffects(self, knownTruth):
        '''
        Record the knownTruth in Equals.knownEqualities, associated from
        the left hand side and the right hand side.  This information may
        be useful for concluding new equations via transitivity. 
        If the right hand side is an "irreducible value" (see 
        isIrreducibleValue), also record it in Equals.evaluations for use
        when the evaluate method is called.   Also derive the reversed 
        form, as a side effect.  If the right side is TRUE or FALSE, 
        `deriveViaBooleanEquality` as a side effect.
        '''
        from proveit.logic import TRUE, FALSE
        Equals.knownEqualities.setdefault(self.lhs, set()).add(knownTruth)
        Equals.knownEqualities.setdefault(self.rhs, set()).add(knownTruth)
        if isIrreducibleValue(self.rhs):
            Equals.evaluations.setdefault(self.lhs, set()).add(knownTruth)
        if (self.lhs != self.rhs):
            # automatically derive the reversed form which is equivalent
            self.deriveReversed(knownTruth.assumptions) # uses an axiom
        if self.rhs in (TRUE, FALSE):
            # automatically derive A from A=TRUE or Not(A) from A=FALSE
            tryDerivation(self.deriveViaBooleanEquality, knownTruth.assumptions)
        
    def conclude(self, assumptions):
        '''
        Use other equalities that are known to be true to try to conclude 
        this equality via transitivity.  For example, if a=b, b=c, and c=d are 
        known truths (under the given assumptions), we can conclude that a=d
        (under these assumptions).  Also, reflexive equations (x=x) are
        concluded automatically, as are x=TRUE or TRUE=x given x
        and x=FALSE or FALSE=x given Not(x).
        '''
        from proveit.logic import TRUE, FALSE
        if self.lhs==self.rhs:
            return self.concludeViaReflexivity()
        if self.lhs or self.rhs in (TRUE, FALSE):
            try:
                return self.concludeBooleanEquality(assumptions)
            except ProofFailure:
                pass
        try:
            # try to prove the equality via evaluation reduction.
            # if that is possible, it is a relatively straightforward thing to do.
            return BinaryOperation.conclude(assumptions)
        except:
            pass
        # Use a breadth-first search approach to find the shortest
        # path to get from one end-point to the other.
        return transitivitySearch(self, assumptions)
                
    @staticmethod
    def knownRelationsFromLeft(expr, assumptionsSet):
        '''
        For each KnownTruth that is an Equals involving the given expression on
        the left hand side, yield the KnownTruth and the right hand side.
        '''
        for knownTruth in Equals.knownEqualities.get(expr, frozenset()):
            if knownTruth.lhs == expr:
                if assumptionsSet.issuperset(knownTruth.assumptions):
                    yield (knownTruth, knownTruth.rhs)
    
    @staticmethod
    def knownRelationsFromRight(expr, assumptionsSet):
        '''
        For each KnownTruth that is an Equals involving the given expression on
        the right hand side, yield the KnownTruth and the left hand side.
        '''
        for knownTruth in Equals.knownEqualities.get(expr, frozenset()):
            if knownTruth.rhs == expr:
                if assumptionsSet.issuperset(knownTruth.assumptions):
                    yield (knownTruth, knownTruth.lhs)
            
    @classmethod
    def operatorOfOperation(subClass):
        return EQUALS    

    def concludeViaReflexivity(self):
        '''
        Prove and return self of the form x = x.
        '''
        from _axioms_ import equalsReflexivity
        assert self.lhs == self.rhs
        return equalsReflexivity.specialize({x:self.lhs})
            
    def deriveReversed(self, assumptions=USE_DEFAULTS):
        '''
        From x = y derive y = x.  This derivation is an automatic side-effect.
        '''
        from _axioms_ import equalsSymmetry
        return equalsSymmetry.specialize({x:self.lhs, y:self.rhs}, assumptions=assumptions)
            
    def applyTransitivity(self, otherEquality, assumptions=USE_DEFAULTS):
        '''
        From x = y (self) and y = z (otherEquality) derive and return x = z.
        Also works more generally as long as there is a common side to the equations.
        '''
        from _axioms_ import equalsTransitivity
        # We can assume that y=x will be a KnownTruth if x=y is a KnownTruth because it is derived as a side-effect.
        if self.rhs == otherEquality.lhs:
            return equalsTransitivity.specialize({x:self.lhs, y:self.rhs, z:otherEquality.rhs}, assumptions=assumptions)
        elif self.rhs == otherEquality.rhs:
            return equalsTransitivity.specialize({x:self.lhs, y:self.rhs, z:otherEquality.lhs}, assumptions=assumptions)
        elif self.lhs == otherEquality.lhs:
            return equalsTransitivity.specialize({x:self.rhs, y:self.lhs, z:otherEquality.rhs}, assumptions=assumptions)
        elif self.lhs == otherEquality.rhs:
            return equalsTransitivity.specialize({x:self.rhs, y:self.lhs, z:otherEquality.lhs}, assumptions=assumptions)
        else:
            raise TransitivityException(self, otherEquality)
        
    def deriveViaBooleanEquality(self, assumptions=USE_DEFAULTS):
        '''
        From A = TRUE derive A, or from A = FALSE derive Not(A).  This derivation
        is an automatic side-effect.
        Note, see deriveStmtEqTrue or Not.equateNegatedToFalse for the reverse process.
        '''
        from proveit.logic import TRUE, FALSE        
        from proveit.logic.boolean._axioms_ import eqTrueElim
        from proveit.logic.boolean.negation._theorems_ import notFromEqFalse
        if self.rhs == TRUE:
            return eqTrueElim.specialize({A:self.lhs}, assumptions=assumptions) # A
        elif self.rhs == FALSE:
            return notFromEqFalse.specialize({A:self.lhs}, assumptions=assumptions) # Not(A)
        
    def deriveContradiction(self, assumptions=USE_DEFAULTS):
        '''
        From A=FALSE, derive A=>FALSE.
        '''
        from proveit.logic import FALSE        
        from _theorems_ import contradictionFromFalseEquivalence, contradictionFromFalseEquivalenceReversed
        if self.rhs == FALSE:
            return contradictionFromFalseEquivalence.specialize({A:self.lhs}).deriveConclusion(assumptions)
        elif self.lhs == FALSE:
            return contradictionFromFalseEquivalenceReversed.specialize({A:self.rhs}).deriveConclusion(assumptions)
    
    def concludeBooleanEquality(self, assumptions=USE_DEFAULTS):
        '''
        Prove and return self of the form (A=TRUE) assuming A, A=FALSE assuming Not(A), [Not(A)=FALSE] assuming A.
        '''
        from proveit.logic import TRUE, FALSE, Not        
        from proveit.logic.boolean._axioms_ import eqTrueIntro
        from proveit.logic.boolean.negation._theorems_ import eqFalseFromNegation
        if self.rhs == TRUE:
            return eqTrueIntro.specialize({A:self.lhs}, assumptions=assumptions)
        elif self.rhs == FALSE:
            if isinstance(self.lhs, Not):
                return eqFalseFromNegation.specialize({A:self.lhs.operands}, assumptions=assumptions)
            else:
                return Not(self.lhs).equateNegatedToFalse(assumptions)
        elif self.lhs == TRUE or self.lhs == FALSE:
            return Equals(self.rhs, self.lhs).prove(assumptions).deriveReversed(assumptions)
        raise ProofFailure(self, assumptions, "May only conclude via boolean equality if one side of the equality is TRUE or FALSE")
    
    def deriveIsInSingleton(self, assumptions=USE_DEFAULTS):
        '''
        From (x = y), derive (x in {y}).
        '''
        from proveit.logic.set_theory._axioms_ import singletonDef
        return singletonDef.specialize({x:self.lhs, y:self.rhs}).deriveLeftViaEquivalence(assumptions)
    
    """
    def _subFn(self, fnExpr, fnArg, subbing, replacement):
        if fnArg is None:
            dummyVar = safeDummyVar(self, fnExpr)
            if isinstance(replacement, ExpressionList):
                fnArg = Etcetera(MultiVariable(dummyVar))
            elif isinstance(replacement, ExpressionTensor):
                fnArg = Block(dummyVar)
            else:
                fnArg = dummyVar
            fnExpr = fnExpr.substituted({subbing:fnArg})
            if dummyVar not in fnExpr.freeVars():
                raise Exception('Expression to be substituted is not found within the expression that the substitution is applied to.')
        return fnExpr, fnArg
    """
    
    @staticmethod
    def _lambdaExpr(lambdaMap):
        if hasattr(lambdaMap, 'lambdaMap'):
            lambdaExpr = lambdaMap.lambdaMap()
        else: lambdaExpr = lambdaMap
        if not isinstance(lambdaExpr, Lambda):
            raise TypeError('lambdaMap is expected to be a Lambda Expression or return a Lambda Expression via calling lambdaMap()')
        return lambdaExpr
    
    def substitution(self, lambdaMap, assumptions=USE_DEFAULTS):
        '''
        From x = y, and given f(x), derive f(x)=f(y).
        f(x) is provided via lambdaMap as a Lambda expression or an 
        object that returns a Lambda expression when calling lambdaMap()
        (see proveit.lambda_map, proveit.lambda_map.SubExprRepl in
        particular)
        '''
        from _axioms_ import substitution
        fxLambda = Equals._lambdaExpr(lambdaMap)
        return substitution.specialize({x:self.lhs, y:self.rhs, f:fxLambda}, assumptions=assumptions)
        
    def lhsSubstitute(self, lambdaMap, assumptions=USE_DEFAULTS):
        '''
        From x = y, and given P(y), derive P(x) assuming P(y).  
        P(x) is provided via lambdaMap as a Lambda expression or an 
        object that returns a Lambda expression when calling lambdaMap()
        (see proveit.lambda_map, proveit.lambda_map.SubExprRepl in
        particular).
        '''
        from _theorems_ import substitute
        PxLambda = Equals._lambdaExpr(lambdaMap)
        return substitute.specialize({x:self.rhs, y:self.lhs, P:PxLambda}, assumptions=assumptions)
        
    def rhsSubstitute(self, lambdaMap, assumptions=USE_DEFAULTS):
        '''
        From x = y, and given P(x), derive P(y) assuming P(x).  
        P(x) is provided via lambdaMap as a Lambda expression or an 
        object that returns a Lambda expression when calling lambdaMap()
        (see proveit.lambda_map, proveit.lambda_map.SubExprRepl in
        particular).
        '''
        from _theorems_ import substitute
        PxLambda = Equals._lambdaExpr(lambdaMap)
        return substitute.specialize({x:self.lhs, y:self.rhs, P:PxLambda}, assumptions=assumptions)
        
    def deriveRightViaEquivalence(self, assumptions=USE_DEFAULTS):
        '''
        From A = B, derive B (the Right-Hand-Side) assuming A.
        '''
        return self.rhsSubstitute(Lambda(X, X), assumptions)

    def deriveLeftViaEquivalence(self, assumptions=USE_DEFAULTS):
        '''
        From A = B, derive A (the Right-Hand-Side) assuming B.
        '''
        return self.lhsSubstitute(Lambda(X, X), assumptions)
    
    def deduceInBool(self, assumptions=USE_DEFAULTS):
        '''
        Deduce and return that this equality statement is in the set of Booleans.
        '''
        from _axioms_ import equalityInBool
        return equalityInBool.specialize({x:self.lhs, y:self.rhs})
        
    def evaluate(self, assumptions=USE_DEFAULTS):
        '''
        Given operands that may be evaluated to irreducible values that
        may be compared, or if there is a known evaluation of this
        equality, derive and return this expression equated to
        TRUE or FALSE.
        '''
        if self.lhs == self.rhs:
            # prove equality is true by reflexivity
            return evaluateTruth(self.prove().expr, assumptions=[])
        if isIrreducibleValue(self.lhs) and isIrreducibleValue(self.rhs):
            # Irreducible values must know how to evaluate the equality
            # between each other, where appropriate.
            return self.lhs.evalEquality(self.rhs)
        return BinaryOperation.evaluate(self, assumptions)

def isIrreducibleValue(expr):
    return isinstance(expr, IrreducibleValue)
    
def reduceOperands(operation, assumptions=USE_DEFAULTS):
    '''
    Attempt to return a provably equivalent expression whose operands
    are all irreducible values (IrreducibleValue objects).
    '''
    from proveit.lambda_map import globalRepl
    # Any of the operands that are not irreducible values must be replaced with their evaluation
    expr = operation
    for operand in tuple(expr.operands):
        if not isIrreducibleValue(operand):
            # the operand is not an irreducible value so it must be evaluated
            operandEval = operand.evaluate(assumptions=assumptions)
            if not isIrreducibleValue(operandEval.rhs):
                raise EvaluationError('Evaluations expected to be irreducible values')
            # substitute in the evaluated value
            expr = operandEval.substitution(globalRepl(expr, operand)).rhs
    for operand in expr.operands:
        if not isIrreducibleValue(operand):
            raise EvaluationError('All operands should be irreducible values')
    return expr

def proveViaReduction(expr, assumptions):
    '''
    Attempts to prove that the given expression is TRUE under the
    given assumptions via evaluating that the expression is equal to true.
    Returns the resulting KnownTruth if successful.
    '''
    reducedExpr = reduceOperands(expr, assumptions)
    equiv =  Equals(expr, reducedExpr).prove(assumptions)
    reducedExpr.prove(assumptions)
    return equiv.deriveLeftViaEquivalence(assumptions)
            
def defaultEvaluate(expr, assumptions=USE_DEFAULTS):
    '''
    Default attempt to evaluate the given expression under the given assumptions.
    If successful, returns a KnownTruth (using a subset of the given assumptions)
    that expresses an equality between the expression (on the left) and
    and irreducible value (see isIrreducibleValue).  Specifically, this
    method checks to see if an appropriate evaluation has already been
    proven.  If not, but if it is an Operation, call the evaluate method on
    all operands, make these substitions, then call evaluate on the expression
    with operands substituted for irreducible values.  It also treats, as a
    special case, evaluating the expression to be true if it is in the set
    of assumptions [also see KnownTruth.evaluate and evaluateTruth].
    '''
    from proveit.lambda_map import globalRepl
    from proveit import defaults
    assumptionsSet = set(defaults.checkedAssumptions(assumptions))
    # See if the expression already has a proven evaluation
    if expr in Equals.evaluations:
        for knownTruth in Equals.evaluations[expr]:
            if assumptionsSet.issuperset(knownTruth.assumptions):
                return knownTruth # found existing evaluation suitable for the assumptions
        return Equals.evaluations[expr] # found existing evaluation
    # see if the assumption is in the set of assumptions as a special case
    if expr in assumptionsSet:
        return evaluateTruth(expr, [expr]) # A=TRUE assuming A
    if not isinstance(expr, Operation):
        raise EvaluationError('Unknown evaluation: ' + str(expr))
    reducedExpr = reduceOperands(expr, assumptions)
    if reducedExpr == expr:
        raise EvaluationError('Unable to evaluate: ' + str(expr))
    evaluation = Equals(expr, reducedExpr.evaluate().rhs).prove(assumptions=assumptions)
    # store it in the evaluations dictionary for next time
    Equals.evaluations.setdefault(expr, set()).add(evaluation)
    return evaluation  

def evaluateTruth(expr, assumptions):
    '''
    Attempts to prove that the given expression equals TRUE under
    the given assumptions via proving the expression.
    Returns the resulting KnownTruth if successful.
    '''
    from proveit.logic import TRUE
    return Equals(expr, TRUE).prove(assumptions)

class EvaluationError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message
        
      
        
"""
This is obsolete (mostly) -- use proveit.lambda_map techniques instead.

def _autoSub(outcome, outerExpr, superExpr, subExpr, eqGenMethodName, eqGenMethodArgs=None, eqGenKeywordArgs=None, criteria=None, subExprClass=None, suppressWarnings=False):
    if eqGenMethodArgs is None: eqGenMethodArgs = []
    if eqGenKeywordArgs is None: eqGenKeywordArgs = dict()
    meetsCriteria = (subExprClass is None or isinstance(subExpr, subExprClass)) and \
        (criteria is None or criteria(subExpr))
    if meetsCriteria and hasattr(subExpr, eqGenMethodName):
        generatedEquality = None
        try:
            generatedEquality = getattr(subExpr, eqGenMethodName)(*eqGenMethodArgs, **eqGenKeywordArgs)
        except Exception as e:
            if not suppressWarnings:
                print "Warning, failure in autosub attempt when applying '" + eqGenMethodName + "' method to " + str(subExpr) + ":"
                print e
                print "Continuing on"
            
        if generatedEquality is not None and isinstance(generatedEquality, Equals) and (generatedEquality.lhs == subExpr or generatedEquality.rhs == subExpr):
            if superExpr == outerExpr:
                # substitute all occurences
                fnExpr, fnArgs = outerExpr, None 
            else:
                # substitute only occurences within superExpr
                subbing = generatedEquality.lhs if generatedEquality.lhs == subExpr else generatedEquality.rhs
                replacement = generatedEquality.rhs if generatedEquality.lhs == subExpr else generatedEquality.lhs
                fnExpr, fnArgs = generatedEquality._subFn(superExpr, None, subbing, replacement)
                fnExpr = outerExpr.substituted({superExpr:fnExpr})
            if outcome == 'substitution':
                return generatedEquality.substitution(fnExpr, fnArgs)
            elif generatedEquality.lhs == subExpr:
                if outcome == 'substitute':
                    return generatedEquality.rhsSubstitute(fnExpr, fnArgs)
                elif outcome == 'statement_substitution':
                    return generatedEquality.rhsStatementSubstitute(fnExpr, fnArgs)
            elif generatedEquality.rhs == subExpr:
                if outcome == 'substitute':
                    return generatedEquality.lhsSubstitute(fnExpr, fnArgs)
                elif outcome == 'statement_substitution':
                    return generatedEquality.lhsStatementSubstitute(fnExpr, fnArgs)
    for subExpr in subExpr.subExprGen():
        result = _autoSub(outcome, outerExpr, superExpr, subExpr, eqGenMethodName, eqGenMethodArgs, eqGenKeywordArgs, criteria, subExprClass, suppressWarnings)
        if result is not None: return result
    return None            
    
def autoSubstitute(expr, eqGenMethodName, eqGenMethodArgs=None, eqGenKeywordArgs=None, criteria=None, subExprClass=None, superExpr=None, suppressWarnings = False):
    '''
    From a given expr = P(x), derives and returns some P(y) via some x=y that is generated by
    calling a method of the name eqGenMethodName on one of its sub-expressions.  eqGenMethodArgs
    and eqGenKeywordArgs may be a list of arguments and/or a dictionary of keyword arguments
    respectively to pass on to the eqGenMethodName method.  If provided, criteria, subExprClass,
    and superExpr will force selectivity in choosing the sub-expression to generate x=y.
    Specificially the sub-expression must be a sub-expression of superExpr (if provided)
    beyond being a sub-expression of expr, it must be an instance of subExprClass (if provided), 
    and the criteria method (if provide) must return true when passed in the sub-expression.
    If superExpr is provided, replacements are only made within superExpr.
    '''
    if superExpr is None: superExpr = expr
    return _autoSub('substitute', expr, superExpr, superExpr, eqGenMethodName, eqGenMethodArgs, eqGenKeywordArgs, criteria, subExprClass, suppressWarnings)

def autoSubstitution(expr, eqGenMethodName, eqGenMethodArgs=None, eqGenKeywordArgs=None, criteria=None, subExprClass=None, superExpr=None, suppressWarnings = False):
    '''
    From a given expr = f(x), derives and returns some f(x) = f(y) via some x=y that is generated by
    calling a method of the name eqGenMethodName on one of its sub-expressions.  eqGenMethodArgs
    and eqGenKeywordArgs may be a list of arguments and/or a dictionary of keyword arguments
    respectively to pass on to the eqGenMethodName method.  If provided, criteria, subExprClass,
    and superExpr will force selectivity in choosing the sub-expression to generate x=y.
    Specificially the sub-expression must be a sub-expression of superExpr (if provided)
    beyond being a sub-expression of expr, it must be an instance of subExprClass (if provided), 
    and the criteria method (if provide) must return true when passed in the sub-expression.
    If superExpr is provided, replacements are only made within superExpr.
    '''
    if superExpr is None: superExpr = expr
    return _autoSub('substitution', expr, superExpr, superExpr, eqGenMethodName, eqGenMethodArgs, eqGenKeywordArgs, criteria, subExprClass, suppressWarnings)

def autoStatementSubstitution(expr, eqGenMethodName, eqGenMethodArgs=None, eqGenKeywordArgs=None, criteria=None, subExprClass=None, superExpr=None, suppressWarnings = False):
    '''
    From a given expr = P(x), derives and returns some P(x) => P(y) via some x=y that is 
    generated by calling a method of the name eqGenMethodName on one of its sub-expressions.
    eqGenMethodArgs and eqGenKeywordArgs may be a list of arguments and/or a dictionary of 
    keyword arguments respectively to pass on to the eqGenMethodName method.  If provided, 
    criteria, subExprClass, and superExpr will force selectivity in choosing the sub-expression 
    to generate x=y.  Specificially the sub-expression must be a sub-expression of superExpr 
    (if provided) beyond being a sub-expression of expr, it must be an instance of subExprClass 
    (if provided), and the criteria method (if provide) must return true when passed in the 
    sub-expression. If superExpr is provided, replacements are only made within superExpr.
    '''
    if superExpr is None: superExpr = expr
    return _autoSub('statement_substitution', expr, superExpr, superExpr, eqGenMethodName, eqGenMethodArgs, eqGenKeywordArgs, criteria, subExprClass, suppressWarnings)        
"""

"""
Either move this elsewhere or use other techniques.  Perhaps no longer needed.

def generateSubExpressions(expr, criteria=None, subExprClass=None):
    meetsCriteria = (subExprClass is None or isinstance(expr, subExprClass)) and \
        (criteria is None or criteria(expr))
    if meetsCriteria: yield expr
    for subExpr in expr.subExprGen():
        for subSubExpr in generateSubExpressions(subExpr, criteria, subExprClass):
            yield subSubExpr

def extractSubExpr(expr, criteria=None, subExprClass=None):
    for subExpr in generateSubExpressions(expr, criteria=criteria, subExprClass=subExprClass):
        return subExpr
    print "Sub expression meeting the criteria not found"

"""

class TransitivityException:
    def __init__(self, expr1, expr2):
        self.expr1 = expr1
        self.expr2 = expr2
    
    def __str__(self):
        return 'Transitivity cannot be applied unless there is something in common in the equalities'