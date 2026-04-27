## 1. What pygbag Actually Does

pygbag is a command-line tool that takes a Python/pygame project and compiles
it to run in a browser via WebAssembly (WASM).  Understanding what it does at
each stage is the key to understanding every networking decision in this demo.

### Build phase

When you run `pygbag .` inside the client directory, it:

1. Packages all Python files and assets into a WASM-loadable archive.
2. Wraps CPython compiled to WASM (via Emscripten) in an HTML/JS shell.
3. Serves the result over a local HTTP dev server (default port 8000).

### Runtime phase

Once the browser loads the page:

1. The Emscripten-compiled CPython boots inside a Web Worker.
2. Before your `main.py` runs, pygbag injects a set of "support modules"
   directly into `sys.modules` — these are not files on disk that you can
   `import` normally; they are constructed entirely in memory and registered
   by pygbag's bootstrap code.
3. Your code then runs inside a cooperative async event loop that is ticked
   by `window.requestAnimationFrame()` — meaning the event loop advances once
   per display frame (~60 times per second), not continuously.

The critical injected modules are `aio`, `aio.cross`, and `js`.  There is no
PyPI package for any of them.  They do not exist on desktop.  This is the
entire source of the cross-platform complexity.

---
