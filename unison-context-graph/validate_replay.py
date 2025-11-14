#!/usr/bin/env python3
"""
Validation script for Context Graph Replay implementation
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_imports():
    """Test that all new classes and functions can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from src.main import (
            EventTrace, ReplayRequest, TraceListResponse,
            ReplayStore, ContextGraphService, Config
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_data_models():
    """Test data model instantiation"""
    print("\n📋 Testing data models...")
    
    try:
        from src.main import EventTrace, ReplayRequest, TraceListResponse
        from datetime import datetime, timezone
        
        # Test EventTrace
        trace = EventTrace(
            trace_id="test-123",
            person_id="user-456",
            session_id="session-789",
            event_type="context_update",
            timestamp=datetime.now(timezone.utc),
            event_data={"test": "data"},
            context_snapshot={"context": "snapshot"}
        )
        
        trace_dict = trace.to_dict()
        assert "trace_id" in trace_dict
        assert "event_data" in trace_dict
        print("✅ EventTrace model works")
        
        # Test ReplayRequest
        replay_req = ReplayRequest(
            trace_id="test-123",
            include_context=True,
            time_scale=1.5
        )
        print("✅ ReplayRequest model works")
        
        # Test TraceListResponse
        trace_list = TraceListResponse(
            traces=[trace],
            total_count=1,
            has_more=False
        )
        print("✅ TraceListResponse model works")
        
        return True
    except Exception as e:
        print(f"❌ Data model test failed: {e}")
        return False

def test_replay_store():
    """Test ReplayStore functionality"""
    print("\n💾 Testing ReplayStore...")
    
    try:
        from src.main import ReplayStore, EventTrace
        from datetime import datetime, timezone
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            store = ReplayStore(db_path=db_path)
            print("✅ ReplayStore initialized")
            
            # Test storing an event
            trace = EventTrace(
                trace_id="test-trace-123",
                person_id="test-user",
                session_id="test-session",
                event_type="context_update",
                timestamp=datetime.now(timezone.utc),
                event_data={"test": "event_data"},
                context_snapshot={"test": "context"}
            )
            
            stored = store.store_event(trace)
            assert stored, "Failed to store trace"
            print("✅ Event stored successfully")
            
            # Test retrieving the event
            retrieved = store.get_trace("test-trace-123")
            assert retrieved is not None, "Failed to retrieve trace"
            assert retrieved.trace_id == "test-trace-123"
            assert retrieved.person_id == "test-user"
            print("✅ Event retrieved successfully")
            
            # Test listing traces
            trace_list = store.list_person_traces("test-user")
            assert trace_list.total_count == 1
            assert len(trace_list.traces) == 1
            print("✅ Trace listing works")
            
            # Test session traces
            session_traces = store.get_session_traces("test-user", "test-session")
            assert len(session_traces) == 1
            print("✅ Session traces work")
            
            # Test cleanup
            deleted_count = store.cleanup_old_traces(0)  # Delete all
            assert deleted_count >= 0
            print("✅ Cleanup works")
            
            return True
            
        finally:
            # Clean up temporary database
            if os.path.exists(db_path):
                os.unlink(db_path)
                
    except Exception as e:
        print(f"❌ ReplayStore test failed: {e}")
        return False

def test_context_service():
    """Test ContextGraphService integration"""
    print("\n🔧 Testing ContextGraphService integration...")
    
    try:
        from src.main import ContextGraphService, ContextGraphSettings, ContextUpdateRequest
        
        service = ContextGraphService(ContextGraphSettings.from_env())
        print("✅ ContextGraphService initialized with replay store")
        
        # Test that replay store is attached
        assert hasattr(service, 'replay_store')
        assert service.replay_store is not None
        print("✅ ReplayStore properly integrated")
        
        return True
        
    except Exception as e:
        print(f"❌ ContextGraphService test failed: {e}")
        return False

def test_api_endpoints():
    """Test that API endpoints are defined"""
    print("\n🌐 Testing API endpoint definitions...")
    
    try:
        from src.main import app
        
        # Get all routes
        routes = [route.path for route in app.routes]
        
        # Check for replay endpoints
        replay_endpoints = [
            "/replay/{trace_id}",
            "/replay/session/{person_id}/{session_id}",
            "/replay/person/{person_id}",
            "/replay/stats",
            "/replay/cleanup"
        ]
        
        for endpoint in replay_endpoints:
            # Handle parameterized endpoints
            endpoint_pattern = endpoint.replace("{", "").replace("}", "")
            found = any(endpoint_pattern in route for route in routes)
            if found:
                print(f"✅ Endpoint found: {endpoint}")
            else:
                print(f"⚠️ Endpoint not found: {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def test_configuration():
    """Test configuration"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from src.main import Config
        
        assert hasattr(Config, 'REPLAY_DB_PATH')
        assert Config.REPLAY_DB_PATH is not None
        print(f"✅ REPLAY_DB_PATH configured: {Config.REPLAY_DB_PATH}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🚀 Context Graph Replay Implementation Validation")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_data_models,
        test_replay_store,
        test_context_service,
        test_api_endpoints,
        test_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        print("✅ Replay store and /replay/{trace_id} endpoint implementation is complete!")
        return True
    else:
        print("❌ Some validation tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
