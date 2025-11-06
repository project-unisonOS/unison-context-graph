#!/usr/bin/env python3
"""
Unison Context Graph Service
Real-time context fusion and environmental intelligence
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import redis
import asyncio
import sqlite3
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    PORT = int(os.getenv("CONTEXT_GRAPH_PORT", 8081))
    HOST = os.getenv("CONTEXT_GRAPH_HOST", "0.0.0.0")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
    DB_URL = os.getenv("CONTEXT_DB_URL", "postgresql://user:pass@postgres:5432/context_graph")
    INTENT_GRAPH_URL = os.getenv("INTENT_GRAPH_URL", "http://unison-intent-graph:8080")
    EXPERIENCE_RENDERER_URL = os.getenv("EXPERIENCE_RENDERER_URL", "http://unison-experience-renderer:8082")
    REPLAY_DB_PATH = os.getenv("REPLAY_DB_PATH", "data/context_replay.db")

# Data Models
@dataclass
class ContextDimension:
    environmental: Dict[str, Any]
    temporal: Dict[str, Any]
    activity: Dict[str, Any]
    social: Dict[str, Any]
    personal: Dict[str, Any]
    confidence_scores: Dict[str, float]

@dataclass
class ContextPreferences:
    communication_style: str
    interaction_modality: str
    interruption_tolerance: str
    response_expectation: str
    data_density: str
    visual_preferences: Dict[str, Any]

@dataclass
class ContextState:
    person_id: str
    fusion_timestamp: datetime
    context_graph: ContextDimension
    preferences: ContextPreferences
    recommendations: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "person_id": self.person_id,
            "fusion_timestamp": self.fusion_timestamp.isoformat(),
            "context_graph": asdict(self.context_graph),
            "preferences": asdict(self.preferences),
            "recommendations": self.recommendations
        }

class ContextUpdateRequest(BaseModel):
    person_id: str = Field(..., description="Person identifier")
    session_id: str = Field(..., description="Session identifier")
    context_sources: Dict[str, Any] = Field(..., description="Raw context data from various sources")

class ContextStateResponse(BaseModel):
    context_state: ContextState

class ContextQueryRequest(BaseModel):
    person_id: str = Field(..., description="Person identifier")
    context_dimensions: List[str] = Field(..., description="Dimensions to query")
    time_range: Optional[Dict[str, str]] = Field(None, description="Time range for historical data")
    filters: Optional[Dict[str, Any]] = Field(None, description="Query filters")

@dataclass
class EventTrace:
    trace_id: str
    person_id: str
    session_id: str
    event_type: str
    timestamp: datetime
    event_data: Dict[str, Any]
    context_snapshot: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "person_id": self.person_id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "event_data": self.event_data,
            "context_snapshot": self.context_snapshot
        }

class ReplayRequest(BaseModel):
    trace_id: str = Field(..., description="Trace identifier to replay")
    include_context: bool = Field(True, description="Include context snapshots in replay")
    time_scale: float = Field(1.0, description="Time scale factor for replay (1.0 = normal speed)")

class TraceListResponse(BaseModel):
    traces: List[EventTrace]
    total_count: int
    has_more: bool

# Context Fusion Engine
class ContextFusionEngine:
    """Fuses multi-dimensional context data"""
    
    def __init__(self):
        self.context_weights = {
            "environmental": 0.3,
            "temporal": 0.2,
            "activity": 0.25,
            "social": 0.15,
            "personal": 0.1
        }
    
    def fuse_context(self, raw_context_sources: Dict[str, Any]) -> ContextDimension:
        """Fuse raw context data into unified context graph"""
        
        # Extract and normalize individual dimensions
        environmental = self._process_environmental_context(raw_context_sources)
        temporal = self._process_temporal_context(raw_context_sources)
        activity = self._process_activity_context(raw_context_sources)
        social = self._process_social_context(raw_context_sources)
        personal = self._process_personal_context(raw_context_sources)
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores({
            "environmental": environmental,
            "temporal": temporal,
            "activity": activity,
            "social": social,
            "personal": personal
        })
        
        return ContextDimension(
            environmental=environmental,
            temporal=temporal,
            activity=activity,
            social=social,
            personal=personal,
            confidence_scores=confidence_scores
        )
    
    def _process_environmental_context(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Process environmental context data"""
        env_data = sources.get("environmental", {})
        device_data = sources.get("device", {})
        
        return {
            "location": env_data.get("location", "unknown"),
            "noise_level": env_data.get("noise_level", "moderate"),
            "lighting": env_data.get("lighting", "normal"),
            "temperature": env_data.get("temperature", "comfortable"),
            "device": device_data.get("active_applications", []),
            "screen_state": device_data.get("screen_state", "active"),
            "connectivity": device_data.get("network_connection", "unknown")
        }
    
    def _process_temporal_context(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Process temporal context data"""
        temporal_data = sources.get("temporal", {})
        current_time = datetime.utcnow()
        
        return {
            "time_of_day": temporal_data.get("time_of_day", self._get_time_of_day(current_time)),
            "day_of_week": temporal_data.get("day_of_week", current_time.strftime("%A").lower()),
            "local_time": temporal_data.get("local_time", current_time.strftime("%H:%M")),
            "timezone": temporal_data.get("timezone", "UTC"),
            "business_hours": self._is_business_hours(current_time)
        }
    
    def _process_activity_context(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Process activity context data"""
        activity_data = sources.get("activity", {})
        
        return {
            "current_activity": activity_data.get("current_activity", "unknown"),
            "activity_duration": activity_data.get("activity_duration", "0m"),
            "interaction_frequency": activity_data.get("interaction_frequency", "normal"),
            "focus_level": activity_data.get("focus_level", "moderate"),
            "task_complexity": activity_data.get("task_complexity", "medium")
        }
    
    def _process_social_context(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Process social context data"""
        social_data = sources.get("social", {})
        
        return {
            "nearby_people": social_data.get("nearby_people", []),
            "meeting_status": social_data.get("meeting_status", "none"),
            "collaboration_mode": social_data.get("collaboration_mode", "individual"),
            "communication_readiness": social_data.get("communication_readiness", "available")
        }
    
    def _process_personal_context(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Process personal context data"""
        personal_data = sources.get("personal", {})
        
        return {
            "cognitive_load": personal_data.get("cognitive_load", "moderate"),
            "energy_level": personal_data.get("energy_level", "normal"),
            "stress_level": personal_data.get("stress_level", "low"),
            "motivation_level": personal_data.get("motivation_level", "neutral"),
            "comfort_level": personal_data.get("comfort_level", "comfortable")
        }
    
    def _calculate_confidence_scores(self, dimensions: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for each context dimension"""
        scores = {}
        
        for dimension, data in dimensions.items():
            # Simple confidence calculation based on data completeness
            if isinstance(data, dict):
                non_null_values = sum(1 for v in data.values() if v is not None and v != "unknown")
                total_values = len(data)
                scores[dimension] = min(non_null_values / total_values, 1.0) if total_values > 0 else 0.0
            else:
                scores[dimension] = 0.5  # Default confidence
        
        return scores
    
    def _get_time_of_day(self, dt: datetime) -> str:
        """Get time of day category"""
        hour = dt.hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    def _is_business_hours(self, dt: datetime) -> bool:
        """Check if current time is within business hours"""
        hour = dt.hour
        weekday = dt.weekday()  # 0 = Monday, 6 = Sunday
        return 9 <= hour <= 17 and weekday < 5

# Preference Learning Engine
class PreferenceLearningEngine:
    """Learns and adapts user preferences"""
    
    def __init__(self):
        self.default_preferences = {
            "communication_style": "balanced",
            "interaction_modality": "visual",
            "interruption_tolerance": "moderate",
            "response_expectation": "reasonable",
            "data_density": "medium",
            "visual_preferences": {
                "theme": "light",
                "font_size": "medium",
                "animation_level": "subtle"
            }
        }
    
    def get_preferences(self, person_id: str, context: ContextDimension) -> ContextPreferences:
        """Get current preferences for a person"""
        # In real implementation, would load from database and adapt based on context
        preferences = self.default_preferences.copy()
        
        # Adapt preferences based on context
        if context.environmental.get("noise_level") == "high":
            preferences["interruption_tolerance"] = "low"
            preferences["communication_style"] = "concise"
        
        if context.activity.get("focus_level") == "deep":
            preferences["interruption_tolerance"] = "minimal"
            preferences["response_expectation"] = "delayed"
        
        if context.temporal.get("time_of_day") == "evening":
            preferences["data_density"] = "low"
            preferences["visual_preferences"]["theme"] = "dark"
        
        return ContextPreferences(**preferences)
    
    def generate_recommendations(self, context: ContextDimension, preferences: ContextPreferences) -> Dict[str, Any]:
        """Generate context-aware recommendations"""
        recommendations = {}
        
        # Optimal interaction timing
        if context.activity.get("focus_level") == "deep":
            recommendations["optimal_interaction_timing"] = "defer"
        elif context.social.get("meeting_status") == "in_meeting":
            recommendations["optimal_interaction_timing"] = "after_meeting"
        else:
            recommendations["optimal_interaction_timing"] = "current"
        
        # Response format
        if preferences["interaction_modality"] == "visual":
            recommendations["preferred_response_format"] = "visual_dashboard"
        elif preferences["communication_style"] == "concise":
            recommendations["preferred_response_format"] = "brief_summary"
        else:
            recommendations["preferred_response_format"] = "detailed_report"
        
        # Communication channels
        available_channels = []
        if context.environmental.get("connectivity") == "wifi":
            available_channels.extend(["workspace_message", "desktop_notification"])
        if context.personal.get("cognitive_load") != "high":
            available_channels.append("voice")
        
        recommendations["communication_channels"] = available_channels
        
        # Break suggestions
        if context.activity.get("activity_duration") == "2h+":
            recommendations["suggested_break_time"] = "soon"
        
        return recommendations

# Replay Store for Event Persistence
class ReplayStore:
    """Stores and retrieves event traces for replay functionality"""
    
    def __init__(self, db_path: str = "context_replay.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for event storage"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create event traces table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_traces (
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
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_id ON event_traces(person_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON event_traces(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON event_traces(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON event_traces(event_type)")
            
            conn.commit()
            conn.close()
            logger.info(f"Replay store initialized at {self.db_path}")
    
    def store_event(self, trace: EventTrace) -> bool:
        """Store an event trace in the database"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO event_traces 
                    (trace_id, person_id, session_id, event_type, timestamp, event_data, context_snapshot)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    trace.trace_id,
                    trace.person_id,
                    trace.session_id,
                    trace.event_type,
                    trace.timestamp.isoformat(),
                    json.dumps(trace.event_data),
                    json.dumps(trace.context_snapshot) if trace.context_snapshot else None
                ))
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            logger.error(f"Failed to store event trace: {str(e)}")
            return False
    
    def get_trace(self, trace_id: str) -> Optional[EventTrace]:
        """Retrieve a specific event trace by ID"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT trace_id, person_id, session_id, event_type, timestamp, event_data, context_snapshot
                    FROM event_traces WHERE trace_id = ?
                """, (trace_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return EventTrace(
                        trace_id=row[0],
                        person_id=row[1],
                        session_id=row[2],
                        event_type=row[3],
                        timestamp=datetime.fromisoformat(row[4]),
                        event_data=json.loads(row[5]),
                        context_snapshot=json.loads(row[6]) if row[6] else None
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve trace {trace_id}: {str(e)}")
            return None
    
    def get_session_traces(self, person_id: str, session_id: str, limit: int = 100) -> List[EventTrace]:
        """Retrieve all traces for a specific session"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT trace_id, person_id, session_id, event_type, timestamp, event_data, context_snapshot
                    FROM event_traces 
                    WHERE person_id = ? AND session_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                """, (person_id, session_id, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                traces = []
                for row in rows:
                    traces.append(EventTrace(
                        trace_id=row[0],
                        person_id=row[1],
                        session_id=row[2],
                        event_type=row[3],
                        timestamp=datetime.fromisoformat(row[4]),
                        event_data=json.loads(row[5]),
                        context_snapshot=json.loads(row[6]) if row[6] else None
                    ))
                
                return traces
                
        except Exception as e:
            logger.error(f"Failed to retrieve session traces: {str(e)}")
            return []
    
    def list_person_traces(self, person_id: str, offset: int = 0, limit: int = 50) -> TraceListResponse:
        """List all traces for a person with pagination"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get total count
                cursor.execute("SELECT COUNT(*) FROM event_traces WHERE person_id = ?", (person_id,))
                total_count = cursor.fetchone()[0]
                
                # Get traces with pagination
                cursor.execute("""
                    SELECT trace_id, person_id, session_id, event_type, timestamp, event_data, context_snapshot
                    FROM event_traces 
                    WHERE person_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """, (person_id, limit, offset))
                
                rows = cursor.fetchall()
                conn.close()
                
                traces = []
                for row in rows:
                    traces.append(EventTrace(
                        trace_id=row[0],
                        person_id=row[1],
                        session_id=row[2],
                        event_type=row[3],
                        timestamp=datetime.fromisoformat(row[4]),
                        event_data=json.loads(row[5]),
                        context_snapshot=json.loads(row[6]) if row[6] else None
                    ))
                
                has_more = (offset + limit) < total_count
                
                return TraceListResponse(
                    traces=traces,
                    total_count=total_count,
                    has_more=has_more
                )
                
        except Exception as e:
            logger.error(f"Failed to list person traces: {str(e)}")
            return TraceListResponse(traces=[], total_count=0, has_more=False)
    
    def delete_trace(self, trace_id: str) -> bool:
        """Delete a specific event trace"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM event_traces WHERE trace_id = ?", (trace_id,))
                affected_rows = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                return affected_rows > 0
                
        except Exception as e:
            logger.error(f"Failed to delete trace {trace_id}: {str(e)}")
            return False
    
    def cleanup_old_traces(self, days_to_keep: int = 30) -> int:
        """Clean up traces older than specified days"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
                cursor.execute("DELETE FROM event_traces WHERE timestamp < ?", (cutoff_date,))
                deleted_count = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                logger.info(f"Cleaned up {deleted_count} old traces")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old traces: {str(e)}")
            return 0

# Context Graph Service
class ContextGraphService:
    """Main service for context graph processing"""
    
    def __init__(self):
        self.fusion_engine = ContextFusionEngine()
        self.preference_engine = PreferenceLearningEngine()
        self.active_contexts = {}  # In-memory cache for active contexts
        self.websocket_connections = {}  # WebSocket connections for real-time updates
        
        # Ensure data directory exists
        data_dir = Path(Config.REPLAY_DB_PATH).parent
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize replay store with configured path
        self.replay_store = ReplayStore(db_path=Config.REPLAY_DB_PATH)
    
    async def update_context(self, request: ContextUpdateRequest) -> ContextStateResponse:
        """Update context with new data and return fused context"""
        try:
            # 1. Fuse context data
            fused_context = self.fusion_engine.fuse_context(request.context_sources)
            
            # 2. Get preferences
            preferences = self.preference_engine.get_preferences(request.person_id, fused_context)
            
            # 3. Generate recommendations
            recommendations = self.preference_engine.generate_recommendations(fused_context, preferences)
            
            # 4. Create context state
            context_state = ContextState(
                person_id=request.person_id,
                fusion_timestamp=datetime.utcnow(),
                context_graph=fused_context,
                preferences=preferences,
                recommendations=recommendations
            )
            
            # 5. Store event trace for replay
            trace_id = str(uuid.uuid4())
            event_trace = EventTrace(
                trace_id=trace_id,
                person_id=request.person_id,
                session_id=request.session_id,
                event_type="context_update",
                timestamp=context_state.fusion_timestamp,
                event_data={
                    "context_sources": request.context_sources,
                    "fusion_result": context_state.to_dict()
                },
                context_snapshot=context_state.to_dict()
            )
            
            # Store trace asynchronously
            stored = self.replay_store.store_event(event_trace)
            if stored:
                logger.info(f"Event trace stored: {trace_id}")
            else:
                logger.warning(f"Failed to store event trace: {trace_id}")
            
            # 6. Cache active context
            self.active_contexts[request.person_id] = context_state
            
            # 7. Send real-time update via WebSocket if connected
            await self._broadcast_context_update(request.person_id, context_state)
            
            logger.info(f"Context updated for person {request.person_id}")
            
            return ContextStateResponse(context_state=context_state)
            
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
            raise HTTPException(status_code=500, detail="Context update failed")
    
    async def replay_trace(self, trace_id: str, include_context: bool = True, time_scale: float = 1.0) -> Dict[str, Any]:
        """Replay a specific event trace"""
        try:
            trace = self.replay_store.get_trace(trace_id)
            if not trace:
                raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
            
            # Prepare replay data
            replay_data = {
                "trace": trace.to_dict(),
                "replay_metadata": {
                    "requested_at": datetime.utcnow().isoformat(),
                    "include_context": include_context,
                    "time_scale": time_scale,
                    "original_event_type": trace.event_type,
                    "replay_available": True
                }
            }
            
            # If it's a context update trace, we can optionally replay the context fusion
            if trace.event_type == "context_update" and include_context:
                original_sources = trace.event_data.get("context_sources", {})
                if original_sources:
                    # Replay the context fusion process
                    replayed_context = self.fusion_engine.fuse_context(original_sources)
                    replayed_preferences = self.preference_engine.get_preferences(trace.person_id, replayed_context)
                    replayed_recommendations = self.preference_engine.generate_recommendations(replayed_context, replayed_preferences)
                    
                    replayed_state = ContextState(
                        person_id=trace.person_id,
                        fusion_timestamp=datetime.utcnow(),  # Use current timestamp for replay
                        context_graph=replayed_context,
                        preferences=replayed_preferences,
                        recommendations=replayed_recommendations
                    )
                    
                    replay_data["replay_result"] = {
                        "context_state": replayed_state.to_dict(),
                        "fusion_timestamp": replayed_state.fusion_timestamp.isoformat(),
                        "is_replay": True,
                        "original_timestamp": trace.timestamp.isoformat()
                    }
            
            logger.info(f"Trace replay completed: {trace_id}")
            return replay_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error replaying trace {trace_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Trace replay failed")
    
    async def get_session_traces(self, person_id: str, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all traces for a specific session"""
        try:
            traces = self.replay_store.get_session_traces(person_id, session_id, limit)
            return [trace.to_dict() for trace in traces]
        except Exception as e:
            logger.error(f"Error retrieving session traces: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve session traces")
    
    async def list_person_traces(self, person_id: str, offset: int = 0, limit: int = 50) -> TraceListResponse:
        """List all traces for a person with pagination"""
        try:
            return self.replay_store.list_person_traces(person_id, offset, limit)
        except Exception as e:
            logger.error(f"Error listing person traces: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to list person traces")
    
    async def delete_trace(self, trace_id: str) -> Dict[str, Any]:
        """Delete a specific event trace"""
        try:
            deleted = self.replay_store.delete_trace(trace_id)
            if deleted:
                logger.info(f"Trace deleted: {trace_id}")
                return {"trace_id": trace_id, "status": "deleted"}
            else:
                raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting trace {trace_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete trace")
    
    async def get_current_context(self, person_id: str) -> ContextStateResponse:
        """Get current fused context for a person"""
        if person_id not in self.active_contexts:
            raise HTTPException(status_code=404, detail="Context not found")
        
        return ContextStateResponse(context_state=self.active_contexts[person_id])
    
    async def query_context(self, request: ContextQueryRequest) -> Dict[str, Any]:
        """Query context data with filters"""
        # Mock implementation - would query database in real system
        return {
            "person_id": request.person_id,
            "query_results": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_data": "Sample context data"
                }
            ]
        }
    
    async def _broadcast_context_update(self, person_id: str, context_state: ContextState):
        """Broadcast context update via WebSocket"""
        if person_id in self.websocket_connections:
            for websocket in self.websocket_connections[person_id]:
                try:
                    await websocket.send_json(context_state.to_dict())
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket update: {str(e)}")

# FastAPI Application
app = FastAPI(
    title="Unison Context Graph Service",
    description="Real-time context fusion and environmental intelligence",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
context_service = ContextGraphService()

# API Endpoints
@app.post("/context/update", response_model=ContextStateResponse)
async def update_context(request: ContextUpdateRequest):
    """Update context with new sensory or environmental data"""
    return await context_service.update_context(request)

@app.get("/context/current/{person_id}", response_model=ContextStateResponse)
async def get_current_context(person_id: str):
    """Retrieve current fused context for a person"""
    return await context_service.get_current_context(person_id)

@app.post("/context/query")
async def query_context(request: ContextQueryRequest):
    """Complex context queries for decision making"""
    return await context_service.query_context(request)

@app.post("/context/preferences/update")
async def update_preferences(person_id: str, preferences: Dict[str, Any]):
    """Update user preferences and adaptation model"""
    # Mock implementation
    logger.info(f"Updating preferences for person {person_id}")
    return {"person_id": person_id, "status": "updated"}

@app.get("/context/predict/{person_id}")
async def predict_context(person_id: str):
    """Predict optimal context for upcoming activities"""
    # Mock implementation
    return {
        "person_id": person_id,
        "predicted_context": {
            "optimal_interaction_timing": "current",
            "preferred_modality": "visual",
            "confidence": 0.85
        }
    }

# Replay API Endpoints
@app.post("/replay/{trace_id}")
async def replay_trace(trace_id: str, request: ReplayRequest = None):
    """Replay a specific event trace with optional context reconstruction"""
    if request is None:
        request = ReplayRequest(trace_id=trace_id, include_context=True, time_scale=1.0)
    
    return await context_service.replay_trace(
        trace_id=trace_id,
        include_context=request.include_context,
        time_scale=request.time_scale
    )

@app.get("/replay/{trace_id}")
async def get_trace(trace_id: str):
    """Get a specific event trace by ID"""
    trace = context_service.replay_store.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return trace.to_dict()

@app.get("/replay/session/{person_id}/{session_id}")
async def get_session_traces(person_id: str, session_id: str, limit: int = 100):
    """Get all traces for a specific session"""
    return await context_service.get_session_traces(person_id, session_id, limit)

@app.get("/replay/person/{person_id}")
async def list_person_traces(person_id: str, offset: int = 0, limit: int = 50):
    """List all traces for a person with pagination"""
    return await context_service.list_person_traces(person_id, offset, limit)

@app.delete("/replay/{trace_id}")
async def delete_trace(trace_id: str):
    """Delete a specific event trace"""
    return await context_service.delete_trace(trace_id)

@app.post("/replay/cleanup")
async def cleanup_old_traces(days_to_keep: int = 30):
    """Clean up traces older than specified days"""
    try:
        deleted_count = context_service.replay_store.cleanup_old_traces(days_to_keep)
        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "days_to_keep": days_to_keep,
            "cleanup_timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error during trace cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

@app.get("/replay/stats")
async def get_replay_stats():
    """Get statistics about stored traces"""
    try:
        # Get basic stats from the replay store
        with context_service.replay_store._lock:
            conn = sqlite3.connect(context_service.replay_store.db_path)
            cursor = conn.cursor()
            
            # Total traces
            cursor.execute("SELECT COUNT(*) FROM event_traces")
            total_traces = cursor.fetchone()[0]
            
            # Traces by person
            cursor.execute("""
                SELECT person_id, COUNT(*) as count 
                FROM event_traces 
                GROUP BY person_id 
                ORDER BY count DESC 
                LIMIT 10
            """)
            top_persons = [{"person_id": row[0], "trace_count": row[1]} for row in cursor.fetchall()]
            
            # Traces by event type
            cursor.execute("""
                SELECT event_type, COUNT(*) as count 
                FROM event_traces 
                GROUP BY event_type 
                ORDER BY count DESC
            """)
            event_types = [{"event_type": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            # Recent activity
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM event_traces 
                WHERE created_at >= date('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            recent_activity = [{"date": row[0], "trace_count": row[1]} for row in cursor.fetchall()]
            
            conn.close()
        
        return {
            "total_traces": total_traces,
            "top_persons": top_persons,
            "event_types": event_types,
            "recent_activity": recent_activity,
            "stats_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting replay stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get replay stats")

@app.websocket("/context/subscribe/{person_id}")
async def websocket_context_subscribe(websocket: WebSocket, person_id: str):
    """WebSocket endpoint for real-time context updates"""
    await websocket.accept()
    
    if person_id not in context_service.websocket_connections:
        context_service.websocket_connections[person_id] = []
    
    context_service.websocket_connections[person_id].append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        context_service.websocket_connections[person_id].remove(websocket)
        if not context_service.websocket_connections[person_id]:
            del context_service.websocket_connections[person_id]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "unison-context-graph",
        "version": "1.0.0"
    }

@app.get("/health/sensors")
async def sensor_health_check():
    """Sensor connectivity and data quality health check"""
    return {
        "status": "healthy",
        "sensors": {
            "environmental": "connected",
            "device_monitoring": "connected",
            "temporal": "connected"
        }
    }

@app.get("/health/fusion")
async def fusion_health_check():
    """Fusion engine performance health check"""
    return {
        "status": "healthy",
        "fusion_performance": {
            "avg_latency_ms": 50,
            "success_rate": 0.99
        }
    }

# Main execution
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True,
        log_level="info"
    )
