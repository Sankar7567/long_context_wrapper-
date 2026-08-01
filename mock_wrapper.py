import asyncio
from pydantic import BaseModel
from typing import List, AsyncGenerator

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
    """Generates a mock outline instantly for testing purposes."""
    await asyncio.sleep(1) # simulate thinking
    return Outline(
        title=f"A Guide to: {prompt}",
        sections=[
            SubSection(id="sec1", title="Introduction", key_points=["Overview", "History"]),
            SubSection(id="sec2", title="Core Concepts", key_points=["Variables", "Control Flow"]),
            SubSection(id="sec3", title="Conclusion", key_points=["Summary", "Next Steps"])
        ]
    )

async def stream_section(outline: Outline, current_section: SubSection, running_state: RunningState) -> AsyncGenerator[str, None]:
    """Streams mock content for a single section."""
    await asyncio.sleep(0.5)
    
    mock_content = (
        f"Here is some mock content for the section **{current_section.title}**.\n\n"
        f"This section covers:\n"
    )
    for point in current_section.key_points:
        mock_content += f"- {point}\n"
        
    mock_content += "\nThis is just a simulation of the streaming response to test if the Vanilla JS UI and the SSE FastAPI endpoint are working seamlessly together."
    
    # stream it chunk by chunk
    words = mock_content.split(" ")
    for word in words:
        yield word + " "
        await asyncio.sleep(0.05) # fast streaming

async def update_state(running_state: RunningState, new_content: str) -> RunningState:
    """Mocks updating the state."""
    await asyncio.sleep(0.5)
    return RunningState(
        summary="This is a mocked running summary.",
        transition_anchor="This is a mocked transition anchor."
    )
