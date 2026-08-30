import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app.runner import run_scrapers
from app.services.process_venturebeat import process_venturebeat_markdown
from app.services.process_youtube import process_youtube_transcripts
from app.services.process_digest import process_digests
from app.services.process_email import send_digest_email

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def run_daily_pipeline(hours: int = 24, top_n: int = 10) -> dict:
    start_time = datetime.now()
    logger.info("Starting Daily AI News Aggregator Pipeline...")
    
    results = {
        "start_time": start_time.isoformat(),
        "scraping": {},
        "processing": {},
        "digests": {},
        "email": {},
        "success": False
    }
    try:
        scraping_results = run_scrapers(hours=hours)
        scraped_total = len(scraping_results.get("youtube", [])) + len(scraping_results.get("techcrunch", [])) + len(scraping_results.get("venturebeat", []))
        
        if scraped_total < 8:
            logger.info(f"Scraped only {scraped_total} items in the last {hours} hours. Widening search window to 3 days (72 hours)...")
            scraping_results = run_scrapers(hours=max(hours, 72))
        
        results["scraping"] = {
            "youtube": len(scraping_results.get("youtube", [])),
            "techcrunch": len(scraping_results.get("techcrunch", [])),
            "venturebeat": len(scraping_results.get("venturebeat", []))
        }
        
        venturebeat_result = process_venturebeat_markdown()
        results["processing"]["venturebeat"] = venturebeat_result
        
        youtube_result = process_youtube_transcripts()
        results["processing"]["youtube"] = youtube_result
        
        digest_result = process_digests(limit=15)
        results["digests"] = digest_result
        
        email_result = send_digest_email(hours=hours, top_n=top_n)
        results["email"] = email_result
        
        if email_result["success"]:
            results["success"] = True
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        results["error"] = str(e)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    results["end_time"] = end_time.isoformat()
    results["duration_seconds"] = duration
    
    if results["success"]:
        scraped_total = results["scraping"]["youtube"] + results["scraping"]["techcrunch"] + results["scraping"]["venturebeat"]
        logger.info(f"Pipeline completed: Scraped {scraped_total} items, created {results['digests'].get('processed', 0)} digests, sent email with {results['email'].get('articles_count', 0)} articles ({duration:.1f}s).")
    else:
        logger.error(f"Pipeline failed after {duration:.1f}s.")
        
    return results


if __name__ == "__main__":
    result = run_daily_pipeline(hours=24, top_n=10)
    exit(0 if result["success"] else 1)

