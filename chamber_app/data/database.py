"""
Database management for persistent storage.
Handles SQLite database operations for chambers, telemetry, and work requests.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from contextlib import contextmanager

from ..utils import get_logger


class DatabaseManager:
    """
    Manages SQLite database operations for the chamber application.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Get database path
        db_path = config.get('DATABASE_PATH', 'data/chambers.db')
        if not Path(db_path).is_absolute():
            project_root = Path(config.get('PROJECT_ROOT', '.'))
            self.db_path = project_root / db_path
        else:
            self.db_path = Path(db_path)
          # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.connection: Optional[sqlite3.Connection] = None
        self.logger.info(f"Database manager initialized with path: {self.db_path}")
    
    def initialize(self):
        """Initialize database connection and create tables."""
        try:
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
              # Create tables
            self._create_tables()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    def _create_tables(self):
        """Create database tables."""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        
        # Chambers table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS chambers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Telemetry data table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamber_id TEXT NOT NULL,
                temperature REAL,
                vacuum_level REAL,
                humidity REAL,
                pressure REAL,
                elapsed_time REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chamber_id) REFERENCES chambers (id) ON DELETE CASCADE
            )
        """)
        
        # State transitions table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS state_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamber_id TEXT NOT NULL,
                transition_type TEXT NOT NULL,  -- 'state' or 'status'
                from_value TEXT,
                to_value TEXT NOT NULL,
                duration_seconds REAL,
                reason TEXT,
                user_name TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chamber_id) REFERENCES chambers (id) ON DELETE CASCADE
            )
        """)
        
        # Work requests table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS work_requests (
                id TEXT PRIMARY KEY,
                chamber_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                assigned_to TEXT,
                created_by TEXT,
                estimated_hours REAL DEFAULT 0,
                actual_hours REAL DEFAULT 0,
                data TEXT,  -- JSON data for notes and other fields
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (chamber_id) REFERENCES chambers (id) ON DELETE SET NULL
            )
        """)
        
        # Application settings table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Audit log table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                user_name TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
          # Create indexes for better performance
        self._create_indexes()
        
        self.connection.commit()
        self.logger.info("Database tables created/verified")
    
    def _create_indexes(self):
        """Create database indexes for performance."""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
            
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_telemetry_chamber_time ON telemetry (chamber_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_transitions_chamber_time ON state_transitions (chamber_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_work_requests_chamber ON work_requests (chamber_id)",
            "CREATE INDEX IF NOT EXISTS idx_work_requests_status ON work_requests (status)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_time ON audit_log (timestamp)",        ]
        
        for index_sql in indexes:
            self.connection.execute(index_sql)
    
    @contextmanager
    def get_cursor(self):
        """Get database cursor with automatic transaction management."""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
            
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()
    
    def save_chamber(self, chamber_data: Dict[str, Any]):
        """Save chamber data to database."""
        try:
            with self.get_cursor() as cursor:
                # Convert chamber data to JSON
                data_json = json.dumps(chamber_data)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO chambers (id, name, type, data, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    chamber_data['id'],
                    chamber_data['name'], 
                    chamber_data['type'],
                    data_json
                ))
                
                self._log_audit_action(
                    "chamber_saved",
                    "chamber",
                    chamber_data['id'],
                    chamber_data['name']
                )
                
        except Exception as e:
            self.logger.error(f"Failed to save chamber {chamber_data.get('id')}: {e}", exc_info=True)
            raise
    
    def get_chamber(self, chamber_id: str) -> Optional[Dict[str, Any]]:
        """Get chamber data by ID."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    "SELECT data FROM chambers WHERE id = ?",
                    (chamber_id,)
                )
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get chamber {chamber_id}: {e}", exc_info=True)
            return None
    
    def get_all_chambers(self) -> List[Dict[str, Any]]:
        """Get all chambers from database."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT data FROM chambers ORDER BY name")
                
                chambers = []
                for row in cursor.fetchall():
                    chambers.append(json.loads(row[0]))
                
                return chambers
                
        except Exception as e:
            self.logger.error(f"Failed to get all chambers: {e}", exc_info=True)
            return []
    
    def delete_chamber(self, chamber_id: str):
        """Delete chamber from database."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("DELETE FROM chambers WHERE id = ?", (chamber_id,))
                
                self._log_audit_action(
                    "chamber_deleted",
                    "chamber", 
                    chamber_id
                )
                
        except Exception as e:
            self.logger.error(f"Failed to delete chamber {chamber_id}: {e}", exc_info=True)
            raise
    
    def save_telemetry(self, chamber_id: str, temperature: float, vacuum_level: float, 
                      humidity: float, pressure: float, elapsed_time: float):
        """Save telemetry data to database."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO telemetry 
                    (chamber_id, temperature, vacuum_level, humidity, pressure, elapsed_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (chamber_id, temperature, vacuum_level, humidity, pressure, elapsed_time))
                
        except Exception as e:
            self.logger.error(f"Failed to save telemetry for chamber {chamber_id}: {e}")
            # Don't raise for telemetry errors to avoid disrupting main flow
    
    def get_telemetry_history(self, chamber_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get telemetry history for a chamber."""
        try:
            since_time = datetime.now() - timedelta(hours=hours)
            
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT temperature, vacuum_level, humidity, pressure, 
                           elapsed_time, timestamp
                    FROM telemetry 
                    WHERE chamber_id = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                """, (chamber_id, since_time))
                
                telemetry = []
                for row in cursor.fetchall():
                    telemetry.append({
                        'temperature': row[0],
                        'vacuum_level': row[1],
                        'humidity': row[2],
                        'pressure': row[3],
                        'elapsed_time': row[4],
                        'timestamp': row[5]
                    })
                
                return telemetry
                
        except Exception as e:
            self.logger.error(f"Failed to get telemetry history for chamber {chamber_id}: {e}")
            return []
    
    def save_state_transition(self, chamber_id: str, transition_type: str, 
                            from_value: str, to_value: str, duration_seconds: float,
                            reason: str = "", user_name: str = ""):
        """Save state transition to database."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO state_transitions 
                    (chamber_id, transition_type, from_value, to_value, 
                     duration_seconds, reason, user_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)                """, (chamber_id, transition_type, from_value, to_value, 
                      duration_seconds, reason, user_name))
                
                self._log_audit_action(
                    f"{transition_type}_transition",
                    "chamber",
                    chamber_id,
                    f"{from_value} -> {to_value}"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to save state transition: {e}")
    
    async def cleanup_old_telemetry(self, retention_days: int):
        """Clean up old telemetry data."""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with self.get_cursor() as cursor:
                cursor.execute(
                    "DELETE FROM telemetry WHERE timestamp < ?",
                    (cutoff_date,)
                )
                
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old telemetry records")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old telemetry: {e}")
    
    def _log_audit_action(self, action: str, entity_type: Optional[str] = None, 
                         entity_id: Optional[str] = None, details: Optional[str] = None):
        """Log an action to the audit trail."""
        if not self.config.get('ENABLE_AUDIT_LOG', True):
            return
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO audit_log (action, entity_type, entity_id, details)
                    VALUES (?, ?, ?, ?)
                """, (action, entity_type, entity_id, details))
                
        except Exception as e:
            self.logger.error(f"Failed to log audit action: {e}")
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT action, entity_type, entity_id, details, timestamp
                    FROM audit_log 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                entries = []
                for row in cursor.fetchall():
                    entries.append({
                        'action': row[0],
                        'entity_type': row[1],
                        'entity_id': row[2],
                        'details': row[3],
                        'timestamp': row[4]                })
                
                return entries
                
        except Exception as e:
            self.logger.error(f"Failed to get audit log: {e}")
            return []
    
    def backup_database(self, backup_path: Optional[str] = None):
        """Create a backup of the database."""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
            
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.db_path.stem}_backup_{timestamp}.db"
            
            backup_path_obj = Path(backup_path)
            
            # Create backup directory if needed
            backup_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy database
            with sqlite3.connect(str(backup_path_obj)) as backup_conn:
                self.connection.backup(backup_conn)
            
            self.logger.info(f"Database backed up to: {backup_path_obj}")
            return str(backup_path_obj)
            
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}", exc_info=True)
            raise
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Database connection closed")
