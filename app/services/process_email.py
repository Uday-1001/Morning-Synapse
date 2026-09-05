from typing import List
import logging
from dotenv import load_dotenv

load_dotenv()

from app.agent.email_agent import EmailAgent, RankedArticleDetail, EmailDigestResponse
from app.agent.curator_agent import CuratorAgent
from app.profiles.user_profile import USER_PROFILE
from app.database.repository import Repository
from app.services.email import send_email, digest_to_html
logger = logging.getLogger(__name__)


def select_diverse_top_articles(article_details: List[RankedArticleDetail], limit: int = 10) -> List[RankedArticleDetail]:
    if len(article_details) <= limit:
        return article_details
    
    by_type = {}
    for a in article_details:
        by_type.setdefault(a.article_type, []).append(a)
    
    selected = []
    selected_ids = set()
    
    target_per_type = max(1, limit // len(by_type)) if by_type else 3
    for art_type, items in by_type.items():
        for item in items[:target_per_type]:
            if item.digest_id not in selected_ids:
                selected.append(item)
                selected_ids.add(item.digest_id)
    
    for item in article_details:
        if len(selected) >= limit:
            break
        if item.digest_id not in selected_ids:
            selected.append(item)
            selected_ids.add(item.digest_id)
            
    selected.sort(key=lambda x: x.rank)
    return selected


def generate_email_digest(hours: int = 24, top_n: int = 10) -> EmailDigestResponse:
    curator = CuratorAgent(USER_PROFILE)
    email_agent = EmailAgent(USER_PROFILE)
    repo = Repository()
    
    raw_digests = repo.get_recent_digests(hours=max(hours, 72))
    if len(raw_digests) < 10:
        raw_digests = repo.get_recent_digests(hours=max(hours, 168))
    
    by_type_digests = {}
    for d in raw_digests:
        by_type_digests.setdefault(d["article_type"], []).append(d)
    
    digests = []
    seen_ids = set()
    for art_type, items in by_type_digests.items():
        for item in items[:9]:
            if item["id"] not in seen_ids and len(digests) < 25:
                digests.append(item)
                seen_ids.add(item["id"])
    
    for d in raw_digests:
        if len(digests) >= 25:
            break
        if d["id"] not in seen_ids:
            digests.append(d)
            seen_ids.add(d["id"])
            
    total = len(digests)
    
    if total == 0:
        logger.warning(f"No digests found from the last {hours} hours")
        raise ValueError("No digests available")
    
    logger.info(f"Ranking {total} digests for email generation")
    ranked_articles = curator.rank_digests(digests)
    
    if not ranked_articles:
        logger.error("Failed to rank digests")
        raise ValueError("Failed to rank articles")
    
    logger.info(f"Generating email digest with top {top_n} articles")
    
    article_details = [
        RankedArticleDetail(
            digest_id=a.digest_id,
            rank=a.rank,
            relevance_score=a.relevance_score,
            reasoning=a.reasoning,
            title=next((d["title"] for d in digests if d["id"] == a.digest_id), ""),
            summary=next((d["summary"] for d in digests if d["id"] == a.digest_id), ""),
            url=next((d["url"] for d in digests if d["id"] == a.digest_id), ""),
            article_type=next((d["article_type"] for d in digests if d["id"] == a.digest_id), "")
        )
        for a in ranked_articles
    ]
    
    diverse_article_details = select_diverse_top_articles(article_details, limit=top_n)
    
    email_digest = email_agent.create_email_digest_response(
        ranked_articles=diverse_article_details,
        total_ranked=len(ranked_articles),
        limit=top_n
    )
    
    logger.info("Email digest generated successfully")
    logger.info(f"\n=== Email Introduction ===")
    logger.info(email_digest.introduction.greeting)
    logger.info(f"\n{email_digest.introduction.introduction}")
    
    return email_digest


def send_digest_email(hours: int = 24, top_n: int = 10) -> dict:
    try:
        result = generate_email_digest(hours=hours, top_n=top_n)
        markdown_content = result.to_markdown()
        html_content = digest_to_html(result)
        
        subject = f"Daily AI News Digest - {result.introduction.greeting.split('for ')[-1] if 'for ' in result.introduction.greeting else 'Today'}"
        
        send_email(
            subject=subject,
            body_text=markdown_content,
            body_html=html_content
        )
        
        logger.info("Email sent successfully!")
        return {
            "success": True,
            "subject": subject,
            "articles_count": len(result.articles)
        }
    except ValueError as e:
        logger.error(f"Error sending email: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    result = send_digest_email(hours=24, top_n=10)
    if result["success"]:
        print("\n=== Email Digest Sent ===")
        print(f"Subject: {result['subject']}")
        print(f"Articles: {result['articles_count']}")
    else:
        print(f"Error: {result['error']}")

