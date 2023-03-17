import math
import os
from unified_planning.shortcuts import *
# from planning_tests.commons.problem import TestCaseProblem

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class TampLogistics01: # (TestCaseProblem):

    def __init__(self, expected_version):
        pass
        # TestCaseProblem.__init__(self, expected_version)


    def get_problem(self):
        t_forklift = MovableType("forklift")
        t_truck = MovableType("truck")

        occ_map = OccupancyMap(os.path.join(FILE_PATH, "maps", "logistics-map-1.yaml"), (0, 0))

        t_robot_config = ConfigurationType("robot_config", occ_map, 3)
        t_container = UserType("container")
        t_slot = UserType("slot")

        forklift_at = Fluent("forklift_at", BoolType(), robot=t_forklift, configuration=t_robot_config)
        truck_at = Fluent("truck_at", BoolType(), robot=t_truck, configuration=t_robot_config)
        container_at = Fluent("container_at", BoolType(), container=t_container, configuration=t_robot_config)
        forklift_carries = Fluent("forklift_cargo", BoolType(), robot=t_forklift, container=t_container)

        truck_carries = Fluent("truck_cargo", BoolType(), robot=t_truck, t_slot=t_slot, container=t_container)

        pick1 = ConfigurationObject("pick-up-1", t_robot_config, (46.0, 26.0, 3*math.pi/2))
        pick2 = ConfigurationObject("pick-up-2", t_robot_config, (40.0, 26.0, 3*math.pi/2))

        loading1 = ConfigurationObject("loading-1", t_robot_config, (4.0, 4.0, 3*math.pi/2))

        delivery1 = ConfigurationObject("office-8", t_robot_config, (32.0, 24.0, math.pi/2))

        fl1 = MovableObject(
            "forklift-1",
            t_forklift,
            footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
            motion_model=MotionModels.REEDSSHEPP,
            parameters={"turning_radius": 2.0},
        )

        t1 = MovableObject(
            "delivery-truck-1",
            t_truck,
            footprint=[(-1.0, 0.5), (2.0, 0.5), (2.0, -0.5), (-1.0, -0.5)],
            motion_model=MotionModels.REEDSSHEPP,
            parameters={"turning_radius": 4.0},
        )

        nothing = Object("nothing", t_container)
        c1 = Object("container-1", t_container)
        c2 = Object("container-2", t_container)

        slot1 = Object("slot-1", t_slot)
        slot2 = Object("slot-2", t_slot)
        slot3 = Object("slot-3", t_slot)

        def move_forklift():
            action = InstantaneousMotionAction(
                "move-forklift", forklift=t_forklift, c_from=t_robot_config, c_to=t_robot_config
            )
            r = action.parameter("forklift")
            a = action.parameter("c_from")
            b = action.parameter("c_to")
            action.add_precondition(forklift_at(r, a))
            action.add_effect(forklift_at(r, a), False)
            action.add_effect(forklift_at(r, b), True)
            #action.add_motion_constraint(Waypoints(r, a, [b]))
            return action

        def move_truck():
            action = InstantaneousMotionAction(
                "move-truck", truck=t_truck, c_from=t_robot_config, c_to=t_robot_config
            )
            r = action.parameter("truck")
            a = action.parameter("c_from")
            b = action.parameter("c_to")
            action.add_precondition(truck_at(r, a))
            action.add_effect(truck_at(r, a), False)
            action.add_effect(truck_at(r, b), True)
            #action.add_motion_constraint(Waypoints(r, a, [b]))
            return action

        def pick_up():
            action = InstantaneousMotionAction(
                "pick", robot=t_forklift, loc=t_robot_config, container=t_container
            )
            r = action.parameter("robot")
            loc = action.parameter("loc")
            c = action.parameter("container")
            action.add_precondition(forklift_at(r, loc))
            action.add_precondition(container_at(c, loc))
            action.add_precondition(forklift_carries(r, nothing))
            action.add_precondition(Not(forklift_carries(r, c)))
            action.add_effect(forklift_carries(r, c), True)
            action.add_effect(container_at(c, loc), False)
            action.add_effect(forklift_carries(r, nothing), False)
            return action

        def load_on_truck():
            action = InstantaneousMotionAction(
                "load-truck", forklift=t_forklift, truck=t_truck, slot=t_slot, loc=t_robot_config, container=t_container
            )
            forklift = action.parameter("forklift")
            truck = action.parameter("truck")
            slot = action.parameter("slot")
            loc = action.parameter("loc")
            container = action.parameter("container")

            action.add_precondition(forklift_at(forklift, loc))
            action.add_precondition(truck_at(truck, loc))
            action.add_precondition(forklift_carries(forklift, container))
            action.add_precondition(truck_carries(truck, slot, nothing))

            action.add_effect(forklift_carries(forklift, container), False)
            action.add_effect(truck_carries(truck, slot, container), True)
            return action

        def dump_from_truck():
            action = InstantaneousMotionAction(
                "unload-truck", truck=t_truck, slot=t_slot, loc=t_robot_config, container=t_container
            )
            truck = action.parameter("truck")
            slot = action.parameter("slot")
            loc = action.parameter("loc")
            container = action.parameter("container")

            action.add_precondition(truck_at(truck, loc))
            action.add_precondition(truck_carries(truck, slot, container))
            action.add_effect(truck_carries(truck, slot, container), False)
            action.add_effect(container_at(container, loc), True)
            return action


        problem = Problem("robot")
        problem.add_fluent(forklift_at, default_initial_value=False)
        problem.add_fluent(truck_at, default_initial_value=False)
        problem.add_fluent(container_at, default_initial_value=False)
        problem.add_fluent(forklift_carries, default_initial_value=False)
        problem.add_fluent(truck_carries, default_initial_value=False)

        problem.add_action(move_forklift())
        problem.add_action(move_truck())
        problem.add_action(pick_up())
        problem.add_action(load_on_truck())
        problem.add_action(dump_from_truck())

        problem.add_object(pick1)
        problem.add_object(pick2)
        problem.add_object(loading1)
        problem.add_object(delivery1)

        problem.add_object(fl1)
        problem.add_object(t1)

        problem.add_object(nothing)
        problem.add_object(c1)
        problem.add_object(c2)

        problem.add_object(slot1)
        problem.add_object(slot2)
        problem.add_object(slot3)

        problem.set_initial_value(forklift_carries(fl1, nothing), True)
        problem.set_initial_value(truck_carries(t1, slot1, nothing), True)
        problem.set_initial_value(truck_carries(t1, slot2, nothing), True)
        problem.set_initial_value(truck_carries(t1, slot3, nothing), True)

        problem.set_initial_value(container_at(c1, pick1), True)
        problem.set_initial_value(container_at(c2, pick2), True)

        problem.set_initial_value(forklift_at(fl1, pick1), True)
        problem.set_initial_value(truck_at(t1, loading1), True)

        problem.add_goal(container_at(c1, delivery1))
        problem.add_goal(container_at(c2, delivery1))

        return problem

    def get_description(self):
        return 'Moving a robot in a simple office map'

    def version(self):
        return 1
