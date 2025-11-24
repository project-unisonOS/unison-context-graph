# Storage Durability

## Overview

The context-graph service implements comprehensive storage durability features to ensure data reliability and crash recovery.

## Features

- **Write-Ahead Log (WAL)**: SQLite WAL mode for better crash recovery and concurrent performance
- **Crash Recovery**: Automatic recovery on startup with WAL replay
- **Data Integrity**: Checksum verification during recovery
- **Graceful Shutdown**: Proper WAL cleanup on service shutdown

## Write-Ahead Log (WAL)

### What is WAL?

Write-Ahead Logging is a standard method for ensuring data integrity. Changes are written to a log file before being applied to the main database, providing:

- Better crash recovery
- Improved concurrent read/write performance
- Atomic commits

### Configuration

```bash
# Enable/disable WAL mode
DURABILITY_WAL_ENABLED=true

# Checkpoint interval (transactions)
DURABILITY_WAL_CHECKPOINT=1000

# Sync mode (FULL, NORMAL, OFF)
DURABILITY_WAL_SYNC=NORMAL
```

### How It Works

1. **Write Phase**: Changes are written to WAL file (`*.db-wal`)
2. **Checkpoint**: Periodically, WAL is merged into main database
3. **Cleanup**: On shutdown, final checkpoint ensures all data is persisted

### Performance

- **Sync Mode NORMAL**: Good balance of safety and performance
- **Checkpoint Interval**: 1000 transactions (configurable)
- **Typical Overhead**: < 5%

### Monitoring

Check WAL status via API:

```bash
GET /durability/status
```

Response:
```json
{
  "wal": {
    "enabled": true,
    "wal_exists": true,
    "wal_size_bytes": 4096,
    "wal_path": "data/context_replay.db-wal",
    "transaction_count": 150
  }
}
```

### Grafana / Prometheus Export

Durability and replay metrics are exposed in Prometheus text format so Grafana can scrape them directly:

```bash
GET /metrics
```

Sample output:

```
# HELP unison_context_graph_replay_events_total Total replayable context events stored in SQLite.
# TYPE unison_context_graph_replay_events_total gauge
unison_context_graph_replay_events_total 42
# HELP unison_context_graph_durability_wal_checkpoints Durability metric 'wal_checkpoints'.
# TYPE unison_context_graph_durability_wal_checkpoints gauge
unison_context_graph_durability_wal_checkpoints 3
# HELP unison_context_graph_wal_size_bytes Current WAL file size in bytes.
# TYPE unison_context_graph_wal_size_bytes gauge
unison_context_graph_wal_size_bytes 8192
```

Add the endpoint to your Prometheus scrape configuration:

```yaml
- job_name: unison-context-graph
  scrape_interval: 30s
  static_configs:
    - targets: ["context-graph:8081"]
```

The exported series include replay totals, WAL file size, durability counters (checkpoints, recovery attempts), TTL activity, and PII scrubbing statistics, enabling dashboards and alerts aligned with the Section 3.3 reliability goals.

## Crash Recovery

### Automatic Recovery

On service startup, the system automatically:

1. **Detects** WAL file presence
2. **Replays** uncommitted transactions
3. **Verifies** database integrity
4. **Checkpoints** WAL to main database

### Recovery Process

```
Startup → Check for WAL → Replay Transactions → Verify Integrity → Resume
```

### Recovery Metrics

```json
{
  "metrics": {
    "recovery_attempts": 1,
    "recovery_duration_ms": 45.2,
    "recovery_transactions_replayed": 15
  }
}
```

### Manual Recovery

If automatic recovery fails, you can:

1. **Check database integrity**:
   ```bash
   sqlite3 data/context_replay.db "PRAGMA integrity_check"
   ```

2. **Manual checkpoint**:
   ```bash
   sqlite3 data/context_replay.db "PRAGMA wal_checkpoint(FULL)"
   ```

3. **Restore from backup** (if available)

## Data Integrity

### Checksums

During recovery, the system verifies:
- Database integrity
- WAL file consistency
- Transaction completeness

### Verification

```bash
# Enable checksum verification
DURABILITY_VERIFY_CHECKSUMS=true
```

### Integrity Check

```bash
GET /durability/status
```

If integrity check fails, the service will:
1. Log error
2. Attempt recovery
3. Alert monitoring system

## Performance Considerations

### WAL Mode Benefits

- **Concurrent Reads**: Multiple readers don't block
- **Fast Writes**: Sequential writes to WAL
- **Atomic Commits**: All-or-nothing transactions

### Overhead

| Feature | Overhead |
|---------|----------|
| WAL Mode | < 5% |
| Checkpoints | ~10-50ms per 1000 transactions |
| Recovery | ~50-200ms on startup |

### Tuning

**For High Write Throughput**:
```bash
DURABILITY_WAL_SYNC=NORMAL
DURABILITY_WAL_CHECKPOINT=2000
```

**For Maximum Safety**:
```bash
DURABILITY_WAL_SYNC=FULL
DURABILITY_WAL_CHECKPOINT=500
```

**For Testing**:
```bash
DURABILITY_WAL_SYNC=OFF  # Not recommended for production!
```

## Operational Procedures

### Backup

**With WAL Mode**:
```bash
# Checkpoint first
sqlite3 data/context_replay.db "PRAGMA wal_checkpoint(FULL)"

# Then backup
cp data/context_replay.db backup/context_replay_$(date +%Y%m%d).db
```

### Restore

```bash
# Stop service
systemctl stop unison-context-graph

# Restore database
cp backup/context_replay_20251107.db data/context_replay.db

# Remove WAL files
rm -f data/context_replay.db-wal data/context_replay.db-shm

# Start service
systemctl start unison-context-graph
```

### Monitoring

**Key Metrics**:
- `wal_checkpoints` - Number of checkpoints performed
- `wal_checkpoint_duration_ms` - Checkpoint duration
- `recovery_attempts` - Number of recovery attempts
- `recovery_duration_ms` - Recovery duration

**Alerts**:
```prometheus
# Alert on recovery failures
alert: DatabaseRecoveryFailed
expr: increase(unison_context_recovery_attempts[5m]) > 0 and increase(unison_context_recovery_duration_ms[5m]) == 0

# Alert on large WAL file
alert: WALFileTooLarge
expr: unison_context_wal_size_bytes > 100000000  # 100MB
```

## Troubleshooting

### WAL File Growing Too Large

**Symptom**: WAL file > 100MB

**Cause**: Checkpoints not running frequently enough

**Solution**:
```bash
# Reduce checkpoint interval
DURABILITY_WAL_CHECKPOINT=500

# Or manually checkpoint
curl -X POST http://localhost:8081/durability/wal/checkpoint
```

### Recovery Taking Too Long

**Symptom**: Startup takes > 10 seconds

**Cause**: Large WAL file with many transactions

**Solution**:
1. Checkpoint before shutdown
2. Reduce checkpoint interval
3. Consider database optimization

### Database Corruption

**Symptom**: Integrity check fails

**Cause**: Hardware failure, power loss, or bug

**Solution**:
1. Restore from backup
2. Check hardware (disk, memory)
3. Report bug with logs

### WAL Mode Not Enabled

**Symptom**: `wal_enabled: false` in status

**Cause**: Configuration or initialization error

**Solution**:
```bash
# Check configuration
echo $DURABILITY_WAL_ENABLED

# Check logs
journalctl -u unison-context-graph | grep WAL

# Manually enable
sqlite3 data/context_replay.db "PRAGMA journal_mode=WAL"
```

## Best Practices

### 1. Always Enable WAL in Production

WAL mode provides better reliability and performance with minimal overhead.

### 2. Monitor WAL File Size

Set up alerts for WAL files > 50MB to catch checkpoint issues early.

### 3. Checkpoint Before Shutdown

Ensure clean shutdown with final checkpoint to minimize recovery time.

### 4. Regular Backups

Backup database after checkpointing to ensure consistency.

### 5. Test Recovery

Periodically test recovery process to ensure it works correctly.

### 6. Use NORMAL Sync Mode

NORMAL provides good balance of safety and performance for most use cases.

## Architecture

### Components

```
┌─────────────────────────────────────┐
│     DurabilityManager               │
│  ┌──────────────────────────────┐   │
│  │      WALManager              │   │
│  │  - Enable WAL                │   │
│  │  - Checkpoint                │   │
│  │  - Monitor                   │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │    RecoveryManager           │   │
│  │  - Detect WAL                │   │
│  │  - Replay transactions       │   │
│  │  - Verify integrity          │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Data Flow

```
Write Request
    ↓
WAL File (*.db-wal)
    ↓
Checkpoint (periodic)
    ↓
Main Database (*.db)
```

### Recovery Flow

```
Startup
    ↓
Check for WAL file
    ↓
Replay transactions
    ↓
Verify integrity
    ↓
Checkpoint WAL
    ↓
Resume normal operation
```

## API Reference

### GET /durability/status

Get durability features status.

**Response**:
```json
{
  "config": {
    "wal_enabled": true,
    "recovery_enabled": true
  },
  "wal": {
    "enabled": true,
    "wal_exists": true,
    "wal_size_bytes": 4096,
    "transaction_count": 150
  },
  "metrics": {
    "wal_checkpoints": 5,
    "wal_checkpoint_duration_ms": 12.5,
    "recovery_attempts": 1,
    "recovery_duration_ms": 45.2
  }
}
```

## See Also

- [Privacy & TTL](PRIVACY.md) - Data retention and PII scrubbing
- [Operations Guide](OPERATIONS.md) - Deployment and maintenance
- [SQLite WAL Documentation](https://www.sqlite.org/wal.html)
