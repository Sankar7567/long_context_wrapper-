# Infinite Scaling AI Tutor Engine 🚀

A highly optimized, infinitely scalable local AI tutoring and long-form writing engine. Built with a minimalist stack (Vanilla JS, FastAPI, and local Ollama), this engine is designed to generate comprehensive, structured mini-books and guides without ever exceeding the Large Language Model's (LLM) context window.

## Features

- **O(1) Memory Complexity:** The engine dynamically passes only the Blueprint and a rolling "Transition Anchor" (the last 100 words of the previous section) to the LLM. This guarantees the context window never balloons, allowing you to generate 30+ page documents without crashing or slowing down.
- **Native PDF Export:** A built-in Print Media Query Engine dynamically formats the generated Markdown content into a beautiful, paginated PDF textbook (hiding the UI and forcing chapter page breaks).
- **Math Rendering:** Native integration with `KaTeX` via the marked extension ensures all mathematical equations (`\( E=mc^2 \)`) are parsed and rendered perfectly in real-time.
- **Server-Sent Events (SSE):** Seamless, ultra-fast streaming directly from the local Ollama backend to your browser.
- **Auto-queue Flushing:** Robust client-disconnect handling ensures that refreshing the browser instantly kills background LLM generations, keeping your compute queue clean and responsive.

## Tech Stack

- **Frontend:** Vanilla HTML, JS, CSS
- **Backend:** Python (FastAPI, Uvicorn, HTTPX, Pydantic v2)
- **AI Inference:** Local Ollama (`qwen3:8b` or equivalent)

## Getting Started

### 1. Prerequisites
- Install Python 3
- Install [Ollama](https://ollama.com/) locally.

### 2. Installation
Clone the repository and run the startup script:

```bash
git clone https://github.com/Sankar7567/long_context_wrapper-.git
cd long_context_wrapper-
./start.sh
```

The `start.sh` script will automatically:
1. Verify Ollama is running (and launch it in the background if it isn't).
2. Pull the required model (`qwen3:8b`) if it's missing.
3. Boot the FastAPI streaming server.
4. Launch the web UI in your default browser.

## Architecture Highlights

1. **`server.py`:** Handles the FastAPI routes and the Vanilla JS frontend UI. Manages the Server-Sent Event (SSE) loop and explicit disconnect handlers.
2. **`wrapper.py`:** The core engine. Replaces slow, blocking LLM JSON summarization calls with lightning-fast deterministic Python string slicing to extract the transition anchors.

## License

MIT License
