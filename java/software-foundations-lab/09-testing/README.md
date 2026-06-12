# Module 09 — Testing

> Goal: write code that you can trust to keep working — JUnit 5 for unit
> tests, Mockito for collaborators, Spring Boot Test for integration.

## What's inside

| Folder                | Topic                                                       |
|-----------------------|-------------------------------------------------------------|
| `unit/`               | Plain JUnit 5: `@Test`, parameterised tests, assertions     |
| `mocks/`              | Mockito: `@Mock`, `when().thenReturn()`, `verify()`         |
| `integration/`        | Spring Boot Test with an in-memory MySQL via Testcontainers |
| `testing-pyramid.md`  | Theory: unit / integration / e2e ratios                     |

## Naming convention

```
methodUnderTest_stateUnderTest_expectedBehavior()

// examples
add_twoPositiveNumbers_returnsSum()
withdraw_amountExceedsBalance_throwsInsufficientFunds()
```

## Exercises

1. Add at least one test for every public method in module 08.
2. Mock the `PaymentGateway` in module 07 and verify it's called exactly
   once per checkout.
3. Use `@ParameterizedTest` with a CSV source to cover edge cases of your
   discount strategy.
