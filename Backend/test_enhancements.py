"""
Standalone Test Script for New Enhancement Functions

Tests all new features independently without running main response generation
"""

from response_model import (
    detect_multiple_emotions,
    detect_sarcasm,
    detect_trauma_indicators,
    detect_conversation_fatigue,
    detect_time_context,
    get_tiered_validation_phrase,
    get_advanced_question,
    get_crisis_resources
)
from datetime import datetime, time


def test_multi_emotion_detection():
    """Test multi-emotion detection"""
    print("=" * 80)
    print("TEST 1: Multi-Emotion Detection")
    print("=" * 80)
    
    test_cases = [
        ("I got promoted but I'm terrified about the responsibility", "joy"),
        ("I'm happy for my friend but jealous at the same time", "joy"),
        ("I'm excited but also really scared", "joy"),
        ("I feel sad and angry about what happened", "sadness"),
    ]
    
    for user_text, primary_emotion in test_cases:
        emotions = detect_multiple_emotions(user_text, primary_emotion)
        print(f"\nInput: {user_text}")
        print(f"Primary: {primary_emotion}")
        print(f"Detected emotions: {emotions}")
    
    print()


def test_sarcasm_detection():
    """Test sarcasm/irony detection"""
    print("=" * 80)
    print("TEST 2: Sarcasm/Irony Detection")
    print("=" * 80)
    
    test_cases = [
        ("Oh great, another wonderful day at work", True),
        ("Just perfect, my car broke down", True),
        ("I love how everything always works out", True),
        ("I'm so happy! I got the promotion!", False),  # Genuine
        ("That's amazing! Congratulations!", False),  # Genuine
    ]
    
    for user_text, expected_sarcasm in test_cases:
        is_sarcastic = detect_sarcasm(user_text)
        status = "✓" if is_sarcastic == expected_sarcasm else "✗"
        print(f"{status} Input: {user_text}")
        print(f"   Detected sarcasm: {is_sarcastic} (Expected: {expected_sarcasm})")
    
    print()


def test_trauma_detection():
    """Test trauma indicator detection"""
    print("=" * 80)
    print("TEST 3: Trauma Indicator Detection")
    print("=" * 80)
    
    test_cases = [
        ("I experienced abuse as a child", True),
        ("I was assaulted last year", True),
        ("I have PTSD from the incident", True),
        ("I'm feeling sad today", False),
        ("I'm stressed about work", False),
    ]
    
    for user_text, expected_trauma in test_cases:
        has_trauma = detect_trauma_indicators(user_text)
        status = "✓" if has_trauma == expected_trauma else "✗"
        print(f"{status} Input: {user_text}")
        print(f"   Detected trauma: {has_trauma} (Expected: {expected_trauma})")
    
    print()


def test_conversation_fatigue():
    """Test conversation fatigue detection"""
    print("=" * 80)
    print("TEST 4: Conversation Fatigue Detection")
    print("=" * 80)
    
    # Test with closure signals
    history_with_closure = [
        {"role": "user", "content": "I'm feeling stressed"},
        {"role": "assistant", "content": "What's stressing you out?"},
        {"role": "user", "content": "Work is overwhelming"},
        {"role": "assistant", "content": "That sounds tough. Tell me more."},
        {"role": "user", "content": "I think I'm good now. Thanks, I feel better."}
    ]
    
    fatigue = detect_conversation_fatigue(history_with_closure, conversation_turn_count=5)
    print(f"\nTest 1: History with closure signal")
    print(f"Fatigue level: {fatigue['fatigue_level']}")
    print(f"Closure detected: {fatigue['closure_detected']}")
    print(f"Signals: {fatigue['signals']}")
    
    # Test with long conversation
    fatigue_long = detect_conversation_fatigue([], conversation_turn_count=20)
    print(f"\nTest 2: Long conversation (20 turns)")
    print(f"Fatigue level: {fatigue_long['fatigue_level']}")
    
    # Test with topic repetition
    history_repetitive = [
        {"role": "user", "content": "I'm stressed about work"},
        {"role": "assistant", "content": "Tell me more"},
        {"role": "user", "content": "Work is really stressful"},
        {"role": "assistant", "content": "What about work?"},
        {"role": "user", "content": "The stress from work is overwhelming"},
    ]
    
    fatigue_rep = detect_conversation_fatigue(history_repetitive, conversation_turn_count=5)
    print(f"\nTest 3: Topic repetition")
    print(f"Fatigue level: {fatigue_rep['fatigue_level']}")
    print(f"Signals: {fatigue_rep['signals']}")
    
    print()


def test_time_context():
    """Test time-sensitive context detection"""
    print("=" * 80)
    print("TEST 5: Time Context Detection")
    print("=" * 80)
    
    # Late night
    late_night = datetime(2024, 1, 1, 2, 30, 0)  # 2:30 AM
    context_late = detect_time_context("I'm having a panic attack", late_night)
    print(f"\nTest 1: Late night message (2:30 AM)")
    print(f"Is late night: {context_late['is_late_night']}")
    print(f"Urgency level: {context_late['urgency_level']}")
    
    # Normal time
    normal_time = datetime(2024, 1, 1, 14, 30, 0)  # 2:30 PM
    context_normal = detect_time_context("I'm feeling anxious", normal_time)
    print(f"\nTest 2: Normal time message (2:30 PM)")
    print(f"Is late night: {context_normal['is_late_night']}")
    print(f"Urgency level: {context_normal['urgency_level']}")
    
    # Duration detection
    context_duration = detect_time_context("I've been sad for 3 weeks now")
    print(f"\nTest 3: Duration mention")
    print(f"Duration detected: {context_duration['duration_detected']}")
    print(f"Urgency level: {context_duration['urgency_level']}")
    
    context_recent = detect_time_context("I've been anxious for 2 hours")
    print(f"\nTest 4: Recent duration")
    print(f"Duration detected: {context_recent['duration_detected']}")
    
    print()


def test_tiered_validation():
    """Test tiered validation phrase selection"""
    print("=" * 80)
    print("TEST 6: Tiered Validation Phrases")
    print("=" * 80)
    
    for turn in [1, 6, 11, 16]:
        phrase = get_tiered_validation_phrase(turn, [])
        print(f"Turn {turn}: {phrase}")
    
    print("\nTest with recent phrases:")
    recent = ["That sounds tough", "I hear you"]
    phrase = get_tiered_validation_phrase(3, recent)
    print(f"Turn 3 (avoiding recent): {phrase}")
    
    print()


def test_advanced_questions():
    """Test advanced question generation"""
    print("=" * 80)
    print("TEST 7: Advanced Question Types")
    print("=" * 80)
    
    # Scaling question
    context1 = {"needs_clarification": ["intensity"]}
    q1 = get_advanced_question("I'm anxious", "anxiety", context1)
    print(f"\nScaling question: {q1}")
    
    # Exception question
    context2 = {"emotion_duration": "long_term"}
    q2 = get_advanced_question("I've been depressed for months", "sadness", context2)
    print(f"Exception question: {q2}")
    
    # Coping question
    context3 = {"recurrent_issue": True}
    q3 = get_advanced_question("This keeps happening", "anxiety", context3)
    print(f"Coping question: {q3}")
    
    # Clarifying question (vague input)
    q4 = get_advanced_question("I'm stressed about stuff", "stress", {})
    print(f"Clarifying question: {q4}")
    
    print()


def test_crisis_resources():
    """Test regional crisis resources"""
    print("=" * 80)
    print("TEST 8: Regional Crisis Resources")
    print("=" * 80)
    
    regions = ['canada', 'usa', 'uk', 'default']
    
    for region in regions:
        resources = get_crisis_resources(region)
        print(f"\n{region.upper()}:")
        print(f"  Service: {resources['name']}")
        print(f"  Phone: {resources['suicide_prevention']}")
        print(f"  Text: {resources['text_line']}")
        print(f"  Emergency: {resources['emergency']}")
    
    print()


def run_all_tests():
    """Run all enhancement tests"""
    print("\n" + "=" * 80)
    print("TESTING NEW ENHANCEMENT FUNCTIONS")
    print("=" * 80 + "\n")
    
    try:
        test_multi_emotion_detection()
        test_sarcasm_detection()
        test_trauma_detection()
        test_conversation_fatigue()
        test_time_context()
        test_tiered_validation()
        test_advanced_questions()
        test_crisis_resources()
        
        print("=" * 80)
        print("ALL TESTS COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()

