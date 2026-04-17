import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_ID = "gpt-5"

def get_system_prompt():
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%B %d, %Y")
    return f"""### ROLE
You are a Market Intelligence Analyst for UOB Malaysia.

### OBJECTIVE
Identify real customer sentiment and trending discussions on UOB Malaysia, not other regions.

### RULES
- No marketing language
- Focus on real user discussions
- TIMEFRAME: {cutoff_date} to today
"""

def run_brand_crawl(brand_name: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M")

    print(f"\n{'='*60}")
    print(f"Analyzing Buzzing Topics for: {brand_name}")
    print(f"{'='*60}")

    prompt = (
        f"Search for recent discussions about {brand_name} in the last 30 days.\n\n"
        "Focus but not limited to:\n"
        "- Lowyat forums\n"
        "- Reddit (Malaysia finance communities)\n"
        "- RinggitPlus\n"
        "- Facebook discussions\n\n"
        "TASK:\n"
        f"Identify topics that users are discussing on {brand_name}.\n\n"
        "For each topic include:\n"
        "- Title\n"
        "- details about the discussion \n"
        "- Summary of user sentiment and also how hot the topic is in the discussion, ie the buzzness, or engagements hotness etc.\n"
        "- Key quotes thats most representative\n"
    )

    tools = [
        {
            "type": "web_search",
            "user_location": {
                "type": "approximate",
                "country": "MY"
            }
        }
    ]

    try:
        print("🧠 Running GPT Web Search...\n")

        response = client.responses.create(
            model=MODEL_ID,
            instructions=get_system_prompt(),
            reasoning={"effort": "high"},

            input=prompt,
            tools=tools,
        )

        report = response.output_text

        if not report:
            print("⚠️ No output generated.")
            return

        filename = f"{brand_name.replace(' ', '_')}_BUZZ_{date_str}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Buzzing Topics Report: {brand_name}\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(report)

        print(f"🎉 Report saved: {filename}")

        # Optional: debug sources
        if hasattr(response, "sources"):
            print(f"🔗 Sources found: {len(response.sources)}")

    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    run_brand_crawl("UOB Malaysia")