# Test AI-Powered Resolution Suggestions
# This script tests the enhanced resolution suggestion endpoint

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_resolution_suggestions():
    """Test the AI-powered resolution suggestions endpoint"""
    
    print("="*70)
    print("TESTING AI-POWERED RESOLUTION SUGGESTIONS")
    print("="*70)
    print()
    
    # Test endpoint
    endpoint = f"{BASE_URL}/api/graphs/resolution-suggestions"
    
    print(f"📡 Calling: {endpoint}")
    print()
    
    try:
        # Make request
        response = requests.get(endpoint, params={"hours": 24})
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ SUCCESS - Status Code: {response.status_code}")
            print()
            
            # Show summary
            total_suggestions = len(data.get('suggestions', []))
            print(f"📊 Total Suggestions: {total_suggestions}")
            print()
            
            if total_suggestions > 0:
                print("="*70)
                print("SAMPLE RESOLUTION SUGGESTION")
                print("="*70)
                print()
                
                # Display first suggestion
                suggestion = data['suggestions'][0]
                
                print(f"🎯 Endpoint: {suggestion.get('endpoint', 'N/A')}")
                print(f"🚨 Anomaly Type: {suggestion.get('anomaly_type', 'N/A')}")
                print(f"⚠️  Severity: {suggestion.get('severity', 'N/A')}")
                print(f"📝 Category: {suggestion.get('category', 'N/A')}")
                print(f"⚡ Priority: {suggestion.get('priority', 'N/A')}")
                print(f"💥 Impact Score: {suggestion.get('impact_score', 0)}")
                print()
                print("="*70)
                print("ACTION")
                print("="*70)
                print(suggestion.get('action', 'N/A'))
                print()
                print("="*70)
                print("DETAILS")
                print("="*70)
                print(suggestion.get('detail', 'N/A'))
                print()
                
                # Check if AI-generated
                if suggestion.get('ai_generated'):
                    print("🤖 AI-GENERATED: YES (OpenAI GPT-4)")
                    print()
                    if 'full_content' in suggestion:
                        print("="*70)
                        print("FULL AI CONTENT (First 500 chars)")
                        print("="*70)
                        full_content = suggestion.get('full_content', '')
                        print(full_content[:500])
                        print()
                        if len(full_content) > 500:
                            print(f"... (truncated, total length: {len(full_content)} chars)")
                            print()
                else:
                    print("🤖 AI-GENERATED: NO (Fallback basic resolution)")
                    print()
                
                # Show severity breakdown
                print("="*70)
                print("SEVERITY BREAKDOWN")
                print("="*70)
                severity_counts = {}
                for sug in data['suggestions']:
                    sev = sug.get('severity', 'UNKNOWN')
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
                
                for severity, count in sorted(severity_counts.items()):
                    print(f"{severity}: {count} suggestions")
                print()
                
                # Show category breakdown
                print("="*70)
                print("CATEGORY BREAKDOWN")
                print("="*70)
                category_counts = {}
                for sug in data['suggestions']:
                    cat = sug.get('category', 'UNKNOWN')
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                
                for category, count in sorted(category_counts.items()):
                    print(f"{category}: {count} suggestions")
                print()
                
            else:
                print("⚠️  No suggestions available (no anomalies in last 24 hours)")
                print()
                print("💡 TIP: Start a simulation to generate anomalies:")
                print("   1. Go to http://localhost:3000")
                print("   2. Switch to 'Simulation Mode'")
                print("   3. Select an endpoint and click 'Start Auto-Detection'")
                print()
            
        else:
            print(f"❌ FAILED - Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            print()
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR")
        print("Backend server is not running on http://localhost:8000")
        print()
        print("💡 Start the backend:")
        print("   cd backend")
        print("   python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload")
        print()
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print()

def test_top_endpoints():
    """Test the enhanced risk score calculation"""
    
    print("="*70)
    print("TESTING RISK SCORE DIVERSITY")
    print("="*70)
    print()
    
    endpoint = f"{BASE_URL}/api/graphs/top-affected-endpoints"
    
    print(f"📡 Calling: {endpoint}")
    print()
    
    try:
        response = requests.get(endpoint, params={"hours": 24, "limit": 10})
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ SUCCESS - Status Code: {response.status_code}")
            print()
            
            endpoints = data.get('endpoints', [])
            
            if endpoints:
                print("="*70)
                print("TOP AFFECTED ENDPOINTS - RISK SCORES")
                print("="*70)
                print()
                print(f"{'Endpoint':<30} {'Anomalies':<12} {'Avg Risk':<12} {'Max Risk':<12} {'Composite':<12}")
                print("-"*70)
                
                for ep in endpoints[:10]:
                    print(f"{ep['endpoint']:<30} "
                          f"{ep['anomaly_count']:<12} "
                          f"{ep['avg_risk_score']:<12.2f} "
                          f"{ep['max_risk_score']:<12.2f} "
                          f"{ep['composite_score']:<12.2f}")
                
                print()
                print("="*70)
                print("DIVERSITY CHECK")
                print("="*70)
                
                # Check if scores are unique
                avg_risks = [ep['avg_risk_score'] for ep in endpoints]
                max_risks = [ep['max_risk_score'] for ep in endpoints]
                composite_scores = [ep['composite_score'] for ep in endpoints]
                
                unique_avg = len(set(avg_risks))
                unique_max = len(set(max_risks))
                unique_composite = len(set(composite_scores))
                
                total_eps = len(endpoints)
                
                print(f"Unique Avg Risk Scores: {unique_avg}/{total_eps}")
                print(f"Unique Max Risk Scores: {unique_max}/{total_eps}")
                print(f"Unique Composite Scores: {unique_composite}/{total_eps}")
                print()
                
                if unique_avg > 1 and unique_composite > 1:
                    print("✅ DIVERSITY: PASSED - Endpoints have different risk scores")
                else:
                    print("⚠️  DIVERSITY: FAILED - Risk scores are still identical")
                print()
                
            else:
                print("⚠️  No endpoint data available")
                print()
        else:
            print(f"❌ FAILED - Status Code: {response.status_code}")
            print()
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print()

if __name__ == "__main__":
    print()
    print("🧪 AI RESOLUTION & RISK SCORE TESTING")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Resolution suggestions
    test_resolution_suggestions()
    
    # Test 2: Risk score diversity
    test_top_endpoints()
    
    print("="*70)
    print("TESTING COMPLETE")
    print("="*70)
    print()
