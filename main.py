import os
import re
import glob
import datetime
import requests

HF_DAILY_PAPERS_URL = "https://huggingface.co/api/daily_papers"

# -------------------------------------------------------------------
# 1. FETCH & SAVE DAILY PAPERS
# -------------------------------------------------------------------

def fetch_hf_daily_papers():
    response = requests.get(HF_DAILY_PAPERS_URL)
    if response.status_code != 200:
        print(f"Error fetching data: Status Code {response.status_code}")
        return []
    return response.json()

def process_daily_items(raw_items, limit=10):
    sorted_items = sorted(raw_items, key=lambda x: x.get("upvotes", 0), reverse=True)[:limit]
    processed = []
    
    for item in sorted_items:
        paper_info = item.get("paper", {})
        arxiv_id = paper_info.get("id", "N/A")
        title = paper_info.get("title", "No Title").strip().replace("\n", " ")
        summary = paper_info.get("summary", "No Abstract Available").strip().replace("\n", " ")
        upvotes = item.get("upvotes", 0)

        processed.append({
            "title": title,
            "arxiv_id": arxiv_id,
            "upvotes": upvotes,
            "summary": summary,
            "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            "hf_paper_url": f"https://huggingface.co/papers/{arxiv_id}"
        })
    return processed

def write_markdown_file(papers, title_header, folder_name, file_name):
    if not papers:
        print(f"No papers to write for {folder_name}/{file_name}")
        return

    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {title_header}\n\n")
        f.write(f"*Total Papers Featured: {len(papers)}*\n\n")
        f.write("=" * 80 + "\n\n")

        for idx, paper in enumerate(papers, 1):
            f.write(f"## {idx}. {paper['title']}\n")
            f.write(f"**Upvotes:** 👍 {paper['upvotes']} | **arXiv ID:** `{paper['arxiv_id']}`\n\n")
            f.write(f"**Links:** [arXiv Page]({paper['arxiv_url']}) | [Download PDF]({paper['pdf_url']}) | [Hugging Face Discussion]({paper['hf_paper_url']})\n\n")
            f.write("### Abstract:\n")
            f.write(f"> {paper['summary']}\n\n")
            f.write("-" * 80 + "\n\n")

    print(f"Successfully generated: {file_path}")

# -------------------------------------------------------------------
# 2. LOCAL AGGREGATION (READ DAILY FILES -> GENERATE WEEKLY/MONTHLY)
# -------------------------------------------------------------------

def parse_md_file(file_path):
    """Parses saved daily markdown files back into structured dictionaries."""
    papers = []
    if not os.path.exists(file_path):
        return papers

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.split("## ")[1:]
    for block in blocks:
        try:
            lines = block.strip().split("\n")
            title = lines[0].split(". ", 1)[-1].strip()
            
            upvote_match = re.search(r"👍 (\d+)", block)
            upvotes = int(upvote_match.group(1)) if upvote_match else 0
            
            arxiv_match = re.search(r"`([^`]+)`", block)
            arxiv_id = arxiv_match.group(1) if arxiv_match else "N/A"
            
            abstract_match = re.search(r"### Abstract:\n> (.*)", block)
            summary = abstract_match.group(1) if abstract_match else ""

            papers.append({
                "title": title,
                "arxiv_id": arxiv_id,
                "upvotes": upvotes,
                "summary": summary,
                "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                "hf_paper_url": f"https://huggingface.co/papers/{arxiv_id}"
            })
        except Exception:
            continue
            
    return papers

def aggregate_local_papers(date_filter_func, top_n=15):
    """Reads saved daily files matching a date filter and picks top N unique papers."""
    all_files = glob.glob("daily_papers/hf_daily_*.md")
    combined_papers = {}

    for file_path in all_files:
        filename = os.path.basename(file_path)
        date_str = filename.replace("hf_daily_", "").replace(".md", "")
        
        try:
            file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_filter_func(file_date):
                file_papers = parse_md_file(file_path)
                for paper in file_papers:
                    aid = paper["arxiv_id"]
                    if aid not in combined_papers or paper["upvotes"] > combined_papers[aid]["upvotes"]:
                        combined_papers[aid] = paper
        except ValueError:
            continue

    sorted_papers = sorted(combined_papers.values(), key=lambda x: x["upvotes"], reverse=True)
    return sorted_papers[:top_n]

# -------------------------------------------------------------------
# 3. PIPELINE EXECUTION
# -------------------------------------------------------------------

def run_pipeline():
    today = datetime.datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")

    # Step A: Run Daily Fetch
    raw_data = fetch_hf_daily_papers()
    if raw_data:
        daily_papers = process_daily_items(raw_data, limit=10)
        write_markdown_file(
            papers=daily_papers,
            title_header=f"🌟 Top Hugging Face Daily Papers ({today_str})",
            folder_name="daily_papers",
            file_name=f"hf_daily_{today_str}.md"
        )

    # Step B: Run Weekly Aggregation (Every Sunday)
    if today.weekday() == 6:
        seven_days_ago = today - datetime.timedelta(days=7)
        weekly_papers = aggregate_local_papers(
            date_filter_func=lambda d: seven_days_ago <= d <= today,
            top_n=15
        )
        week_str = today.strftime("%Y-W%U")
        write_markdown_file(
            papers=weekly_papers,
            title_header=f"🏆 Top Hugging Face Weekly Roundup (Week {week_str})",
            folder_name="weekly_papers",
            file_name=f"hf_weekly_{week_str}.md"
        )

    # Step C: Run Monthly Aggregation (1st of Every Month)
    if today.day == 1:
        first_day_this_month = today.replace(day=1)
        last_month_last_day = first_day_this_month - datetime.timedelta(days=1)
        target_year = last_month_last_day.year
        target_month = last_month_last_day.month

        monthly_papers = aggregate_local_papers(
            date_filter_func=lambda d: d.year == target_year and d.month == target_month,
            top_n=20
        )
        month_str = last_month_last_day.strftime("%Y-%m")
        write_markdown_file(
            papers=monthly_papers,
            title_header=f"👑 Top Hugging Face Monthly Highlights ({month_str})",
            folder_name="monthly_papers",
            file_name=f"hf_monthly_{month_str}.md"
        )

if __name__ == "__main__":
    run_pipeline()