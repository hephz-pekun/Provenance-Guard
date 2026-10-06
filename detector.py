import os
import json
import re
import statistics
from groq import Groq
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def llm_classifier(text):

    prompt = f"""
Determine whether the following text appears AI-generated.

Return ONLY valid JSON:

{{
  "score": 0.0
}}

Text:
{text}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response.choices[0].message.content

    result = json.loads(content)

    return float(result["score"])

def stylometric_score(text):
    words = text.split()

    if len(words) < 10:
        return 0.5

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    lengths = [len(s.split()) for s in sentences]

    try:
        variance = statistics.pvariance(lengths)
    except:
        variance = 0

    unique_words = len(set(word.lower() for word in words))
    ttr = unique_words / len(words)

    variance_score = max(0, min(1, 1 - (variance / 50)))
    ttr_score = max(0, min(1, 1 - ttr))

    return round((variance_score + ttr_score) / 2, 2)

def repetition_score(text):

    words = [
        word.lower()
        for word in text.split()
    ]

    if len(words) < 10:
        return 0.5

    counts = Counter(words)

    repeated_words = sum(
        count - 1
        for count in counts.values()
        if count > 1
    )

    score = repeated_words / len(words)

    return round(
        min(score * 2, 1.0),
        2
    )