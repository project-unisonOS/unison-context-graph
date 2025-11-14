"""
Tests for Durability Features

Tests WAL, TTL, PII scrubbing, and crash recovery functionality.
"""

import pytest
import sqlite3
import os
import json
import time
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src and common packages to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(REPO_ROOT / "unison-common" / "src"))

from durability import (
    DurabilityManager,
    DurabilityConfig,
    WALManager,
    TTLManager,
    PIIScrubber,
    RecoveryManager
)
from unison_common.datetime_utils import now_utc, isoformat_utc


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Create test table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE event_traces (
            trace_id TEXT PRIMARY KEY,
            person_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            event_data TEXT NOT NULL,
            context_snapshot TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
        # Remove WAL files if they exist
        for suffix in ['-wal', '-shm']:
            wal_file = f"{db_path}{suffix}"
            if os.path.exists(wal_file):
                os.unlink(wal_file)
    except:
        pass


# ==================== WAL Tests ====================

def test_wal_enable(temp_db):
    """Test WAL mode can be enabled"""
    config = DurabilityConfig()
    config.WAL_ENABLED = True
    
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    success = manager.wal_manager.enable_wal(conn)
    
    assert success is True
    
    # Verify WAL mode
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    
    assert mode.lower() == 'wal'
    
    conn.close()


def test_wal_checkpoint(temp_db):
    """Test WAL checkpoint"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    manager.wal_manager.enable_wal(conn)
    
    # Insert some data
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO event_traces (trace_id, person_id, session_id, event_type, timestamp, event_data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('test1', 'user1', 'session1', 'test', isoformat_utc(), '{}'))
    conn.commit()
    
    # Perform checkpoint
    success = manager.wal_manager.checkpoint(conn, mode="PASSIVE")
    
    assert success is True
    assert manager.metrics.wal_checkpoints >= 1
    
    conn.close()


def test_wal_info(temp_db):
    """Test WAL info retrieval"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    manager.wal_manager.enable_wal(conn)
    
    info = manager.wal_manager.get_wal_info(conn)
    
    assert info['enabled'] is True
    assert 'wal_path' in info
    assert 'transaction_count' in info
    
    conn.close()


def test_wal_transaction_counting(temp_db):
    """Test transaction counting"""
    manager = DurabilityManager(temp_db)
    
    initial_count = manager.wal_manager._transaction_count
    
    manager.wal_manager.increment_transaction_count()
    manager.wal_manager.increment_transaction_count()
    
    assert manager.wal_manager._transaction_count == initial_count + 2


# ==================== TTL Tests ====================

def test_ttl_add_columns(temp_db):
    """Test TTL columns can be added"""
    config = DurabilityConfig()
    config.TTL_ENABLED = True
    
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    success = manager.ttl_manager.add_ttl_columns(conn)
    
    assert success is True
    
    # Verify column exists
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(event_traces)")
    columns = [row[1] for row in cursor.fetchall()]
    
    assert 'expires_at' in columns
    
    conn.close()


def test_ttl_calculate_expiry(temp_db):
    """Test expiry calculation"""
    manager = DurabilityManager(temp_db)
    
    expiry = manager.ttl_manager.calculate_expiry(days=30)
    
    # Parse and verify
    expiry_dt = datetime.fromisoformat(expiry)
    now = now_utc()
    diff = (expiry_dt - now).days
    
    assert 29 <= diff <= 31  # Allow 1 day tolerance


def test_ttl_cleanup_expired(temp_db):
    """Test cleanup of expired records"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    manager.ttl_manager.add_ttl_columns(conn)
    
    cursor = conn.cursor()
    
    # Insert expired record
    expired_date = (now_utc() - timedelta(days=1)).isoformat()
    cursor.execute("""
        INSERT INTO event_traces 
        (trace_id, person_id, session_id, event_type, timestamp, event_data, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('expired1', 'user1', 'session1', 'test', isoformat_utc(), '{}', expired_date))
    
    # Insert non-expired record
    future_date = (now_utc() + timedelta(days=30)).isoformat()
    cursor.execute("""
        INSERT INTO event_traces 
        (trace_id, person_id, session_id, event_type, timestamp, event_data, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('active1', 'user1', 'session1', 'test', isoformat_utc(), '{}', future_date))
    
    conn.commit()
    
    # Cleanup expired
    deleted_count = manager.ttl_manager.cleanup_expired(conn)
    
    assert deleted_count == 1
    
    # Verify only active record remains
    cursor.execute("SELECT COUNT(*) FROM event_traces")
    count = cursor.fetchone()[0]
    assert count == 1
    
    cursor.execute("SELECT trace_id FROM event_traces")
    remaining_id = cursor.fetchone()[0]
    assert remaining_id == 'active1'
    
    conn.close()


def test_ttl_stats(temp_db):
    """Test TTL statistics"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    manager.ttl_manager.add_ttl_columns(conn)
    
    stats = manager.ttl_manager.get_ttl_stats(conn)
    
    assert stats['enabled'] is True
    assert 'ttl_default_days' in stats
    assert 'records_with_ttl' in stats
    assert 'expired_records' in stats
    
    conn.close()


# ==================== PII Scrubbing Tests ====================

def test_pii_add_columns(temp_db):
    """Test PII scrubbing columns can be added"""
    config = DurabilityConfig()
    config.PII_SCRUBBING_ENABLED = True
    
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    success = manager.pii_scrubber.add_scrubbing_columns(conn)
    
    assert success is True
    
    # Verify column exists
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(event_traces)")
    columns = [row[1] for row in cursor.fetchall()]
    
    assert 'scrubbed_at' in columns
    
    conn.close()


def test_pii_hash_person_id(temp_db):
    """Test person_id hashing"""
    manager = DurabilityManager(temp_db)
    
    person_id = "user_12345"
    hashed = manager.pii_scrubber.hash_person_id(person_id)
    
    assert hashed.startswith("SCRUBBED_")
    assert len(hashed) == 25  # SCRUBBED_ + 16 chars
    
    # Same input should produce same hash
    hashed2 = manager.pii_scrubber.hash_person_id(person_id)
    assert hashed == hashed2


def test_pii_scrub_dict_remove_fields(temp_db):
    """Test PII field removal"""
    manager = DurabilityManager(temp_db)
    
    data = {
        "name": "John Doe",
        "email": "john@example.com",
        "device_id": "ABC123",
        "location": "San Francisco, CA, USA"
    }
    
    scrubbed = manager.pii_scrubber._scrub_dict(data)
    
    assert scrubbed['email'] is None
    assert scrubbed['device_id'] is None
    assert scrubbed['name'] == "John Doe"  # Not in remove list


def test_pii_generalize_location(temp_db):
    """Test location generalization"""
    manager = DurabilityManager(temp_db)
    
    location = "San Francisco, CA, USA"
    generalized = manager.pii_scrubber._generalize_location(location)
    
    assert generalized == "San Francisco"


def test_pii_generalize_coordinates(temp_db):
    """Test GPS coordinate generalization"""
    manager = DurabilityManager(temp_db)
    
    coords = {"lat": 37.7749, "lon": -122.4194}
    generalized = manager.pii_scrubber._generalize_coordinates(coords)
    
    assert generalized == "~37.8,~-122.4"


def test_pii_scrub_record(temp_db):
    """Test scrubbing a single record"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    manager.pii_scrubber.add_scrubbing_columns(conn)
    
    cursor = conn.cursor()
    
    # Insert record with PII
    event_data = json.dumps({
        "email": "user@example.com",
        "device_id": "ABC123",
        "location": "San Francisco, CA, USA"
    })
    
    cursor.execute("""
        INSERT INTO event_traces 
        (trace_id, person_id, session_id, event_type, timestamp, event_data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('test1', 'user_12345', 'session1', 'test', isoformat_utc(), event_data))
    
    conn.commit()
    
    # Scrub the record
    success = manager.pii_scrubber.scrub_record(cursor, 'test1')
    conn.commit()
    
    assert success is True
    
    # Verify scrubbing
    cursor.execute("SELECT person_id, event_data, scrubbed_at FROM event_traces WHERE trace_id = ?", ('test1',))
    row = cursor.fetchone()
    
    person_id, event_data_str, scrubbed_at = row
    
    assert person_id.startswith("SCRUBBED_")
    assert scrubbed_at is not None
    
    event_data = json.loads(event_data_str)
    assert event_data['email'] is None
    assert event_data['device_id'] is None
    assert event_data['location'] == "San Francisco"
    
    conn.close()


def test_pii_scrub_old_records(temp_db):
    """Test scrubbing old records"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    manager.pii_scrubber.add_scrubbing_columns(conn)
    
    cursor = conn.cursor()
    
    # Insert old record (> 90 days)
    old_date = (now_utc() - timedelta(days=100)).isoformat()
    cursor.execute("""
        INSERT INTO event_traces 
        (trace_id, person_id, session_id, event_type, timestamp, event_data, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('old1', 'user_old', 'session1', 'test', old_date, '{"email": "old@example.com"}', old_date))
    
    # Insert recent record
    recent_date = isoformat_utc()
    cursor.execute("""
        INSERT INTO event_traces 
        (trace_id, person_id, session_id, event_type, timestamp, event_data, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('recent1', 'user_recent', 'session1', 'test', recent_date, '{"email": "recent@example.com"}', recent_date))
    
    conn.commit()
    
    # Scrub old records
    scrubbed_count = manager.pii_scrubber.scrub_old_records(conn, batch_size=100)
    
    assert scrubbed_count == 1
    
    # Verify old record is scrubbed
    cursor.execute("SELECT person_id, scrubbed_at FROM event_traces WHERE trace_id = ?", ('old1',))
    person_id, scrubbed_at = cursor.fetchone()
    assert person_id.startswith("SCRUBBED_")
    assert scrubbed_at is not None
    
    # Verify recent record is not scrubbed
    cursor.execute("SELECT person_id, scrubbed_at FROM event_traces WHERE trace_id = ?", ('recent1',))
    person_id, scrubbed_at = cursor.fetchone()
    assert person_id == 'user_recent'
    assert scrubbed_at is None
    
    conn.close()


def test_pii_scrubbing_stats(temp_db):
    """Test PII scrubbing statistics"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    manager.pii_scrubber.add_scrubbing_columns(conn)
    
    stats = manager.pii_scrubber.get_scrubbing_stats(conn)
    
    assert stats['enabled'] is True
    assert 'scrubbing_after_days' in stats
    assert 'records_scrubbed' in stats
    assert 'records_pending_scrubbing' in stats
    
    conn.close()


# ==================== Recovery Tests ====================

def test_recovery_check_for_wal(temp_db):
    """Test checking for WAL file"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    # Enable WAL to create WAL file
    manager.wal_manager.enable_wal(conn)
    
    # Insert data
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO event_traces (trace_id, person_id, session_id, event_type, timestamp, event_data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('test1', 'user1', 'session1', 'test', isoformat_utc(), '{}'))
    conn.commit()
    conn.close()
    
    # Check for recovery
    needs_recovery = manager.recovery_manager.check_for_recovery()
    
    # WAL file may or may not exist depending on checkpoint timing
    # Just verify the check doesn't crash
    assert isinstance(needs_recovery, bool)


def test_recovery_perform(temp_db):
    """Test crash recovery"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    # Enable WAL
    manager.wal_manager.enable_wal(conn)
    
    # Insert data
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO event_traces (trace_id, person_id, session_id, event_type, timestamp, event_data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('test1', 'user1', 'session1', 'test', isoformat_utc(), '{}'))
    conn.commit()
    conn.close()
    
    # Perform recovery
    success = manager.recovery_manager.recover()
    
    assert success is True
    assert manager.metrics.recovery_attempts >= 1


# ==================== Integration Tests ====================

def test_durability_manager_initialize(temp_db):
    """Test full durability manager initialization"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    success = manager.initialize(conn)
    
    assert success is True
    
    # Verify all features initialized
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(event_traces)")
    columns = [row[1] for row in cursor.fetchall()]
    
    assert 'expires_at' in columns  # TTL
    assert 'scrubbed_at' in columns  # PII scrubbing
    
    # Verify WAL mode
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    assert mode.lower() == 'wal'
    
    conn.close()


def test_durability_manager_status(temp_db):
    """Test durability status reporting"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    manager.initialize(conn)
    
    status = manager.get_status(conn)
    
    assert 'config' in status
    assert 'wal' in status
    assert 'ttl' in status
    assert 'pii_scrubbing' in status
    assert 'metrics' in status
    
    assert status['config']['wal_enabled'] is True
    assert status['config']['ttl_enabled'] is True
    assert status['config']['pii_scrubbing_enabled'] is True
    
    conn.close()


def test_durability_manager_shutdown(temp_db):
    """Test graceful shutdown"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    manager.initialize(conn)
    
    # Should not raise exception
    manager.shutdown(conn)
    
    conn.close()


def test_full_lifecycle(temp_db):
    """Test full lifecycle: insert, TTL, scrub, cleanup"""
    manager = DurabilityManager(temp_db)
    conn = sqlite3.connect(temp_db)
    
    manager.initialize(conn)
    
    cursor = conn.cursor()
    
    # Insert record
    event_data = json.dumps({"email": "test@example.com", "device_id": "ABC123"})
    expires_at = manager.ttl_manager.calculate_expiry(days=30)
    
    cursor.execute("""
        INSERT INTO event_traces 
        (trace_id, person_id, session_id, event_type, timestamp, event_data, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('test1', 'user_test', 'session1', 'test', isoformat_utc(), event_data, expires_at))
    
    conn.commit()
    manager.on_transaction(conn)
    
    # Verify record exists
    cursor.execute("SELECT COUNT(*) FROM event_traces")
    assert cursor.fetchone()[0] == 1
    
    # Get status
    status = manager.get_status(conn)
    assert status['ttl']['records_with_ttl'] == 1
    
    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
