import mill._
import mill.scalalib._
import mill.modules.Jvm._
import mill.define.Task
import ammonite.ops._
import ammonite.ops.ImplicitWd._

/** All custom mill configs must extends this */
trait WakeModule extends ScalaModule {
  def wakeModuleDeps: Seq[ScalaModule]
}

trait CommonOptions extends ScalaModule {
  def scalaVersion = "2.12.4"

  def scalacOptions = Seq(
    "-deprecation",
    "-explaintypes",
    "-feature",
    "-language:reflectiveCalls",
    "-unchecked",
    "-Xlint:infer-any",
    //"-Xlint:missing-interpolator",
    "-Xsource:2.11"
  )
  def javacOptions = Seq(
    "-source", "1.8",
    "-target", "1.8"
  )
}

trait SingleJar extends SbtModule {
  // This submodule is unrooted - its source directory is in the top level directory.
  //override def millSourcePath = super.millSourcePath / ammonite.ops.up

  // In order to preserve our "all-in-one" policy for published jars,
  //  we define allModuleSources() to include transitive sources, and define
  //  allModuleClasspath() to include transitive classes.
  def transitiveSources = T {
    Task.traverse(moduleDeps)(m =>
      T.task{m.allSources()}
    )().flatten
  }

  def allModuleSources = T {
    allSources() ++ transitiveSources()
  }

  def transitiveResources = T {
    Task.traverse(moduleDeps)(m =>
      T.task{m.resources()}
    )().flatten
  }

  def allModuleResources = T {
    resources() ++ transitiveResources()
  }

  // We package all classes in a singe jar.
  def allModuleClasspath = T {
    localClasspath() ++ transitiveLocalClasspath()
  }

  // We need to copy (and override) the `jar` and `docJar` targets so we can build
  //  single jars implementing our "all-in-one" policy.
  override def jar = T {
    createJar(
      allModuleClasspath().map(_.path).filter(exists),
      mainClass()
    )
  }

  override def docJar = T {
    val outDir = T.ctx().dest

    val javadocDir = outDir / 'javadoc
    mkdir(javadocDir)

    val files = for{
      ref <- allModuleSources()
      if exists(ref.path)
      p <- (if (ref.path.isDir) ls.rec(ref.path) else Seq(ref.path))
      if (p.isFile && ((p.ext == "scala") || (p.ext == "java")))
    } yield p.toNIO.toString

    val pluginOptions = scalacPluginClasspath().map(pluginPathRef => s"-Xplugin:${pluginPathRef.path}")
    val options = Seq("-d", javadocDir.toNIO.toString, "-usejavacp") ++ pluginOptions ++ scalacOptions()

    if (files.nonEmpty) runSubprocess(
      "scala.tools.nsc.ScalaDoc",
      scalaCompilerClasspath().map(_.path) ++ compileClasspath().filter(_.path.ext != "pom").map(_.path),
      mainArgs = (files ++ options).toSeq
    )

    createJar(Agg(javadocDir), None)(outDir)
  }

  def sourceJar = T {
    createJar((allModuleSources() ++ allModuleResources()).map(_.path).filter(exists), None)
  }
}

// Define our own BuildInfo since mill doesn't currently have one.
trait BuildInfo extends ScalaModule { outer =>

  def buildInfoObjectName: String = "BuildInfo"

  def buildInfoMembers: T[Map[String, String]] = T {
    Map.empty[String, String]
  }

  private def generateBuildInfo(outputPath: Path, members: Map[String, String]) = {
    val outputFile = outputPath / "BuildInfo.scala"
    val packageName = members.getOrElse("buildInfoPackage", "")
    val packageDef = if (packageName != "") {
      s"package ${packageName}"
    } else {
      ""
    }
    val internalMembers =
      members
        .map {
          case (name, value) => s"""  val ${name}: String = "${value}""""
        }
        .mkString("\n")
    write(outputFile,
      s"""
         |${packageDef}
         |case object ${buildInfoObjectName}{
         |$internalMembers
         |  override val toString: String = {
         |    "buildInfoPackage: %s, version: %s, scalaVersion: %s" format (
         |        buildInfoPackage, version, scalaVersion
         |    )
         |  }
         |}
       """.stripMargin)
    outputPath
  }

  override def generatedSources = T {
    super.generatedSources() :+ PathRef(generateBuildInfo(T.ctx().dest, buildInfoMembers()))
  }
}
