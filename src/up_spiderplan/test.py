from unified_planning.test.examples import get_example_problems
from unified_planning.model.operators import OperatorKind

from converter import UpCdbConverter
from solver import EngineImpl

problems = get_example_problems()

basic = problems["basic"].problem
basic_nc = problems["basic_nested_conjunctions"].problem
robot = problems["robot"].problem
basic_wc = problems["basic_with_costs"].problem
counter_2_50 = problems["counter_to_50"].problem
matchcellar = problems["matchcellar"].problem

selected = matchcellar

print(selected)

solver = EngineImpl()
solver.solve(selected)
