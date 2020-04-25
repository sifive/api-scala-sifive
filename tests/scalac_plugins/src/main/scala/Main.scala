package test

import com.github.ghik.silencer.silent

object Util {
  @deprecated("Old", "1.0.0")
  def oldAPI(): Unit = println("Hello World!")
}

// The deprecation warning should be suppressed if compiler plugin is working
@silent
object Main extends App {
  Util.oldAPI()
}
