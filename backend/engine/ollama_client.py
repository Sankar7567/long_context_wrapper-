import httpx
import json
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any

class OllamaConnectionError(Exception):
    """Raised when there is a connection issue with Ollama."""
    pass

class OllamaModelNotFoundError(Exception):
    """Raised when the specified model is not found in the Ollama instance."""
    pass

class OllamaTimeoutError(Exception):
    """Raised when an operation with Ollama times out."""
    pass

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "qwen3:8b"):
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = httpx.Timeout(300.0)

    async def check_health(self) -> bool:
        """Verifies Ollama is running and that the default model is pulled and available locally."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if Ollama is running and get local models
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                data = response.json()
                models = [model.get("name") for model in data.get("models", [])]
                
                # Check if the exact model or model with tag (e.g. qwen3:8b or qwen3:8b:latest) exists
                if not any(m == self.default_model or m.startswith(f"{self.default_model}:") for m in models):
                    raise OllamaModelNotFoundError(f"Model '{self.default_model}' not found locally.")
                    
                return True
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(f"Timeout checking health: {e}") from e
        except httpx.RequestError as e:
            raise OllamaConnectionError(f"Failed to connect to Ollama: {e}") from e

    async def generate(self, prompt: str, model: Optional[str] = None, system: Optional[str] = None, format: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> str:
        """Async POST request to /api/generate with stream: False."""
        model = model or self.default_model
        
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        
        if system is not None:
            payload["system"] = system
        if format is not None:
            payload["format"] = format
        if options is not None:
            payload["options"] = options
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                
                data = response.json()
                return data.get("response", "")
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(f"Timeout during generation: {e}") from e
        except httpx.RequestError as e:
            raise OllamaConnectionError(f"Connection error during generation: {e}") from e

    async def stream_generate(self, prompt: str, model: Optional[str] = None, system: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Async generator streaming output chunks via httpx.aiter_lines()."""
        model = model or self.default_model
        
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
        }
        
        if system is not None:
            payload["system"] = system
        if options is not None:
            payload["options"] = options
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done"):
                                break
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(f"Timeout during streaming generation: {e}") from e
        except httpx.RequestError as e:
            raise OllamaConnectionError(f"Connection error during streaming generation: {e}") from e


if __name__ == "__main__":
    async def test_ollama():
        print("Initializing OllamaClient...")
        client = OllamaClient()
        
        print("\n--- Health Check ---")
        try:
            is_healthy = await client.check_health()
            print(f"Health Check Passed: {is_healthy}")
        except Exception as e:
            print(f"Health Check Failed: {e}")
            # Do not exit, try the rest anyway for testing
            
        print("\n--- Testing Regular Generation ---")
        try:
            response = await client.generate(
                prompt="What is the capital of Japan?", 
                system="Answer in a single word."
            )
            print(f"Generation response: {response}")
        except Exception as e:
            print(f"Generation Failed: {e}")
            
        print("\n--- Testing JSON Generation ---")
        try:
            json_response = await client.generate(
                prompt="List two programming languages.", 
                format="json",
                system="Respond strictly in JSON format with a 'languages' array."
            )
            print(f"JSON response: {json_response}")
        except Exception as e:
            print(f"JSON Generation Failed: {e}")
            
        print("\n--- Testing Stream Generation ---")
        try:
            print("Stream output: ", end="", flush=True)
            async for chunk in client.stream_generate(
                prompt="Write a very brief haiku about coding."
            ):
                print(chunk, end="", flush=True)
            print("\n[Stream complete]")
        except Exception as e:
            print(f"\nStream Generation Failed: {e}")

    asyncio.run(test_ollama())
