package org.spiderplan.unified_planning

import org.aiddl.common.scala.execution.Actor.Status
import org.aiddl.core.scala.util.StopWatch
import org.aiddl.core.scala.container.Container
import org.aiddl.core.scala.representation.{CollectionTerm, KeyVal, ListTerm, Num, Sym, Term}
import org.aiddl.external.grpc.scala.container.ContainerServer
import org.spiderplan.solver.SpiderPlanFactory
import org.aiddl.core.scala.function.Function
import org.aiddl.core.scala.util.logger.Logger
import org.spiderplan.solver.SpiderPlanGraphSearch

import org.aiddl.common.scala.planning.state_variable.heuristic.{CausalGraphHeuristic, FastForwardHeuristic}
import org.aiddl.core.scala.function
import org.aiddl.core.scala.representation.*
import org.spiderplan.solver.Solver.{FlawResolver, Propagator}
import org.spiderplan.solver.causal.{ForwardOpenGoalResolver, OperatorGrounder}
import org.spiderplan.solver.causal.heuristic.{ForwardHeuristicWrapper, HAddReuse}
import org.spiderplan.solver.causal.psp.{OpenGoalResolver, OpenGoalResolverSingleFlaw}
import org.spiderplan.solver.conditional.ConditionalConstraintResolver
import org.spiderplan.solver.csp.{CspPreprocessor, CspResolver}
import org.spiderplan.solver.domain.DomainConstraintSolver
import org.spiderplan.solver.temporal.TemporalConstraintSolver

import scala.concurrent.ExecutionContext
import java.util.logging.Level

object Main extends App {
  object spiderPlan extends Function {
    def apply(cdb: Term): Term = {
      val spiderPlan = new SpiderPlanGraphSearch(
        Vector(
          (new ForwardHeuristicWrapper(new FastForwardHeuristic), Num(1))
          //(new ForwardHeuristicWrapper(new FastForwardHeuristic), Num(0.5))
        )) {
        self: SpiderPlanGraphSearch =>

        override val preprocessors: Vector[function.Function] = Vector(
          new TemporalConstraintSolver,
          new CspPreprocessor {
            logSetName("CSP Preprocessor")
          },
          new OperatorGrounder
        )

        override val propagators: Vector[Propagator] = Vector(
          new DomainConstraintSolver {
            logSetName("Domain")
          },
          new TemporalConstraintSolver //{ setVerbose(verbosityLevel) }
        )

        override val solvers: Vector[FlawResolver] = Vector(
          new CspResolver {
            logSetName("CSP")
          },
          new ForwardOpenGoalResolver(heuristic = None) {
            logSetName("GoalResolver")
            setSeenList(self.seenList)
          },
        )
      }
      spiderPlan.logSetName("SpiderPlan")
      spiderPlan.logConfigRecursive(Level.WARNING)

      StopWatch.recordedTimes.clear()

      val c = new Container()
      val input = c.eval(cdb).asCol

      StopWatch.start("[SpiderPlan] Main")
      val r = spiderPlan.solve(input) match {
        case Some(solution) => solution
        case None => Sym("NIL")
      }
      StopWatch.stop("[SpiderPlan] Main")
      spiderPlan.searchGraph2File("search.dot")
      println(StopWatch.summary)
      r
    }
  }

  val c = new Container()
  c.addFunction(Sym("org.spiderplan.unified-planning.basic-graph-search"), spiderPlan)
  val server = new ContainerServer(ExecutionContext.global, 8011, c)

  server.start()
  server.blockUntilShutdown()
}
