package example

import org.json4s._
import org.json4s.native.JsonMethods._

object Main extends App {
  val obj = parse("""{"key": "value"}""")
  assert(obj \ "key" == JString("value"))
  println("Success")
}
