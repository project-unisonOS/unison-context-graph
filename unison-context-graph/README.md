# Unison Context Graph Service

## Status
Reference/archive — upstream snapshot kept for comparison; not used by devstack.

## Overview

The Context Graph Service is a core component of Unison's real-time intent orchestration environment. It fuses multi-dimensional context data to enable intelligent decision-making, providing the environmental intelligence necessary for optimal intent execution and experience generation.

## Purpose

- **Sensory Fusion**: Integrates environmental, temporal, and device context
- **Preference Modeling**: Maintains and updates user preference models
- **Environmental Awareness**: Tracks location, time, activity, and social context
- **Historical Patterns**: Learns from past interactions and outcomes
- **Real-time Adaptation**: Continuously updates context based on new information

## Architecture

### Core Components

```
Context Graph Service
├── Context Collectors
│   ├── Environmental Sensors
│   ├── Device State Monitor
│   ├── Temporal Context Engine
│   └── Social Context Analyzer
├── Fusion Engine
│   ├── Multi-modal Data Integration
│   ├── Context Correlation
│   ├── Conflict Resolution
│   └── Confidence Scoring
├── Preference Model
│   ├── User Behavior Analysis
│   ├── Pattern Recognition
│   ├── Adaptation Learning
│   └── Personalization Engine
├── Context Store
│   ├── Real-time Context Cache
│   ├── Historical Context Archive
│   ├── Preference Database
│   └── Pattern Repository
└── Context API
    ├── Query Interface
    ├── Subscription Service
    ├── Update Endpoints
    └── Analytics Interface
```

## API Specification

### Context Management Endpoints

#### POST /context/update
Updates context with new sensory or environmental data.

```json
{
  "context_update": {
    "person_id": "person-123",
    "session_id": "session-456",
    "timestamp": "2024-01-01T12:00:00Z",
    "context_sources": {
      "environmental": {
        "location": "office",
        "noise_level": "moderate",
        "lighting": "bright",
        "temperature": "comfortable"
      },
      "device": {
        "active_applications": ["browser", "document_editor"],
        "screen_state": "active",
        "battery_level": 0.85,
        "network_connection": "wifi"
      },
      "temporal": {
        "time_of_day": "morning",
        "day_of_week": "monday",
        "local_time": "09:00",
        "timezone": "America/Los_Angeles"
      },
      "activity": {
        "current_activity": "work",
        "activity_duration": "2h",
        "interaction_frequency": "high",
        "focus_level": "deep"
      },
      "social": {
        "nearby_people": ["team_member_1", "team_member_2"],
        "meeting_status": "between_meetings",
        "collaboration_mode": "individual"
      }
    }
  }
}
```

**Response**:
```json
{
  "context_state": {
    "person_id": "person-123",
    "fusion_timestamp": "2024-01-01T12:00:01Z",
    "context_graph": {
      "primary_context": {
        "work_environment": "office_deep_focus",
        "productivity_state": "high",
        "communication_readiness": "available",
        "cognitive_load": "moderate"
      },
      "preferences": {
        "communication_style": "concise",
        "interaction_modality": "visual",
        "interruption_tolerance": "low",
        "response_expectation": "immediate"
      },
      "patterns": {
        "peak_productivity_hours": ["09:00-12:00"],
        "preferred_break_intervals": "every 90 minutes",
        "collaboration_preferences": "scheduled",
        "learning_style": "visual_demonstration"
      },
      "confidence_scores": {
        "environmental": 0.92,
        "activity": 0.87,
        "social": 0.78,
        "overall": 0.86
      }
    },
    "recommendations": {
      "optimal_interaction_timing": "current",
      "preferred_response_format": "visual_dashboard",
      "suggested_break_time": "10:30",
      "communication_channels": ["workspace_message", "desktop_notification"]
    }
  }
}
```

#### GET /context/current/{person_id}
Retrieves current fused context for a person.

#### GET /context/history/{person_id}
Retrieves historical context data for pattern analysis.

#### POST /context/preferences/update
Updates user preferences and adaptation model.

#### GET /context/predict/{person_id}
Predicts optimal context for upcoming activities.

### Context Query Endpoints

#### POST /context/query
Complex context queries for decision making.

```json
{
  "query": {
    "person_id": "person-123",
    "context_dimensions": ["environmental", "temporal", "activity"],
    "time_range": {
      "start": "2024-01-01T09:00:00Z",
      "end": "2024-01-01T17:00:00Z"
    },
    "filters": {
      "activity_type": "work",
      "location": "office"
    }
  }
}
```

#### GET /context/subscribe/{person_id}
WebSocket endpoint for real-time context updates.

## Context Dimensions

### Environmental Context
- **Physical Location**: Office, home, mobile, meeting room
- **Ambient Conditions**: Noise, lighting, temperature, air quality
- **Device Ecosystem**: Available devices, active applications, connectivity
- **Infrastructure**: Network quality, power status, peripheral availability

### Temporal Context
- **Time Patterns**: Hour of day, day of week, seasonality
- **Schedule Context**: Meeting availability, deadline proximity, work hours
- **Rhythms**: Circadian patterns, productivity cycles, break preferences
- **Temporal Constraints**: Time zones, business hours, cultural considerations

### Activity Context
- **Current Activity**: Work, learning, leisure, communication, creation
- **Focus State**: Deep work, light attention, multitasking, break time
- **Interaction Patterns**: Frequency, modality preferences, response expectations
- **Task Context**: Active projects, goal progress, workflow stage

### Social Context
- **Collaboration Mode**: Individual, team, meeting, presentation
- **Social Environment**: Nearby people, team availability, hierarchy
- **Communication Readiness**: Available, busy, do-not-disturb, offline
- **Relationship Context**: Professional, personal, collaborative, hierarchical

### Personal Context
- **Cognitive State**: Alertness, fatigue, stress, creativity level
- **Emotional State**: Motivated, frustrated, satisfied, anxious
- **Physical State**: Energy level, comfort, health status
- **Preference State**: Evolving preferences based on experience

## Fusion Algorithm

### Multi-Modal Data Integration
```python
class ContextFusionEngine:
    def fuse_context(self, raw_context_sources):
        # 1. Normalize and align data from different sources
        normalized_data = self.normalize_sources(raw_context_sources)
        
        # 2. Correlate related context dimensions
        correlated_context = self.correlate_dimensions(normalized_data)
        
        # 3. Resolve conflicts and inconsistencies
        resolved_context = self.resolve_conflicts(correlated_context)
        
        # 4. Calculate confidence scores for each dimension
        scored_context = self.calculate_confidence(resolved_context)
        
        # 5. Generate unified context graph
        return self.generate_context_graph(scored_context)
```

### Confidence Scoring
- **Source Reliability**: Trustworthiness of data sources
- **Data Freshness**: Recency of context updates
- **Cross-Validation**: Consistency across multiple sources
- **Historical Accuracy**: Past prediction accuracy
- **Environmental Stability**: Likelihood of rapid change

## Preference Learning

### Behavior Analysis
- **Interaction Patterns**: How person responds to different contexts
- **Choice Consistency**: Regularity in preference expressions
- **Adaptation Speed**: How quickly preferences change
- **Context Sensitivity**: How preferences vary with environment

### Model Updates
```python
class PreferenceLearningEngine:
    def update_preferences(self, interaction_outcome, context_state):
        # 1. Analyze outcome satisfaction
        satisfaction_score = self.analyze_satisfaction(interaction_outcome)
        
        # 2. Identify context features that influenced outcome
        influential_features = self.extract_context_features(context_state)
        
        # 3. Update preference weights based on feedback
        updated_preferences = self.adjust_preferences(
            influential_features, 
            satisfaction_score
        )
        
        # 4. Validate changes with historical patterns
        validated_preferences = self.validate_with_history(updated_preferences)
        
        return validated_preferences
```

## Integration Points

### Intent Graph Service
- Provides context constraints for goal planning
- Supplies environmental preferences for execution
- Offers temporal context for scheduling decisions

### Experience Rendering Engine
- Delivers fused context for experience generation
- Provides preference data for modality selection
- Supplies environmental constraints for interface design

### Orchestrator Service
- Real-time context updates for execution decisions
- Preference data for resource allocation
- Environmental constraints for service coordination

### Skills and Inference Services
- Context parameters for task execution
- Preference data for output customization
- Environmental constraints for capability selection

## Configuration

### Environment Variables
```bash
# Service Configuration
CONTEXT_GRAPH_PORT=8081
CONTEXT_GRAPH_HOST=0.0.0.0

# Database Configuration
CONTEXT_DB_URL=postgresql://user:pass@postgres:5432/context_graph
REDIS_URL=redis://redis:6379
TIMESERIES_DB_URL=influxdb://influxdb:8086/context

# External Services
INTENT_GRAPH_URL=http://unison-intent-graph:8080
EXPERIENCE_RENDERER_URL=http://unison-experience-renderer:8080

# Sensor Configuration
ENVIRONMENTAL_SENSORS_ENABLED=true
DEVICE_MONITORING_ENABLED=true
TEMPORAL_PRECISION=60  # seconds
```

### Context Model Configuration
```yaml
context_fusion:
  update_frequency: 30  # seconds
  confidence_threshold: 0.7
  max_context_history: 30  # days
  
preference_learning:
  learning_rate: 0.01
  adaptation_threshold: 0.1
  min_interactions_for_learning: 50
  
context_dimensions:
  environmental:
    weight: 0.3
    sources: ["sensors", "device_api", "location_service"]
  temporal:
    weight: 0.2  
    sources: ["system_clock", "calendar", "schedule_api"]
  activity:
    weight: 0.25
    sources: ["interaction_monitor", "application_tracker", "focus_detector"]
  social:
    weight: 0.15
    sources: ["presence_system", "calendar", "communication_api"]
  personal:
    weight: 0.1
    sources: ["biometric_sensors", "feedback_system", "behavior_analyzer"]
```

## Deployment

### Docker Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY models/ ./models/

EXPOSE 8081
CMD ["python", "-m", "src.main"]
```

### Docker Compose
```yaml
context-graph:
  build: .
  ports:
    - "8081:8081"
  environment:
    - CONTEXT_DB_URL=postgresql://user:pass@postgres:5432/context_graph
    - INTENT_GRAPH_URL=http://unison-intent-graph:8080
  depends_on:
    - postgres
    - redis
    - influxdb
  volumes:
    - ./models:/app/models
    - /var/run/docker.sock:/var/run/docker.sock  # For device monitoring
```

## Monitoring and Observability

### Metrics
- Context fusion latency and accuracy
- Preference learning convergence rate
- Environmental sensor data quality
- Cross-context correlation effectiveness
- Prediction accuracy for optimal timing

### Logging
- Structured context change events
- Preference model updates with confidence scores
- Fusion algorithm performance metrics
- Anomaly detection in context patterns

### Health Checks
- `/health` - Basic service health
- `/health/sensors` - Sensor connectivity and data quality
- `/health/fusion` - Fusion engine performance
- `/health/learning` - Preference learning system status

## Privacy and Security

### Data Protection
- Context data encryption at rest and in transit
- Personal data anonymization for pattern analysis
- Configurable data retention policies
- GDPR-compliant right to be forgotten

### Privacy Controls
- Granular consent for different context dimensions
- Context data sharing preferences
- Audit logs for all context access
- User-controlled data deletion

### Security Measures
- API authentication and authorization
- Rate limiting for context queries
- Input validation and sanitization
- Secure sensor communication protocols

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Start development server with mock sensors
python -m src.main --dev --mock-sensors
```

### Testing Strategy
- Unit tests for fusion algorithms
- Integration tests with sensor systems
- Performance tests for real-time processing
- Privacy and security compliance tests

## Future Enhancements

### Advanced Sensing
- Biometric sensor integration for cognitive state
- Environmental IoT sensor networks
- Wearable device context integration
- Computer vision for activity recognition

### Predictive Analytics
- Context prediction using time series analysis
- Proactive preference adaptation
- Anomaly detection in behavior patterns
- Context-aware recommendation systems

### Multi-Person Context
- Group context fusion for collaboration
- Social dynamics modeling
- Team preference synchronization
- Shared context state management

---

The Context Graph Service provides the environmental intelligence that makes Unison's intent orchestration truly adaptive and context-aware, ensuring that every experience is optimized for the person's current situation and preferences.
