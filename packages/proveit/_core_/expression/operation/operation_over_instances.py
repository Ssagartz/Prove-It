from proveit._core_.expression import Expression
from proveit._core_.expression.lambda_expr import Lambda
from proveit._core_.expression.composite import singleOrCompositeExpression, compositeExpression, Composite, NamedExprs
from proveit._core_.defaults import USE_DEFAULTS
from .operation import Operation

class OperationOverInstances(Operation):
    def __init__(self, operator, instanceVars, instanceExpr, domain=None, domains=None, conditions=tuple()):
        '''
        Create an Operation for the given operator over instances of the given instance Variables,
        instanceVars, for the given instance Expression, instanceExpr under the given conditions
        and/or with instance variables restricted to the given domain.
        That is, the operation operates over all possibilities of given Variable(s) wherever
        the condition(s) is/are satisfied.  Examples include forall, exists, summation, etc.
        instanceVars and conditions may be singular or plural (iterable).
        Internally, this is represented as an Operation whose etcExpr is in the following form
        (where '->' represents a Lambda and the list of tuples are NambedExpressions:
        [('imap', instanceVars -> [('iexpr',instanceExpr), ('conditions',conditions)]), ('domain',domain)]
        '''
        if domain is not None:
            if domains is not None:
                raise ValueError("Provide a single domain or multiple domains, not both")
            if not isinstance(domain, Expression):
                raise TypeError("The domain should be an 'Expression' type")
            domain_or_domains = domain
        elif domains is not None: 
            domain_or_domains=compositeExpression(domains)
        else:
            domain_or_domains = None
        Operation.__init__(self, operator, OperationOverInstances._createOperand(instanceVars, instanceExpr, domain_or_domains, conditions))
        self.instanceVars = OperationOverInstances.extractInitArgValue('instanceVars', self.operators, self.operands)
        self.instanceExpr = OperationOverInstances.extractInitArgValue('instanceExpr', self.operators, self.operands)
        if 'domain' in self.operands:
            self.domain_or_domains = self.domain = OperationOverInstances.extractInitArgValue('domain', self.operators, self.operands)
        elif 'domains' in self.operands:
            self.domain_or_domains = self.domains = OperationOverInstances.extractInitArgValue('domains', self.operators, self.operands)
            if len(self.domains) != len(self.instanceVars):
                raise ValueError("When using multiple domains, there should be the same number as the number of instance variables")
        self.conditions = OperationOverInstances.extractInitArgValue('conditions', self.operators, self.operands)
    
    @staticmethod
    def _createOperand(instanceVars, instanceExpr, domain_or_domains, conditions):
        lambdaFn = Lambda(instanceVars, NamedExprs([('iexpr',instanceExpr), ('conds',compositeExpression(conditions))]))
        if domain_or_domains is None:
            return NamedExprs([('imap',lambdaFn)])
        else:
            domain_or_domains = singleOrCompositeExpression(domain_or_domains)
            if isinstance(domain_or_domains, Composite):
                return NamedExprs([('imap',lambdaFn), ('domains',domain_or_domains)])
            else:
                return NamedExprs([('imap',lambdaFn), ('domain',domain_or_domains)])
    
    @staticmethod
    def extractInitArgValue(argName, operators, operands):
        '''
        Given a name of one of the arguments of the __init__ method,
        return the corresponding value contained in the 'operands'
        composite expression (i.e., the operands of a constructed operation).
        
        Override this if the __init__ argument names are different than the
        default.
        '''
        from proveit import singleOrCompositeExpression
        if argName=='operator':
            assert len(operators)==1, "expecting one operator"
            return operators[0] 
        if argName=='domains':
            # multiple domains; one for each instance variable
            return operands['domains'] if 'domains' in operands else None
        elif argName=='domain':
            # one domain for all instance variables
            return operands['domain'] if 'domain' in operands else None
        instanceMapping = operands['imap'] # instance mapping
        if argName=='instanceVars':
            return singleOrCompositeExpression(instanceMapping.parameters)
        elif argName=='instanceExpr':
            return instanceMapping.body['iexpr'] 
        elif argName=='conditions':
            conditions = instanceMapping.body['conds']
            #if len(conditions)==0: return tuple()
            return conditions
        
    def implicitInstanceVars(self, formatType, overriddenImplicitVars = None):
        '''
        Return instance variables that need not be shown explicitly in the
        list of instance variables in the formatting.
        Use overriddenImplicitVars to declare extra implicit instance variables
        (all or just the overridden ones).
        '''
        return set() if overriddenImplicitVars is None else overriddenImplicitVars

    def implicitConditions(self, formatType):
        '''
        Returns conditions that need not be shown explicitly in the formatting.
        By default, this is empty (all conditions are shown).
        '''
        return set()

    def hasDomain(self):
        '''
        Returns True if this OperationOverInstances has a single domain restriction(s).
        '''
        return hasattr(self, 'domain')

    def hasDomains(self):
        '''
        Returns True if this OperationOverInstances has multiple domain restriction(s).
        '''
        return hasattr(self, 'domains')
    
    def hasDomainOrDomains(self):
        '''
        Returns True if this OperationOverInstances has one or more domain restriction(s).
        '''        
        return self.hasDomain() or self.hasDomains()
                                
    def hasCondition(self):
        '''
        Returns True if this OperationOverInstances has conditions.
        '''
        return len(self.conditions) > 0
    
    def string(self, **kwargs):
        return self._formatted('string', **kwargs)

    def latex(self, **kwargs):
        return self._formatted('latex', **kwargs)

    def _formatted(self, formatType, fence=False):
        # override this default as desired
        implicitIvars = self.implicitInstanceVars(formatType)
        hasExplicitIvars = (len(implicitIvars) < len(self.instanceVars))
        implicitConditions = self.implicitConditions(formatType)
        hasExplicitConditions = self.hasCondition() and (len(implicitConditions) < len(self.conditions))
        outStr = ''
        formattedVars = ', '.join([var.formatted(formatType, abbrev=True) for var in self.instanceVars if var not in implicitIvars])
        if formatType == 'string':
            if fence: outStr += '['
            outStr += self.operator.formatted(formatType) + '_{'
            if hasExplicitIvars: 
                if self.hasDomains(): outStr += '(' + formattedVars +')'
                else: outStr += formattedVars
            if self.hasDomainOrDomains():
                outStr += ' in '
                outStr += self.domain_or_domains.formatted(formatType, formattedOperator='*', fence=False)
            if hasExplicitConditions:
                if hasExplicitIvars: outStr += " | "
                outStr += self.conditions.formatted(formatType, fence=False)                
                #outStr += ', '.join(condition.formatted(formatType) for condition in self.conditions if condition not in implicitConditions) 
            outStr += '} ' + self.instanceExpr.formatted(formatType,fence=True)
            if fence: outStr += ']'
        if formatType == 'latex':
            if fence: outStr += r'\left['
            outStr += self.operator.formatted(formatType) + '_{'
            if hasExplicitIvars: 
                if self.hasDomains(): outStr += '(' + formattedVars +')'
                else: outStr += formattedVars
            if self.hasDomainOrDomains():
                outStr += r' \in '
                outStr += self.domain_or_domains.formatted(formatType, formattedOperator=r'\times', fence=False)
            if hasExplicitConditions:
                if hasExplicitIvars: outStr += "~|~"
                outStr += self.conditions.formatted(formatType, fence=False)                
                #outStr += ', '.join(condition.formatted(formatType) for condition in self.conditions if condition not in implicitConditions) 
            outStr += '} ' + self.instanceExpr.formatted(formatType,fence=True)
            if fence: outStr += r'\right]'

        return outStr        

    def instanceSubstitution(self, universality, assumptions=USE_DEFAULTS):
        '''
        Equate this OperationOverInstances, Upsilon_{..x.. in S | ..Q(..x..)..} f(..x..),
        with one that substitutes instance expressions given some 
        universality = forall_{..x.. in S | ..Q(..x..)..} f(..x..) = g(..x..).
        Derive and return the following type of equality assuming universality:
        Upsilon_{..x.. in S | ..Q(..x..)..} f(..x..) = Upsilon_{..x.. in S | ..Q(..x..)..} g(..x..)
        Works also when there is no domain S and/or no conditions ..Q...
        '''
        from proveit.logic.equality._axioms_ import instanceSubstitution, noDomainInstanceSubstitution
        from proveit.logic import Forall, Equals
        from proveit import KnownTruth
        from proveit._common_ import n, Qmulti, xMulti, yMulti, zMulti, f, g, Upsilon, S
        if isinstance(universality, KnownTruth):
            universality = universality.expr
        if not isinstance(universality, Forall):
            raise InstanceSubstitutionException("'universality' must be a forall expression", self, universality)
        if len(universality.instanceVars) != len(self.instanceVars):
            raise InstanceSubstitutionException("'universality' must have the same number of variables as the OperationOverInstances having instances substituted", self, universality)
        if universality.domain != self.domain:
            raise InstanceSubstitutionException("'universality' must have the same domain as the OperationOverInstances having instances substituted", self, universality)
        # map from the forall instance variables to self's instance variables
        iVarSubstitutions = {forallIvar:selfIvar for forallIvar, selfIvar in zip(universality.instanceVars, self.instanceVars)}
        if universality.conditions.substituted(iVarSubstitutions) != self.conditions:
            raise InstanceSubstitutionException("'universality' must have the same conditions as the OperationOverInstances having instances substituted", self, universality)
        if not isinstance(universality.instanceExpr, Equals):
            raise InstanceSubstitutionException("'universality' must be an equivalence within Forall: " + str(universality))
        if universality.instanceExpr.lhs.substituted(iVarSubstitutions) != self.instanceExpr:
            raise InstanceSubstitutionException("lhs of equivalence in 'universality' must match the instance expression of the OperationOverInstances having instances substituted", self, universality)
        f_op, f_op_sub = Operation(f, self.instanceVars), self.instanceExpr
        g_op, g_op_sub = Operation(g, self.instanceVars), universality.instanceExpr.rhs.substituted(iVarSubstitutions)
        Q_op, Q_op_sub = Operation(Qmulti, self.instanceVars), self.conditions
        if self.hasDomain():
            return instanceSubstitution.specialize({Upsilon:self.operator, Q_op:Q_op_sub, S:self.domain, f_op:f_op_sub, g_op:g_op_sub}, 
                                                    relabelMap={xMulti:universality.instanceVars, yMulti:self.instanceVars, zMulti:self.instanceVars}, assumptions=assumptions).deriveConsequent(assumptions=assumptions)
        else:
            return noDomainInstanceSubstitution.specialize({Upsilon:self.operator, Q_op:Q_op_sub, f_op:f_op_sub, g_op:g_op_sub}, 
                                                             relabelMap={xMulti:universality.instanceVars, yMulti:self.instanceVars, zMulti:self.instanceVars}, assumptions=assumptions).deriveConsequent(assumptions=assumptions)

    def substituteInstances(self, universality, assumptions=USE_DEFAULTS):
        '''
        Assuming this OperationOverInstances, Upsilon_{..x.. in S | ..Q(..x..)..} f(..x..)
        to be a true statement, derive and return Upsilon_{..x.. in S | ..Q(..x..)..} g(..x..)
        given some 'universality' = forall_{..x.. in S | ..Q(..x..)..} f(..x..) = g(..x..).
        Works also when there is no domain S and/or no conditions ..Q...
        '''
        substitution = self.instanceSubstitution(universality, assumptions=assumptions)
        return substitution.deriveRightViaEquivalence(assumptions=assumptions)
        
class InstanceSubstitutionException(Exception):
    def __init__(self, msg, operationOverInstances, universality):
        self.msg = msg
        self.operationOverInstances = operationOverInstances
        self.universality = universality
    def __str__(self):
        return self.msg + '.\n  operationOverInstances: ' + str(self.operationOverInstances) + '\n  universality: ' + str(self.universality)