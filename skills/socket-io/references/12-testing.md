# Socket.IO Testing

> Source: https://socket.io/docs/v4/testing/

## Table of Contents

- [Test Setup](#test-setup)
- [Jest Examples](#jest-examples)
- [Vitest Examples](#vitest-examples)
- [Mocha Examples](#mocha-examples)
- [Testing Patterns](#testing-patterns)
- [Helper Utilities](#helper-utilities)

## Test Setup

All Socket.IO test suites follow the same pattern:

1. Create an HTTP server and Socket.IO server in a setup hook
2. Connect a client
3. Run tests against the client-server pair
4. Disconnect the client and close the server in a teardown hook

```bash
npm install --save-dev socket.io-client
# Plus your test framework:
npm install --save-dev jest         # or
npm install --save-dev vitest       # or
npm install --save-dev mocha chai
```

## Jest Examples

### Basic Setup

```javascript
// tests/socket.test.js
import { createServer } from "node:http";
import { Server } from "socket.io";
import { io as ioc } from "socket.io-client";

describe("Socket.IO", () => {
  let io, serverSocket, clientSocket;

  beforeAll((done) => {
    const httpServer = createServer();
    io = new Server(httpServer);

    httpServer.listen(() => {
      const port = httpServer.address().port;
      clientSocket = ioc(`http://localhost:${port}`);

      io.on("connection", (socket) => {
        serverSocket = socket;
      });

      clientSocket.on("connect", done);
    });
  });

  afterAll(() => {
    io.close();
    clientSocket.disconnect();
  });

  test("should emit and receive events", (done) => {
    clientSocket.on("hello", (msg) => {
      expect(msg).toBe("world");
      done();
    });
    serverSocket.emit("hello", "world");
  });

  test("should work with acknowledgements", (done) => {
    serverSocket.on("greet", (name, callback) => {
      callback(`Hello, ${name}!`);
    });

    clientSocket.emit("greet", "Alice", (response) => {
      expect(response).toBe("Hello, Alice!");
      done();
    });
  });

  test("should work with emitWithAck", async () => {
    serverSocket.on("ping", (callback) => {
      callback("pong");
    });

    const response = await clientSocket.emitWithAck("ping");
    expect(response).toBe("pong");
  });
});
```

### Testing Rooms

```javascript
test("should broadcast to room members", (done) => {
  const httpServer = createServer();
  const io = new Server(httpServer);
  let client1, client2, client3;
  const received = [];

  httpServer.listen(() => {
    const port = httpServer.address().port;

    io.on("connection", (socket) => {
      socket.on("join", (room) => socket.join(room));
    });

    client1 = ioc(`http://localhost:${port}`);
    client2 = ioc(`http://localhost:${port}`, { forceNew: true });
    client3 = ioc(`http://localhost:${port}`, { forceNew: true });

    const onMessage = (clientName) => (msg) => {
      received.push({ client: clientName, msg });
      if (received.length === 2) {
        expect(received).toEqual([
          { client: "client1", msg: "hello room" },
          { client: "client2", msg: "hello room" }
        ]);
        io.close();
        client1.disconnect();
        client2.disconnect();
        client3.disconnect();
        done();
      }
    };

    client1.on("connect", () => {
      client1.emit("join", "test-room");
      client1.on("room-msg", onMessage("client1"));
    });

    client2.on("connect", () => {
      client2.emit("join", "test-room");
      client2.on("room-msg", onMessage("client2"));
    });

    client3.on("connect", () => {
      // client3 does NOT join the room
      client3.on("room-msg", () => {
        done(new Error("client3 should not receive room message"));
      });

      // Emit to room after all clients connected
      setTimeout(() => {
        io.to("test-room").emit("room-msg", "hello room");
      }, 100);
    });
  });
});
```

## Vitest Examples

```typescript
// tests/socket.test.ts
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { createServer, type Server as HttpServer } from "node:http";
import { Server, type Socket as ServerSocket } from "socket.io";
import { io as ioc, type Socket as ClientSocket } from "socket.io-client";

describe("Socket.IO", () => {
  let io: Server;
  let serverSocket: ServerSocket;
  let clientSocket: ClientSocket;

  beforeAll(
    () =>
      new Promise<void>((resolve) => {
        const httpServer = createServer();
        io = new Server(httpServer);

        httpServer.listen(() => {
          const addr = httpServer.address();
          const port = typeof addr === "object" ? addr!.port : 0;
          clientSocket = ioc(`http://localhost:${port}`);

          io.on("connection", (socket) => {
            serverSocket = socket;
          });

          clientSocket.on("connect", () => resolve());
        });
      })
  );

  afterAll(() => {
    io.close();
    clientSocket.disconnect();
  });

  it("should emit events", async () => {
    const promise = waitFor(clientSocket, "hello");
    serverSocket.emit("hello", "world");
    const result = await promise;
    expect(result).toBe("world");
  });

  it("should handle async acknowledgements", async () => {
    serverSocket.on("getData", async (key, callback) => {
      const data = await fetchData(key);
      callback(data);
    });

    const response = await clientSocket.emitWithAck("getData", "users");
    expect(response).toBeDefined();
  });
});

function waitFor<T>(socket: ClientSocket, event: string): Promise<T> {
  return new Promise((resolve) => {
    socket.once(event, resolve);
  });
}
```

## Mocha Examples

```javascript
import { createServer } from "node:http";
import { Server } from "socket.io";
import { io as ioc } from "socket.io-client";
import { expect } from "chai";

describe("Socket.IO", function () {
  let io, serverSocket, clientSocket;

  before(function (done) {
    const httpServer = createServer();
    io = new Server(httpServer);

    httpServer.listen(() => {
      const port = httpServer.address().port;
      clientSocket = ioc(`http://localhost:${port}`);

      io.on("connection", (socket) => {
        serverSocket = socket;
      });

      clientSocket.on("connect", done);
    });
  });

  after(function () {
    io.close();
    clientSocket.disconnect();
  });

  it("should emit and receive", function (done) {
    clientSocket.on("test", (data) => {
      expect(data).to.equal("hello");
      done();
    });
    serverSocket.emit("test", "hello");
  });
});
```

## Testing Patterns

### Testing Middleware

```javascript
test("should reject unauthorized connections", (done) => {
  const httpServer = createServer();
  const io = new Server(httpServer);

  io.use((socket, next) => {
    const token = socket.handshake.auth.token;
    if (token === "valid-token") {
      next();
    } else {
      next(new Error("Unauthorized"));
    }
  });

  httpServer.listen(() => {
    const port = httpServer.address().port;
    const client = ioc(`http://localhost:${port}`, {
      auth: { token: "invalid-token" }
    });

    client.on("connect_error", (err) => {
      expect(err.message).toBe("Unauthorized");
      client.disconnect();
      io.close();
      done();
    });
  });
});
```

### Testing Namespaces

```javascript
test("should connect to admin namespace", (done) => {
  const httpServer = createServer();
  const io = new Server(httpServer);

  io.of("/admin").on("connection", (socket) => {
    socket.emit("welcome", "admin");
  });

  httpServer.listen(() => {
    const port = httpServer.address().port;
    const client = ioc(`http://localhost:${port}/admin`);

    client.on("welcome", (msg) => {
      expect(msg).toBe("admin");
      client.disconnect();
      io.close();
      done();
    });
  });
});
```

### Testing Disconnection

```javascript
test("should handle disconnect event", (done) => {
  serverSocket.on("disconnect", (reason) => {
    expect(reason).toBe("client namespace disconnect");
    done();
  });

  clientSocket.disconnect();
});
```

## Helper Utilities

### waitFor — Promise Wrapper

```javascript
function waitFor(socket, event, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`Timeout waiting for "${event}"`));
    }, timeout);

    socket.once(event, (...args) => {
      clearTimeout(timer);
      resolve(args.length === 1 ? args[0] : args);
    });
  });
}

// Usage
const msg = await waitFor(clientSocket, "chat:message");
expect(msg.text).toBe("Hello");
```

### createTestServer — Reusable Factory

```javascript
async function createTestServer(setupFn) {
  const httpServer = createServer();
  const io = new Server(httpServer);

  if (setupFn) setupFn(io);

  await new Promise((resolve) => httpServer.listen(resolve));
  const port = httpServer.address().port;

  return {
    io,
    port,
    createClient(nsp = "/", opts = {}) {
      return ioc(`http://localhost:${port}${nsp}`, {
        forceNew: true,
        ...opts
      });
    },
    close() {
      io.close();
    }
  };
}

// Usage
test("echo server", async () => {
  const server = await createTestServer((io) => {
    io.on("connection", (socket) => {
      socket.onAny((event, data) => {
        socket.emit(event, data);
      });
    });
  });

  const client = server.createClient();
  await waitFor(client, "connect");

  const response = waitFor(client, "ping");
  client.emit("ping", "hello");
  expect(await response).toBe("hello");

  client.disconnect();
  server.close();
});
```

### Multiple Clients Helper

```javascript
async function createClients(port, count, nsp = "/") {
  const clients = [];
  for (let i = 0; i < count; i++) {
    const client = ioc(`http://localhost:${port}${nsp}`, { forceNew: true });
    await waitFor(client, "connect");
    clients.push(client);
  }
  return clients;
}

function disconnectAll(clients) {
  clients.forEach((c) => c.disconnect());
}
```
