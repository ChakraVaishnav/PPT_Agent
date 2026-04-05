import asyncio
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_mcp_adapters.client import MultiServerMCPClient
from config import Config


# LLM SETUP
base_llm = HuggingFaceEndpoint(
    repo_id=Config.MODEL_ID,
    max_new_tokens=512,
    temperature=0.3,
    huggingfacehub_api_token=Config.HUGGINGFACE_TOKEN
)

llm = ChatHuggingFace(llm=base_llm)

# Helper to parse LLM output into a list
def parse_list(text: str):
    lines = text.strip().split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if line.startswith("-") or line.startswith("*"):
            line = line[1:].strip()
        elif "." in line and line.split(".")[0].isdigit():
            line = line.split(".", 1)[1].strip()
        if line:
            cleaned.append(line)
    return cleaned


async def main(topic=None, num_slides=None):
    print("🚀 Starting Auto-PPT Agent...\n")

    # MCP Client setup
    client = MultiServerMCPClient({
        "ppt_server": {
            "command": "python",
            "args": ["ppt_server.py"],
            "transport": "stdio"
        },
        "search_server": {
            "command": "python",
            "args": ["search_server.py"],
            "transport": "stdio"
        }
    })

    tools = await client.get_tools()
    tools_map = {tool.name: tool for tool in tools}

    print("✅ Tools Loaded:", list(tools_map.keys()), "\n")

    # -----------------------------
    # STEP 1: PLAN SLIDES
    # -----------------------------
    import sys
    if topic is None:
        if len(sys.argv) > 1:
            topic = sys.argv[1]
        else:
            topic = input("Enter the topic for your PPT: ")
    if num_slides is None:
        if len(sys.argv) > 2:
            num_slides = sys.argv[2]
        else:
            num_slides = input("How many slides do you want? (e.g. 5): ")
    try:
        num_slides = int(num_slides)
    except Exception:
        num_slides = 5

    print("🧠 Generating slide titles...")
    slides_res = await llm.ainvoke(
        f"Give exactly {num_slides} slide titles for a beginner-friendly presentation on {topic}. Return as a list."
    )
    slides = parse_list(slides_res.content)
    print("📊 Slides:", slides, "\n")

    # Smart filename suggestion from LLM
    filename_res = await llm.ainvoke(
        f"Suggest a short, lowercase, underscore_separated filename for a PowerPoint presentation on the topic '{topic}'. End the filename with '_ai_agent.pptx' and return only the filename."
    )
    ppt_filename = filename_res.content.strip().replace(' ', '_')
    if not ppt_filename.endswith('.pptx'):
        ppt_filename += '_ai_agent.pptx'

    # -----------------------------
    # STEP 2: CREATE PRESENTATION
    # -----------------------------
    print("📂 Creating presentation...")
    await tools_map["create_presentation"].ainvoke({
        "title": topic
    })

    # -----------------------------
    # STEP 3: ADD SLIDES
    # -----------------------------

    for i, slide in enumerate(slides, 1):
        print(f"📝 Generating content for Slide {i}: {slide}")

        # 1. Get web search content
        web_content = await tools_map["search_web"].ainvoke({"query": slide})
        web_text = web_content if isinstance(web_content, str) else getattr(web_content, 'content', '')
        print(f"   🌐 Web search result: {web_text}")

        # 2. Enrich with LLM
        bullets_prompt = (
            f"Given the following web search result for the slide titled '{slide}':\n"
            f"{web_text}\n"
            f"Write 4 concise, informative bullet points for this slide, using the web info and your own knowledge."
        )
        bullets_res = await llm.ainvoke(bullets_prompt)
        bullets = parse_list(bullets_res.content)

        print("   ➤ Bullets:", bullets)

        await tools_map["add_slide_with_image"].ainvoke({
            "title": slide,
            "bullets": bullets
        })

    # -----------------------------
    # STEP 4: SAVE PRESENTATION
    # -----------------------------
    print("\n💾 Saving presentation...")

    save_result = await tools_map["save_presentation"].ainvoke({
        "filename": ppt_filename
    })

    print(f"\n🔥 DONE! PPT save result: {save_result}")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    asyncio.run(main())