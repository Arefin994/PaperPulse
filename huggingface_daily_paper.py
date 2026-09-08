import os
import datetime
import requests

# Hugging Face Daily Papers public API endpoint
HF_DAILY_PAPERS_URL = "https://huggingface.co/api/daily_papers"

def fetch_top_huggingface_papers(limit=10):
    """Fetches the top community-voted papers for today from Hugging Face."""
    print("Fetching top papers from Hugging Face...")
    
    response = requests.get(HF_DAILY_PAPERS_URL)
    
    if response.status_code != 200:
        print(f"Error fetching data: Status Code {response.status_code}")
        return []

    papers_data = response.json()[:limit]
    extracted_papers = []

    for item in papers_data:
        paper_info = item.get("paper", {})
        
        arxiv_id = paper_info.get("id", "N/A")
        title = paper_info.get("title", "No Title").strip()
        summary = paper_info.get("summary", "No Abstract Available").strip()
        upvotes = item.get("upvotes", 0)
        
        # Construct direct links
        arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        hf_paper_url = f"https://huggingface.co/papers/{arxiv_id}"

        extracted_papers.append({
            "title": title,
            "arxiv_id": arxiv_id,
            "upvotes": upvotes,
            "summary": summary,
            "arxiv_url": arxiv_url,
            "pdf_url": pdf_url,
            "hf_paper_url": hf_paper_url
        })

    return extracted_papers


def save_papers_to_markdown(papers):
    """Saves the top 10 papers into a daily Markdown file."""
    if not papers:
        print("No papers to save.")
        return

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    folder = "daily_papers_hf"
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, f"hf_top_papers_{today_str}.md")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# 🌟 Top Hugging Face Daily Papers ({today_str})\n\n")
        f.write(f"*Total Papers Saved: {len(papers)}*\n\n")
        f.write("=" * 80 + "\n\n")

        for idx, paper in enumerate(papers, 1):
            f.write(f"## {idx}. {paper['title']}\n")
            f.write(f"**Upvotes:** 👍 {paper['upvotes']} | **arXiv ID:** `{paper['arxiv_id']}`\n\n")
            f.write(f"**Links:** [arXiv Page]({paper['arxiv_url']}) | [Download PDF]({paper['pdf_url']}) | [Hugging Face Discussion]({paper['hf_paper_url']})\n\n")
            f.write("### Abstract:\n")
            f.write(f"> {paper['summary']}\n\n")
            f.write("-" * 80 + "\n\n")

    print(f"Successfully saved top {len(papers)} papers to: {file_path}")


def main():
    top_papers = fetch_top_huggingface_papers(limit=10)
    save_papers_to_markdown(top_papers)


if __name__ == "__main__":
    main()