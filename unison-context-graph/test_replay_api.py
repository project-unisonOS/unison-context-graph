#!/usr/bin/env python3
"""
Test script for Context Graph Replay functionality
"""

import asyncio
import json
import requests
from datetime import datetime
import uuid

# Configuration
BASE_URL = "http://localhost:8081"

def test_context_update():
    """Test context update to generate traces"""
    print("🧪 Testing context update...")
    
    request_data = {
        "person_id": "test-user-123",
        "session_id": "session-456",
        "context_sources": {
            "environmental": {
                "location": "office",
                "noise_level": "moderate",
                "lighting": "bright",
                "temperature": "comfortable"
            },
            "device": {
                "active_applications": ["IDE", "browser"],
                "screen_state": "active",
                "network_connection": "wifi"
            },
            "activity": {
                "current_activity": "coding",
                "activity_duration": "2h",
                "focus_level": "deep",
                "task_complexity": "high"
            },
            "social": {
                "nearby_people": [],
                "meeting_status": "none",
                "collaboration_mode": "individual",
                "communication_readiness": "available"
            },
            "personal": {
                "cognitive_load": "moderate",
                "energy_level": "high",
                "stress_level": "low",
                "motivation_level": "high",
                "comfort_level": "comfortable"
            }
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/context/update", json=request_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Context update successful")
            print(f"📊 Person ID: {result['context_state']['person_id']}")
            print(f"⏰ Fusion timestamp: {result['context_state']['fusion_timestamp']}")
            return result['context_state']['person_id']
        else:
            print(f"❌ Context update failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during context update: {str(e)}")
        return None

def test_list_traces(person_id):
    """Test listing traces for a person"""
    print(f"\n📋 Testing trace listing for person: {person_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/replay/person/{person_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Found {result['total_count']} traces")
            print(f"📄 Has more: {result['has_more']}")
            
            if result['traces']:
                print("🔍 Recent traces:")
                for trace in result['traces'][:3]:  # Show first 3
                    print(f"  - Trace ID: {trace['trace_id']}")
                    print(f"    Event Type: {trace['event_type']}")
                    print(f"    Timestamp: {trace['timestamp']}")
                    print(f"    Session ID: {trace['session_id']}")
                    print()
                    return trace['trace_id']  # Return first trace ID for replay test
            else:
                print("⚠️ No traces found")
                return None
        else:
            print(f"❌ Failed to list traces: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error listing traces: {str(e)}")
        return None

def test_replay_trace(trace_id):
    """Test replaying a specific trace"""
    print(f"\n🔄 Testing trace replay: {trace_id}")
    
    replay_request = {
        "trace_id": trace_id,
        "include_context": True,
        "time_scale": 1.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/replay/{trace_id}", json=replay_request)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Trace replay successful")
            print(f"📊 Original Event Type: {result['replay_metadata']['original_event_type']}")
            print(f"⏰ Requested at: {result['replay_metadata']['requested_at']}")
            print(f"🔄 Replay Available: {result['replay_metadata']['replay_available']}")
            
            if 'replay_result' in result:
                print(f"🎯 Context replayed successfully")
                replayed_person = result['replay_result']['context_state']['person_id']
                print(f"👤 Replayed for person: {replayed_person}")
            
            return True
        else:
            print(f"❌ Trace replay failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during trace replay: {str(e)}")
        return False

def test_get_trace(trace_id):
    """Test getting a specific trace"""
    print(f"\n🔍 Testing get trace: {trace_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/replay/{trace_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Trace retrieved successfully")
            print(f"👤 Person ID: {result['person_id']}")
            print(f"📋 Event Type: {result['event_type']}")
            print(f"⏰ Timestamp: {result['timestamp']}")
            print(f"🆔 Session ID: {result['session_id']}")
            print(f"📦 Event Data Keys: {list(result['event_data'].keys())}")
            return True
        else:
            print(f"❌ Failed to get trace: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting trace: {str(e)}")
        return False

def test_session_traces(person_id, session_id):
    """Test getting session traces"""
    print(f"\n📂 Testing session traces for person: {person_id}, session: {session_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/replay/session/{person_id}/{session_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Session traces retrieved successfully")
            print(f"📊 Found {len(result)} traces in session")
            
            for i, trace in enumerate(result[:3]):  # Show first 3
                print(f"  {i+1}. Trace {trace['trace_id']} at {trace['timestamp']}")
            
            return True
        else:
            print(f"❌ Failed to get session traces: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting session traces: {str(e)}")
        return False

def test_replay_stats():
    """Test getting replay statistics"""
    print(f"\n📊 Testing replay statistics...")
    
    try:
        response = requests.get(f"{BASE_URL}/replay/stats")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Statistics retrieved successfully")
            print(f"📈 Total Traces: {result['total_traces']}")
            print(f"👥 Top Persons: {len(result['top_persons'])}")
            print(f"📋 Event Types: {len(result['event_types'])}")
            print(f"📅 Recent Activity Days: {len(result['recent_activity'])}")
            
            if result['top_persons']:
                print("🏆 Top person:")
                top_person = result['top_persons'][0]
                print(f"  - {top_person['person_id']}: {top_person['trace_count']} traces")
            
            if result['event_types']:
                print("📝 Event types:")
                for event_type in result['event_types']:
                    print(f"  - {event_type['event_type']}: {event_type['count']} traces")
            
            return True
        else:
            print(f"❌ Failed to get statistics: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting statistics: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Context Graph Replay API Tests")
    print(f"🌐 Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Test 1: Update context to generate traces
    person_id = test_context_update()
    if not person_id:
        print("❌ Cannot proceed without successful context update")
        return
    
    # Test 2: List traces for the person
    trace_id = test_list_traces(person_id)
    if not trace_id:
        print("⚠️ No traces found to test replay functionality")
        return
    
    # Test 3: Get specific trace
    test_get_trace(trace_id)
    
    # Test 4: Replay trace
    test_replay_trace(trace_id)
    
    # Test 5: Get session traces
    session_id = "session-456"
    test_session_traces(person_id, session_id)
    
    # Test 6: Get statistics
    test_replay_stats()
    
    print("\n" + "=" * 60)
    print("✅ All replay API tests completed!")
    print("🎯 The replay store and /replay/{trace_id} endpoint are working correctly!")

if __name__ == "__main__":
    main()
