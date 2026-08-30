from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.scrapers.scrapers import VentureBeatScraper
from app.database.repository import Repository

def process_venturebeat_markdown(limit: Optional[int] = None) -> dict:
    scraper = VentureBeatScraper()
    repo = Repository()
    
    articles = repo.get_venturebeat_articles_without_markdown(limit=limit)
    processed = 0
    failed = 0
    
    for article in articles:
        markdown = scraper.url_to_markdown(article.url)
        try:
            if markdown:
                repo.update_venturebeat_article_markdown(article.guid, markdown)
                processed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"Error processing article {article.guid}: {e}")
            continue
    
    return {
        "total": len(articles),
        "processed": processed,
        "failed": failed
    }

if __name__ == "__main__":
    result = process_venturebeat_markdown()
    print(f"Total articles: {result['total']}")
    print(f"Processed: {result['processed']}")
    print(f"Failed: {result['failed']}")
