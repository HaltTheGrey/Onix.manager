# -*- coding: utf-8 -*-
"""
Data export/import utilities for the Chamber Management Application.
Provides functionality to export/import chamber data, configurations, and telemetry.
"""

import json
import csv
import sqlite3
import zipfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd

from .logging_config import get_logger
from .config import get_database_path


class DataExporter:
    """
    Handles exporting chamber data in various formats.
    """
      def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    def export_chamber_data(self, chamber_id: Optional[str] = None, 
                          date_range: Optional[tuple] = None, 
                          format: str = 'json',
                          output_path: Optional[str] = None) -> str:
        """
        Export chamber data to specified format.
        
        Args:
            chamber_id: Specific chamber ID or None for all chambers
            date_range: Tuple of (start_date, end_date) or None for all data
            format: Export format ('json', 'csv', 'excel', 'zip')
            output_path: Output file path or None for auto-generated
            
        Returns:
            Path to exported file
        """
        try:
            # Get data
            data = self._get_chamber_data(chamber_id, date_range)
            
            # Generate output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                chamber_suffix = f"_{chamber_id}" if chamber_id else "_all"
                output_path = f"chamber_export{chamber_suffix}_{timestamp}.{format}"
            
            # Export based on format
            if format == 'json':
                return self._export_json(data, output_path)
            elif format == 'csv':
                return self._export_csv(data, output_path)
            elif format == 'excel':
                return self._export_excel(data, output_path)
            elif format == 'zip':
                return self._export_zip(data, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise
    
    def export_configuration(self, output_path: Optional[str] = None) -> str:
        """Export complete application configuration."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if not output_path:
                output_path = f"chamber_config_backup_{timestamp}.json"
            
            config_data = {
                'app_config': self.app.config,
                'chambers': [],
                'work_requests': [],
                'export_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'version': self.app.config.get('APP_VERSION', '1.0.0'),
                    'export_type': 'configuration'
                }
            }
            
            # Get chamber configurations
            for chamber in self.app.get_all_chambers():
                config_data['chambers'].append({
                    'id': chamber.id,
                    'name': chamber.name,
                    'type': chamber.type.value,
                    'status': chamber.status.value,
                    'configuration': chamber.configuration,
                    'created_at': chamber.created_at.isoformat() if chamber.created_at else None
                })
            
            # Get work requests
            try:
                work_requests = self.app.get_all_work_requests()
                for wr in work_requests:
                    config_data['work_requests'].append({
                        'id': wr.id,
                        'title': wr.title,
                        'description': wr.description,
                        'chamber_id': wr.chamber_id,
                        'priority': wr.priority.value,
                        'status': wr.status.value,
                        'created_at': wr.created_at.isoformat() if wr.created_at else None,
                        'assigned_to': wr.assigned_to
                    })
            except:
                pass  # Work requests might not be implemented yet
            
            with open(output_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            self.logger.info(f"Configuration exported to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Configuration export failed: {e}")
            raise
      def export_telemetry_data(self, chamber_id: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            format: str = 'csv',
                            output_path: Optional[str] = None) -> str:
        """Export telemetry data for analysis."""
        try:
            # Default to last 30 days if no date range specified
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Get telemetry data from database
            db_path = get_database_path(self.app.config)
            with sqlite3.connect(db_path) as conn:
                query = """
                SELECT chamber_id, timestamp, temperature, pressure, humidity, 
                       vacuum_level, status, metadata
                FROM telemetry_data 
                WHERE timestamp BETWEEN ? AND ?
                """
                params = [start_date.isoformat(), end_date.isoformat()]
                
                if chamber_id:
                    query += " AND chamber_id = ?"
                    params.append(chamber_id)
                
                query += " ORDER BY timestamp"
                
                df = pd.read_sql_query(query, conn, params=params)
            
            # Generate output path
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                chamber_suffix = f"_{chamber_id}" if chamber_id else "_all"
                output_path = f"telemetry_data{chamber_suffix}_{timestamp}.{format}"
            
            # Export based on format
            if format == 'csv':
                df.to_csv(output_path, index=False)
            elif format == 'excel':
                df.to_excel(output_path, index=False)
            elif format == 'json':
                df.to_json(output_path, orient='records', date_format='iso')
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Telemetry data exported to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Telemetry export failed: {e}")
            raise
      def _get_chamber_data(self, chamber_id: Optional[str] = None, 
                         date_range: Optional[tuple] = None) -> Dict[str, Any]:
        """Get chamber data for export."""
        data = {
            'chambers': [],
            'telemetry': [],
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'chamber_id': chamber_id,
                'date_range': date_range,
                'version': self.app.config.get('APP_VERSION', '1.0.0')
            }
        }
        
        # Get chambers
        if chamber_id:
            chamber = self.app.get_chamber(chamber_id)
            if chamber:
                data['chambers'].append(self._chamber_to_dict(chamber))
        else:
            for chamber in self.app.get_all_chambers():
                data['chambers'].append(self._chamber_to_dict(chamber))
        
        # Get telemetry data
        # This would be implemented based on the actual telemetry storage
        try:
            db_path = get_database_path(self.app.config)
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM telemetry_data"
                params = []
                
                if chamber_id:
                    query += " WHERE chamber_id = ?"
                    params.append(chamber_id)
                
                if date_range:
                    start_date, end_date = date_range
                    if chamber_id:
                        query += " AND timestamp BETWEEN ? AND ?"
                    else:
                        query += " WHERE timestamp BETWEEN ? AND ?"
                    params.extend([start_date.isoformat(), end_date.isoformat()])
                
                cursor.execute(query, params)
                telemetry_rows = cursor.fetchall()
                
                # Convert to dict format
                columns = [desc[0] for desc in cursor.description]
                for row in telemetry_rows:
                    data['telemetry'].append(dict(zip(columns, row)))
        except Exception as e:
            self.logger.warning(f"Could not fetch telemetry data: {e}")
        
        return data
    
    def _chamber_to_dict(self, chamber) -> Dict[str, Any]:
        """Convert chamber object to dictionary."""
        return {
            'id': chamber.id,
            'name': chamber.name,
            'type': chamber.type.value,
            'status': chamber.status.value,
            'state': chamber.state.__dict__ if hasattr(chamber, 'state') else {},
            'configuration': chamber.configuration,
            'created_at': chamber.created_at.isoformat() if chamber.created_at else None,
            'last_updated': chamber.last_updated.isoformat() if hasattr(chamber, 'last_updated') and chamber.last_updated else None
        }
    
    def _export_json(self, data: Dict[str, Any], output_path: str) -> str:
        """Export data as JSON."""
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return output_path
    
    def _export_csv(self, data: Dict[str, Any], output_path: str) -> str:
        """Export data as CSV."""
        # Create separate CSV files for chambers and telemetry
        base_path = Path(output_path).stem
        base_dir = Path(output_path).parent
        
        # Export chambers
        if data['chambers']:
            chambers_path = base_dir / f"{base_path}_chambers.csv"
            df_chambers = pd.DataFrame(data['chambers'])
            df_chambers.to_csv(chambers_path, index=False)
        
        # Export telemetry
        if data['telemetry']:
            telemetry_path = base_dir / f"{base_path}_telemetry.csv"
            df_telemetry = pd.DataFrame(data['telemetry'])
            df_telemetry.to_csv(telemetry_path, index=False)
        
        return output_path
    
    def _export_excel(self, data: Dict[str, Any], output_path: str) -> str:
        """Export data as Excel with multiple sheets."""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Chambers sheet
            if data['chambers']:
                df_chambers = pd.DataFrame(data['chambers'])
                df_chambers.to_excel(writer, sheet_name='Chambers', index=False)
            
            # Telemetry sheet
            if data['telemetry']:
                df_telemetry = pd.DataFrame(data['telemetry'])
                df_telemetry.to_excel(writer, sheet_name='Telemetry', index=False)
            
            # Metadata sheet
            df_metadata = pd.DataFrame([data['metadata']])
            df_metadata.to_excel(writer, sheet_name='Metadata', index=False)
        
        return output_path
    
    def _export_zip(self, data: Dict[str, Any], output_path: str) -> str:
        """Export data as ZIP archive with multiple formats."""
        base_path = Path(output_path).stem
        temp_dir = Path(f"temp_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Create files in temporary directory
            json_file = temp_dir / f"{base_path}.json"
            self._export_json(data, str(json_file))
            
            if data['chambers']:
                chambers_csv = temp_dir / f"{base_path}_chambers.csv"
                df_chambers = pd.DataFrame(data['chambers'])
                df_chambers.to_csv(chambers_csv, index=False)
            
            if data['telemetry']:
                telemetry_csv = temp_dir / f"{base_path}_telemetry.csv"
                df_telemetry = pd.DataFrame(data['telemetry'])
                df_telemetry.to_csv(telemetry_csv, index=False)
            
            # Create ZIP archive
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_dir.glob('*'):
                    zipf.write(file_path, file_path.name)
            
            return output_path
            
        finally:
            # Cleanup temporary directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class DataImporter:
    """
    Handles importing chamber data from various formats.
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    def import_configuration(self, file_path: str, 
                           merge: bool = False,
                           backup_current: bool = True) -> Dict[str, Any]:
        """
        Import configuration from JSON file.
        
        Args:
            file_path: Path to configuration file
            merge: Whether to merge with current config or replace
            backup_current: Whether to backup current config before import
            
        Returns:
            Import summary
        """
        try:
            if backup_current:
                # Create backup of current configuration
                exporter = DataExporter(self.app)
                backup_path = exporter.export_configuration()
                self.logger.info(f"Current configuration backed up to {backup_path}")
            
            # Load import data
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            summary = {
                'chambers_imported': 0,
                'chambers_updated': 0,
                'work_requests_imported': 0,
                'config_updated': False,
                'errors': []
            }
            
            # Import chambers
            if 'chambers' in import_data:
                for chamber_data in import_data['chambers']:
                    try:
                        self._import_chamber(chamber_data, merge)
                        if merge and self.app.get_chamber(chamber_data['id']):
                            summary['chambers_updated'] += 1
                        else:
                            summary['chambers_imported'] += 1
                    except Exception as e:
                        error_msg = f"Failed to import chamber {chamber_data.get('id', 'unknown')}: {e}"
                        summary['errors'].append(error_msg)
                        self.logger.error(error_msg)
            
            # Import work requests
            if 'work_requests' in import_data:
                for wr_data in import_data['work_requests']:
                    try:
                        self._import_work_request(wr_data, merge)
                        summary['work_requests_imported'] += 1
                    except Exception as e:
                        error_msg = f"Failed to import work request {wr_data.get('id', 'unknown')}: {e}"
                        summary['errors'].append(error_msg)
                        self.logger.error(error_msg)
            
            # Import app configuration (carefully)
            if 'app_config' in import_data and not merge:
                try:
                    # Only import safe configuration keys
                    safe_keys = [
                        'UI_THEME', 'WINDOW_WIDTH', 'WINDOW_HEIGHT', 
                        'AUTO_REFRESH_INTERVAL', 'DEFAULT_CHAMBER_TYPES',
                        'MAX_CHAMBERS_PER_TYPE', 'TELEMETRY_RETENTION_DAYS'
                    ]
                    for key in safe_keys:
                        if key in import_data['app_config']:
                            self.app.config[key] = import_data['app_config'][key]
                    summary['config_updated'] = True
                except Exception as e:
                    error_msg = f"Failed to import app configuration: {e}"
                    summary['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            self.logger.info(f"Configuration import completed: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Configuration import failed: {e}")
            raise
    
    def import_telemetry_data(self, file_path: str, 
                            format: str = 'auto') -> Dict[str, Any]:
        """Import telemetry data from file."""
        try:
            # Auto-detect format if not specified
            if format == 'auto':
                ext = Path(file_path).suffix.lower()
                if ext == '.csv':
                    format = 'csv'
                elif ext in ['.xlsx', '.xls']:
                    format = 'excel'
                elif ext == '.json':
                    format = 'json'
                else:
                    raise ValueError(f"Cannot auto-detect format for {ext}")
            
            # Load data based on format
            if format == 'csv':
                df = pd.read_csv(file_path)
            elif format == 'excel':
                df = pd.read_excel(file_path)
            elif format == 'json':
                df = pd.read_json(file_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Validate required columns
            required_columns = ['chamber_id', 'timestamp']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Import to database
            db_path = get_database_path(self.app.config)
            imported_count = 0
            
            with sqlite3.connect(db_path) as conn:
                for _, row in df.iterrows():
                    try:
                        # Insert telemetry record
                        conn.execute("""
                            INSERT OR REPLACE INTO telemetry_data 
                            (chamber_id, timestamp, temperature, pressure, humidity, 
                             vacuum_level, status, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row.get('chamber_id'),
                            row.get('timestamp'),
                            row.get('temperature'),
                            row.get('pressure'),
                            row.get('humidity'),
                            row.get('vacuum_level'),
                            row.get('status'),
                            row.get('metadata', '{}')
                        ))
                        imported_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to import telemetry row: {e}")
                
                conn.commit()
            
            summary = {
                'records_imported': imported_count,
                'total_records': len(df),
                'file_path': file_path
            }
            
            self.logger.info(f"Telemetry import completed: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Telemetry import failed: {e}")
            raise
    
    def _import_chamber(self, chamber_data: Dict[str, Any], merge: bool = False):
        """Import a single chamber."""
        from ..core.chamber_state import ChamberType, ChamberStatus
        
        # Check if chamber exists
        existing_chamber = self.app.get_chamber(chamber_data['id'])
        
        if existing_chamber and not merge:
            raise ValueError(f"Chamber {chamber_data['id']} already exists")
        
        if not existing_chamber:
            # Create new chamber
            chamber_type = ChamberType(chamber_data['type'])
            new_chamber = self.app.add_chamber(
                chamber_data['name'], 
                chamber_type, 
                chamber_id=chamber_data['id']
            )
            
            # Set additional properties
            if 'configuration' in chamber_data:
                new_chamber.configuration.update(chamber_data['configuration'])
            
            if 'status' in chamber_data:
                new_chamber.status = ChamberStatus(chamber_data['status'])
        else:
            # Update existing chamber
            if 'name' in chamber_data:
                existing_chamber.name = chamber_data['name']
            
            if 'configuration' in chamber_data:
                existing_chamber.configuration.update(chamber_data['configuration'])
            
            if 'status' in chamber_data:
                existing_chamber.status = ChamberStatus(chamber_data['status'])
    
    def _import_work_request(self, wr_data: Dict[str, Any], merge: bool = False):
        """Import a single work request."""
        # This would be implemented based on the actual work request system
        # For now, just log that we would import it
        self.logger.info(f"Would import work request: {wr_data.get('title', 'Unknown')}")
