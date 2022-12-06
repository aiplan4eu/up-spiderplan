import unified_planning as up
from unified_planning.model import Fluent, InstantaneousAction, Object, Problem
from unified_planning.shortcuts import UserType, BoolType, ObjectExp

Location = UserType("location")
Robot = UserType("robot")
robot_at = Fluent("robot_at", BoolType(), robot=Robot, position=Location)

move = InstantaneousAction("move", robot=Robot, l_from=Location, l_to=Location)
robot = move.parameter("robot")
l_from = move.parameter("l_from")
l_to = move.parameter("l_to")
move.add_precondition(robot_at(robot, l_from))
move.add_effect(robot_at(robot, l_from), False)
move.add_effect(robot_at(robot, l_to), True)

l1 = Object("l1", Location)
l2 = Object("l2", Location)
r1 = Object("r1", Location)

problem = Problem("robot")
problem.add_fluent(robot_at)
problem.add_action(move)
problem.add_object(l1)
problem.add_object(l2)
problem.set_initial_value(robot_at(l1), True)
problem.set_initial_value(robot_at(l2), False)
problem.add_goal(robot_at(l2))

# Fixed frames in 2D. We attach poses and frames to objects and motion requirements to operators:

class ReedsSheppCar:
    def __init__(self, turning_radius=4.0):
        self.turning_radius = turning_radius


map1 = problem.add_map("./maps/my-map.yaml")
frame1 = problem.add_robot_frame([(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)])
problem.attach_frame(r1, frame1)
problem.attach_pose(l1, (4.0, 4.0, 0.0))
problem.attach_pose(l2, (26.0, 3.6, 0.0))
move.add_motion_requirement(robot, map1, l1, l2)

problem.attach_motion_model(r1, ReedsSheppCar(turning_radius=4.0))

# Solution plane:
# - list (or similar) of actions (same as before)
# - look-up of paths attached to motions: action-instance X (robot, map1, l1, l2) -> [...]


