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

    libraryDependencies += "org.aiddl" % "aiddl-common-scala" % "1.0.0-SNAPSHOT",
    libraryDependencies += "org.aiddl" % "aiddl-core-scala" % "1.0.0-SNAPSHOT",
    libraryDependencies += "org.aiddl" % "aiddl-external-grpc-scala" % "0.1.0-SNAPSHOT",
    libraryDependencies += "org.spiderplan" % "spiderplan" % "0.3.0-SNAPSHOT"
  )
