# Module 05 — Web & HTTP / Networking

> Goal: understand how computers talk to each other and how a modern web
> application uses that to expose features over HTTP.

## Topics

| Folder                   | What you'll build                                            |
|--------------------------|--------------------------------------------------------------|
| `docs/http-basics.md`    | Notes on HTTP/1.1 vs HTTP/2, methods, status codes, headers, cookies, CORS. |
| `tcp-udp-demo/`          | Tiny chat server with `java.net.ServerSocket` and a UDP echo with `DatagramSocket`. |
| `rest-controller/`       | A Spring Boot REST API exposing `/api/books` with proper status codes and JSON. |
| `websocket-chat/`        | A WebSocket endpoint that broadcasts messages to every connected client. |

## OSI / TCP-IP cheat-sheet

```
Layer        Protocols                 What Java gives you
-------      -------------------       --------------------------------
Application  HTTP, WebSocket, SMTP     HttpClient, Spring MVC, JavaMail
Transport    TCP, UDP                  Socket, DatagramSocket
Internet     IP, ICMP                  InetAddress
Link         Ethernet, Wi-Fi           (handled by the OS)
```

## Exercises

1. Use `curl -v` to call your REST endpoint and read the response headers.
2. Open two terminal windows running `tcp-udp-demo` clients and chat.
3. Change the REST controller to require a JWT (links to module 06).
4. Compare HTTP status `401` vs `403` — when do you use each?
