from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import YouTubeVideo, TechCrunchArticle, VentureBeatArticle, Digest
from .connection import get_session


class Repository:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def create_youtube_video(self, video_id: str, title: str, url: str, channel_id: str, 
                            published_at: datetime, description: str = "", transcript: Optional[str] = None) -> Optional[YouTubeVideo]:
        existing = self.session.query(YouTubeVideo).filter_by(video_id=video_id).first()
        if existing:
            return None
        video = YouTubeVideo(
            video_id=video_id,
            title=title,
            url=url,
            channel_id=channel_id,
            published_at=published_at,
            description=description,
            transcript=transcript
        )
        self.session.add(video)
        self.session.commit()
        return video
    
    def create_techcrunch_article(self, guid: str, title: str, url: str, published_at: datetime,
                              description: str = "", category: Optional[str] = None) -> Optional[TechCrunchArticle]:
        existing = self.session.query(TechCrunchArticle).filter_by(guid=guid).first()
        if existing:
            return None
        article = TechCrunchArticle(
            guid=guid,
            title=title,
            url=url,
            published_at=published_at,
            description=description,
            category=category
        )
        self.session.add(article)
        self.session.commit()
        return article
    
    def create_venturebeat_article(self, guid: str, title: str, url: str, published_at: datetime,
                                 description: str = "", category: Optional[str] = None) -> Optional[VentureBeatArticle]:
        existing = self.session.query(VentureBeatArticle).filter_by(guid=guid).first()
        if existing:
            return None
        article = VentureBeatArticle(
            guid=guid,
            title=title,
            url=url,
            published_at=published_at,
            description=description,
            category=category
        )
        self.session.add(article)
        self.session.commit()
        return article
    
    def bulk_create_youtube_videos(self, videos: List[dict]) -> int:
        new_videos = []
        for v in videos:
            existing = self.session.query(YouTubeVideo).filter_by(video_id=v["video_id"]).first()
            if not existing:
                new_videos.append(YouTubeVideo(
                    video_id=v["video_id"],
                    title=v["title"],
                    url=v["url"],
                    channel_id=v.get("channel_id", ""),
                    published_at=v["published_at"],
                    description=v.get("description", ""),
                    transcript=v.get("transcript")
                ))
        if new_videos:
            self.session.add_all(new_videos)
            self.session.commit()
        return len(new_videos)
    
    def bulk_create_techcrunch_articles(self, articles: List[dict]) -> int:
        new_articles = []
        for a in articles:
            existing = self.session.query(TechCrunchArticle).filter_by(guid=a["guid"]).first()
            if not existing:
                new_articles.append(TechCrunchArticle(
                    guid=a["guid"],
                    title=a["title"],
                    url=a["url"],
                    published_at=a["published_at"],
                    description=a.get("description", ""),
                    category=a.get("category")
                ))
        if new_articles:
            self.session.add_all(new_articles)
            self.session.commit()
        return len(new_articles)
    
    def bulk_create_venturebeat_articles(self, articles: List[dict]) -> int:
        new_articles = []
        for a in articles:
            existing = self.session.query(VentureBeatArticle).filter_by(guid=a["guid"]).first()
            if not existing:
                new_articles.append(VentureBeatArticle(
                    guid=a["guid"],
                    title=a["title"],
                    url=a["url"],
                    published_at=a["published_at"],
                    description=a.get("description", ""),
                    category=a.get("category")
                ))
        if new_articles:
            self.session.add_all(new_articles)
            self.session.commit()
        return len(new_articles)
    
    def get_venturebeat_articles_without_markdown(self, limit: Optional[int] = None) -> List[VentureBeatArticle]:
        query = self.session.query(VentureBeatArticle).filter(VentureBeatArticle.markdown.is_(None))
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def update_venturebeat_article_markdown(self, guid: str, markdown: str) -> bool:
        article = self.session.query(VentureBeatArticle).filter_by(guid=guid).first()
        if article:
            article.markdown = markdown
            self.session.commit()
            return True
        return False
    
    def get_youtube_videos_without_transcript(self, limit: Optional[int] = None) -> List[YouTubeVideo]:
        query = self.session.query(YouTubeVideo).filter(YouTubeVideo.transcript.is_(None))
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def update_youtube_video_transcript(self, video_id: str, transcript: str) -> bool:
        video = self.session.query(YouTubeVideo).filter_by(video_id=video_id).first()
        if video:
            video.transcript = transcript
            self.session.commit()
            return True
        return False
    
    def get_articles_without_digest(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        articles = []
        seen_ids = set()
        
        digests = self.session.query(Digest).all()
        for d in digests:
            seen_ids.add(f"{d.article_type}:{d.article_id}")
        
        youtube_videos = self.session.query(YouTubeVideo).all()
        for video in youtube_videos:
            key = f"youtube:{video.video_id}"
            if key not in seen_ids:
                transcript_text = video.transcript if (video.transcript and video.transcript != "__UNAVAILABLE__") else None
                content_text = transcript_text or video.description or video.title or ""
                articles.append({
                    "type": "youtube",
                    "id": video.video_id,
                    "title": video.title,
                    "url": video.url,
                    "content": content_text,
                    "published_at": video.published_at
                })
        
        techcrunch_articles = self.session.query(TechCrunchArticle).all()
        for article in techcrunch_articles:
            key = f"techcrunch:{article.guid}"
            if key not in seen_ids:
                articles.append({
                    "type": "techcrunch",
                    "id": article.guid,
                    "title": article.title,
                    "url": article.url,
                    "content": article.description or "",
                    "published_at": article.published_at
                })
        
        venturebeat_articles = self.session.query(VentureBeatArticle).filter(
            VentureBeatArticle.markdown.isnot(None)
        ).all()
        for article in venturebeat_articles:
            key = f"venturebeat:{article.guid}"
            if key not in seen_ids:
                articles.append({
                    "type": "venturebeat",
                    "id": article.guid,
                    "title": article.title,
                    "url": article.url,
                    "content": article.markdown or article.description or "",
                    "published_at": article.published_at
                })
        
        def get_pub_date(x):
            d = x.get("published_at")
            if not d:
                from datetime import timezone
                return datetime.min.replace(tzinfo=timezone.utc)
            if d.tzinfo is None:
                from datetime import timezone
                return d.replace(tzinfo=timezone.utc)
            return d
            
        articles.sort(key=get_pub_date, reverse=True)
        
        if limit:
            articles = articles[:limit]
        
        return articles
    
    def create_digest(self, article_type: str, article_id: str, url: str, title: str, summary: str, published_at: Optional[datetime] = None) -> Optional[Digest]:
        digest_id = f"{article_type}:{article_id}"
        existing = self.session.query(Digest).filter_by(id=digest_id).first()
        if existing:
            return None
        
        if published_at:
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
            created_at = published_at
        else:
            created_at = datetime.now(timezone.utc)
        
        digest = Digest(
            id=digest_id,
            article_type=article_type,
            article_id=article_id,
            url=url,
            title=title,
            summary=summary,
            created_at=created_at
        )
        self.session.add(digest)
        self.session.commit()
        return digest
    
    def get_recent_digests(self, hours: int = 24) -> List[Dict[str, Any]]:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        digests = self.session.query(Digest).filter(
            Digest.created_at >= cutoff_time
        ).order_by(Digest.created_at.desc()).all()
        
        return [
            {
                "id": d.id,
                "article_type": d.article_type,
                "article_id": d.article_id,
                "url": d.url,
                "title": d.title,
                "summary": d.summary,
                "created_at": d.created_at
            }
            for d in digests
        ]

