import os
import smtplib
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import markdown

load_dotenv()

MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")


def send_email(subject: str, body_text: str, body_html: str = None, recipients: list = None):
    if recipients is None:
        if not MY_EMAIL:
            raise ValueError("MY_EMAIL environment variable is not set")
        recipients = [MY_EMAIL]
    
    recipients = [r for r in recipients if r is not None]
    if not recipients:
        raise ValueError("No valid recipients provided")
    
    if not MY_EMAIL:
        raise ValueError("MY_EMAIL environment variable is not set")
    if not APP_PASSWORD:
        raise ValueError("APP_PASSWORD environment variable is not set")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = MY_EMAIL
    msg["To"] = ", ".join(recipients)
    
    part1 = MIMEText(body_text, "plain")
    msg.attach(part1)
    
    if body_html:
        part2 = MIMEText(body_html, "html")
        msg.attach(part2)
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(MY_EMAIL, APP_PASSWORD)
        smtp.sendmail(MY_EMAIL, recipients, msg.as_string())


def markdown_to_html(markdown_text: str) -> str:
    html_body = markdown.markdown(markdown_text, extensions=['extra', 'nl2br'])
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #334155;
            background-color: #f8fafc;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
        }}
        .container {{
            max-width: 600px;
            margin: 24px auto;
            padding: 24px;
            background-color: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }}
        .header-banner {{
            background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
            padding: 32px 24px;
            border-radius: 12px;
            color: #ffffff;
            text-align: center;
            margin-bottom: 24px;
        }}
        .header-title {{
            font-size: 28px;
            font-weight: 800;
            margin: 0 0 8px 0;
            letter-spacing: -0.025em;
        }}
        .header-subtitle {{
            font-size: 14px;
            font-weight: 500;
            opacity: 0.9;
            margin: 0;
        }}
        h2 {{
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
            margin-top: 24px;
            margin-bottom: 12px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 6px;
        }}
        h3 {{
            font-size: 16px;
            font-weight: 600;
            color: #0f172a;
            margin-top: 20px;
            margin-bottom: 8px;
        }}
        p {{
            margin: 8px 0;
            color: #334155;
        }}
        a {{
            color: #4f46e5;
            text-decoration: none;
            font-weight: 600;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-banner">
            <div class="header-title">Morning Synapse 🌅</div>
            <div class="header-subtitle">Your AI-Curated Daily Tech Intelligence</div>
        </div>
        {html_body}
    </div>
</body>
</html>"""


def digest_to_html(digest_response) -> str:
    from app.agent.email_agent import EmailDigestResponse
    
    if not isinstance(digest_response, EmailDigestResponse):
        return markdown_to_html(digest_response.to_markdown() if hasattr(digest_response, 'to_markdown') else str(digest_response))
    
    html_parts = []
    
    html_parts.append("""
    <div class="header-banner">
        <div class="header-title">Morning Synapse 🌅</div>
        <div class="header-subtitle">Your AI-Curated Daily Tech Intelligence</div>
    </div>
    """)
    
    greeting_html = markdown.markdown(digest_response.introduction.greeting, extensions=['extra', 'nl2br'])
    introduction_html = markdown.markdown(digest_response.introduction.introduction, extensions=['extra', 'nl2br'])
    
    html_parts.append(f"""
    <div class="intro-section">
        <div class="greeting">{greeting_html}</div>
        <div class="introduction">{introduction_html}</div>
    </div>
    """)
    
    for article in digest_response.articles:
        url_lower = (article.url or "").lower()
        is_video = "youtube.com" in url_lower or "youtu.be" in url_lower or "vimeo.com" in url_lower
        
        site_name = "Article"
        if article.url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(article.url)
                netloc = parsed.netloc.lower()
                if netloc.startswith("www."):
                    netloc = netloc[4:]
                
                parts = netloc.split('.')
                if len(parts) >= 2:
                    if parts[-2] in ("co", "com", "org", "net", "edu", "gov") and len(parts) >= 3:
                        site = parts[-3]
                    else:
                        site = parts[-2]
                else:
                    site = netloc
                
                if site in ("youtube", "youtu"):
                    site_name = "YouTube"
                elif site == "techcrunch":
                    site_name = "TechCrunch"
                elif site == "venturebeat":
                    site_name = "VentureBeat"
                elif site == "theverge":
                    site_name = "The Verge"
                elif site == "technologyreview":
                    site_name = "MIT Tech Review"
                else:
                    site_name = site.capitalize()
            except Exception:
                site_name = (article.article_type or "Article").capitalize()
        else:
            site_name = (article.article_type or "Article").capitalize()
            
        h = sum(ord(c) for c in site_name) % 360
        badge_style = f"background-color: hsl({h}, 70%, 96%); color: hsl({h}, 80%, 25%); border: 1px solid hsl({h}, 50%, 88%);"
        
        icon = "🎥" if is_video else "📰"
        badge_text = f"{icon} {site_name}"
        btn_text = "Watch Video →" if is_video else "Read Article →"
        
        summary_html = markdown.markdown(article.summary, extensions=['extra', 'nl2br'])
        
        html_parts.append(f"""
        <div class="article-card">
            <div class="badge-row">
                <span class="badge" style="{badge_style}">{badge_text}</span>
            </div>
            <h3 class="article-title">{html.escape(article.title)}</h3>
            <div class="article-summary">{summary_html}</div>
            <div class="article-action">
                <a href="{html.escape(article.url)}" class="action-btn" target="_blank">{btn_text}</a>
            </div>
        </div>
        """)
    
    html_content = '\n'.join(html_parts)
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #334155;
            background-color: #f8fafc;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
        }}
        .container {{
            max-width: 600px;
            margin: 24px auto;
            padding: 24px;
            background-color: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }}
        .header-banner {{
            background: linear-gradient(135deg, #4f46e5 0%, #ec4899 100%);
            padding: 36px 24px;
            border-radius: 12px;
            color: #ffffff;
            text-align: center;
            margin-bottom: 24px;
        }}
        .header-title {{
            font-size: 28px;
            font-weight: 800;
            margin: 0 0 6px 0;
            letter-spacing: -0.025em;
        }}
        .header-subtitle {{
            font-size: 14px;
            font-weight: 500;
            opacity: 0.95;
            margin: 0;
        }}
        .intro-section {{
            background-color: #f8fafc;
            border-left: 4px solid #4f46e5;
            padding: 16px 20px;
            border-radius: 4px 8px 8px 4px;
            margin-bottom: 32px;
            border-top: 1px solid #e2e8f0;
            border-right: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
        }}
        .greeting p {{
            margin: 0 0 6px 0;
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
        }}
        .introduction p {{
            margin: 0;
            font-size: 14px;
            color: #475569;
        }}
        .article-card {{
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }}
        .badge-row {{
            margin-bottom: 12px;
        }}
        .badge {{
            display: inline-block;
            font-size: 10px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .article-title {{
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
            margin: 0 0 10px 0;
            line-height: 1.4;
        }}
        .article-summary p {{
            font-size: 14px;
            color: #334155;
            margin: 0 0 8px 0;
        }}
        .article-summary p:last-child {{
            margin-bottom: 0;
        }}
        .article-summary strong {{
            color: #0f172a;
        }}
        .article-action {{
            margin-top: 16px;
        }}
        .action-btn {{
            display: inline-block;
            padding: 8px 16px;
            background-color: #4f46e5;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
        }}
        .action-btn:hover {{
            background-color: #4338ca;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>"""


def send_email_to_self(subject: str, body: str):
    if not MY_EMAIL:
        raise ValueError("MY_EMAIL environment variable is not set. Please set it in your .env file.")
    send_email(subject, body, recipients=[MY_EMAIL])


if __name__ == "__main__":
    send_email_to_self("Test from Python", "Hello from my script.")