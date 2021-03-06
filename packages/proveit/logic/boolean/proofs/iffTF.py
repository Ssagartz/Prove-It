from proveit.basiclogic.boolean.axioms import iffDef, andFT, impliesTF
from proveit.basiclogic.boolean.theorems import impliesFT
from proveit.basiclogic import TRUE, FALSE, Implies, And, Equation
from proveit.common import A, B, X

# (TRUE <=> FALSE) = [(TRUE => FALSE) and (FALSE => TRUE)]
eqn = Equation(iffDef.specialize({A:TRUE, B:FALSE})).proven()
# (TRUE <=> FALSE) = [FALSE and (FALSE => TRUE)]
eqn.update(impliesTF.substitution(eqn.eqExpr.rhs)).proven()
# (TRUE <=> FALSE) = (FALSE and TRUE)
eqn.update(impliesFT.substitution(eqn.eqExpr.rhs)).proven()
# (TRUE <=> FALSE) = FALSE
eqn.update(andFT).qed(__file__)
