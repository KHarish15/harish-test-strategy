import os, re, json
from io import BytesIO
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
import graphviz

load_dotenv()

def gemini_generate_flowchart_structure(text):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY_1")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GENAI_API_KEY_1 not set in environment.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    prompt = (
        "You are an expert at extracting flowchart logic from code or pseudocode. "
        "Given the following content, extract a flowchart structure as JSON with nodes (id, label, type) and edges (from, to, label). "
        "Types can be: start, end, process, io, decision, predefined, preprocessor, data, off_page, page_connector, comment. "
        "For decisions, include Yes/No labels on edges. "
        "Content:\n" + text +
        "\nRespond ONLY with a JSON object: {nodes: [...], edges: [...]}"
    )
    response = model.generate_content(prompt)
    gemini_text = None
    if hasattr(response, "text") and isinstance(response.text, str):
        gemini_text = response.text
    elif hasattr(response, "candidates"):
        try:
            gemini_text = response.candidates[0].content.parts[0].text
        except Exception:
            pass
    if not isinstance(gemini_text, str):
        gemini_text_str = str(gemini_text) if gemini_text is not None else ""
    else:
        gemini_text_str = gemini_text
    gemini_text_str = gemini_text_str.strip()
    cleaned = re.sub(r"^```json\s*|```$", "", gemini_text_str, flags=re.MULTILINE)
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if not match:
        raise ValueError("Gemini did not return a valid JSON structure.")
    return json.loads(match.group(0))

def build_flowchart_from_gemini(flowchart):
    dot = graphviz.Digraph(format="png", engine="dot", graph_attr={
        "dpi": "300",
        "nodesep": "0.5",
        "ranksep": "0.5",
        "splines": "true",
        "concentrate": "false"
    })
    style_map = {
        "start": ("oval", "#a7f3d0"),
        "end": ("oval", "#fca5a5"),
        "process": ("box", "#bfdbfe"),
        "predefined": ("rect", "#c7d2fe"),
        "decision": ("diamond", "#fde68a"),
        "io": ("parallelogram", "#d8b4fe"),
        "data": ("cylinder", "#bbf7d0"),
        "preprocessor": ("trapezium", "#ddd6fe"),
        "off_page": ("box", "#a5f3fc"),
        "page_connector": ("circle", "#fbcfe8"),
        "comment": ("note", "#f3f4f6")
    }
    for node in flowchart["nodes"]:
        shape, color = style_map.get(node.get("type", "process"), ("box", "#ffffff"))
        if node.get("type") == "page_connector":
            dot.node(str(node["id"]), node["label"], shape=shape, fillcolor=color, style="filled", fontname="Segoe UI", fontsize="14", width="0.7", height="0.7", fixedsize="true")
        else:
            dot.node(str(node["id"]), node["label"], shape=shape, fillcolor=color, style="filled", fontname="Segoe UI", fontsize="14")
    for edge in flowchart["edges"]:
        label = edge.get("label", "")
        dot.edge(str(edge["from"]), str(edge["to"]), label=label, arrowsize="0.5", fontname="Segoe UI", fontsize="12")
    return dot

def generate_flowchart_image(content: str) -> bytes:
    """
    Given code or pseudocode content, generate a flowchart PNG image (as bytes) using Gemini and Graphviz.
    """
    flowchart = gemini_generate_flowchart_structure(content)
    dot = build_flowchart_from_gemini(flowchart)
    path = dot.render("flowchart", format="png", cleanup=True)
    with open(path, "rb") as f:
        img_bytes = f.read()
    return img_bytes 