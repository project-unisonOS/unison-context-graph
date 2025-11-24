# Context Graph Replay Store & API

## Overview

The Context Graph service now includes a comprehensive replay store system that provides event persistence and replay capabilities. This allows you to store, retrieve, and replay context events for debugging, analysis, and testing purposes.

## Features

### 🔄 Event Persistence
- **Automatic Trace Storage**: Every context update is automatically stored as an event trace
- **Comprehensive Data**: Stores original context sources, fusion results, and context snapshots
- **Unique Trace IDs**: Each event gets a unique UUID for precise identification
- **Session Tracking**: Events are organized by person and session for easy retrieval

### 📊 Replay Capabilities
- **Full Event Replay**: Replay any stored event with full context reconstruction
- **Context Reconstruction**: Optionally replay the context fusion process
- **Time Scaling**: Control replay speed with configurable time scale factors
- **Selective Replay**: Choose whether to include context snapshots in replay

### 🔍 Query & Management
- **Trace Listing**: List traces by person with pagination support
- **Session Queries**: Retrieve all traces for a specific session
- **Trace Search**: Get specific traces by ID
- **Cleanup Operations**: Automatic cleanup of old traces
- **Statistics**: Comprehensive statistics about stored traces

## API Endpoints

### Core Replay Endpoints

#### `POST /replay/{trace_id}`
Replay a specific event trace with optional context reconstruction.

**Request Body:**
```json
{
  "trace_id": "uuid-here",
  "include_context": true,
  "time_scale": 1.0
}
```

**Response:**
```json
{
  "trace": {
    "trace_id": "uuid-here",
    "person_id": "user-123",
    "session_id": "session-456",
    "event_type": "context_update",
    "timestamp": "2025-01-15T10:30:00Z",
    "event_data": { ... },
    "context_snapshot": { ... }
  },
  "replay_metadata": {
    "requested_at": "2025-01-15T10:35:00Z",
    "include_context": true,
    "time_scale": 1.0,
    "original_event_type": "context_update",
    "replay_available": true
  },
  "replay_result": {
    "context_state": { ... },
    "fusion_timestamp": "2025-01-15T10:35:00Z",
    "is_replay": true,
    "original_timestamp": "2025-01-15T10:30:00Z"
  }
}
```

#### `GET /replay/{trace_id}`
Retrieve a specific event trace by ID.

**Response:** Event trace object (same format as in replay response)

#### `GET /replay/session/{person_id}/{session_id}?limit=100`
Get all traces for a specific session.

**Response:** Array of event trace objects

#### `GET /replay/person/{person_id}?offset=0&limit=50`
List all traces for a person with pagination.

**Response:**
```json
{
  "traces": [ ... ],
  "total_count": 150,
  "has_more": true
}
```

### Management Endpoints

#### `DELETE /replay/{trace_id}`
Delete a specific event trace.

#### `POST /replay/cleanup?days_to_keep=30`
Clean up traces older than specified days.

#### `GET /replay/stats`
Get comprehensive statistics about stored traces.

**Response:**
```json
{
  "total_traces": 1250,
  "top_persons": [
    {
      "person_id": "user-123",
      "trace_count": 45
    }
  ],
  "event_types": [
    {
      "event_type": "context_update",
      "count": 1250
    }
  ],
  "recent_activity": [
    {
      "date": "2025-01-15",
      "trace_count": 85
    }
  ],
  "stats_timestamp": "2025-01-15T10:30:00Z"
}
```

## Data Models

### EventTrace
```python
@dataclass
class EventTrace:
    trace_id: str
    person_id: str
    session_id: str
    event_type: str
    timestamp: datetime
    event_data: Dict[str, Any]
    context_snapshot: Optional[Dict[str, Any]]
```

### ReplayRequest
```python
class ReplayRequest(BaseModel):
    trace_id: str
    include_context: bool = True
    time_scale: float = 1.0
```

## Storage Architecture

### Database Schema
The replay store uses SQLite with the following schema:

```sql
CREATE TABLE event_traces (
    trace_id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_data TEXT NOT NULL,
    context_snapshot TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes
- `idx_person_id`: Fast queries by person
- `idx_session_id`: Fast session-based queries
- `idx_timestamp`: Time-based queries and cleanup
- `idx_event_type`: Event type filtering

### Configuration
- **Database Path**: `data/context_replay.db` (configurable via `REPLAY_DB_PATH`)
- **Auto-cleanup**: 30 days retention by default
- **Thread Safety**: Full thread-safe operations with locks

## Usage Examples

### Basic Replay Workflow

1. **Update Context** (generates trace):
```bash
curl -X POST http://localhost:8081/context/update \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "user-123",
    "session_id": "session-456",
    "context_sources": { ... }
  }'
```

2. **List Traces**:
```bash
curl http://localhost:8081/replay/person/user-123
```

3. **Replay Trace**:
```bash
curl -X POST http://localhost:8081/replay/{trace_id} \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "uuid-here",
    "include_context": true,
    "time_scale": 1.0
  }'
```

### Testing
Run the included test script to verify functionality:

```bash
python test_replay_api.py
```

## Performance Considerations

### Storage Optimization
- **JSON Compression**: Event data stored as JSON strings
- **Selective Context**: Context snapshots optional per trace
- **Automatic Cleanup**: Configurable retention policies

### Query Performance
- **Indexed Queries**: All common query patterns indexed
- **Pagination**: Efficient pagination for large datasets
- **Connection Pooling**: Thread-safe database access

### Memory Usage
- **On-Demand Loading**: Traces loaded from disk as needed
- **Efficient Serialization**: Minimal memory footprint
- **Cleanup Automation**: Prevents unlimited storage growth

## Integration Points

### Context Updates
Every context update automatically generates a trace with:
- Original context sources
- Fusion result (context state)
- Context snapshot
- Metadata (person, session, timestamp)

### WebSocket Integration
Real-time context updates continue to work seamlessly with trace storage in the background.

### Future Enhancements
- **Batch Replay**: Replay multiple traces in sequence
- **Export/Import**: Trace data portability
- **Advanced Filtering**: Complex query capabilities
- **Performance Metrics**: Replay performance tracking

## Security & Privacy

### Data Protection
- **Local Storage**: SQLite database stored locally
- **No External Exposure**: Traces not exposed externally
- **Configurable Retention**: Automatic cleanup policies

### Access Control
- **Person Isolation**: Users can only access their own traces
- **Session Boundaries**: Clear session-based access patterns
- **Admin Functions**: Separate cleanup and statistics endpoints

This replay system provides comprehensive event persistence and replay capabilities while maintaining performance and security standards.
