package test

class Foo

object Main extends App {
  val foo = new Foo {
    val x = 3
  }
  println(foo.x) // Reflective call will warn
}
