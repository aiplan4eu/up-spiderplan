package org.spiderplan.unified_planning

import org.aiddl.common.scala.execution.Actor.Status
import org.aiddl.core.scala.container.Container
import org.aiddl.core.scala.representation.{KeyVal, ListTerm, Num, Sym, Term}
import org.aiddl.external.grpc.function_call.AiddlGrpcServer
import org.spiderplan.solver.SpiderPlanFactory

import scala.concurrent.ExecutionContext

def spiderPlanFunction(cdb: Term): Term = {
  val spiderplan = SpiderPlanFactory.fullGraphSearch(cdb.asCol, 0)
  spiderplan.solve(cdb.asCol) match {
    case Some(solution) => solution
    case None => Sym("NIL")
  }
}

@main def runServer = {
  val c = new Container()

  c.addFunction(Sym("org.spiderplan.unified-planning.basic-graph-search"), spiderPlanFunction)

  val server = new AiddlGrpcServer(ExecutionContext.global, 8011, c)

  server.start()
  server.blockUntilShutdown()

}
