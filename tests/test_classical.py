import unittest

from unified_planning.test.examples import get_example_problems
from unified_planning.engines import PlanGenerationResultStatus, CompilationKind
from unified_planning.engines.results import POSITIVE_OUTCOMES

from up_spiderplan.solver import EngineImpl

problems = get_example_problems()


basic_nc = problems["basic_nested_conjunctions"].problem
robot = problems["robot"].problem
basic_wc = problems["basic_with_costs"].problem
counter_2_50 = problems["counter_to_50"].problem
match_cellar = problems["matchcellar"].problem

robot_no_neg = problems["robot_no_negative_preconditions"].problem


class TestClassical(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.problems = get_example_problems()
        self.planner = EngineImpl()

    def test_basic(self):
        problem = self.problems["basic"].problem

        final_report = self.planner.solve(problem)
        a = problem.action("a")

        print(final_report)
    
        plan = final_report.plan
        self.assertEqual(
            final_report.status, PlanGenerationResultStatus.SOLVED_SATISFICING
        )
        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.actions[0].action, a)
        self.assertEqual(len(plan.actions[0].actual_parameters), 0)


    def test_robot_no_negative_preconditions(self):
        problem = self.problems["robot_no_negative_preconditions"].problem

        final_report = self.planner.solve(problem)
        #a = problem.action("a")

        print(final_report)
    
        plan = final_report.plan
        self.assertEqual(
            final_report.status, PlanGenerationResultStatus.SOLVED_SATISFICING
        )
        self.assertEqual(len(plan.actions), 1)
        # self.assertEqual(plan.actions[0].action, a)
        self.assertEqual(len(plan.actions[0].actual_parameters), 2)
        
    
    