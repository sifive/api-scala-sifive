package test

import scala.io.Source

object Main extends App {
  val contents = Source.fromResource("file.txt").mkString.trim
  assert(contents == "foo")
}
