package org.spiderplan.unified_planning

import org.aiddl.common.scala.execution.Actor.Status
import org.aiddl.core.scala.container.Container
import org.aiddl.core.scala.representation.{KeyVal, ListTerm, Num, Sym, Term}
import org.aiddl.external.grpc.scala.container.ContainerServer
import org.spiderplan.solver.SpiderPlanFactory

import org.aiddl.core.scala.function.Function
import scala.concurrent.ExecutionContext
import java.util.logging.Level

@main def runServer = {
  val c = new Container()

  object spiderPlan extends Function {
    def apply(cdb: Term): Term = {
      val spiderPlan = SpiderPlanFactory.fullGraphSearch(cdb.asCol, Level.FINE)

      val input = c.eval(cdb).asCol
      val r = spiderPlan.solve(input) match {
        case Some(solution) => solution
        case None => Sym("NIL")
      }
      spiderPlan.searchGraph2File("search.dot")
      r
    }
  }

  c.addFunction(Sym("org.spiderplan.unified-planning.basic-graph-search"), spiderPlan)

  val server = new ContainerServer(ExecutionContext.global, 8011, c)

  server.start()
  server.blockUntilShutdown()
}
