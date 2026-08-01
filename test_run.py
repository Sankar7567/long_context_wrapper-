import asyncio
import time
from wrapper import generate_outline

async def main():
    print("Starting test...")
    start_time = time.time()
    try:
        print("Calling generate_outline...")
        # A simple prompt that shouldn't take too much effort
        outline = await generate_outline("Write a short guide about the Python programming language.")
        print(f"Success! Outline generated in {time.time() - start_time:.2f} seconds.")
        print(outline.model_dump_json(indent=2))
    except Exception as e:
        print(f"Error during generate_outline: {e}")

if __name__ == "__main__":
    asyncio.run(main())
