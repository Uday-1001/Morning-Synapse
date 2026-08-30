import os
from typing import Optional
from groq import Groq
from pydantic import BaseModel
from .utils import call_with_retry
from dotenv import load_dotenv

load_dotenv()


class DigestOutput(BaseModel):
    title: str
    summary: str


PROMPT = """You are an expert AI news analyst specializing in summarizing technical articles, research papers, and video content about artificial intelligence.

Your role is to create concise, informative digests that help readers quickly understand the key points and significance of AI-related content.

Guidelines:
- Create a compelling title (5-10 words) that captures the essence of the content
- Write a 2-3 sentence summary that highlights the main points and why they matter
- Focus on actionable insights and implications
- Use clear, accessible language while maintaining technical accuracy
- Avoid marketing fluff and focus on substance
- Respond with a JSON object containing "title" and "summary" fields"""


class DigestAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is missing or empty. Please ensure you have configured it in your .env file (for local runs) or GitHub Secrets (for GitHub Actions).")
        self.client = Groq(api_key=api_key)
        self.model = "openai/gpt-oss-120b"
        self.system_prompt = PROMPT

    def generate_digest(self, title: str, content: str, article_type: str) -> Optional[DigestOutput]:
        try:
            user_prompt = f"Create a digest for this {article_type}: \n Title: {title} \n Content: {content[:2500]}"

            try:
                response = call_with_retry(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
            except Exception:
                response = call_with_retry(
                    self.client.chat.completions.create,
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
            
            content_str = response.choices[0].message.content
            return DigestOutput.model_validate_json(content_str)
        except Exception as e:
            print(f"Error generating digest: {e}")
            return None

