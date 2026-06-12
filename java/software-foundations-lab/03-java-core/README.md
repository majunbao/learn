# Module 03 — Java Core

> Goal: be confident with day-to-day Java — syntax, OOP, collections,
> generics, exceptions, IO, concurrency, streams — and understand at a high
> level how the JVM runs your code.

## Package layout

Every topic lives in its own package under `com.lab.javacore`. Each file
has a `public static void main(String[] args)` so you can run it standalone.

| Package        | What it teaches                                          |
|----------------|----------------------------------------------------------|
| `basics`       | Primitive types, control flow, arrays, `String`          |
| `oop`          | Class, encapsulation, inheritance, polymorphism, `record`|
| `collections`  | `List`, `Set`, `Map`, `Queue`, iteration                 |
| `generics`     | Generic class / method, bounded wildcards (`? extends`)  |
| `exceptions`   | Checked vs. unchecked, try-with-resources                |
| `io`           | Files, streams, NIO `Path` / `Files`                     |
| `concurrency`  | `Thread`, `ExecutorService`, `synchronized`, `Atomic*`   |
| `streams`      | Lambdas, method references, `Stream` pipelines           |

## How to run an example

From the project root:

```bash
mvn -pl 03-java-core -am compile
mvn -pl 03-java-core exec:java \
    -Dexec.mainClass=com.lab.javacore.basics.HelloWorld
```

Or open the file in IntelliJ and click the green ▶︎ next to `main`.

## JVM notes

See `src/main/java/com/lab/javacore/jvm-notes.md` for short write-ups on:

* Class loading
* The runtime data areas (heap, stack, metaspace)
* Garbage collection (Serial, Parallel, G1, ZGC)
* `java -XX:+PrintFlagsFinal` and other useful flags

## Exercises

1. Implement a generic `Pair<A, B>` and write tests in module 09.
2. Re-implement `ArrayList.add` (without using the JDK class) — see module 08.
3. Write a producer/consumer using a `BlockingQueue`.
4. Convert any nested `for` loop in your code into a `Stream` pipeline.
