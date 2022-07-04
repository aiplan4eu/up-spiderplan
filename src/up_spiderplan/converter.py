from unified_planning.test.examples import get_example_problems
from unified_planning.model.operators import OperatorKind

from aiddl_core.representation import Sym
from aiddl_core.representation import Boolean
from aiddl_core.representation import Tuple
from aiddl_core.representation import List
from aiddl_core.representation import Set
from aiddl_core.representation import Int
from aiddl_core.representation import KeyValue
from aiddl_core.representation import Var
from aiddl_core.representation import Infinity


OpMap = {}
OpMap[OperatorKind.AND] = Sym("and")
OpMap[OperatorKind.OR] = Sym("or")
OpMap[OperatorKind.NOT] = Sym("not")
OpMap[OperatorKind.IMPLIES] = Sym("implies")
OpMap[OperatorKind.IFF] = Sym("iff")
OpMap[OperatorKind.EXISTS] = Sym("exists")
OpMap[OperatorKind.FORALL] = Sym("forall")
OpMap[OperatorKind.PLUS] = Sym("+")
OpMap[OperatorKind.MINUS] = Sym("-")
OpMap[OperatorKind.TIMES] = Sym("*")
OpMap[OperatorKind.DIV] = Sym("div")
OpMap[OperatorKind.EQUALS] = Sym("=")
OpMap[OperatorKind.LE] = Sym("<=")
OpMap[OperatorKind.LT] = Sym("<")

class UpCdbConverter:
    def __init__(self):
        self.next_id = 0

    def __call__(self, problem):
        init = self._convert_initial_values(problem.initial_values)
        print(init)
        goal = self._convert_goal(problem.goals)
        print(goal)


    def _convert_fnode(self, n):
        print("=== FNODE: %s ===" % (str(n)))
        term = None

        if n.is_fluent_exp():
            if len(n.args) == 0:
                term = Sym(str(n))
        elif n.is_bool_constant():
            term = Boolean(n.bool_constant_value())
        elif n.is_int_constant():
            term = Int(n.int_constant_value())

        if term is None:
            raise ValueError("Fluent not supported: %s" % str(n))

        print("=== TERM: %s ===" % (str(term)))
        return term

    def _convert_constraint(self, c, fluents):
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
        return term

    def _convert_condition(self, c, is_goal=True):
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
        
        if c.is_fluent_exp() or c.is_not():
            self.next_id += 1
            if is_goal:
                i = Sym("G%d" % self.next_id)
            else:
                i = Tuple([Sym("P%d" % self.next_id), Var("ID")])
            if c.is_not():
                g_var = self._convert_fnode(c.args()[0])
            else:
                g_var = self._convert_fnode(c)
            g_val = Boolean(not c.is_not())
            
            s = Tuple([i, KeyValue(g_var, g_val)])
            d = Tuple([Sym("duration"), i, Tuple([Int(1), Infinity.pos()])])
            if is_goal:
                goals.append(s)
            else:
                preconditions.append(s)
            temporal.append(d)
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
                s = Tuple([i, KeyValue(var, val)])
                d = Tuple([Sym("duration"), i, Tuple([Int(1), Infinity.pos()])])
                if is_goal:
                    goals.append(s)
                else:
                    preconditions.append(s)
                temporal.append(d)
                scope.append(fluents[fluent])

            vars = List(scope)
            domains = List([KeyValue(x,
                                     List([Boolean(True),
                                           Boolean(False)]))
                            for x in vars])
            scope = Tuple(scope)
            constraint_exp = List([
                KeyValue(Sym("variables"), vars),
                KeyValue(Sym("domains"), domains),
                KeyValue(Sym("constraints"),
                         Set([Tuple([
                             scope,
                             Tuple([
                                 Sym("lambda"),
                                 scope,
                                 constraint_term])])]))])
            
            
            csp.append(constraint_exp)
            print(constraint_exp)
            print(fluents)

        cdb = []
        if len(goals) > 0:
            cdb.append(KeyValue(Sym("goal"), List(goals)))
        if len(statements) > 0:
            cdb.append(KeyValue(Sym("statement"), List(statements)))
        if len(temporal) > 0:
            cdb.append(KeyValue(Sym("temporal"), List(temporal)))
        if len(preconditions) > 0:
            cdb.append(KeyValue(Sym("preconditions"), List(preconditions)))
        if len(csp) > 0:
            cdb.append(KeyValue(Sym("csp"), List(csp)))
            
        return Set(cdb)
        
    def _convert_initial_values(self, init_vals):
        statements = []
        temporal = []
        for e in init_vals:
            self.next_id += 1
            interval = Sym("s%d" % self.next_id)
            s = Tuple([interval,
                       KeyValue(
                           self._convert_fnode(e),
                           self._convert_fnode(init_vals[e]))])

            r = Tuple([Sym("release"), interval, Tuple([Int(0), Int(0)])])
            d = Tuple([Sym("duration"), interval, Tuple([Int(1), Infinity.pos()])])
            statements.append(s)
            temporal.append(r)
            temporal.append(d)
        return Set([
            KeyValue(Sym("statement"), List(statements)),
            KeyValue(Sym("temporal"), List(temporal))])

    def _convert_goal(self, goal):
        cdbs = []
        for g in goal:
            g_cdb = self._convert_condition(g, is_goal=True)
            cdbs.append(g_cdb)
        return cdbs
