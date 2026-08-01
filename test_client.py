from fastapi.testclient import TestClient
from server import app
import json

client = TestClient(app)

def test_stream():
    print("Testing SSE stream via TestClient...")
    with client.stream("GET", "/api/stream", params={"prompt": "test"}) as response:
        for line in response.iter_lines():
            if line:
                print(line)

if __name__ == "__main__":
    test_stream()
