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
        print(problem)
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
        
        
    def test_basic_2(self):
        from planning_tests.classical_planning.problems.problem_basic import UPBasic
        problem = UPBasic(1).get_problem()
        result = self.planner.solve(problem)
        self.assertNotEqual(result.status, PlanGenerationResultStatus.INTERNAL_ERROR)
        # result status must reflect that there is no plan
        self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)

    def test_basic_unsolvable(self):
        from planning_tests.classical_planning.problems.problem_basic_unsolvable import UPBasicUnsolvable
        problem = UPBasicUnsolvable(1).get_problem()
        result = self.planner.solve(problem)
        self.assertNotEqual(result.status, PlanGenerationResultStatus.INTERNAL_ERROR)
        # result status must reflect that there is no plan
        self.assertEqual(result.status, PlanGenerationResultStatus.UNSOLVABLE_PROVEN)

    def test_depot_1(self):
        from planning_tests.classical_planning.pddl_problems.depots.depots import depots_pfile1
        problem = depots_pfile1(1).get_problem()

        print(problem)

        result = self.planner.solve(problem)
        self.assertNotEqual(result.status, PlanGenerationResultStatus.INTERNAL_ERROR)
        # result status must reflect that there is no plan
        self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)

    def test_depot_2(self):
        from planning_tests.classical_planning.pddl_problems.depots.depots import depots_pfile2
        problem = depots_pfile2(1).get_problem()

        print(problem)

        result = self.planner.solve(problem)
        self.assertNotEqual(result.status, PlanGenerationResultStatus.INTERNAL_ERROR)
        # result status must reflect that there is no plan
        self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)

    def test_depot_3(self):
        from planning_tests.classical_planning.pddl_problems.depots.depots import depots_pfile3
        problem = depots_pfile3(1).get_problem()
        print(problem)

        result = self.planner.solve(problem)
        self.assertNotEqual(result.status, PlanGenerationResultStatus.INTERNAL_ERROR)
        # result status must reflect that there is no plan
        self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)

    def test_tpp_1(self):
        from planning_tests.classical_planning.pddl_problems.tpp.tpp import tpp_pfile1
        problem = tpp_pfile1(1).get_problem()

        print(problem)

        result = self.planner.solve(problem)
        self.assertNotEqual(result.status, PlanGenerationResultStatus.INTERNAL_ERROR)
        # result status must reflect that there is no plan
        self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)

    def test_tpp_2(self):
        from planning_tests.classical_planning.pddl_problems.tpp.tpp import tpp_pfile2
        problem = tpp_pfile2(1).get_problem()

        print(problem)

        result = self.planner.solve(problem)
        self.assertNotEqual(result.status, PlanGenerationResultStatus.INTERNAL_ERROR)
        # result status must reflect that there is no plan
        self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)

    def test_tpp_3(self):
        from planning_tests.classical_planning.pddl_problems.tpp.tpp import tpp_pfile3
        problem = tpp_pfile3(1).get_problem()

        print(problem)

        result = self.planner.solve(problem)
        self.assertNotEqual(result.status, PlanGenerationResultStatus.INTERNAL_ERROR)
        # result status must reflect that there is no plan
        self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)

    def test_tpp_6(self):
        from planning_tests.classical_planning.pddl_problems.tpp.tpp import tpp_pfile6
        problem = tpp_pfile6(1).get_problem()

        print(problem)

        result = self.planner.solve(problem)
        self.assertNotEqual(result.status, PlanGenerationResultStatus.INTERNAL_ERROR)
        # result status must reflect that there is no plan
        self.assertEqual(result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)
