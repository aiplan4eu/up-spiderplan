# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from functools import partial
from typing import IO, Callable, List, Dict, Optional, Set, Tuple
import warnings
import unified_planning as up
import unified_planning.engines
from unified_planning.exceptions import UPUnsupportedProblemTypeError
from unified_planning.engines import PlanGenerationResultStatus, Credits
from unified_planning.model import FNode, ProblemKind, Type as UPType

from aiddl_core.representation import Term, Sym
from aiddl_core.util.logger import Logger
from aiddl_external_grpc import GrpcFunction

from converter import UpCdbConverter


credits = Credits('spiderplan',
                  'Örebro University',
                  'Uwe Köckemann',
                  'spiderplan.org',
                  'MIT LICENSE',
                  'Spiderplan is an extentable constraint-based hybrid planner.',
                  'Spiderplan is an extentable constraint-based hybrid planner.'
                )

class EngineImpl(unified_planning.engines.Engine):
    def __init__(self, **options):
        if len(options) > 0:
            raise

    @property
    def name(self) -> str:
        return "Spiderplan"

    def solve(self, problem: 'up.model.Problem',
                callback: Optional[Callable[['up.engines.PlanGenerationResult'], None]] = None,
                timeout: Optional[float] = None,
                output_stream: Optional[IO[str]] = None) -> 'up.engines.results.PlanGenerationResult':
        '''This function converts a UP problem to a constraint database and uses SpiderPlan to resolve any open flaws.'''
        if not self.supports(problem.kind):
            print('SpiderPlan cannot solve this kind of problem!')
            # raise UPUnsupportedProblemTypeError('Spiderplan cannot solve this kind of problem!')

        if timeout is not None:
            warnings.warn('SpiderPlan does not support timeout.', UserWarning)
        if output_stream is not None:
            warnings.warn('SpiderPlan does not support output stream.', UserWarning)
            
        cdb = self._convert(problem)
        solution_cdb = self._solve(cdb)
  
        actions: List[up.plans.ActionInstance] = []
        if solution_cdb == Sym("NIL"):
            return up.plans.FinalReport(PlanGenerationResultStatus.UNSOLVABLE_PROVEN, None, self.name)

        plan = self._extract_plan(solution_cdb)
        return up.engines.PlanGenerationResult(PlanGenerationResultStatus.SOLVED_SATISFICING, plan, self.name)


    def _convert(self, problem: 'unified_planning.model.Problem') -> Term:
        conv = UpCdbConverter()
        return conv(problem)

    def _solve(self, cdb: 'aiddl_core.representation.Set') -> Term:
        # Call Spiderplan and get resulting CDB or NIL if no solution exists.
        spiderplan_proxy = GrpcFunction("localhost", 8011, Sym("org.spiderplan.unified-planning.basic-graph-search"))

        print("SpiderPlan Problem:")
        print(Logger.pretty_print(cdb, 0))

        answer = spiderplan_proxy(cdb)

        print("SpiderPlan Solution:")
        print(Logger.pretty_print(answer, 0))

        return answer

    def _extract_plan(self, cdb: 'aiddl_core.representation.Set') -> up.plans.Plan:
        # Convert CDB to a plan type supported by UP
        # -> sequence or partial-order based on EST in propagated STN 
        actions: List[up.plans.ActionInstance] = []
        return up.plans.SequentialPlan(actions)


    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class('ACTION_BASED')
        supported_kind.set_typing('FLAT_TYPING')
        supported_kind.set_typing('HIERARCHICAL_TYPING')
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        return supported_kind

    @staticmethod
    def supports(problem_kind: 'up.model.ProblemKind') -> bool:
        return problem_kind <= EngineImpl.supported_kind()

    @staticmethod
    def is_oneshot_planner():
        return True

    @staticmethod
    def is_grounder():
        return False

    @staticmethod
    def get_credits(**kwargs) -> Optional[unified_planning.engines.Credits]:
        return credits

    def destroy(self):
        pass
