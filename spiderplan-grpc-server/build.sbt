val scala3Version = "3.1.2"

lazy val root = project
  .in(file("."))
  .settings(
      name := "up-spiderplan-server",
      version := "0.1.0",
      organization := "org.spiderplan",

      assemblyMergeStrategy := {
          case PathList("META-INF", xs @ _*) => MergeStrategy.discard
          case x if x.contains("io.netty.versions.properties") => MergeStrategy.discard
          case _ => MergeStrategy.deduplicate
      },

      mainClass in (Compile, run) := Some("org.spiderplan.unified_planning.Main"),
      mainClass in (Compile, packageBin) := Some("org.spiderplan.unified_planning.Main"),

      isSnapshot := true,

      resolvers += Resolver.mavenCentral,
      resolvers += Resolver.mavenLocal,
      resolvers += Resolver.jcenterRepo,
      resolvers += "jitpack Repo" at "https://jitpack.io/",
      resolvers += "rosjava Repo" at "https://github.com/rosjava/rosjava_mvn_repo/raw/master/",

      parallelExecution := false,

      libraryDependencies += "org.scalactic" %% "scalactic" % "3.2.9",
      libraryDependencies += "org.scalatest" %% "scalatest" % "3.2.9" % "test",
      libraryDependencies += "org.aiddl" % "aiddl-common-scala" % "1.0.0-SNAPSHOT",
      libraryDependencies += "org.aiddl" % "aiddl-core-scala" % "1.0.0-SNAPSHOT",
      libraryDependencies += "org.aiddl" % "aiddl-external-grpc-scala" % "0.1.0-SNAPSHOT",
      libraryDependencies += "org.aiddl" % "aiddl-external-coordination_oru" % "0.1.0-SNAPSHOT",
      libraryDependencies += "org.spiderplan" % "spiderplan" % "0.3.0-SNAPSHOT",
      libraryDependencies += "org.spiderplan" % "spiderplan_coorination_oru" % "0.1.0-SNAPSHOT",
        libraryDependencies += "io.grpc" % "grpc-netty-shaded" % "1.51.0",
    libraryDependencies += "io.grpc" % "grpc-netty" % "1.51.0",

        scalaVersion := scala3Version


  )
