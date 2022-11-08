package org.spiderplan.unified_planning

import org.aiddl.common.scala.execution.Actor.Status
import org.aiddl.core.scala.container.Container
import org.aiddl.core.scala.representation.{KeyVal, ListTerm, Num, Sym, Term}
import org.aiddl.external.grpc.scala.container.ContainerServer
import org.spiderplan.solver.SpiderPlanFactory

import scala.concurrent.ExecutionContext

@main def runServer = {
  val c = new Container()

  def spiderPlanFunction(cdb: Term): Term = {
    val spiderplan = SpiderPlanFactory.fullGraphSearch(cdb.asCol, 2)

    val input = c.eval(cdb).asCol
      spiderplan.solve(input) match {
        case Some(solution) => solution
        case None => Sym("NIL")
      }
  }

  c.addFunction(Sym("org.spiderplan.unified-planning.basic-graph-search"), spiderPlanFunction)

  val server = new ContainerServer(ExecutionContext.global, 8011, c)

  server.start()
  server.blockUntilShutdown()

}
