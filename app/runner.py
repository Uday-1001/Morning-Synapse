from typing import List
from .config import YOUTUBE_CHANNELS
from .scrapers.scrapers import (
    YouTubeScraper, ChannelVideo,
    TechCrunchScraper, TechCrunchArticle,
    VentureBeatScraper, VentureBeatArticle
)
from .database.repository import Repository


def run_scrapers(hours: int = 24) -> dict:
    youtube_scraper = YouTubeScraper()
    techcrunch_scraper = TechCrunchScraper()
    venturebeat_scraper = VentureBeatScraper()
    repo = Repository()
    
    youtube_videos = []
    video_dicts = []
    for channel_id in YOUTUBE_CHANNELS:
        videos = youtube_scraper.get_latest_videos(channel_id, hours=hours)
        youtube_videos.extend(videos)
        video_dicts.extend([
            {
                "video_id": v.video_id,
                "title": v.title,
                "url": v.url,
                "channel_id": channel_id,
                "published_at": v.published_at,
                "description": v.description,
                "transcript": v.transcript
            }
            for v in videos
        ])
    
    techcrunch_articles = techcrunch_scraper.get_articles(hours=hours)
    venturebeat_articles = venturebeat_scraper.get_articles(hours=hours)
    
    if video_dicts:
        repo.bulk_create_youtube_videos(video_dicts)
    
    if techcrunch_articles:
        article_dicts = [
            {
                "guid": a.guid,
                "title": a.title,
                "url": a.url,
                "published_at": a.published_at,
                "description": a.description,
                "category": a.category
            }
            for a in techcrunch_articles
        ]
        repo.bulk_create_techcrunch_articles(article_dicts)
    
    if venturebeat_articles:
        article_dicts = [
            {
                "guid": a.guid,
                "title": a.title,
                "url": a.url,
                "published_at": a.published_at,
                "description": a.description,
                "category": a.category
            }
            for a in venturebeat_articles
        ]
        repo.bulk_create_venturebeat_articles(article_dicts)
    
    return {
        "youtube": youtube_videos,
        "techcrunch": techcrunch_articles,
        "venturebeat": venturebeat_articles,
    }


if __name__ == "__main__":
    results = run_scrapers(hours=24)
    print(f"YouTube videos: {len(results['youtube'])}")
    print(f"TechCrunch articles: {len(results['techcrunch'])}")
    print(f"VentureBeat articles: {len(results['venturebeat'])}")

