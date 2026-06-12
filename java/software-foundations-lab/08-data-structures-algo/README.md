# Module 08 — Data Structures & Algorithms

> Goal: implement the classic data structures from scratch, measure their
> Big-O behaviour, and know when to reach for each.

## Structures (under `com.lab.dsa.structures`)

| Class                  | What it is                                                  |
|------------------------|-------------------------------------------------------------|
| `ArrayList`            | Resizable array backed by `Object[]`                        |
| `LinkedList`           | Doubly linked list                                          |
| `Stack`                | LIFO on top of `LinkedList`                                 |
| `Queue` / `Deque`      | FIFO on top of `LinkedList`                                 |
| `HashMap`              | Open addressing vs. separate chaining — both versions       |
| `BinarySearchTree`     | Insert / find / inorder traversal                           |
| `MinHeap`              | Binary heap backed by an array                              |
| `Graph`                | Adjacency list, BFS, DFS                                    |

## Algorithms (under `com.lab.dsa.algorithms`)

| File                | Topic                              |
|---------------------|------------------------------------|
| `Sorts.java`        | Bubble, insertion, merge, quick    |
| `Searches.java`     | Linear, binary                     |
| `GraphAlgos.java`   | BFS, DFS, Dijkstra (small grid)    |
| `Dp.java`           | Fibonacci, 0/1 knapsack            |

## Big-O cheat-sheet (`bigO.md`)

| Operation             | Array | LinkedList | HashMap   | BST (balanced) |
|-----------------------|-------|------------|-----------|----------------|
| Random access         | O(1)  | O(n)       | —         | O(log n)       |
| Insert at end         | O(1)* | O(1)       | O(1) avg  | O(log n)       |
| Insert in middle      | O(n)  | O(1)†      | —         | O(log n)       |
| Lookup by key         | O(n)  | O(n)       | O(1) avg  | O(log n)       |

\* amortized.   † if you already hold the node reference.

## Exercises

1. Add a `LRUCache` on top of your `LinkedHashMap`-style implementation.
2. Compare your `HashMap` benchmark numbers with `java.util.HashMap`.
3. Solve "two sum" in O(n) using your hash map.
