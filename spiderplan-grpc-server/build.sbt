val scala3Version = "3.1.2"

lazy val root = project
  .in(file("."))
  .settings(
    name := "up-spiderplan-server",
    version := "0.1.0",
    organization := "org.spiderplan",

    isSnapshot := true,
    scalaVersion := scala3Version,

    resolvers += Resolver.mavenLocal,

    parallelExecution := false,

    libraryDependencies += "org.scalactic" %% "scalactic" % "3.2.9",
    libraryDependencies += "org.scalatest" %% "scalatest" % "3.2.9" % "test",
    libraryDependencies += "org.scala-lang.modules" %% "scala-swing" % "3.0.0",
    libraryDependencies += "org.aiddl" % "aiddl-common-scala_3" % "2.1.0",
    libraryDependencies += "org.aiddl" % "aiddl-core-scala_3" % "2.1.0",
    libraryDependencies += "org.aiddl" % "aiddl-util-scala_3" % "2.1.0",
    libraryDependencies += "org.aiddl" % "aiddl-external-grpc-scala_3" % "0.1.0",
    libraryDependencies += "org.spiderplan" % "spiderplan_3" % "0.3.0"
  )
