import asyncio
import json
import re
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

AVAILABLE_THEMES = [
    "dark_tech",         # Dark bg, cyan/blue accents — good for tech, AI, software
    "minimal_light",     # White bg, clean typography — good for business, finance
    "corporate_blue",    # Navy/blue tones — good for corporate, formal topics
    "vibrant_creative",  # Bold colors, playful — good for marketing, design, education
    "nature_green",      # Green tones — good for environment, health, sustainability
    "berlin",            # Dark dramatic — good for architecture, fashion, luxury
    "slate_dark",        # Muted charcoal — good for data, analytics, research
    "warm_terracotta",   # Earthy warm tones — good for culture, travel, food
    "ocean_depth",       # Deep blue-teal — good for science, marine, geography
    "berry_bold",        # Berry/rose tones — good for healthcare, wellness, beauty
    "coral_energy",      # Coral + gold — good for startups, pitches, innovation
    "midnight_exec",     # Navy + ice blue — good for finance, law, consulting
    "vintage_wood",      # Warm wood tones — good for history, literature, arts
    "circuit_board",     # Grid + neon green — good for cybersecurity, hardware, IoT
    "celestial",         # Deep space blues — good for astronomy, physics, future-tech
    "sage_calm",         # Soft sage green — good for mental health, education, yoga
    "cherry_bold",       # Cherry red + white — good for sports, energy, motivation
    "droplet_fresh",     # Water greens + white — good for environment, NGO, pharma
    "golden_exec",       # Gold + dark brown — good for premium brands, real estate
    "pastel_soft",       # Soft pastels — good for kids, events, creative writing
]

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

    # ─── STEP 1: GET TOPIC & SLIDE COUNT ───────────────────────────────────────
    import sys
    if topic is None:
        topic = sys.argv[1] if len(sys.argv) > 1 else input("Enter the topic for your PPT: ")
    if num_slides is None:
        num_slides = sys.argv[2] if len(sys.argv) > 2 else input("How many slides? (e.g. 5): ")
    try:
        num_slides = int(num_slides)
    except Exception:
        num_slides = 5

    # ─── STEP 2: LLM PICKS THEME ───────────────────────────────────────────────
    print("🎨 Selecting design theme...")
    theme_prompt = (
        f"You are a presentation designer. Given the topic '{topic}', "
        f"pick the MOST suitable theme from this list: {AVAILABLE_THEMES}. "
        f"Return ONLY the theme name, nothing else."
    )
    theme_res = await llm.ainvoke(theme_prompt)
    chosen_theme = theme_res.content.strip().lower().replace(" ", "_")

    # Fallback if LLM returns something unexpected
    if chosen_theme not in AVAILABLE_THEMES:
        chosen_theme = "minimal_light"

    print(f"🎨 Theme selected: {chosen_theme}\n")

    # ─── STEP 3: CREATE PRESENTATION WITH THEME ────────────────────────────────
    print("📂 Creating presentation...")
    await tools_map["create_presentation"].ainvoke({
        "title": topic,
        "theme": chosen_theme
    })

    # ─── STEP 4: PLAN SLIDE TITLES ─────────────────────────────────────────────
    print("🧠 Generating slide titles...")
    slides_res = await llm.ainvoke(
        f"Give exactly {num_slides} slide titles for a beginner-friendly presentation on {topic}. "
        f"Return as a plain list, one title per line."
    )
    slides = parse_list(slides_res.content)
    print("📊 Slides:", slides, "\n")

    # Smart filename
    filename_res = await llm.ainvoke(
        f"Suggest a short, lowercase, underscore_separated filename for a PowerPoint on '{topic}'. "
        f"End with '_ai_agent.pptx'. Return only the filename."
    )
    ppt_filename = filename_res.content.strip().replace(" ", "_")
    if not ppt_filename.endswith(".pptx"):
        ppt_filename += "_ai_agent.pptx"

    # ─── STEP 5: ADD SLIDES ────────────────────────────────────────────────────
    for i, slide in enumerate(slides, 1):
        print(f"📝 Generating content for Slide {i}: {slide}")

        web_content = await tools_map["search_web"].ainvoke({"query": slide})
        web_text = web_content if isinstance(web_content, str) else getattr(web_content, "content", "")
        print(f"   🌐 Web result: {web_text[:100]}...")

        bullets_prompt = (
            f"Given this web search result for slide titled '{slide}':\n"
            f"{web_text}\n"
            f"Write 4 concise, informative bullet points using this info. Return as a plain list."
        )
        bullets_res = await llm.ainvoke(bullets_prompt)
        bullets = parse_list(bullets_res.content)
        print("   ➤ Bullets:", bullets)

        await tools_map["add_slide_with_image"].ainvoke({
            "title": slide,
            "bullets": bullets
        })

    # ─── STEP 6: SAVE ──────────────────────────────────────────────────────────
    print("\n💾 Saving presentation...")
    save_result = await tools_map["save_presentation"].ainvoke({
        "filename": ppt_filename
    })
    print(f"\n✅ DONE! {save_result}")


if __name__ == "__main__":
    asyncio.run(main())