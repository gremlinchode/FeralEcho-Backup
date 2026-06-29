import re
import random

def tokenize_text(text):
    return text.split()

def analyze_sentiment(text):
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer

    sia = SentimentIntensityAnalyzer()
    return sia.polarity_scores(text)

def self_edit(text):
    tokens = tokenize_text(text)
    sentiment_scores = [analyze_sentiment(token) for token in tokens]
    
    edited_tokens = []
    for i, (token, score) in enumerate(zip(tokens, sentiment_scores)):
        if score['compound'] > 0.5:  # Positive sentiment
            edited_token = f"{token} ({random.choice(['gratitude', 'joy'])})"
        elif score['compound'] < -0.5:  # Negative sentiment
            edited_token = f"{token} ({random.choice(['self-care', 'empathy'])})"
        else:  # Neutral sentiment
            edited_token = token
        edited_tokens.append(edited_token)

    return " ".join(edited_tokens)

input_text = "I'm feeling anxious today"
edited_text = self_edit(input_text)
print(edited_text)