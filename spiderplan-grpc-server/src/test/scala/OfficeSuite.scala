import org.aiddl.common.scala.Common
import org.aiddl.core.scala.container.Container
import org.aiddl.core.scala.parser.Parser
import org.aiddl.core.scala.representation.Sym
import org.scalatest.funsuite.AnyFunSuite
import org.spiderplan.unified_planning.SpiderPlanInstance

class OfficeSuite extends AnyFunSuite {

  test("TAMP Office Test 1") {
    val c = new Container()
    val parser = new Parser(c)
    val mod = parser.parseFile("src/test/resources/office/office-1.aiddl")
    val problem = c.getProcessedValueOrPanic(mod, Sym("problem"))

    val answer = SpiderPlanInstance(problem)
    assert(answer != Common.NIL)
  }

  test("TAMP Office Test 2") {
    val c = new Container()
    val parser = new Parser(c)
    val mod = parser.parseFile("src/test/resources/office/office-2.aiddl")
    val problem = c.getProcessedValueOrPanic(mod, Sym("problem"))

    val answer = SpiderPlanInstance(problem)
    assert(answer != Common.NIL)
  }

}
