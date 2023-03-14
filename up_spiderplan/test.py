import unified_planning.engines.results as results
from combined_task_motion_planning.office.test_01 import TampOffice01
from combined_task_motion_planning.office.test_02 import TampOffice02
from combined_task_motion_planning.office.test_03 import TampOffice03

from combined_task_motion_planning.construction.test_01 import TampConstruction01
from combined_task_motion_planning.construction.test_02 import TampConstruction02
from combined_task_motion_planning.construction.test_03 import TampConstruction03

from solver import EngineImpl

from util import plot_path

# tamp = problems["tamp_feasible"].problem

office_tamp_01 = TampOffice01(1).get_problem()
office_tamp_02 = TampOffice02(1).get_problem()
office_tamp_03 = TampOffice03(1).get_problem()

selected = TampConstruction01(1).get_problem()

print(selected)

solver = EngineImpl(run_docker=True)
result = solver.solve(selected)

if result.status in results.POSITIVE_OUTCOMES:
    for a in result.plan.actions:
        print(a)

    plot_path(result)
else:
    print("NO-PLAN-FOUND")
