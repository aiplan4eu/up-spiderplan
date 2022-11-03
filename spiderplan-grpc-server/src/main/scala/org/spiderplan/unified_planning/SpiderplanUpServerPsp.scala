package org.spiderplan.unified_planning

import org.aiddl.common.scala.execution.Actor.Status
import org.aiddl.core.scala.container.Container
import org.aiddl.core.scala.function.Function
import org.aiddl.core.scala.representation.*
import org.aiddl.external.grpc.scala.function_call.AiddlGrpcServer
import org.spiderplan.solver._
import org.aiddl.common.scala.planning.state_variable.heuristic.CausalGraphHeuristic
import org.aiddl.core.scala.function
import org.aiddl.core.scala.representation.*
import org.spiderplan.solver.Solver.{FlawResolver, Propagator}
import org.spiderplan.solver.causal.{ForwardOpenGoalResolver, OperatorGrounderFull}
import org.spiderplan.solver.causal.heuristic.{ForwardHeuristicWrapper, HAddReuse}
import org.spiderplan.solver.causal.psp.{OpenGoalResolver, OpenGoalResolverSingleFlaw}
import org.spiderplan.solver.conditional.ConditionalConstraintResolver
import org.spiderplan.solver.csp.{CspPreprocessor, CspResolver}
import org.spiderplan.solver.domain.DomainConstraintSolver
import org.spiderplan.solver.temporal.TemporalConstraintSolver

import scala.concurrent.ExecutionContext

@main def runServerPsp = {
  val c = new Container()
  val verbosityLevel = 2

  object spiderPlan extends Function {
    def apply(cdb: Term): Term = {
      val subSolver: SpiderPlanTreeSearch = new SpiderPlanTreeSearch {
        override val preprocessors: Vector[function.Function] = Vector.empty
        override val propagators: Vector[Propagator] = Vector(
          new DomainConstraintSolver {
            setVerbose("Domain", verbosityLevel)
          },
          new TemporalConstraintSolver //{ setVerbose(verbosityLevel) }
        )
        override val solvers: Vector[FlawResolver] = Vector(
        )
      }

      val spiderPlan = new SpiderPlanGraphSearch {
        setVerbose("Spider", verbosityLevel)
        //this.includePathLength = true
        override val preprocessors: Vector[function.Function] = Vector(
          new TemporalConstraintSolver,
          new CspPreprocessor {
            setVerbose("CspPreprocessor", verbosityLevel)
          },
          new OperatorGrounderFull
        )

        override val propagators: Vector[Propagator] = Vector(
          new DomainConstraintSolver {
            setVerbose("Domain", verbosityLevel)
          },
          new TemporalConstraintSolver //{ setVerbose(verbosityLevel) }
        )

        override val solvers: Vector[FlawResolver] = Vector(
          new CspResolver {
            setVerbose("CSP", verbosityLevel)
          },
          new ForwardOpenGoalResolver(heuristic = None) {
            setVerbose("GoalResolver", verbosityLevel)
          },
          new ConditionalConstraintResolver(subSolver) {
            setVerbose("Conditional", verbosityLevel)
          }
        )

        override val heuristics: Vector[Heuristic] = Vector(
          new HAddReuse //{ setVerbose(verbosityLevel) }
          //new ForwardHeuristicWrapper(new CausalGraphHeuristic)
        )
      }

      val input = c.eval(cdb).asCol
      spiderPlan.solve(input) match {
        case Some(solution) => solution
        case None => Sym("NIL")
      }
    }
  }

  c.addFunction(Sym("org.spiderplan.unified-planning.basic-graph-search"), spiderPlan)

  val server = new AiddlGrpcServer(ExecutionContext.global, 8011, c)

  server.start()
  server.blockUntilShutdown()
}
