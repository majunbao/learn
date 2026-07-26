# 02 — Basic Components of Programming Languages

> Syllabus reference: P8–P19
>
> Every programming language, regardless of paradigm, shares a common
> set of **basic components**: data types, operators, control structures,
> and subprograms. The exam tests your ability to identify and classify
> these components across different languages.

---

## 1. Data Types (数据类型)

### 1.1 Primitive types

| Type | Chinese | Typical size | Example |
|------|---------|-------------|---------|
| Integer | 整型 | 4 bytes | `int x = 42;` |
| Float / Double | 浮点型 | 4 / 8 bytes | `double y = 3.14;` |
| Boolean | 布尔型 | 1 byte | `bool flag = true;` |
| Character | 字符型 | 1 byte | `char c = 'A';` |

### 1.2 Composite / structured types

| Type | Chinese | Description | Example |
|------|---------|-------------|---------|
| Array | 数组 | Fixed-size collection of same-type elements | `int a[10];` |
| Record / Struct | 记录 / 结构体 | Collection of named fields (possibly different types) | `struct Point { int x; int y; };` |
| Union | 联合体 | Overlapping fields sharing memory | `union Data { int i; float f; };` |
| String | 字符串 | Sequence of characters | `"hello"` |
| Enum | 枚举 | Named integer constants | `enum Color { RED, GREEN, BLUE };` |
| Pointer | 指针 | Address of another variable | `int *p = &x;` |

### 1.3 Type systems

| Property | Chinese | Description |
|----------|---------|-------------|
| **Static typing** | 静态类型 | Types checked at compile time (C, Java, C++) |
| **Dynamic typing** | 动态类型 | Types checked at run time (Python, Ruby) |
| **Strong typing** | 强类型 | No implicit type coercion (Python, Java) |
| **Weak typing** | 弱类型 | Implicit type coercion allowed (C, JavaScript) |

> Exam tip: **static vs dynamic** = when types are checked; **strong
> vs weak** = how strictly types are enforced. These are independent
> axes.

### 1.4 Type compatibility

| Concept | Chinese | Meaning |
|---------|---------|---------|
| **Type equivalence (name)** | 名字等价 | Two types are the same only if they have the same name |
| **Type equivalence (structural)** | 结构等价 | Two types are the same if they have the same structure |
| **Type coercion** | 类型转换 / 隐式转换 | Automatic conversion from one type to another |
| **Type casting** | 强制类型转换 | Explicit conversion by the programmer |

---

## 2. Operators (运算符)

### 2.1 Classification

| Category | Operators | Chinese |
|----------|-----------|---------|
| Arithmetic | `+ − * / %` | 算术运算符 |
| Relational | `< > <= >= == !=` | 关系运算符 |
| Logical | `&& \|\| !` | 逻辑运算符 |
| Bitwise | `& \| ^ ~ << >>` | 位运算符 |
| Assignment | `= += -= *=` | 赋值运算符 |
| Conditional | `? :` | 条件运算符 |

### 2.2 Operator precedence (high → low)

```
1. ()  []  .  →
2. !  ~  ++  --  (type)  sizeof     (unary)
3. *  /  %
4. +  −
5. <<  >>
6. <  <=  >  >=
7. ==  !=
8. &
9. ^
10. |
11. &&
12. ||
13. ?:
14. =  +=  −=  *=  /=  %=
15. ,
```

> Exam tip: precedence questions are common. When in doubt, use
> parentheses.

### 2.3 Associativity

| Direction | Operators | Example |
|-----------|-----------|---------|
| Left to right | Most binary ops | `a − b − c = (a − b) − c` |
| Right to left | Assignment, unary, `?:` | `a = b = c → a = (b = c)` |

---

## 3. Control Structures (控制结构)

### 3.1 The three fundamental structures

Every program can be built from just three structures (Böhm-Jacopini
theorem):

| Structure | Chinese | Description |
|-----------|---------|-------------|
| **Sequence** | 顺序 | Execute statements one after another |
| **Selection** | 选择 | Choose between alternative paths |
| **Repetition / Iteration** | 循环 | Repeat a block of statements |

### 3.2 Selection structures

| Type | Chinese | Example |
|------|---------|---------|
| **if-else** | 双分支选择 | `if (x > 0) ... else ...` |
| **if-else if-else** | 多分支选择 | `if (...) else if (...) else ...` |
| **switch-case** | 开关语句 | `switch (x) { case 1: ... }` |

### 3.3 Repetition structures

| Type | Chinese | When to test | Minimum iterations |
|------|---------|-------------|-------------------|
| **while** | 当型循环 | Before body | 0 |
| **do-while** | 直到型循环 | After body | 1 |
| **for** | 计数循环 | Before body | 0 |

> Exam tip: **while** tests first (may execute 0 times); **do-while**
> tests after (always executes at least once).

### 3.4 Loop control

| Statement | Chinese | Effect |
|-----------|---------|--------|
| `break` | 跳出循环 | Exit the innermost loop immediately |
| `continue` | 继续下一次 | Skip to the next iteration |

---

## 4. Subprograms (子程序)

### 4.1 Functions and procedures

| Type | Chinese | Returns a value? | Example |
|------|---------|------------------|---------|
| **Function** | 函数 | Yes | `int add(int a, int b) { return a+b; }` |
| **Procedure** | 过程 | No | `void print(String s) { ... }` |

### 4.2 Subprogram features

| Feature | Chinese | Description |
|---------|---------|-------------|
| **Parameter** | 参数 / 形参 | Variable in the subprogram declaration |
| **Argument** | 实参 | Actual value passed when calling |
| **Return value** | 返回值 | Result sent back to the caller |
| **Side effect** | 副作用 | Modification of non-local state |

### 4.3 Parameter types

| Type | Chinese | Description |
|------|---------|-------------|
| **Formal parameter** | 形式参数 (形参) | Variable in the function signature |
| **Actual parameter** | 实际参数 (实参) | Value/expression passed at call site |
| **Default parameter** | 默认参数 | Value used if no argument is provided |
| **Variable-length parameter** | 可变参数 | Accepts a variable number of arguments |

---

## 5. Scope and Lifetime (作用域与生存期)

### 5.1 Scope

| Type | Chinese | Description |
|------|---------|-------------|
| **Local scope** | 局部作用域 | Variable visible only within the block/function |
| **Global scope** | 全局作用域 | Variable visible throughout the program |
| **Block scope** | 块作用域 | Variable visible only within `{ }` |
| **Static scope (lexical)** | 静态作用域 | Determined by program text (most languages) |
| **Dynamic scope** | 动态作用域 | Determined by call chain (some Lisps, Bash) |

### 5.2 Lifetime

| Type | Chinese | When allocated | When freed |
|------|---------|---------------|-----------|
| **Automatic** | 自动变量 | On function entry | On function exit |
| **Static** | 静态变量 | Program start | Program end |
| **Heap (dynamic)** | 堆变量 | `malloc` / `new` | `free` / `delete` / GC |

> Exam tip: **scope** ≠ **lifetime**. A static variable inside a
> function has local scope but program-long lifetime.

---

## 6. Worked Examples

**Example 1:** What is the output?

```c
int x = 10;
void foo() {
    int x = 20;
    printf("%d ", x);
}
int main() {
    foo();
    printf("%d\n", x);
    return 0;
}
```

```
Output: 20 10
(Inside foo, local x shadows global x. After foo returns, global x is still 10.)
```

**Example 2:** What is the output?

```c
void bar() {
    static int count = 0;
    count++;
    printf("%d ", count);
}
int main() {
    bar(); bar(); bar();
    return 0;
}
```

```
Output: 1 2 3
(static variable retains its value between calls)
```

---

## 7. Exam-Style Questions

**Q1.** Static typing means types are checked at:
A. run time  B. compile time  C. link time  D. load time
> Answer: B.

**Q2.** A do-while loop executes its body at least:
A. 0 times  B. 1 time  C. 2 times  D. depends on condition
> Answer: B.

**Q3.** A static variable inside a function has:
A. global scope, program-long lifetime  B. local scope, program-long lifetime  C. local scope, function lifetime  D. global scope, function lifetime
> Answer: B.

**Q4.** Name equivalence means two types are the same if:
A. they have the same structure  B. they have the same name  C. they have the same size  D. they are compatible
> Answer: B.

**Q5.** Which control structure is NOT one of the three fundamental
structures?
A. Sequence  B. Selection  C. Repetition  D. Goto
> Answer: D (goto is not a fundamental structured programming construct).

**Q6.** In the expression `a + b * c`, multiplication is evaluated
first because:
A. it appears first  B. `*` has higher precedence than `+`  C. left-to-right associativity  D. right-to-left associativity
> Answer: B.

---

## 8. Further Reading

* Sebesta — *Concepts of Programming Languages*, ch. 5–6.
* Tucker & Noonan — *Programming Languages: Principles and Paradigms*,
  ch. 3–4.

---

## 9. Chinese-English Glossary (中英术语对照)

| English | 中文 | Chapter |
|---------|------|---------|
| Data type | 数据类型 | 02 |
| Primitive type | 基本类型 | 02 |
| Composite type | 构造类型 | 02 |
| Static typing | 静态类型 | 02 |
| Dynamic typing | 动态类型 | 02 |
| Strong typing | 强类型 | 02 |
| Weak typing | 弱类型 | 02 |
| Type coercion | 隐式类型转换 | 02 |
| Operator precedence | 运算符优先级 | 02 |
| Associativity | 结合性 | 02 |
| Sequence | 顺序结构 | 02 |
| Selection | 选择结构 | 02 |
| Repetition / Iteration | 循环结构 | 02 |
| Subprogram | 子程序 | 02 |
| Formal parameter | 形式参数 / 形参 | 02 |
| Actual parameter | 实际参数 / 实参 | 02 |
| Scope | 作用域 | 02 |
| Lifetime | 生存期 | 02 |
| Static variable | 静态变量 | 02 |
| Automatic variable | 自动变量 | 02 |
