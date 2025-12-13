#!/usr/bin/env python3
"""
SentimentAnalyzerAgent - Interactive Demo
Demonstrates sentiment analysis capabilities with multiple examples
"""

import asyncio
import sys
from pathlib import Path

# Add src/ to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent


async def demo_basic():
    """Basic sentiment analysis examples"""
    print("\n" + "="*70)
    print("DEMO 1: Basic Sentiment Analysis")
    print("="*70 + "\n")
    
    agent = SentimentAnalyzerAgent()
    
    test_cases = [
        "This product is excellent! I love it.",
        "Terrible experience. Never buying again.",
        "The item was delivered on Tuesday.",
        "Amazing quality! Best purchase ever!",
        "Poor customer service and bad quality.",
    ]
    
    for text in test_cases:
        result = await agent.execute(task=text, context={})
        
        # Color coding
        emoji = {
            "positive": "😊 ✅",
            "negative": "😞 ❌",
            "neutral": "😐 ➖"
        }[result["sentiment"]]
        
        print(f"{emoji} Sentiment: {result['sentiment'].upper():<10} (Confidence: {result['confidence']:.2f})")
        print(f"   Text: \"{text}\"")
        print()


async def demo_detailed():
    """Detailed analysis with keyword extraction"""
    print("\n" + "="*70)
    print("DEMO 2: Detailed Analysis with Keywords")
    print("="*70 + "\n")
    
    agent = SentimentAnalyzerAgent()
    
    text = "This is absolutely fantastic and wonderful! I'm so happy with it. Great product!"
    
    result = await agent.execute(task=text, context={"detailed": True})
    
    print(f"📝 Text: \"{text}\"")
    print()
    print(f"Sentiment:       {result['sentiment'].upper()}")
    print(f"Confidence:      {result['confidence']:.2%}")
    print(f"Positive Score:  {result['positive_score']:.2%}")
    print(f"Negative Score:  {result['negative_score']:.2%}")
    print(f"Keywords Found:  {', '.join(result['keywords'])}")
    print()


async def demo_multilingual():
    """Multilingual sentiment analysis"""
    print("\n" + "="*70)
    print("DEMO 3: Multilingual Support")
    print("="*70 + "\n")
    
    agent = SentimentAnalyzerAgent()
    
    test_cases = [
        ("English", "Excellent and amazing!"),
        ("French", "C'est génial et super formidable!"),
        ("French", "C'est catastrophique et nul."),
        ("English", "Awful and disappointing."),
    ]
    
    for language, text in test_cases:
        result = await agent.execute(task=text, context={"detailed": True})
        
        flag = "🇬🇧" if language == "English" else "🇫🇷"
        
        print(f"{flag} {language}: \"{text}\"")
        print(f"   Sentiment: {result['sentiment'].upper()} ({result['confidence']:.2f})")
        print(f"   Keywords: {', '.join(result['keywords'])}")
        print()


async def demo_batch():
    """Batch processing of multiple texts"""
    print("\n" + "="*70)
    print("DEMO 4: Batch Processing - Customer Reviews")
    print("="*70 + "\n")
    
    agent = SentimentAnalyzerAgent()
    
    reviews = [
        "Great product, highly recommend!",
        "Poor quality, fell apart after 2 days.",
        "Okay, nothing special.",
        "Love it! Exceeded my expectations.",
        "Terrible customer service.",
        "Works as expected.",
        "Fantastic! Will buy again.",
        "Disappointing and overpriced.",
    ]
    
    print(f"Analyzing {len(reviews)} customer reviews...\n")
    
    # Parallel analysis
    results = await asyncio.gather(*[
        agent.execute(task=review, context={})
        for review in reviews
    ])
    
    # Aggregate statistics
    sentiments = {"positive": 0, "negative": 0, "neutral": 0}
    total_confidence = 0.0
    
    for i, (review, result) in enumerate(zip(reviews, results), 1):
        sentiments[result["sentiment"]] += 1
        total_confidence += result["confidence"]
        
        emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}[result["sentiment"]]
        print(f"{i:2d}. {emoji} {result['sentiment'][:3].upper()} ({result['confidence']:.2f}): \"{review[:45]}...\"")
    
    print("\n" + "-"*70)
    print(f"Summary:")
    print(f"  Positive: {sentiments['positive']} ({sentiments['positive']/len(reviews)*100:.0f}%)")
    print(f"  Negative: {sentiments['negative']} ({sentiments['negative']/len(reviews)*100:.0f}%)")
    print(f"  Neutral:  {sentiments['neutral']} ({sentiments['neutral']/len(reviews)*100:.0f}%)")
    print(f"  Average Confidence: {total_confidence/len(reviews):.2%}")
    print()


async def demo_interactive():
    """Interactive mode - analyze user input"""
    print("\n" + "="*70)
    print("DEMO 5: Interactive Mode")
    print("="*70 + "\n")
    
    agent = SentimentAnalyzerAgent()
    
    print("Enter text to analyze sentiment (or 'quit' to exit)\n")
    
    while True:
        try:
            text = input("💬 Your text: ").strip()
            
            if text.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!\n")
                break
            
            if not text:
                print("   ⚠️  Please enter some text.\n")
                continue
            
            # Ask for detailed analysis
            detailed_input = input("   Detailed analysis? (y/n): ").strip().lower()
            detailed = detailed_input in ["y", "yes"]
            
            result = await agent.execute(task=text, context={"detailed": detailed})
            
            emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}[result["sentiment"]]
            
            print(f"\n   {emoji} Sentiment: {result['sentiment'].upper()}")
            print(f"   Confidence: {result['confidence']:.2%}")
            
            if detailed:
                print(f"   Positive Score: {result['positive_score']:.2%}")
                print(f"   Negative Score: {result['negative_score']:.2%}")
                if result.get('keywords'):
                    print(f"   Keywords: {', '.join(result['keywords'])}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n   ❌ Error: {e}\n")


async def main():
    """Run all demos"""
    print("\n" + "🌀"*35)
    print(" "*25 + "TwisterLab")
    print(" "*15 + "SentimentAnalyzerAgent - Interactive Demo")
    print("🌀"*35)
    
    demos = [
        ("Basic Sentiment Analysis", demo_basic),
        ("Detailed Analysis with Keywords", demo_detailed),
        ("Multilingual Support", demo_multilingual),
        ("Batch Processing", demo_batch),
        ("Interactive Mode", demo_interactive),
    ]
    
    print("\nAvailable Demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos)+1}. Run all demos")
    print(f"  0. Exit")
    
    try:
        choice = input("\nSelect demo (0-6): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!\n")
            return
        elif choice == str(len(demos)+1):
            # Run all demos except interactive
            for name, demo in demos[:-1]:
                await demo()
            print("\n✅ All demos completed!\n")
        elif choice.isdigit() and 1 <= int(choice) <= len(demos):
            await demos[int(choice)-1][1]()
        else:
            print(f"\n❌ Invalid choice: {choice}\n")
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")


if __name__ == "__main__":
    asyncio.run(main())
