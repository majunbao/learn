# Module 07 — Design Patterns

> Goal: recognise the classic Gang-of-Four patterns when you see them and
> know when *not* to use them. Every example uses a bookstore scenario so
> you can compare apples-to-apples.

## Patterns covered

| Category    | Pattern             | Bookstore example                                           |
|-------------|---------------------|-------------------------------------------------------------|
| Creational  | Singleton           | `ConfigRegistry`                                            |
|             | Factory Method      | `PaymentGatewayFactory.of("STRIPE")`                        |
|             | Builder             | `OrderBuilder` to assemble an order step by step            |
|             | Prototype           | Clone a draft order                                         |
| Structural  | Adapter             | Adapt a legacy `OldPaymentApi` to the new `PaymentGateway`  |
|             | Decorator           | Add gift-wrap on top of `ShippingService`                   |
|             | Facade              | `CheckoutFacade` coordinates stock, payment, shipping       |
|             | Proxy               | Lazy-loading proxy for `Book.cover`                         |
| Behavioral  | Strategy            | Swap discount strategies at checkout                        |
|             | Observer            | Notify subscribers when stock returns                       |
|             | Template Method     | `AbstractImporter` for CSV / XLSX importers                 |
|             | State               | `Order` transitions: NEW → PAID → SHIPPED → DELIVERED       |
|             | Chain of Responsibility | Validation pipeline before checkout                     |

## Anti-pattern alert

> "When all you have is a hammer, everything looks like a nail."

Don't introduce a pattern just because you learned it. Each example file
ends with a "**When NOT to use this**" section.
