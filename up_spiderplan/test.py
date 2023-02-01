from unified_planning.test.examples import get_example_problems

from solver import EngineImpl

problems = get_example_problems()

basic = problems["basic"].problem
basic_nc = problems["basic_nested_conjunctions"].problem
robot = problems["robot"].problem
basic_wc = problems["basic_with_costs"].problem
counter_2_50 = problems["counter_to_50"].problem
match_cellar = problems["matchcellar"].problem
robot_no_neg = problems["robot_no_negative_preconditions"].problem

tamp = problems["tamp_feasible"].problem

selected = tamp

print(selected)

solver = EngineImpl()
solver.solve(selected)
