package org.spiderplan.unified_planning

import org.aiddl.common.scala.execution.Actor.Status
import org.aiddl.core.scala.container.Container
import org.aiddl.core.scala.representation.{KeyVal, ListTerm, Num, Sym, Term}
import org.aiddl.external.grpc.scala.container.ContainerServer
import org.aiddl.external.grpc.scala.function_call.AiddlGrpcServer
import org.spiderplan.solver.SpiderPlanFactory

import org.aiddl.core.scala.function.Function
import scala.concurrent.ExecutionContext

@main def runServer = {
  val c = new Container()

  object spiderPlan extends Function {
    def apply(cdb: Term): Term = {
      val spiderPlan = SpiderPlanFactory.fullGraphSearch(cdb.asCol, 2)

      val input = c.eval(cdb).asCol
      spiderPlan.solve(input) match {
        case Some(solution) => solution
        case None => Sym("NIL")
      }
    }
  }

  c.addFunction(Sym("org.spiderplan.unified-planning.basic-graph-search"), spiderPlan)

  val server = new ContainerServer(ExecutionContext.global, 8011, c)

  server.start()
  server.blockUntilShutdown()
}
