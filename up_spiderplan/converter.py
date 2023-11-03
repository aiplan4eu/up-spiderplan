import os

import unified_planning.model.problem
from aiddl_core.util.logger import Logger
from unified_planning.model.tamp.objects import MotionModels
from unified_planning.model import InstantaneousAction, StartTiming, TimepointKind, Timing, TimeInterval
from unified_planning.model.tamp import InstantaneousMotionAction, Waypoints, ConfigurationObject
from unified_planning.shortcuts import ConfigurationType
from unified_planning.model.operators import OperatorKind
from unified_planning.model.problem import Problem

from aiddl_core.representation import Sym, Num, Real, Substitution, Str
from aiddl_core.representation import Boolean
from aiddl_core.representation import Tuple
from aiddl_core.representation import List
from aiddl_core.representation import Set
from aiddl_core.representation import Int
from aiddl_core.representation import KeyVal
from aiddl_core.representation import Var
from aiddl_core.representation import Inf
from aiddl_core.parser.parser import parse_term

from aiddl_core.util.logger import Logger

OpMap = {}
OpMap[OperatorKind.AND] = Sym("org.aiddl.eval.logic.and")
OpMap[OperatorKind.OR] = Sym("org.aiddl.eval.logic.or")
OpMap[OperatorKind.NOT] = Sym("org.aiddl.eval.logic.not")
OpMap[OperatorKind.IMPLIES] = Sym("org.aiddl.eval.logic.implies")
OpMap[OperatorKind.IFF] = Sym("org.aiddl.eval.logic.iff")
OpMap[OperatorKind.EXISTS] = Sym("org.aiddl.eval.logic.exists")
OpMap[OperatorKind.FORALL] = Sym("org.aiddl.eval.logic.forall")
OpMap[OperatorKind.PLUS] = Sym("org.aiddl.eval.numerical.add")
OpMap[OperatorKind.MINUS] = Sym("org.aiddl.eval.numerical.sub")
OpMap[OperatorKind.TIMES] = Sym("org.aiddl.eval.numerical.mult")
OpMap[OperatorKind.DIV] = Sym("org.aiddl.eval.numerical.div")
OpMap[OperatorKind.EQUALS] = Sym("org.aiddl.eval.equals")
OpMap[OperatorKind.LE] = Sym("org.aiddl.eval.numerical.less-than-eq")
OpMap[OperatorKind.LT] = Sym("org.aiddl.eval.numerical.less-than")


def merge_cdb(a, b):
    result = {}
    for kvp in a:
        k_a = kvp.key
        if b.contains_key(k_a):
            result[k_a] = kvp.value.add_all(b[k_a])
        else:
            result[k_a] = kvp.value

    for kvp in b:
        k_b = kvp.key
        if k_b not in result.keys():
            result[k_b] = kvp.value

    r = []
    for k in result.keys():
        r.append(KeyVal(k, result[k]))
    return Set(set(r)) #  for k, v in result])
        
        
class UpCdbConverter:

    def __init__(self):
        self.next_id = 0
        self.map_look_up = {}
        self.map_files = {}

    def __call__(self, problem):
        cdb = Set([])
        init = self._convert_initial_values(problem.initial_values)
        # print(init)
        cdb = merge_cdb(cdb, init)
        goal = self._convert_goal(problem.goals)
        cdb = merge_cdb(cdb, goal)

        cdb = merge_cdb(cdb, self._convert_motion_info(problem))

        type_look_up = {}
        self._convert_user_types(problem, type_look_up)

        operators = self._convert_operators(problem.actions, type_look_up)
        cdb = merge_cdb(cdb, operators)

        signatures = self._convert_fluents(problem, type_look_up)
        cdb = merge_cdb(cdb, signatures)

        cdb = merge_cdb(cdb, self._convert_domains(type_look_up))

        return cdb
        
    def _convert_fnode(self, n):
        # print("=== FNODE: %s (%s) ===" % (str(n), str(type(n))))
        term = None

        if n.is_fluent_exp():
            if len(n.args) == 0:
                term = Sym(str(n))
            else:
                args = [Sym(n.fluent().name)]
                for x in n.args:
                    args.append(self._convert_fnode(x))

                term = Tuple(args)
                
        elif n.is_bool_constant():
            term = Boolean(n.bool_constant_value())
        elif n.is_int_constant():
            term = Int(n.int_constant_value())
        elif n.is_object_exp():
            term = Sym(str(n))
        elif n.is_parameter_exp():
            term = Var(str(n))

        if term is None:
            raise ValueError("Fluent not supported: %s" % str(n))

        # print("=== TERM: %s ===" % (str(term)))
        return term

    def _convert_fluents(self, problem: Problem, t_look_up):
        signatures = []
        for f in problem.fluents:
            name = Sym(str(f.name))
            r_type = self._convert_type(f.type, t_look_up)
            signature = [self._convert_type(s.type, t_look_up) for s in f.signature]
            if len(signature) == 0:
                signatures.append(KeyVal(name, r_type))
            else:
                # print(f)
                signatures.append(KeyVal(Tuple([name] + signature), r_type))

        return Set([
            KeyVal(Sym("signature"), Set(signatures))
        ])

    def _convert_domains(self, t_look_up):
        domains = []
        for d in t_look_up.values():
            domains.append(d)
        return Set([KeyVal(Sym("domain"), Set(domains))])

    def _convert_object(self, o):
        return Sym(o.name)

    def _convert_constraint(self, c, fluents):
        # print("Converting constraint:", c)
        if c.node_type in OpMap.keys():
            exp = [OpMap[c.node_type]]
            for arg in c.args:
                exp.append(self._convert_constraint(arg, fluents))
            term = Tuple(exp)
        else:
            
            if c.is_fluent_exp():
                if c in fluents.keys():
                    term = fluents[c]
                else:
                    self.next_id += 1
                    term = Var("x%d" % self.next_id)
                    fluents[c] = term
            else:
                term = self._convert_fnode(c)
                if isinstance(term, Var):
                    fluents[c] = term
                
        return term

    def _convert_condition(self, c, is_goal=True, op_id=None, effect_vars=[]):
        # UP conditions may correspond to various constraint types
        # Fluent -> goal/precondition + temporal
        # (not Fluent) -> statement with false value + temporal
        # boolean or arithmetic formula -> AIDDL eval constraint expression
        # -> need to track fluents and assign variables + preconditions when they appear (e.g., (and a (or b c)) needs SVAs for a, b, and c
        # -> try to propagate (planning easier if we know which value we need, otherwise we may pick random values and reject based on constraints. in the example above, at least a has to be true)
        # -> CAST AS CSP and link fluents to values of SVAs
        # CSP solver can propagate if single value possible. Otherwise search over options. This nicely works with conjunctive goals
        
        statements = []
        temporal = []
        goals = []
        preconditions = []
        csp = []
        
        if c.is_fluent_exp() or (c.is_not() and c.args[0].is_fluent_exp()):
            self.next_id += 1
            if is_goal:
                i = Sym("G%d" % self.next_id)
            else:
                i = Tuple([Sym("P%d" % self.next_id), Var("ID")])
            if c.is_not():
                g_var = self._convert_fnode(c.args[0])
            else:
                g_var = self._convert_fnode(c)
            g_val = Boolean(not c.is_not())
            
            s = Tuple([i, KeyVal(g_var, g_val)])
            d = Tuple([Sym("duration"), i, Tuple([Int(1), Inf.pos()])])
            if is_goal:
                goals.append(s)
            else:
                preconditions.append(s)
            temporal.append(d)
            if op_id is not None and g_var in effect_vars:
                temporal.append(Tuple(Sym("before"), i, op_id, Tuple(Int(1), Int(1))))
            elif op_id is not None:
                temporal.append(Tuple(Sym("contains"), i, op_id, Tuple(Int(1), Inf.pos()),Tuple(Int(1), Inf.pos())))

        else:
            fluents = {}
            constraint_term = self._convert_constraint(c, fluents)
            scope = []
            for fluent in fluents.keys():
                self.next_id += 1
                if is_goal:
                    i = Sym("G%d" % self.next_id)
                else:
                    i = Tuple([Sym("P%d" % self.next_id), Var("ID")])
                var = self._convert_fnode(fluent)
                val = fluents[fluent]
                if var != val:
                    s = Tuple([i, KeyVal(var, val)])
                    d = Tuple([Sym("duration"), i, Tuple([Int(1), Inf.pos()])])
                    if is_goal:
                        goals.append(s)
                    else:
                        preconditions.append(s)
                    temporal.append(d)
                    if op_id is not None and var in effect_vars:
                        temporal.append(Tuple(Sym("before"), i, op_id, Tuple(Int(1),  Int(1))))
                    elif op_id is not None:
                        temporal.append(Tuple(Sym("contains"), i, op_id, Tuple(Int(1), Inf.pos()),Tuple(Int(1), Inf.pos())))
                scope.append(fluents[fluent])

            vars = List(scope)
            domains = List([KeyVal(x,
                                     List([Boolean(True),
                                           Boolean(False)]))
                            for x in vars])
            scope = Tuple(scope)
            constraint_exp = [
                KeyVal(Sym("variables"), vars),
                KeyVal(Sym("domains"), domains),
                KeyVal(Sym("constraints"),
                         Set([Tuple([
                             scope,
                             Tuple([
                                 Sym("org.aiddl.eval.lambda"),
                                 scope,
                                 constraint_term])])]))]
            
            
            csp += constraint_exp

        cdb = []
        if len(goals) > 0:
            cdb.append(KeyVal(Sym("goal"), List(goals)))
        if len(statements) > 0:
            cdb.append(KeyVal(Sym("statement"), List(statements)))
        if len(temporal) > 0:
            cdb.append(KeyVal(Sym("temporal"), List(temporal)))
        if len(preconditions) > 0:
            cdb.append(KeyVal(Sym("preconditions"), List(preconditions)))
        if len(csp) > 0:
            cdb.append(KeyVal(Sym("csp"), List(csp)))
            
        return Set(cdb)

    def _convert_effect(self, e, op_id, effect_id, durative=False):
        statement = []
        temporal = []
        interval = Tuple([Sym("E%d" % effect_id), Var('ID')])
        s = Tuple([interval,
                   KeyVal(
                       self._convert_fnode(e.fluent),
                       self._convert_fnode(e.value))])

        d = Tuple([Sym("duration"), interval, Tuple([Int(1), Inf.pos()])])
        m = Tuple([Sym("before"), op_id, interval, Tuple(Int(1),  Int(1))])

        statement.append(s)
        if not durative:
            temporal.append(m)
            m = Tuple(Sym("before"), op_id, interval, Tuple(Int(1),  Int(1)))
        temporal.append(d)
        return Set([
            KeyVal(Sym("effects"), List(statement)),
            KeyVal(Sym("temporal"), List(temporal))])
        
    def _convert_initial_values(self, init_vals):
        statements = []
        temporal = []
        for e in init_vals:
            self.next_id += 1
            interval = Sym("s%d" % self.next_id)
            s = Tuple([interval,
                       KeyVal(
                           self._convert_fnode(e),
                           self._convert_fnode(init_vals[e]))])

            r = Tuple([Sym("release"), interval, Tuple([Int(0), Int(0)])])
            d = Tuple([Sym("duration"), interval, Tuple([Int(1), Inf.pos()])])
            statements.append(s)
            temporal.append(r)
            temporal.append(d)
        return Set([
            KeyVal(Sym("statement"), List(statements)),
            KeyVal(Sym("temporal"), List(temporal))])

    def _convert_goal(self, goal):
        goal_cdb = Set([])
        for g in goal:
            g_cdb = self._convert_condition(g, is_goal=True)
            goal_cdb = merge_cdb(goal_cdb, g_cdb)
        return goal_cdb

    def _convert_operators(self, ops, t_look_up):
        spider_ops = []
        signatures = []
        for o in ops:
            if isinstance(o, InstantaneousAction):
                spider_op = self._convert_instantaneous_action(o, t_look_up)
            else:
                spider_op = self._convert_durative_action(o, t_look_up)

            # print("SPIDER:", Logger.pretty_print(spider_op, 0))

            name = spider_op[Sym("name")]
            signature = spider_op[Sym("signature")]

            if len(signature) == 0:
                signatures.append(KeyVal(name, Sym("t_bool")))
            else:
                # print(signature)
                sig = [name[0]]
                for p in signature:
                    sig.append(p.value)
                signatures.append(KeyVal(Tuple(sig), Sym("t_bool")))

            spider_ops.append(spider_op)
        return Set([
            KeyVal(Sym("operator"), Set(spider_ops)),
            KeyVal(Sym("signature"), Set(signatures)),
        ])

    def _convert_durative_action(self, a, t_look_up):
        # print("-------------------------------------")
        base_name = Sym(a.name)
        id_var = Var('ID')
        op_id = Tuple([base_name, id_var])
        args = [base_name]
        sig = []
        for p in a.parameters:
            x, t = self._convert_parameter(p, t_look_up)
            args.append(x)
            sig.append(KeyVal(x, t))

        if len(args) == 1:
            name = args[0]
        else:
            name = Tuple(args)
        signature = List(sig)

        preconditions = []
        effects = []
        temporal = [Tuple([Sym("duration"), op_id, Tuple([Int(1), Inf.pos()])])]
        csp = []
        for i, cs in a.conditions.items():
            ac = None
            ti1 = i.lower
            ti2 = i.upper

            if ti1.timepoint.kind == TimepointKind.START and ti2.timepoint.kind == TimepointKind.START:
                delay = ti1.delay
                ac = Tuple(Sym("overlaps"), Var("I"), op_id, Tuple(Int(delay), Inf.pos()))
            elif ti1.timepoint.kind == TimepointKind.START and ti2.timepoint.kind == TimepointKind.END:
                ac = Tuple(Sym("contains"), Var("I"), op_id, Tuple(Int(1), Inf.pos()), Tuple(Int(1), Inf.pos()))

            for c in cs:
                self.next_id += 1
                cond_i = Tuple([Sym("P%d" % self.next_id), Var("ID")])
                sub = Substitution()
                sub.add(Var("I"), cond_i)
                ac_sub = ac.substitute(sub)
                self.next_id -= 1
                cond_aiddl = self._convert_condition(c, is_goal=False, op_id=None)
                if cond_aiddl.contains_key(Sym('preconditions')):
                    for p in cond_aiddl[Sym('preconditions')]:
                        preconditions.append(p)
                if cond_aiddl.contains_key(Sym('temporal')):
                    for p in cond_aiddl[Sym('temporal')]:
                        temporal.append(p)
                if cond_aiddl.contains_key(Sym('csp')):
                    for p in cond_aiddl[Sym('csp')]:
                        csp.append(p)
                # print("COND:", cond_aiddl)
                # print("TEMP:", ac_sub)

                temporal.append(ac_sub)

        for i, es in a.effects.items():
            ac = None
            delay = i.delay
            if i.timepoint.kind == TimepointKind.START:
                ac = Tuple(Sym("started-by"), Var("I"), op_id, Tuple(Int(delay), Int(delay)))
            elif i.timepoint.kind == TimepointKind.END:
                ac = Tuple(Sym("before"), op_id, Var("I"), Tuple(Int(delay), Int(delay)))

            for e in es:
                self.next_id += 1
                effect_id = Tuple([Sym("E%d" % self.next_id), Var("ID")])
                sub = Substitution()
                sub.add(Var("I"), effect_id)
                ac_sub = ac.substitute(sub)
                temporal.append(ac_sub)
                constraints = self._convert_effect(e, op_id, self.next_id, durative=True)
                # print("Effect extracted:", constraints)
                if constraints.contains_key(Sym('effects')):
                    for p in constraints[Sym('effects')]:
                        effects.append(p)
                if constraints.contains_key(Sym('temporal')):
                    for p in constraints[Sym('temporal')]:
                        temporal.append(p)

        constraint_list = []
        constraint_list.append(KeyVal(Sym('temporal'), List(temporal)))
        if len(csp) > 0:
            constraint_list.append(KeyVal(Sym('csp'), List(csp)))

        return Tuple([
            KeyVal(Sym('name'), name),
            KeyVal(Sym('signature'), signature),
            KeyVal(Sym('id'), id_var),
            KeyVal(Sym('interval'), op_id),
            KeyVal(Sym('preconditions'), List(preconditions)),
            KeyVal(Sym('effects'), List(effects)),
            KeyVal(Sym('constraints'), List(constraint_list))
        ])


    
    def _convert_instantaneous_action(self, o, t_look_up):
        base_name = Sym(o.name)
        id_var = Var('ID')
        op_id = Tuple([base_name, id_var])
        args = [base_name]
        sig = []
        for p in o.parameters:
            x, t = self._convert_parameter(p, t_look_up)
            args.append(x)
            sig.append(KeyVal(x, t))

        preconditions = []
        effects = []

        temporal = [Tuple([Sym("duration"), op_id, Tuple([Int(1), Inf.pos()])])]

        csp = []

        effect_vars = []
        effect_id = 0
        for e in o.effects:
            effect_id += 1
            constraints = self._convert_effect(e, op_id, effect_id)
            # print("Effect extracted:", constraints)
            if constraints.contains_key(Sym('effects')):
                for p in constraints[Sym('effects')]:
                    effect_vars.append(p[1].key)
                    effects.append(p)
            if constraints.contains_key(Sym('temporal')):
                for p in constraints[Sym('temporal')]:
                    temporal.append(p)

        for p in o.preconditions:
            constraints = self._convert_condition(p, is_goal=False, op_id=op_id, effect_vars=effect_vars)
            if constraints.contains_key(Sym('preconditions')):
                for p in constraints[Sym('preconditions')]:
                    preconditions.append(p)
            if constraints.contains_key(Sym('temporal')):
                for p in constraints[Sym('temporal')]:
                    temporal.append(p)
            if constraints.contains_key(Sym('csp')):
                for p in constraints[Sym('csp')]:
                    csp.append(p)



        if len(args) == 1:
            name = args[0]
        else:
            name = Tuple(args)
        signature = List(sig)

        # print(preconditions)

        constraint_list = []
        constraint_list.append(KeyVal(Sym('temporal'), List(temporal)))
        if len(csp) > 0:
            constraint_list.append(KeyVal(Sym('csp'), List(csp)))

        if isinstance(o, InstantaneousMotionAction):
            #motion:{
            #    (path ?ID ?r ?l1 ?l2 map-1 ?path)
            #}
            motion_constraints = []
            # print("CONVERTING MOTION CONSTRAINTS")
            for mc in o.motion_constraints:
                if isinstance(mc, Waypoints):
                    movable = self._convert_fnode(mc.movable)
                    start = self._convert_fnode(mc.starting)
                    wps = List([self._convert_fnode(wp) for wp in mc.waypoints])
                    # print(movable)

                    map_name = self.map_look_up[mc.starting.type.occupancy_map]

                    c = Tuple(Sym("path"), Var("ID"), movable, start, wps[0], map_name, Var("path"))
                    # print(c)
                    motion_constraints.append(c)
                else:
                    raise ValueError(f"Unsupported motion constraint of type {type(mc)}: {mc}")

                constraint_list.append(KeyVal(Sym('motion'), List(motion_constraints)))

                
        return Tuple([
            KeyVal(Sym('name'), name),
            KeyVal(Sym('signature'), signature),
            KeyVal(Sym('id'), id_var),
            KeyVal(Sym('interval'), op_id),
            KeyVal(Sym('preconditions'), List(preconditions)),
            KeyVal(Sym('effects'), List(effects)),
            KeyVal(Sym('constraints'), List(constraint_list))
        ])

    def _convert_type(self, t, t_look_up):
        type_name = None
        if t.is_bool_type():
            type_name = Sym("t_bool")
            t_look_up[t] = KeyVal(type_name, List([Boolean(True), Boolean(False)]))
        elif t.is_int_type() or t.is_real_type():
            if t.is_int_type():
                range_type = Sym("int")
            else:
                range_type = Sym("real")
            if t.lower_bound is None:
                lb = Inf.neg()
            else:
                if t.is_int_type():
                    lb = Int(t.lower_bound)
                else:
                    lb = Real(t.lower_bound)
            if t.upper_bound is None:
                ub = Inf.pos()
            else:
                if t.is_int_type():
                    ub = Int(t.upper_bound)
                else:
                    ub = Real(t.upper_bound)
            domain = Tuple([Sym("range"), Tuple([lb, ub]), List([KeyVal(Sym("type"), range_type)])])
            self.next_id += 1
            type_name = Sym(f't_range-{self.next_id}')
            t_look_up[t] = KeyVal(type_name, domain)
        else: # UserType
            type_name = Sym(t.name)

        return type_name

    def _convert_parameter(self, p, t_look_up):
        if p not in t_look_up.keys():
            if p.type.is_bool_type():
                t_look_up[p] = KeyVal(Sym("t_bool"), List([Boolean(True), Boolean(False)]))
            elif p.type.is_int_type() or p.type.is_real_type():
                if p.type.is_int_type():
                    range_type = Sym("int")
                else:
                    range_type = Sym("real")
                if p.type.lower_bound is None:
                    lb = Inf.neg()
                else:
                    lb = Num(p.type.lower_bound)
                if p.type.upper_bound is None:
                    ub = Inf.pos()
                else:
                    ub = Num(p.type.lower_bound)
                domain = Tuple([Sym("range"), Tuple([lb, ub]), List([KeyVal(Sym("type"), range_type)])])
                self.next_id += 1
                t_look_up[p.type] = (Sym(f'range-{self.next_id}'), domain)

                return domain
        
        return (Var(p.name), Sym(p.type.name))

    def _convert_user_types(self, problem, type_look_up):
        for utype in problem.user_types:
            name = Sym(utype.name)
            domain = List([self._convert_object(o) for o in problem.objects(utype)])
            type_look_up[utype] = KeyVal(name, domain)

    def _convert_motion_info(self, problem):
        next_map_idx = 0
        constraints = []
        poses = {}

        # print("GETTING MOTION OBJECT INFO")

        for utype in problem.user_types:
            # print(utype, type(utype))
            if utype.is_configuration_type():
                m = utype.occupancy_map

                if m not in self.map_look_up.keys():
                    next_map_idx += 1
                    name = Sym(f"map-{next_map_idx}")
                    self.map_look_up[m] = name

                    # Copy YAML and image file into running Docker container
                    filename = m.filename.split(os.sep)[-1]
                    path = m.filename.replace(filename, "")
                    image_filename = None
                    f = open(m.filename)
                    for l in f.readlines():
                        if "image" in l:
                            image_filename = l.split("image: ")[1].strip()
                    f.close()
                    self.map_files[name] = m.filename
                        
                    cmd_yaml = f'docker cp "{path}{os.sep}{filename}" up-spiderplan-server:/planner/{filename}'
                    cmd_image = f'docker cp "{path}{os.sep}{image_filename}" up-spiderplan-server:/planner/{image_filename}'
                    os.system(cmd_yaml)
                    os.system(cmd_image)

                    constraints.append(Tuple(Sym("map"), name, Str(filename)))
                else:
                    name = self.map_look_up[m]

                if name not in poses.keys():
                    poses[name] = []

                for o in problem.objects(utype):
                    symbol = Sym(o.name)
                    cfg = Tuple([Real(x) for x in list(o.configuration)])
                    poses[name].append(KeyVal(symbol, cfg))

            elif utype.is_movable_type():
                for o in problem.objects(utype):
                    name = Sym(o.name)
                    footprint = List([Tuple(Real(p[0]), Real(p[1])) for p in o.footprint])
                    parameters = []
                    if o.motion_model == MotionModels.REEDSSHEPP:
                        model = Sym("ReedsSheppCar")
                        parameters.append(KeyVal(Sym("turning-radius"), Real(o.parameters["turning_radius"])))
                    else:
                        raise ValueError(f"Motion model {o.motion_model} is not supported by SpiderPlan")
                    constraints.append(Tuple(Sym("frame"), name, footprint))
                    constraints.append(Tuple(Sym("robot"), name, List(
                        KeyVal(Sym("name"), name),
                        KeyVal(Sym("footprint"), footprint),
                        KeyVal(Sym("model"), model),
                        KeyVal(Sym("turning-radius"), Real(o.parameters["turning_radius"]))
                    )))

        for map_name in poses.keys():
            con = Tuple(Sym("poses"), map_name, List(poses[map_name]))
            constraints.append(con)

        return Set([
            KeyVal(Sym("motion"), Set(constraints))
        ])


