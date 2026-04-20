import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_ID = "gpt-5"

def get_system_prompt():
    # Explicitly defining the Q1 2026 window
    start_date = "January 01, 2026"
    end_date = "March 31, 2026"
    
    return f"""### ROLE
You are a Market Intelligence Analyst for UOB Thailand.

### OBJECTIVE
Identify real customer sentiment and trending discussions on UOB Thailand, not other regions.

### RULES
- No marketing language.
- Focus on real user discussions, complaints, and praises.
- TIMEFRAME: Fixed Q1 Window ({start_date} to {end_date}).
"""

def run_brand_crawl(brand_name: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
    
    # Defining the search window for the prompt
    q1_start = "2026-01-01"
    q1_end = "2026-03-31"

    print(f"\n{'='*60}")
    print(f"Analyzing Q1 Buzzing Topics for: {brand_name}")
    print(f"Period: {q1_start} to {q1_end}")
    print(f"{'='*60}")

    # Updated prompt with explicit Q1 dates
    prompt = (
        f"Search for and analyze discussions about {brand_name} specifically occurring "
        f"between {q1_start} and {q1_end} (First Quarter of 2026).\n\n"
        "Focus but not limited to:\n"
        "- Pantip (Thailand's primary forum)\n"
        "- Reddit (r/Thailand and r/Bangkok finance threads)\n"
        "- Thai Finance Blogs (Chaimiles, Money Buffalo)\n"
        "- Facebook groups (e.g., 'พวกเราคือผู้ประสบภัยจาก UOB' and 'คนรักบัตรเครดิต')\n\n"
        "TASK:\n"
        f"Identify topics that users discussed regarding {brand_name} during this specific Q1 window.\n\n"
        "For each topic include:\n"
        "- Title\n"
        "- Date range of the peak discussion within Q1\n"
        "- Details about the discussion\n"
        "- Summary of user sentiment and the 'Buzzness' (engagement level, number of comments/shares)\n"
        "- Key quotes that are most representative of user feelings\n\n"
        "Translate all Thai source material to English."
    )

    tools = [
        {
            "type": "web_search",
            "user_location": {
                "type": "approximate",
                "country": "TH"
            }
        }
    ]

    try:
        print("🧠 Running GPT Web Search for Q1 Data...\n")

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

        filename = f"{brand_name.replace(' ', '_')}_Q1_REPORT_{date_str}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Q1 Market Intelligence Report: {brand_name}\n")
            f.write(f"Search Window: {q1_start} to {q1_end}\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(report)

        print(f"🎉 Q1 Report saved: {filename}")

        if hasattr(response, "sources"):
            print(f"🔗 Sources found: {len(response.sources)}")

    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    run_brand_crawl("UOB Thailand")