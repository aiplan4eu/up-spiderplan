from unified_planning.test.examples import get_example_problems
from unified_planning.model.operators import OperatorKind

from aiddl_core.representation import Sym
from aiddl_core.representation import Boolean
from aiddl_core.representation import Tuple
from aiddl_core.representation import List
from aiddl_core.representation import Set
from aiddl_core.representation import Int
from aiddl_core.representation import KeyValue
from aiddl_core.representation import Var
from aiddl_core.representation import Infinity

from converter import UpCdbConverter

problems = get_example_problems()

basic = problems["basic"].problem
basic_nc = problems["basic_nested_conjunctions"].problem

print(basic_nc)

print(basic.initial_values)

conv = UpCdbConverter()

conv(basic_nc)
