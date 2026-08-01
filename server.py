from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from wrapper import generate_outline, stream_section, update_state, RunningState

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Tutoring Engine</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --surface-color: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --border-color: #334155;
        }
        body {
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        #sidebar {
            width: 300px;
            background-color: var(--surface-color);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            padding: 20px;
            box-sizing: border-box;
            overflow-y: auto;
        }
        #main {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 40px;
            box-sizing: border-box;
            overflow-y: auto;
        }
        textarea {
            width: 100%;
            height: 100px;
            background-color: var(--surface-color);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 10px;
            border-radius: 8px;
            resize: none;
            margin-bottom: 10px;
            font-family: inherit;
        }
        button {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: #2563eb;
        }
        button:disabled {
            background-color: var(--border-color);
            color: var(--text-muted);
            cursor: not-allowed;
        }
        .section-badge {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 6px;
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            font-size: 0.9em;
            color: var(--text-muted);
            cursor: pointer;
            transition: background-color 0.2s, border-color 0.2s;
        }
        .section-badge:hover {
            background-color: var(--surface-color);
        }
        .section-badge.active {
            border-color: var(--primary);
            color: var(--text-main);
        }
        .section-badge.completed {
            border-color: #10b981;
            color: #10b981;
        }
        #content-view {
            margin-top: 30px;
            line-height: 1.6;
            font-size: 1.1em;
            padding-bottom: 100px;
        }
        .content-section {
            margin-bottom: 40px;
        }
        .content-section h2 {
            color: var(--primary);
            margin-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
        }
        @media print {
            #sidebar, #prompt-input, #generate-btn, #export-btn {
                display: none !important;
            }
            #main {
                padding: 0 !important;
                overflow: visible !important;
            }
            body {
                background-color: white !important;
                color: black !important;
                height: auto !important;
                overflow: visible !important;
            }
            #content-view {
                padding-bottom: 0 !important;
                margin-top: 0 !important;
            }
            .content-section h2 {
                color: black !important;
                break-before: page;
                page-break-before: always;
                border-bottom: 2px solid #ccc;
            }
            .content-section:first-of-type h2 {
                break-before: auto;
                page-break-before: auto;
            }
        }
    </style>
    <!-- Use marked for minimal markdown rendering -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked-katex-extension/lib/index.umd.js"></script>
    <script>
        marked.use(markedKatex({throwOnError: false}));
    </script>
</head>
<body>

    <div id="sidebar">
        <h2 style="margin-top:0">Blueprint</h2>
        <div id="blueprint-container">
            <p style="color: var(--text-muted); font-size: 0.9em;">Enter a prompt to generate an outline.</p>
        </div>
    </div>

    <div id="main">
        <div>
            <textarea id="prompt-input" placeholder="What do you want to write about? (e.g. A comprehensive guide on Quantum Computing)"></textarea>
            <br>
            <button id="generate-btn" onclick="startGeneration()">Generate</button>
            <button id="export-btn" onclick="window.print()" disabled style="background-color: #10b981; margin-left: 10px;">Export PDF</button>
        </div>
        
        <div id="content-view"></div>
    </div>

    <script>
        let eventSource = null;

        function scrollToSection(id) {
            const el = document.getElementById('content-' + id);
            if (el) {
                el.scrollIntoView({behavior: 'smooth'});
            }
        }

        function startGeneration() {
            const prompt = document.getElementById('prompt-input').value.trim();
            if (!prompt) return;

            // Reset UI
            document.getElementById('generate-btn').disabled = true;
            document.getElementById('export-btn').disabled = true;
            document.getElementById('blueprint-container').innerHTML = 'Generating blueprint...';
            document.getElementById('content-view').innerHTML = '';

            if (eventSource) {
                eventSource.close();
            }

            eventSource = new EventSource(`/api/stream?prompt=${encodeURIComponent(prompt)}`);
            let activeSectionContent = "";
            let activeSectionId = null;
            let activeSectionDom = null;
            let activeMarkdownDom = null;

            eventSource.onmessage = function(event) {
                const msg = JSON.parse(event.data);

                if (msg.type === "blueprint") {
                    const outline = msg.data;
                    let html = `<h3>${outline.title}</h3>`;
                    outline.sections.forEach(sec => {
                        html += `<div id="badge-${sec.id}" class="section-badge" onclick="scrollToSection('${sec.id}')">${sec.title}</div>`;
                    });
                    document.getElementById('blueprint-container').innerHTML = html;
                } 
                else if (msg.type === "section_start") {
                    const section = msg.data;
                    activeSectionId = section.id;
                    activeSectionContent = "";
                    
                    // Mark badge active
                    document.querySelectorAll('.section-badge').forEach(el => el.classList.remove('active'));
                    document.getElementById(`badge-${section.id}`).classList.add('active');

                    // Create DOM for section
                    activeSectionDom = document.createElement('div');
                    activeSectionDom.className = 'content-section';
                    activeSectionDom.id = `content-${section.id}`;
                    
                    const titleDom = document.createElement('h2');
                    titleDom.innerText = section.title;
                    activeSectionDom.appendChild(titleDom);

                    activeMarkdownDom = document.createElement('div');
                    activeSectionDom.appendChild(activeMarkdownDom);

                    document.getElementById('content-view').appendChild(activeSectionDom);
                    
                    // Only auto-scroll on new section if user is at the bottom
                    const mainDiv = document.getElementById('main');
                    const isAtBottom = mainDiv.scrollHeight - mainDiv.scrollTop - mainDiv.clientHeight < 150;
                    if (isAtBottom) {
                        mainDiv.scrollTo(0, mainDiv.scrollHeight);
                    }
                }
                else if (msg.type === "token") {
                    activeSectionContent += msg.data;
                    // For performance, we use marked.parse synchronously. 
                    // In a production ultra-high-perf app we'd debounce this or use a lightweight markdown renderer.
                    if (activeMarkdownDom) {
                        activeMarkdownDom.innerHTML = marked.parse(activeSectionContent);
                    }
                    
                    const mainDiv = document.getElementById('main');
                    // Only auto-scroll if the user is already near the bottom
                    const isAtBottom = mainDiv.scrollHeight - mainDiv.scrollTop - mainDiv.clientHeight < 150;
                    if (isAtBottom) {
                        mainDiv.scrollTo(0, mainDiv.scrollHeight);
                    }
                }
                else if (msg.type === "section_complete") {
                    const section = msg.data;
                    document.getElementById(`badge-${section.id}`).classList.remove('active');
                    document.getElementById(`badge-${section.id}`).classList.add('completed');
                }
                else if (msg.type === "complete") {
                    document.getElementById('generate-btn').disabled = false;
                    document.getElementById('export-btn').disabled = false;
                    eventSource.close();
                }
                else if (msg.type === "error") {
                    console.error("Error from server:", msg.data);
                    document.getElementById('generate-btn').disabled = false;
                    eventSource.close();
                }
            };

            eventSource.onerror = function(err) {
                console.error("EventSource failed:", err);
                document.getElementById('generate-btn').disabled = false;
                eventSource.close();
            };
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get_index():
    return HTMLResponse(HTML_CONTENT)

@app.get("/api/stream")
async def stream_content(request: Request, prompt: str = Query(...)):
    async def event_generator():
        try:
            if await request.is_disconnected():
                return
            
            # 1. Generate Outline
            outline = await generate_outline(prompt)
            if await request.is_disconnected():
                return
            yield f"data: {json.dumps({'type': 'blueprint', 'data': outline.model_dump()})}\n\n"
            
            # 2. Initialize State
            running_state = RunningState()
            
            # 3. Stream Sections Sequentially
            for section in outline.sections:
                if await request.is_disconnected():
                    return
                yield f"data: {json.dumps({'type': 'section_start', 'data': {'id': section.id, 'title': section.title}})}\n\n"
                
                section_text = ""
                async for token in stream_section(outline, section, running_state):
                    if await request.is_disconnected():
                        return
                    section_text += token
                    yield f"data: {json.dumps({'type': 'token', 'data': token})}\n\n"
                
                # Update running state with newly generated text
                running_state = await update_state(running_state, section_text, section)
                yield f"data: {json.dumps({'type': 'section_complete', 'data': {'id': section.id}})}\n\n"
                
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
