from proveit.basiclogic.boolean.axioms import existsDef
from proveit.basiclogic import Forall, NotEquals, Implies, TRUE, FALSE, deriveStmtEqTrue, In
from proveit.basiclogic.variables import X, P, S
from proveit.basiclogic.simpleExpr import xEtc, yEtc, PxEtc, PyEtc, etcQ, etc_QxEtc, etc_QyEtc

inDomain = In(xEtc, S) # ..x.. in S

# neverPy = [forall_{..y.. in S | ..Q(..y..)..} (P(..y..) != TRUE)]
neverPy = Forall(yEtc, NotEquals(PyEtc, TRUE), etc_QyEtc, domain=S)
# (P(..x..) != TRUE) assuming ..Q(..x..).., neverPy
neverPy.specialize({yEtc:xEtc}).prove({etc_QxEtc, neverPy, inDomain})
# (TRUE != TRUE) assuming ..Q(..x..).., P(..x..), neverPy
trueNotEqTrue = deriveStmtEqTrue(PxEtc).rhsSubstitute(X, NotEquals(X, TRUE)).prove({etc_QxEtc, PxEtc, neverPy, inDomain})
# FALSE assuming ..Q(..x..).., P(..x..), neverPy
trueNotEqTrue.evaluate().deriveContradiction().deriveConclusion().prove({etc_QxEtc, PxEtc, neverPy, inDomain})
# [forall_{..y.. in S | ..Q(..y..)..} (P(..y..) != TRUE)] in BOOLEANS
neverPy.deduceInBool().prove()
# Not(forall_{..y.. in S | ..Q(..y..)..} (P(..y..) != TRUE) assuming ..Q(..x..).., P(..x..)
Implies(neverPy, FALSE).deriveViaContradiction().prove({etc_QxEtc, PxEtc, inDomain})
# exists_{..y.. in S | ..Q(..y..)..} P(..y..) assuming Q(..x..), P(..x..)
existence = existsDef.specialize({xEtc:yEtc}).deriveLeftViaEquivalence().prove({etc_QxEtc, PxEtc, inDomain})
# forall_{P, ..Q.., S} forall_{..x.. in S | ..Q(..x..)..} [P(..x..) => exists_{..y.. in S | ..Q(..y..)..} P(..y..)]
Implies(PxEtc, existence).generalize(xEtc, etc_QxEtc, domain=S).generalize((P, etcQ, S)).qed(__file__)