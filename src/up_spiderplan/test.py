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

from aiddl_core.tools.logger import Logger

from converter import UpCdbConverter
from solver import EngineImpl

problems = get_example_problems()

basic = problems["basic"].problem
basic_nc = problems["basic_nested_conjunctions"].problem
robot = problems["robot"].problem

print(robot)


conv = UpCdbConverter()

print('Converting...')

r = conv(basic)

print(Logger.pretty_print(r, 0))

print(basic.kind)

solver = EngineImpl()

solver.solve(basic)
