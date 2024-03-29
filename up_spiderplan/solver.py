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
import subprocess
import shutil
import os
import time

from functools import partial
from typing import IO, Callable, List, Dict, Optional, Set, Tuple
import warnings
import unified_planning as up
import unified_planning.engines
from aiddl_core.container import Container, Entry
from unified_planning.exceptions import UPUnsupportedProblemTypeError
from unified_planning.engines import PlanGenerationResultStatus, Credits
from unified_planning.model import FNode, ProblemKind, Type as UPType
from unified_planning.model.tamp import ReedsSheppPath
from unified_planning.model.tamp import Waypoints
from aiddl_core.representation import Term, Sym, Var
from aiddl_core.representation import Tuple as AiddlTuple

from aiddl_core.util.logger import Logger
from aiddl_external_grpc_python.container import GrpcFunction

from up_spiderplan.converter import UpCdbConverter

import tempfile

credits = Credits('spiderplan',
                  'Örebro University',
                  'Uwe Köckemann',
                  'spiderplan.org',
                  'GPL3 LICENSE',
                  'Spiderplan is an extentable constraint-based hybrid planner.',
                  'Spiderplan is an extentable constraint-based hybrid planner.'
                )

SPIDER_dst = tempfile.gettempdir() + "/"
SPIDER_PUBLIC = "up-spiderplan"
SPIDER_TAG = "master"
SPIDER_REPO = "https://github.com/aiplan4eu/up-spiderplan.git"
SPIDER_PORT = 8061

class EngineImpl(
    unified_planning.engines.Engine,
    unified_planning.engines.mixins.OneshotPlannerMixin):
    def __init__(self, run_docker=True, build_docker=False, verbose=False, **options):
        self._run_docker = run_docker
        self._build_docker = build_docker
        self._docker_name = "up-spiderplan-server"
        self._problem = None
        self._verbose = verbose
        if not self._build_docker:
            self._docker_name = "up-spiderplan-server-web"
        self.conv = UpCdbConverter(self._docker_name)
        if len(options) > 0:
            raise

    def copy_file_to_container(self, path, name):
        cmd = f'docker cp "{path}/{name}" {self._docker_name}:/planner/{name}'
        os.system(cmd)

    def install_grpc_server(self):
        subprocess.run(["git", "clone", "-b", SPIDER_TAG, SPIDER_REPO])
        shutil.move(SPIDER_PUBLIC, SPIDER_dst)
        curr_dir = os.getcwd()
        os.chdir(SPIDER_dst + SPIDER_PUBLIC + "/spiderplan-grpc-server")
        os.system("docker-compose build")
        os.chdir(curr_dir)

    def grpc_server_installed(self):
        return os.path.exists(SPIDER_dst  + SPIDER_PUBLIC)

    def start_grpc_server(self):
        curr_dir = os.getcwd()

        if not self._build_docker:
            os.chdir("/tmp/")
            f = open("docker-compose.yml", "w")
            f.write('version: "3.3"\nservices:\n  web:\n    container_name: up-spiderplan-server-web\n    image: uekn/up-spiderplan-server:v03\n    ports:\n      - "8061:8061"\n')
            f.close()
        else:
            os.chdir(SPIDER_dst  + SPIDER_PUBLIC + "/spiderplan-grpc-server")

        os.system("docker-compose up -d")
        os.chdir(curr_dir)


    def stop_grpc_server(self):
        os.system(f"docker cp {self._docker_name}:/planner/search.dot ./search.dot")
        os.system(f"docker cp {self._docker_name}:/planner/stopwatch.txt ./stopwatch.txt")

        curr_dir = os.getcwd()
        if self._build_docker:
            os.chdir(SPIDER_dst  + SPIDER_PUBLIC + "/spiderplan-grpc-server")
        else:
            os.chdir("/tmp/")
        os.system("docker-compose stop")
        os.chdir(curr_dir)

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

        if self._run_docker and self._build_docker and not self.grpc_server_installed():
            self.install_grpc_server()

        self._problem = problem
        t_start_conversion = time.time()
        cdb = self._convert(problem)
        t_conversion = time.time() - t_start_conversion

        if self._verbose:
            print(f'Time to convert UP to CDB: {t_conversion}s')

        solution_cdb = self._solve(cdb)

        if self._verbose:
            print(f"Docker overhead: {self.docker_overhead_seconds}s")

        if solution_cdb == Sym("NIL"):
            result = up.engines.PlanGenerationResult(PlanGenerationResultStatus.UNSOLVABLE_PROVEN, None, self.name)
            result.metrics = {
                "engine_internal_time": self.internal_engine_time,
                "docker_overhead_time": self.docker_overhead_seconds
            }
            return result
        plan = self._extract_plan(solution_cdb)
        result = up.engines.PlanGenerationResult(PlanGenerationResultStatus.SOLVED_SATISFICING, plan, self.name)
        result.metrics = {
            "engine_internal_time": self.internal_engine_time,
            "docker_overhead_time": self.docker_overhead_seconds
        }
        return result

    def _convert(self, problem: 'unified_planning.model.Problem') -> Term:
        return self.conv(problem)

    def _solve(self, cdb: 'aiddl_core.representation.Set') -> Term:
        # Call Spiderplan and get resulting CDB or NIL if no solution exists.
        container = Container()
        spiderplan_proxy = GrpcFunction("0.0.0.0", SPIDER_PORT, Sym("org.spiderplan.unified-planning.basic-graph-search"), container)

        mod_name = Sym("aiplan4eu.up-spiderplan.up-input")
        container.add_module(mod_name)
        e = Entry(Sym("org.aiddl.type.term"), Sym("problem"), cdb)
        container.set_entry(e, mod_name)
        container.export(mod_name, "converted-from-up.aiddl")

        t_run_docker_start = time.time()
        if self._run_docker:
            self.start_grpc_server()
        success = False
        while not success:
            from grpc._channel import _InactiveRpcError
            try:
                t_run_docker = time.time() - t_run_docker_start
                t_spiderplan_call_start = time.time()
                answer = spiderplan_proxy(cdb)
                t_spiderplan_call = time.time() - t_spiderplan_call_start
                self.internal_engine_time = t_spiderplan_call
                if self._verbose:
                    print(f'Time to start docker service: {t_run_docker}s')
                    print(f'Time in SpiderPlan from engine point of view: {t_spiderplan_call}s')
                success = True
            except _InactiveRpcError as e:
                if self._verbose:
                    print("Waiting for Spiderplan gRPC server...")
                success = False
                time.sleep(0.01)

        if self._run_docker:
            t_stop_docker_start = time.time()
            self.stop_grpc_server()
            t_stop_docker = time.time() - t_stop_docker_start
            if self._verbose:
                print(f'Time to stop docker: {t_stop_docker}')
            self.docker_overhead_seconds = t_run_docker + t_stop_docker

        return answer

    def _extract_plan(self, cdb: 'aiddl_core.representation.Set') -> up.plans.Plan:
        # Convert CDB to a plan type supported by UP
        # -> sequence or partial-order based on EST in propagated STN
        op_map = {}

        # print(Logger.pretty_print(cdb, 0))

        for a in cdb.get((Sym("operator"))):
            op_map[a[Sym("name")]] = a

        path_expressions = {}

        for mc in cdb.get_or_default(Sym("motion"), []):
            if mc[0] == Sym("path") and not isinstance(mc[1], Var):
                if mc[1] not in path_expressions.keys():
                    path_expressions[mc[1]] = []
                path_expressions[mc[1]].append(mc)

        instance_map = {}
        plan_stmts = []
        for s in cdb[Sym("statement")]:
            variable = s[1].key
            if variable in op_map.keys():
                earliest_start_time = cdb[Sym("propagated-value")][AiddlTuple(Sym("ST"), s[0])][0]
                plan_stmts.append((earliest_start_time, s))

                operator = op_map[variable]

                # print(earliest_start_time, ":", s)
                # print(Logger.pretty_print(operator, 1))

                id_var = operator[Sym("id")]
                interval_pattern = operator[Sym("interval")]
                sub = interval_pattern.match(s[0])
                id = sub.substitute(id_var)

                instance_map[s] = id

                if a.get(Sym("constraints")).contains_key(Sym("motion")):
                    mcs = a.get(Sym("constraints")).get(Sym("motion"))




        plan_stmts = sorted(plan_stmts, key=lambda x: x[0])

        actions: List[up.plans.ActionInstance] = []
        # print("Plan statements:")
        for pair in cdb[Sym("goal.plan.latest")]:

            # print(plan_stmts)
            # print(pair)

            s = pair[1]
            # print(s)
            id = instance_map[s]

            aiddl_action = s[1].key
            action_params = []
            if isinstance(aiddl_action, AiddlTuple):
                action_name = str(aiddl_action[0])
                for p in range(1, len(aiddl_action)):
                    action_params.append(str(aiddl_action[p]))
            else:
                action_name = str(aiddl_action)

            paths = {}
            if id in path_expressions.keys():
                for pathExp in path_expressions[id]:
                    # print(pathExp)
                    path = pathExp[6].unpack()
                    upPath = ReedsSheppPath(path)

                    mover = str(pathExp[2])
                    start = str(pathExp[3])
                    wps = []
                    if isinstance(pathExp[4], List):
                        for wp in pathExp[4]:
                            wps.append(self._problem.object(str(wp)))
                    else:
                        wps.append(self._problem.object(str(pathExp[4])))

                    upMotionCon = Waypoints(
                        self._problem.object(mover),
                        self._problem.object(start),
                        wps)
                    paths[upMotionCon] = path

            up_action = self._problem.action(action_name)
            expr_manager = self._problem.environment.expression_manager
            param = tuple(expr_manager.ObjectExp(self._problem.object(o_name)) for o_name in action_params)
            if len(paths) == 0:
                actions.append(up.plans.ActionInstance(up_action, param))
            else:
                actions.append(up.plans.ActionInstance(up_action, param, None, motion_paths=paths))

        # for up_action in actions:
            # print(up_action)
        #    for mc in up_action.motion_paths.keys():
                # print(mc, up_action.motion_paths[mc])

        return up.plans.SequentialPlan(actions)


    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class('ACTION_BASED')
        supported_kind.set_problem_class('TAMP')
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
