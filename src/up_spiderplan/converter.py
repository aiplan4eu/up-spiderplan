import unified_planning.model.problem
from unified_planning.test.examples import get_example_problems
from unified_planning.model.operators import OperatorKind
from unified_planning.model.problem import Problem

from aiddl_core.representation import Sym, Num, Real
from aiddl_core.representation import Boolean
from aiddl_core.representation import Tuple
from aiddl_core.representation import List
from aiddl_core.representation import Set
from aiddl_core.representation import Int
from aiddl_core.representation import KeyVal
from aiddl_core.representation import Var
from aiddl_core.representation import Infinity

from aiddl_core.tools.logger import Logger

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
        k_a = kvp.get_key()
        if b.contains_key(k_a):
            result[k_a] = kvp.get_value().add_all(b[k_a])
        else:
            result[k_a] = kvp.get_value()

    for kvp in b:
        print(kvp)
        k_b = kvp.get_key()
        if k_b not in result.keys():
            result[k_b] = kvp.get_value()

    r = []
    for k in result.keys():
        r.append(KeyVal(k, result[k]))
    return Set(set(r)) #  for k, v in result])
        
        
class UpCdbConverter:

    def __init__(self):
        self.next_id = 0

    def __call__(self, problem):
        cdb = Set([])
        init = self._convert_initial_values(problem.initial_values)
        print(init)
        cdb = merge_cdb(cdb, init)
        goal = self._convert_goal(problem.goals)
        cdb = merge_cdb(cdb, goal)
        
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
            signature = [self._convert_type(s.type) for s in f.signature]
            if len(signature) == 0:
                signatures.append(KeyVal(name, r_type))
            else:
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

    def _convert_condition(self, c, is_goal=True, op_id=None):
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
            d = Tuple([Sym("duration"), i, Tuple([Int(1), Infinity.pos()])])
            if is_goal:
                goals.append(s)
            else:
                preconditions.append(s)
            temporal.append(d)
            if op_id is not None:
                temporal.append(Tuple([Sym("meets"), i, op_id]))
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
                    d = Tuple([Sym("duration"), i, Tuple([Int(1), Infinity.pos()])])
                    if is_goal:
                        goals.append(s)
                    else:
                        preconditions.append(s)
                    temporal.append(d)
                    if op_id is not None:
                        temporal.append(Tuple([Sym("meets"), i, op_id]))
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

    def _convert_effect(self, e, op_id, effect_id):
        statement = []
        temporal = []
        interval = Tuple([Sym("E%d" % effect_id), Var('ID')])
        s = Tuple([interval,
                   KeyVal(
                       self._convert_fnode(e.fluent),
                       self._convert_fnode(e.value))])

        d = Tuple([Sym("duration"), interval, Tuple([Int(1), Infinity.pos()])])
        m = Tuple([Sym("meets"), op_id, interval])
        statement.append(s)
        temporal.append(m)
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
            d = Tuple([Sym("duration"), interval, Tuple([Int(1), Infinity.pos()])])
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
            spider_op = self._convert_operator(o, t_look_up)

            name = spider_op[Sym("name")]
            signature = spider_op[Sym("signature")]

            if len(signature) == 0:
                signatures.append(KeyVal(name, Sym("t_bool")))
            else:
                sig = [name]
                for p in signature:
                    sig.append(p.get_value())
                signatures.append(KeyVal(Tuple(sig), Sym("t_bool")))

            spider_ops.append(spider_op)
        return Set([
            KeyVal(Sym("operator"), Set(spider_ops)),
            KeyVal(Sym("signature"), Set(signatures)),
        ])
    
    def _convert_operator(self, o, t_look_up):
        base_name = Sym(o.name)
        id_var = Var('ID')
        op_id = Tuple([base_name, id_var])
        args = [base_name]
        sig = []
        for p in o.parameters:
            x, t = self._convert_parameter(p, t_look_up)
            args.append(x)
            sig.append(t)

        preconditions = []
        effects = []
        temporal = [Tuple([Sym("duration"), op_id, Tuple([Int(1), Infinity.pos()])])]
        csp = []
        for p in o.preconditions:
            constraints = self._convert_condition(p, is_goal=False, op_id=op_id)
            if constraints.contains_key(Sym('preconditions')):
                for p in constraints[Sym('preconditions')]:
                    preconditions.append(p)
            if constraints.contains_key(Sym('temporal')):
                for p in constraints[Sym('temporal')]:
                    temporal.append(p)
            if constraints.contains_key(Sym('csp')):
                for p in constraints[Sym('csp')]:
                    csp.append(p)

        effect_id = 0
        for e in o.effects:
            effect_id += 1
            constraints = self._convert_effect(e, op_id, effect_id)
            print("Effect extracted:", constraints)
            if constraints.contains_key(Sym('effects')):
                for p in constraints[Sym('effects')]:
                    effects.append(p)
            if constraints.contains_key(Sym('temporal')):
                for p in constraints[Sym('temporal')]:
                    temporal.append(p)

        if len(args) == 1:
            name = args[0]
        else:
            name = Tuple(args)
        signature = List(sig)

        print(preconditions)

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
                lb = Infinity.neg()
            else:
                if t.is_int_type():
                    lb = Int(t.lower_bound)
                else:
                    lb = Real(t.lower_bound)
            if t.upper_bound is None:
                ub = Infinity.pos()
            else:
                if t.is_int_type():
                    ub = Int(t.upper_bound)
                else:
                    ub = Real(t.upper_bound)
            domain = Tuple([Sym("range"), Tuple([lb, ub]), List([KeyVal(Sym("type"), range_type)])])
            self.next_id += 1
            type_name = Sym(f't_range-{self.next_id}')
            t_look_up[t] = KeyVal(type_name, domain)

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
                    lb = Infinity.neg()
                else:
                    lb = Num(p.type.lower_bound)
                if p.type.upper_bound is None:
                    ub = Infinity.pos()
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
            domain = [self._convert_object(o) for o in problem.objects(utype)]
            type_look_up[utype] = (name, domain)
            
