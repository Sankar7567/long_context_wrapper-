import json
import httpx
from pydantic import BaseModel
from typing import List, AsyncGenerator

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen3:8b"

class SubSection(BaseModel):
    id: str
    title: str
    key_points: List[str]

class Outline(BaseModel):
    title: str
    sections: List[SubSection]

class RunningState(BaseModel):
    summary: str = ""
    transition_anchor: str = ""

async def generate_outline(prompt: str) -> Outline:
    """Generates a structured outline for the given prompt."""
    system_prompt = (
        "You are a master planner. Create an outline for the user's topic. "
        "Return STRICTLY JSON matching this schema: "
        "{'title': '...', 'sections': [{'id': 'sec1', 'title': '...', 'key_points': ['...']}]}"
    )
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "format": "json"
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Parse into Pydantic model
        outline_dict = json.loads(data.get("response", "{}"))
        return Outline.model_validate(outline_dict)

async def stream_section(outline: Outline, current_section: SubSection, running_state: RunningState) -> AsyncGenerator[str, None]:
    """Streams the content for a single section."""
    system_prompt = (
        f"You are writing a section titled '{current_section.title}' for the document '{outline.title}'.\n"
        f"Key points to cover:\n" + "\n".join(f"- {kp}" for kp in current_section.key_points) + "\n\n"
        "Maintain continuity with the previous text. Do not write conclusions or introductions for the whole document.\n"
        "Respond directly with the markdown text for this section."
    )
    
    context = ""
    if running_state.summary:
        context += f"Previous context summary: {running_state.summary}\n"
    if running_state.transition_anchor:
        context += f"Text leading into this section: {running_state.transition_anchor}\n"
        
    prompt = f"{context}\nNow write the section: {current_section.title}"
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system_prompt,
        "stream": True,
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream("POST", f"{OLLAMA_URL}/api/generate", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done"):
                        break

async def update_state(running_state: RunningState, new_content: str, current_section: SubSection) -> RunningState:
    """Deterministically extracts a transition anchor and updates the summary without LLM delay."""
    # 1. Transition Anchor: Last ~100 words
    words = new_content.split()
    anchor = " ".join(words[-100:]) if len(words) > 100 else new_content
    
    # 2. Running Summary: Append completed section title
    new_summary = running_state.summary
    if not new_summary:
        new_summary = "Completed sections:\n"
    new_summary += f"- {current_section.title}\n"
    
    return RunningState(
        summary=new_summary,
        transition_anchor=anchor
    )
