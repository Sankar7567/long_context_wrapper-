#!/usr/bin/env bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ensure ollama is running
if ! curl -s http://localhost:11434/api/tags >/dev/null; then
    echo "Starting Ollama locally..."
    ollama serve > ollama.log 2>&1 &
    # Wait for Ollama to boot
    sleep 5
fi

# Ensure model is pulled
echo "Ensuring qwen3:8b model is available..."
ollama pull qwen3:8b

# Start uvicorn server in the background
echo "Starting FastAPI server..."
uvicorn server:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait a second for the server to spin up
sleep 2

# Open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8000
elif command -v open &> /dev/null; then
    open http://localhost:8000
else
    echo "Please open http://localhost:8000 in your browser."
fi

# Bring the server to foreground so script blocks
wait $SERVER_PID
