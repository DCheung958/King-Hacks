"""
Test script to verify AI-based response generation via API endpoint
Tests the /api/respond endpoint to ensure it's using the AI model (GPT-2)
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

print("=" * 70)
print("Testing AI Response Generation API Endpoint")
print("=" * 70)

# Test cases with different emotions and contexts
test_cases = [
    {
        "text": "I'm feeling really anxious about my job interview tomorrow",
        "emotion": None,  # Will be detected automatically
        "description": "Anxiety about job interview"
    },
    {
        "text": "I've been feeling really sad and lonely lately",
        "emotion": "sadness",
        "description": "Sadness and loneliness"
    },
    {
        "text": "I'm so angry at my boss for treating me unfairly",
        "emotion": "anger",
        "description": "Anger at unfair treatment"
    },
    {
        "text": "I'm really happy about my recent achievements!",
        "emotion": "joy",
        "description": "Joy about achievements"
    },
    {
        "text": "I'm struggling with stress from work and family responsibilities",
        "emotion": None,
        "description": "Stress and overwhelm"
    },
    {
        "text": "I feel lost and don't know what to do with my life",
        "emotion": None,
        "description": "Feeling lost"
    }
]

def test_health_check():
    """Check if the API server is running"""
    print("\n1. Checking if API server is running...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✓ API server is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"   ✗ API server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ✗ Cannot connect to API server at {API_BASE_URL}")
        print(f"   Please make sure the server is running with: python main.py")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_response_endpoint(text, emotion=None, description=""):
    """Test the /api/respond endpoint with a given text"""
    try:
        payload = {"text": text}
        if emotion:
            payload["emotion"] = emotion
        
        response = requests.post(
            f"{API_BASE_URL}/api/respond",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30  # Longer timeout for AI generation
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response_text", "")
            detected_emotion = data.get("emotion", "")
            
            print(f"\n   Test: {description}")
            print(f"   Input: '{text[:60]}{'...' if len(text) > 60 else ''}'")
            print(f"   Detected Emotion: {detected_emotion}")
            print(f"   AI Response: '{response_text}'")
            print(f"   Response Length: {len(response_text)} characters")
            
            # Check if response looks AI-generated (varied, contextual)
            is_ai_like = len(response_text) > 30 and not response_text.startswith("I'm really glad")
            
            if is_ai_like:
                print(f"   ✓ Response appears to be AI-generated (varied and contextual)")
            else:
                print(f"   ⚠ Response might be using mock fallback (shorter/predefined)")
            
            return True, response_text, detected_emotion
        else:
            print(f"   ✗ Request failed with status {response.status_code}")
            print(f"      Response: {response.text}")
            return False, None, None
    except requests.exceptions.Timeout:
        print(f"   ✗ Request timed out (model might be generating, try again)")
        return False, None, None
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False, None, None

def compare_responses():
    """Test the same input twice to see if responses vary (indicating AI)"""
    print("\n" + "=" * 70)
    print("Variability Test (AI should generate different responses)")
    print("=" * 70)
    
    test_text = "I'm feeling anxious about my future"
    responses = []
    
    for i in range(3):
        print(f"\n   Attempt {i+1}/3:")
        success, response_text, emotion = test_response_endpoint(
            test_text,
            emotion=None,
            description="Anxiety test (repeat)"
        )
        if success and response_text:
            responses.append(response_text)
        time.sleep(1)  # Small delay between requests
    
    if len(responses) >= 2:
        # Check if responses are different
        unique_responses = set(responses)
        if len(unique_responses) > 1:
            print(f"\n   ✓ Responses are VARIED (AI is generating different responses each time)")
            print(f"   Unique responses: {len(unique_responses)}/{len(responses)}")
        else:
            print(f"\n   ⚠ Responses are IDENTICAL (might be using mock fallback)")
            print(f"   All {len(responses)} responses were the same")

def main():
    # Check if server is running
    if not test_health_check():
        print("\n" + "=" * 70)
        print("API server is not running. Please start it first:")
        print("  python main.py")
        print("=" * 70)
        return
    
    # Test response generation endpoint
    print("\n2. Testing /api/respond endpoint with various inputs...")
    print("-" * 70)
    
    results = []
    response_lengths = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test {i}/{len(test_cases)}:")
        success, response_text, emotion = test_response_endpoint(
            test_case["text"],
            test_case.get("emotion"),
            test_case["description"]
        )
        
        results.append({
            "success": success,
            "response_text": response_text,
            "emotion": emotion,
            "description": test_case["description"]
        })
        
        if response_text:
            response_lengths.append(len(response_text))
        
        time.sleep(0.5)  # Small delay between requests
    
    # Variability test
    compare_responses()
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    successful = sum(1 for r in results if r["success"])
    print(f"Successful requests: {successful}/{len(results)}")
    
    if response_lengths:
        avg_length = sum(response_lengths) / len(response_lengths)
        min_length = min(response_lengths)
        max_length = max(response_lengths)
        
        print(f"\nResponse Statistics:")
        print(f"  Average length: {avg_length:.1f} characters")
        print(f"  Min length: {min_length} characters")
        print(f"  Max length: {max_length} characters")
        
        # Check for AI-like characteristics
        if avg_length > 50 and max_length > 80:
            print(f"\n✓ Responses show AI-like characteristics:")
            print(f"  - Varied lengths (AI generates different lengths)")
            print(f"  - Longer responses (AI can generate detailed responses)")
        elif avg_length < 100:
            print(f"\n⚠ Responses might be using mock fallback:")
            print(f"  - Shorter responses (mock responses are predefined)")
        else:
            print(f"\n✓ Responses appear to be AI-generated")
    
    # Check for response variety
    unique_responses = set(r["response_text"] for r in results if r["response_text"])
    print(f"\nUnique responses: {len(unique_responses)}/{successful}")
    if len(unique_responses) > len(results) * 0.7:
        print("✓ High variety indicates AI generation (mock has limited variety)")
    else:
        print("⚠ Lower variety - might be using mock or model needs fine-tuning")
    
    print("\n" + "=" * 70)
    print("Note: If responses are identical or very short, the AI model")
    print("might not be loaded yet, or there was an error loading it.")
    print("Check server logs for 'Response generation model loaded successfully!'")
    print("=" * 70)

if __name__ == "__main__":
    main()
