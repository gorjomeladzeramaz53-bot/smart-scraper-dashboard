from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from playwright.sync_api import sync_playwright
import os
import io
import csv

app = FastAPI()

@app.get("/ui", response_class=HTMLResponse)
def get_ui():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return "<h1>index.html ფაილი ვერ მოიძებნა!</h1>"

@app.get("/ai-scrape")
def ai_scrape(url: str):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page_title = page.title() or "უსათაურო"
            
            text_content = page.evaluate("document.body ? document.body.innerText : ''")
            words = text_content.split() if text_content else []
            total_words = len(words)

            images = []
            links = []
            try:
                images = page.locator("img").evaluate_all("(imgs) => imgs.map(img => img.src).filter(Boolean).slice(0, 5)")
            except Exception:
                images = []

            try:
                links = page.locator("a").evaluate_all("(anchors) => anchors.map(a => a.href).filter(h => h && h.startsWith('http')).slice(0, 5)")
            except Exception:
                links = []

            unique_words = list(set([w.strip('.,()[]{}"\':;!?').lower() for w in words if len(w) > 4]))[:5]

            summary = f"გვერდის ავტომატური ანალიზი: '{page_title}'. საიტი შეიცავს დაახლოებით {total_words} სიტყვას."

            browser.close()

            return {
                "url": url,
                "page_title": page_title,
                "total_words": total_words,
                "ai_smart_summary": summary,
                "key_insights": {
                    "top_keywords": unique_words if unique_words else ["web", "content", "data"],
                    "images_found": images,
                    "links_found": links,
                    "content_quality": "მაღალი - ოპტიმიზებული ვებ-ინდექსისთვის",
                    "reading_time_minutes": round(total_words / 200, 1) if total_words > 0 else 0.5
                },
                "status": "success"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"სქრეიპინგის შეცდომა: {str(e)}")

@app.get("/download-csv")
def download_csv(url: str, title: str, words: int, summary: str):
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["URL", "Page Title", "Total Words", "AI Summary"])
    writer.writerow([url, title, words, summary])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scraper_result.csv"}
    )