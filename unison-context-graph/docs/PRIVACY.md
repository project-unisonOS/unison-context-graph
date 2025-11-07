# Privacy & Data Retention

## Overview

The context-graph service implements comprehensive privacy features to comply with data protection regulations (GDPR, CCPA) and minimize data retention.

## Features

- **Time-To-Live (TTL)**: Automatic deletion of old data
- **PII Scrubbing**: Anonymization of personally identifiable information
- **Configurable Retention**: Flexible retention policies
- **Audit Trail**: Track all privacy operations

## Time-To-Live (TTL)

### What is TTL?

TTL automatically deletes data after a specified retention period, ensuring compliance with data minimization principles.

### Configuration

```bash
# Enable/disable TTL
DURABILITY_TTL_ENABLED=true

# Default retention period (days)
DURABILITY_TTL_DAYS=30

# Cleanup interval (seconds)
DURABILITY_TTL_INTERVAL=3600  # 1 hour
```

### How It Works

1. **On Insert**: Each record gets an `expires_at` timestamp
2. **Background Job**: Runs every hour to delete expired records
3. **Batch Deletion**: Processes records in batches for efficiency

### Retention Policies

| Data Type | Default TTL | Configurable |
|-----------|-------------|--------------|
| Event Traces | 30 days | Yes |
| Context Snapshots | 7 days | Yes |
| Replay Data | 90 days | Yes |

### Manual Cleanup

Trigger cleanup manually:

```bash
POST /durability/ttl/cleanup
```

Response:
```json
{
  "success": true,
  "deleted_count": 150,
  "timestamp": "2025-11-07T21:00:00Z"
}
```

### Monitoring

Check TTL status:

```bash
GET /durability/status
```

Response:
```json
{
  "ttl": {
    "enabled": true,
    "ttl_default_days": 30,
    "cleanup_interval_seconds": 3600,
    "records_with_ttl": 1500,
    "expired_records": 25,
    "oldest_expiry": "2025-12-07T12:00:00Z",
    "cleanup_job_running": true
  }
}
```

## PII Scrubbing

### What is PII Scrubbing?

PII scrubbing removes or anonymizes personally identifiable information from old records to protect user privacy.

### Configuration

```bash
# Enable/disable PII scrubbing
DURABILITY_PII_ENABLED=true

# Scrub records older than (days)
DURABILITY_PII_AFTER_DAYS=90

# Scrubbing interval (seconds)
DURABILITY_PII_INTERVAL=86400  # 24 hours
```

### Scrubbing Strategies

#### 1. Hash/Anonymize

**person_id**: One-way hash with prefix
```
"user_12345" → "SCRUBBED_a1b2c3d4e5f6g7h8"
```

#### 2. Generalize

**Location**: Reduce to city level
```
"San Francisco, CA, USA" → "San Francisco"
```

**GPS Coordinates**: Round to ~11km precision
```
{"lat": 37.7749, "lon": -122.4194} → "~37.8,~-122.4"
```

**Timestamps**: Date only
```
"2025-11-07T12:30:45Z" → "2025-11-07"
```

#### 3. Remove Completely

Fields removed:
- `device_id`
- `ip_address`
- `mac_address`
- `email`
- `phone`
- `address`
- `ssn`
- `credit_card`
- `password`
- `token`

### Example

**Before Scrubbing**:
```json
{
  "person_id": "user_12345",
  "event_data": {
    "location": "San Francisco, CA, USA",
    "device_id": "ABC123XYZ",
    "email": "user@example.com",
    "gps_coordinates": {"lat": 37.7749, "lon": -122.4194}
  }
}
```

**After Scrubbing**:
```json
{
  "person_id": "SCRUBBED_a1b2c3d4e5f6",
  "event_data": {
    "location": "San Francisco",
    "device_id": null,
    "email": null,
    "gps_coordinates": "~37.8,~-122.4"
  },
  "scrubbed_at": "2025-11-07T21:00:00Z"
}
```

### Manual Scrubbing

Trigger scrubbing manually:

```bash
POST /durability/pii/scrub?batch_size=100
```

Response:
```json
{
  "success": true,
  "scrubbed_count": 25,
  "batch_size": 100,
  "timestamp": "2025-11-07T21:00:00Z"
}
```

### Monitoring

Check scrubbing status:

```bash
GET /durability/status
```

Response:
```json
{
  "pii_scrubbing": {
    "enabled": true,
    "scrubbing_after_days": 90,
    "scrubbing_interval_seconds": 86400,
    "records_scrubbed": 150,
    "records_pending_scrubbing": 25,
    "oldest_scrubbed_at": "2025-10-01T10:00:00Z",
    "scrubbing_job_running": true
  }
}
```

## Compliance

### GDPR Compliance

**Right to Erasure (Article 17)**:
- TTL ensures data is not kept longer than necessary
- PII scrubbing anonymizes old data
- Manual deletion available via API

**Data Minimization (Article 5)**:
- Only essential data is retained
- PII is scrubbed after retention period
- Configurable retention policies

**Privacy by Design (Article 25)**:
- Privacy features enabled by default
- Automatic data cleanup
- Audit trail for all operations

### CCPA Compliance

**Data Deletion**:
- Automatic deletion after retention period
- Manual deletion on request
- Verification of deletion

**Data Minimization**:
- Limited retention periods
- PII anonymization
- Regular cleanup

### HIPAA Compliance

**Minimum Necessary**:
- Data retained only as long as needed
- PII scrubbed after use
- Access controls

**Audit Trail**:
- All scrubbing operations logged
- Deletion tracking
- Compliance reporting

## Data Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                    Data Lifecycle                        │
└─────────────────────────────────────────────────────────┘

Insert
  ↓
Set TTL (30 days)
  ↓
Active Period (0-30 days)
  ↓
Retention Period (30-90 days)
  ↓
PII Scrubbing (90 days)
  ↓
Extended Retention (90-120 days)
  ↓
Deletion (120 days)
```

## Operational Procedures

### Adjusting Retention Periods

**For Specific Data Types**:
```python
# In code
ttl_days = 7 if event_type == "context_snapshot" else 30
expires_at = durability.ttl_manager.calculate_expiry(days=ttl_days)
```

**Via Environment**:
```bash
# Shorter retention
DURABILITY_TTL_DAYS=7

# Longer retention
DURABILITY_TTL_DAYS=90
```

### Manual Data Deletion

**Delete Specific Record**:
```bash
DELETE /replay/{trace_id}
```

**Delete All User Data**:
```bash
DELETE /replay/person/{person_id}
```

**Cleanup Old Data**:
```bash
POST /replay/cleanup?days_to_keep=30
```

### Audit Trail

All privacy operations are logged:

```
INFO: TTL cleanup: deleted 150 expired records (45.2ms)
INFO: PII scrubbing: scrubbed 25 records (123.5ms)
INFO: Manual deletion: trace_id=abc123, user=admin
```

### Compliance Reporting

Generate compliance report:

```bash
GET /durability/status
```

Extract key metrics:
- Records with TTL
- Expired records
- Scrubbed records
- Pending scrubbing

## Best Practices

### 1. Set Appropriate Retention Periods

Balance business needs with privacy:
- **Operational Data**: 7-30 days
- **Analytics Data**: 30-90 days
- **Audit Logs**: 1 year

### 2. Enable PII Scrubbing

Always enable PII scrubbing in production to protect user privacy.

### 3. Monitor Cleanup Jobs

Ensure cleanup jobs are running and completing successfully.

### 4. Regular Audits

Periodically review:
- Retention policies
- Scrubbing effectiveness
- Compliance status

### 5. Document Retention Policies

Maintain clear documentation of:
- What data is collected
- How long it's retained
- When it's deleted/scrubbed

### 6. Test Recovery

Ensure you can recover data if needed during retention period.

## Troubleshooting

### TTL Cleanup Not Running

**Symptom**: `expired_records` count increasing

**Cause**: Background job not running

**Solution**:
```bash
# Check status
GET /durability/status

# Manually trigger
POST /durability/ttl/cleanup

# Check logs
journalctl -u unison-context-graph | grep TTL
```

### PII Scrubbing Not Working

**Symptom**: `records_pending_scrubbing` not decreasing

**Cause**: Background job not running or configuration issue

**Solution**:
```bash
# Check configuration
echo $DURABILITY_PII_ENABLED

# Manually trigger
POST /durability/pii/scrub

# Check logs
journalctl -u unison-context-graph | grep PII
```

### Records Not Expiring

**Symptom**: Old records still present

**Cause**: TTL not set on records

**Solution**:
```bash
# Check if expires_at column exists
sqlite3 data/context_replay.db "PRAGMA table_info(event_traces)"

# Add TTL to existing records
sqlite3 data/context_replay.db "UPDATE event_traces SET expires_at = datetime(created_at, '+30 days') WHERE expires_at IS NULL"
```

## API Reference

### GET /durability/status

Get privacy features status.

**Response**:
```json
{
  "ttl": {
    "enabled": true,
    "ttl_default_days": 30,
    "records_with_ttl": 1500,
    "expired_records": 25
  },
  "pii_scrubbing": {
    "enabled": true,
    "scrubbing_after_days": 90,
    "records_scrubbed": 150,
    "records_pending_scrubbing": 25
  }
}
```

### POST /durability/ttl/cleanup

Manually trigger TTL cleanup.

**Response**:
```json
{
  "success": true,
  "deleted_count": 150,
  "timestamp": "2025-11-07T21:00:00Z"
}
```

### POST /durability/pii/scrub

Manually trigger PII scrubbing.

**Parameters**:
- `batch_size` (optional): Number of records to scrub (default: 100)

**Response**:
```json
{
  "success": true,
  "scrubbed_count": 25,
  "batch_size": 100,
  "timestamp": "2025-11-07T21:00:00Z"
}
```

## See Also

- [Durability](DURABILITY.md) - WAL and crash recovery
- [Operations Guide](OPERATIONS.md) - Deployment and maintenance
- [GDPR Compliance](https://gdpr.eu/)
- [CCPA Compliance](https://oag.ca.gov/privacy/ccpa)
