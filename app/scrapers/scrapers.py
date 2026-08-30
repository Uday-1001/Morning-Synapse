import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import feedparser
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.proxies import WebshareProxyConfig

class Transcript(BaseModel):
    text: str


class ChannelVideo(BaseModel):
    title: str
    url: str
    video_id: str
    published_at: datetime
    description: str
    transcript: Optional[str] = None


class YouTubeScraper:
    def __init__(self):
        proxy_config = None
        proxy_username = os.getenv("PROXY_USERNAME")
        proxy_password = os.getenv("PROXY_PASSWORD")
        
        if proxy_username and proxy_password:
            proxy_config = WebshareProxyConfig(
                proxy_username=proxy_username,
                proxy_password=proxy_password
            )
        
        self.transcript_api = YouTubeTranscriptApi(proxy_config=proxy_config)

    def _get_rss_url(self, channel_id: str) -> str:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    def _extract_video_id(self, video_url: str) -> str:
        if "youtube.com/watch?v=" in video_url:
            return video_url.split("v=")[1].split("&")[0]
        if "youtube.com/shorts/" in video_url:
            return video_url.split("shorts/")[1].split("?")[0]
        if "youtu.be/" in video_url:
            return video_url.split("youtu.be/")[1].split("?")[0]
        return video_url

    def get_transcript(self, video_id: str) -> Optional[Transcript]:
        try:
            transcript = self.transcript_api.fetch(video_id)
            text = " ".join([snippet.text for snippet in transcript.snippets])
            return Transcript(text=text)
        except (TranscriptsDisabled, NoTranscriptFound):
            return None
        except Exception:
            return None

    def get_latest_videos(self, channel_id: str, hours: int = 24) -> list[ChannelVideo]:
        feed = feedparser.parse(self._get_rss_url(channel_id))
        if not feed.entries:
            return []
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        videos = []
        
        for entry in feed.entries:
            if "/shorts/" in entry.link:
                continue
            published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published_time >= cutoff_time:
                video_id = self._extract_video_id(entry.link)
                videos.append(ChannelVideo(
                    title=entry.title,
                    url=entry.link,
                    video_id=video_id,
                    published_at=published_time,
                    description=entry.get("summary", "")
                ))
        
        return videos

    def scrape_channel(self, channel_id: str, hours: int = 150) -> list[ChannelVideo]:
        videos = self.get_latest_videos(channel_id, hours)
        result = []
        for video in videos:
            transcript = self.get_transcript(video.video_id)
            result.append(video.model_copy(update={"transcript": transcript.text if transcript else None}))
        return result


class TechCrunchArticle(BaseModel):
    title: str
    description: str
    url: str
    guid: str
    published_at: datetime
    category: Optional[str] = None


class TechCrunchScraper:
    def __init__(self):
        self.rss_url = "https://techcrunch.com/category/artificial-intelligence/feed/"

    def get_articles(self, hours: int = 24) -> List[TechCrunchArticle]:
        feed = feedparser.parse(self.rss_url)
        if not feed.entries:
            return []
        
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours)
        articles = []
        
        for entry in feed.entries:
            published_parsed = getattr(entry, "published_parsed", None)
            if not published_parsed:
                continue
            
            published_time = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            if published_time >= cutoff_time:
                articles.append(TechCrunchArticle(
                    title=entry.get("title", ""),
                    description=entry.get("description", ""),
                    url=entry.get("link", ""),
                    guid=entry.get("id", entry.get("link", "")),
                    published_at=published_time,
                    category=entry.get("tags", [{}])[0].get("term") if entry.get("tags") else None
                ))
        
        return articles


class VentureBeatArticle(BaseModel):
    title: str
    description: str
    url: str
    guid: str
    published_at: datetime
    category: Optional[str] = None


class VentureBeatScraper:
    def __init__(self):
        self.rss_urls = [
            "https://venturebeat.com/category/ai/feed/"
        ]

    def get_articles(self, hours: int = 24) -> List[VentureBeatArticle]:
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours)
        articles = []
        seen_guids = set()
        
        for rss_url in self.rss_urls:
            feed = feedparser.parse(rss_url)
            if not feed.entries:
                continue
            
            for entry in feed.entries:
                published_parsed = getattr(entry, "published_parsed", None)
                if not published_parsed:
                    continue
                
                published_time = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                if published_time >= cutoff_time:
                    guid = entry.get("id", entry.get("link", ""))
                    if guid not in seen_guids:
                        seen_guids.add(guid)
                        articles.append(VentureBeatArticle(
                            title=entry.get("title", ""),
                            description=entry.get("description", ""),
                            url=entry.get("link", ""),
                            guid=guid,
                            published_at=published_time,
                            category=entry.get("tags", [{}])[0].get("term") if entry.get("tags") else None
                        ))
        
        return articles

    def url_to_markdown(self, url: str) -> Optional[str]:
        try:
            import requests
            from markdownify import markdownify as md
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if response.status_code == 200:
                return md(response.text)
            return None
        except Exception:
            return None
