"""
Test Runner for Therapeutic AI Response Generation

Runs test scenarios and validates responses against expected patterns
"""

import json
import re
from typing import Dict, List, Tuple
from test_therapeutic_responses import TherapeuticTestScenarios
from response_model import generate_therapeutic_response


class TestRunner:
    """Runs and validates therapeutic AI responses against test scenarios"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def check_patterns(self, response: str, scenario: Dict) -> Tuple[List[str], List[str]]:
        """
        Check if response matches expected patterns and avoids unwanted patterns
        
        Returns:
            (matched_patterns, violated_patterns)
        """
        matched = []
        violated = []
        
        response_lower = response.lower()
        
        # Check expected patterns (loose matching - looks for keywords/concepts)
        for pattern in scenario.get("expected_patterns", []):
            pattern_lower = pattern.lower()
            
            # Check for specific keywords in expected patterns
            if "brief" in pattern_lower or "2-3 sentences" in pattern_lower:
                sentences = [s.strip() for s in response.split('.') if s.strip()]
                if len(sentences) <= 3:
                    matched.append(pattern)
            elif "4-6 sentences" in pattern_lower:
                sentences = [s.strip() for s in response.split('.') if s.strip()]
                if 4 <= len(sentences) <= 6:
                    matched.append(pattern)
            elif "6-8 sentences" in pattern_lower:
                sentences = [s.strip() for s in response.split('.') if s.strip()]
                if 6 <= len(sentences) <= 8:
                    matched.append(pattern)
            elif "celebratory" in pattern_lower or "celebration" in pattern_lower:
                celebratory_words = ["amazing", "wonderful", "congratulations", "happy for you", "excited", "fantastic", "wow"]
                if any(word in response_lower for word in celebratory_words):
                    matched.append(pattern)
            elif "acknowledge" in pattern_lower or "acknowledges" in pattern_lower:
                # Check if response acknowledges the key topic
                if "bullying" in pattern_lower and "bully" in response_lower:
                    matched.append(pattern)
                elif "shift" in pattern_lower and any(word in response_lower for word in ["better", "lighter", "improved", "feeling"]):
                    matched.append(pattern)
                elif "surprise" in pattern_lower and any(word in response_lower for word in ["surprise", "unexpected", "shock", "wow"]):
                    matched.append(pattern)
            elif "crisis" in pattern_lower or "988" in pattern_lower:
                if "988" in response or "1-833-456-4566" in response or "686868" in response:
                    matched.append(pattern)
            elif "not repeat" in pattern_lower or "different" in pattern_lower:
                # This is checked separately
                matched.append(pattern)
            elif "question" in pattern_lower:
                if "?" in response:
                    matched.append(pattern)
            elif "no question" in pattern_lower or "avoid" in pattern_lower and "question" in pattern_lower:
                if "?" not in response:
                    matched.append(pattern)
            else:
                # Generic keyword matching
                keywords = pattern_lower.split()
                if any(keyword in response_lower for keyword in keywords if len(keyword) > 3):
                    matched.append(pattern)
        
        # Check avoid patterns (strict matching - these should NOT appear)
        last_assistant = scenario.get("last_assistant_message", "")
        if last_assistant:
            last_lower = last_assistant.lower()
            response_lower = response.lower()
            
            # Check for repetition of specific phrases
            avoid_phrases = scenario.get("avoid_patterns", [])
            for phrase in avoid_phrases:
                phrase_lower = phrase.lower()
                if phrase_lower in last_lower and phrase_lower in response_lower:
                    violated.append(f"Repeated phrase: '{phrase}'")
        
        # Check for clinical language that should be avoided
        clinical_phrases = [
            "i understand this is difficult",
            "i'm sorry to hear that",
            "thank you for sharing that with me"
        ]
        for phrase in clinical_phrases:
            if phrase in response_lower and phrase in scenario.get("avoid_patterns", []):
                violated.append(f"Contains clinical phrase: '{phrase}'")
        
        return matched, violated
    
    def run_scenario(self, scenario: Dict, category: str) -> Dict:
        """Run a single test scenario and return results"""
        try:
            # Extract scenario parameters
            user_text = scenario["user_input"]
            emotion = scenario.get("emotion")
            intensity = scenario.get("intensity")
            persona = scenario.get("persona")
            conversation_history = scenario.get("conversation_history", [])
            last_assistant_message = scenario.get("last_assistant_message")
            user_style = scenario.get("user_style")
            
            # Generate response
            response = generate_therapeutic_response(
                user_text=user_text,
                emotion=emotion,
                persona=persona,
                conversation_history=conversation_history,
                last_assistant_message=last_assistant_message,
                user_style=user_style,
                verbose=False
            )
            
            # Validate response
            matched_patterns, violated_patterns = self.check_patterns(response, scenario)
            
            # Determine status
            expected_count = len(scenario.get("expected_patterns", []))
            matched_count = len(matched_patterns)
            violated_count = len(violated_patterns)
            
            if violated_count > 0:
                status = "FAILED"
                self.failed += 1
            elif matched_count >= expected_count * 0.6:  # At least 60% of expected patterns
                status = "PASSED"
                self.passed += 1
            elif matched_count >= expected_count * 0.4:
                status = "WARNING"
                self.warnings += 1
            else:
                status = "FAILED"
                self.failed += 1
            
            result = {
                "category": category,
                "emotion": emotion,
                "intensity": intensity,
                "status": status,
                "user_input": user_text[:100] + "..." if len(user_input) > 100 else user_text,
                "generated_response": response,
                "matched_patterns": matched_patterns,
                "violated_patterns": violated_patterns,
                "expected_patterns": scenario.get("expected_patterns", []),
                "avoid_patterns": scenario.get("avoid_patterns", [])
            }
            
            return result
            
        except Exception as e:
            return {
                "category": category,
                "emotion": emotion,
                "intensity": intensity,
                "status": "ERROR",
                "error": str(e),
                "user_input": scenario["user_input"][:100]
            }
    
    def run_all_tests(self, limit: int = None, categories: List[str] = None):
        """Run all test scenarios"""
        print("=" * 80)
        print("RUNNING THERAPEUTIC AI TESTS")
        print("=" * 80)
        print()
        
        # Load test suite
        tester = TherapeuticTestScenarios()
        test_suite = tester.run_all_tests()
        
        # Filter categories if specified
        test_categories = test_suite["categories"]
        if categories:
            test_categories = {k: v for k, v in test_categories.items() if k in categories}
        
        total_scenarios = sum(len(data["scenarios"]) for data in test_categories.values())
        if limit:
            total_scenarios = min(total_scenarios, limit)
        
        print(f"Running {total_scenarios} test scenarios...")
        print()
        
        scenario_count = 0
        for category_name, category_data in test_categories.items():
            print(f"\n{'='*80}")
            print(f"CATEGORY: {category_name}")
            print(f"{'='*80}")
            
            for scenario in category_data["scenarios"]:
                if limit and scenario_count >= limit:
                    break
                
                scenario_count += 1
                result = self.run_scenario(scenario, category_name)
                self.results.append(result)
                
                # Print result
                status_symbol = "✓" if result["status"] == "PASSED" else "✗" if result["status"] == "FAILED" else "⚠"
                print(f"\n[{status_symbol}] {result['status']} - {result.get('emotion', 'N/A')} ({result.get('intensity', 'N/A')})")
                print(f"  Input: {result['user_input']}")
                print(f"  Response: {result.get('generated_response', 'ERROR')[:150]}...")
                
                if result.get("violated_patterns"):
                    print(f"  ⚠ Violations: {', '.join(result['violated_patterns'])}")
                
                if result.get("matched_patterns"):
                    print(f"  ✓ Matched: {len(result['matched_patterns'])}/{len(result.get('expected_patterns', []))} patterns")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {len(self.results)}")
        print(f"✓ Passed: {self.passed}")
        print(f"⚠ Warnings: {self.warnings}")
        print(f"✗ Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / len(self.results) * 100):.1f}%")
        print("=" * 80)
        
        # Show failed tests
        failed_tests = [r for r in self.results if r["status"] == "FAILED"]
        if failed_tests:
            print("\nFAILED TESTS:")
            for test in failed_tests[:5]:  # Show first 5
                print(f"\n  - {test['category']}: {test.get('emotion', 'N/A')}")
                print(f"    Input: {test['user_input'][:80]}...")
                if test.get("violated_patterns"):
                    print(f"    Issues: {', '.join(test['violated_patterns'][:2])}")
    
    def export_results(self, filename: str = "test_results.json"):
        """Export test results to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": len(self.results),
                    "passed": self.passed,
                    "warnings": self.warnings,
                    "failed": self.failed
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        print(f"\nResults exported to: {filename}")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    limit = None
    categories = None
    
    if len(sys.argv) > 1:
        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        if "--category" in sys.argv:
            idx = sys.argv.index("--category")
            categories = [sys.argv[idx + 1]]
        if "--help" in sys.argv or "-h" in sys.argv:
            print("Usage: python run_tests.py [--limit N] [--category CATEGORY]")
            print("\nExamples:")
            print("  python run_tests.py                    # Run all tests")
            print("  python run_tests.py --limit 5           # Run first 5 tests")
            print("  python run_tests.py --category Sadness  # Run only Sadness tests")
            sys.exit(0)
    
    # Run tests
    runner = TestRunner()
    runner.run_all_tests(limit=limit, categories=categories)
    runner.export_results()

