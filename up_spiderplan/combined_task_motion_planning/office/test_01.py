import math
import os
from unified_planning.shortcuts import *
from planning_tests.commons.problem import TestCaseProblem

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class TampOffice01(TestCaseProblem):

    def __init__(self, expected_version):
        TestCaseProblem.__init__(self, expected_version)

    def get_problem(self):
        robot = MovableType("robot")

        occ_map = OccupancyMap(os.path.join(FILE_PATH, "maps", "office-map-1.yaml"), (0, 0))

        robot_config = ConfigurationType("robot_config", occ_map, 3)

        robot_at = Fluent("robot_at", BoolType(), robot=robot, configuration=robot_config)

        park1 = ConfigurationObject("parking-1", robot_config, (46.0, 26.0, 3*math.pi/2))
        park2 = ConfigurationObject("parking-2", robot_config, (40.0, 26.0, 3*math.pi/2))

        office1 = ConfigurationObject("office-1", robot_config, (4.0, 4.0, 3*math.pi/2))
        office2 = ConfigurationObject("office-2", robot_config, (14.0, 4.0, math.pi/2))
        office3 = ConfigurationObject("office-3", robot_config, (24.0, 4.0, 3*math.pi/2))
        office4 = ConfigurationObject("office-4", robot_config, (32.0, 4.0, 3*math.pi/2))
        office5 = ConfigurationObject("office-5", robot_config, (4.0, 24.0, 3*math.pi/2))
        office6 = ConfigurationObject("office-6", robot_config, (14.0, 24.0, math.pi/2))
        office7 = ConfigurationObject("office-7", robot_config, (24.0, 24.0, math.pi/2))
        office8 = ConfigurationObject("office-8", robot_config, (32.0, 24.0, math.pi/2))

        r1 = MovableObject(
            "r1",
            robot,
            footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
            motion_model=MotionModels.REEDSSHEPP,
            parameters={"turning_radius": 2.0},
        )

        r2 = MovableObject(
            "r2",
            robot,
            footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
            motion_model=MotionModels.REEDSSHEPP,
            parameters={"turning_radius": 2.0},
        )

        move = InstantaneousMotionAction(
            "move", robot=robot, c_from=robot_config, c_to=robot_config
        )
        robot = move.parameter("robot")
        c_from = move.parameter("c_from")
        c_to = move.parameter("c_to")
        move.add_precondition(robot_at(robot, c_from))
        move.add_effect(robot_at(robot, c_from), False)
        move.add_effect(robot_at(robot, c_to), True)

        move.add_motion_constraint(Waypoints(robot, c_from, [c_to]))

        problem = Problem("robot")
        problem.add_fluent(robot_at)
        problem.add_action(move)
        problem.add_object(park1)
        problem.add_object(park2)
        problem.add_object(office1)
        problem.add_object(office2)
        problem.add_object(office3)
        problem.add_object(office4)
        problem.add_object(office5)
        problem.add_object(office6)
        problem.add_object(office7)
        problem.add_object(office8)

        problem.add_object(r1)
        problem.add_object(r2)

        problem.set_initial_value(robot_at(r1, park1), True)
        # TODO: Shortcut
        problem.set_initial_value(robot_at(r1, park2), False)
        problem.set_initial_value(robot_at(r1, office1), False)
        problem.set_initial_value(robot_at(r1, office2), False)
        problem.set_initial_value(robot_at(r1, office3), False)
        problem.set_initial_value(robot_at(r1, office4), False)
        problem.set_initial_value(robot_at(r1, office5), False)
        problem.set_initial_value(robot_at(r1, office6), False)
        problem.set_initial_value(robot_at(r1, office7), False)
        problem.set_initial_value(robot_at(r1, office8), False)

        problem.set_initial_value(robot_at(r2, park2), True)
        # TODO: Shortcut
        problem.set_initial_value(robot_at(r2, park1), False)
        problem.set_initial_value(robot_at(r2, office1), False)
        problem.set_initial_value(robot_at(r2, office2), False)
        problem.set_initial_value(robot_at(r2, office3), False)
        problem.set_initial_value(robot_at(r2, office4), False)
        problem.set_initial_value(robot_at(r2, office5), False)
        problem.set_initial_value(robot_at(r2, office6), False)
        problem.set_initial_value(robot_at(r2, office7), False)
        problem.set_initial_value(robot_at(r2, office8), False)

        problem.add_goal(robot_at(r1, office8))
        problem.add_goal(robot_at(r2, office4))

        return problem

    def get_description(self):
        return 'Moving a robot in a simple office map'

    def version(self):
        return 1
