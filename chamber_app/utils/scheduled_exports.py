# -*- coding: utf-8 -*-
"""
Scheduled export system for the Chamber Management Application.
Provides automated data export capabilities on schedules.
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import json

from .logging_config import get_logger
from .data_export import DataExporter
from .report_generator import ReportGenerator


class ScheduledExportManager:
    """
    Manages scheduled data exports and report generation.
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        self.data_exporter = DataExporter(app)
        self.report_generator = ReportGenerator(app)
        
        self.scheduled_jobs = []
        self.running = False
        self.worker_thread = None
        
        self._load_scheduled_exports()
    
    def start(self):
        """Start the scheduled export manager."""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.logger.info("Scheduled export manager started")
    
    def stop(self):
        """Stop the scheduled export manager."""
        self.running = False
        self._save_scheduled_exports()
        self.logger.info("Scheduled export manager stopped")
    
    def schedule_daily_export(self, 
                            export_type: str = 'chamber_data',
                            time_str: str = '23:00',
                            format: str = 'json',
                            retention_days: int = 30,
                            enabled: bool = True) -> str:
        """
        Schedule a daily export.
        
        Args:
            export_type: Type of export ('chamber_data', 'telemetry', 'work_requests', 'report')
            time_str: Time to run export (HH:MM format)
            format: Export format
            retention_days: Days to retain old exports
            enabled: Whether the schedule is enabled
            
        Returns:
            Job ID
        """
        job_id = f"daily_{export_type}_{datetime.now().timestamp()}"
        
        job_config = {
            'id': job_id,
            'type': 'daily',
            'export_type': export_type,
            'time': time_str,
            'format': format,
            'retention_days': retention_days,
            'enabled': enabled,
            'created_at': datetime.now().isoformat(),
            'last_run': None,
            'next_run': None
        }
        
        self.scheduled_jobs.append(job_config)
        self._schedule_job(job_config)
        
        self.logger.info(f"Scheduled daily {export_type} export at {time_str}")
        return job_id
    
    def schedule_weekly_export(self,
                             export_type: str = 'chamber_data', 
                             day_of_week: str = 'sunday',
                             time_str: str = '23:00',
                             format: str = 'json',
                             retention_days: int = 90,
                             enabled: bool = True) -> str:
        """
        Schedule a weekly export.
        
        Args:
            export_type: Type of export
            day_of_week: Day to run export (monday, tuesday, etc.)
            time_str: Time to run export
            format: Export format
            retention_days: Days to retain old exports
            enabled: Whether the schedule is enabled
            
        Returns:
            Job ID
        """
        job_id = f"weekly_{export_type}_{datetime.now().timestamp()}"
        
        job_config = {
            'id': job_id,
            'type': 'weekly',
            'export_type': export_type,
            'day_of_week': day_of_week.lower(),
            'time': time_str,
            'format': format,
            'retention_days': retention_days,
            'enabled': enabled,
            'created_at': datetime.now().isoformat(),
            'last_run': None,
            'next_run': None
        }
        
        self.scheduled_jobs.append(job_config)
        self._schedule_job(job_config)
        
        self.logger.info(f"Scheduled weekly {export_type} export on {day_of_week} at {time_str}")
        return job_id
    
    def schedule_monthly_export(self,
                              export_type: str = 'report',
                              day_of_month: int = 1,
                              time_str: str = '23:00',
                              format: str = 'pdf',
                              retention_days: int = 365,
                              enabled: bool = True) -> str:
        """
        Schedule a monthly export.
        
        Args:
            export_type: Type of export
            day_of_month: Day of month to run (1-28)
            time_str: Time to run export
            format: Export format
            retention_days: Days to retain old exports
            enabled: Whether the schedule is enabled
            
        Returns:
            Job ID
        """
        job_id = f"monthly_{export_type}_{datetime.now().timestamp()}"
        
        job_config = {
            'id': job_id,
            'type': 'monthly',
            'export_type': export_type,
            'day_of_month': min(max(day_of_month, 1), 28),  # Clamp to safe range
            'time': time_str,
            'format': format,
            'retention_days': retention_days,
            'enabled': enabled,
            'created_at': datetime.now().isoformat(),
            'last_run': None,
            'next_run': None
        }
        
        self.scheduled_jobs.append(job_config)
        self._schedule_job(job_config)
        
        self.logger.info(f"Scheduled monthly {export_type} export on day {day_of_month} at {time_str}")
        return job_id
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get all scheduled jobs."""
        return self.scheduled_jobs.copy()
    
    def enable_job(self, job_id: str) -> bool:
        """Enable a scheduled job."""
        for job in self.scheduled_jobs:
            if job['id'] == job_id:
                job['enabled'] = True
                self._schedule_job(job)
                self.logger.info(f"Enabled scheduled job: {job_id}")
                return True
        return False
    
    def disable_job(self, job_id: str) -> bool:
        """Disable a scheduled job."""
        for job in self.scheduled_jobs:
            if job['id'] == job_id:
                job['enabled'] = False
                self._unschedule_job(job_id)
                self.logger.info(f"Disabled scheduled job: {job_id}")
                return True
        return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        for i, job in enumerate(self.scheduled_jobs):
            if job['id'] == job_id:
                self._unschedule_job(job_id)
                del self.scheduled_jobs[i]
                self.logger.info(f"Removed scheduled job: {job_id}")
                return True
        return False
    
    def run_job_now(self, job_id: str) -> bool:
        """Run a scheduled job immediately."""
        for job in self.scheduled_jobs:
            if job['id'] == job_id:
                self._execute_job(job)
                return True
        return False
    
    def _schedule_job(self, job_config: Dict[str, Any]):
        """Schedule a job with the schedule library."""
        if not job_config['enabled']:
            return
        
        job_id = job_config['id']
        export_type = job_config['export_type']
        time_str = job_config['time']
        
        # Clear existing schedule for this job
        self._unschedule_job(job_id)
        
        # Create job function
        job_func = lambda: self._execute_job(job_config)
        job_func.__name__ = f"export_job_{job_id}"
        
        # Schedule based on type
        if job_config['type'] == 'daily':
            schedule.every().day.at(time_str).do(job_func).tag(job_id)
        elif job_config['type'] == 'weekly':
            day_of_week = job_config['day_of_week']
            getattr(schedule.every(), day_of_week).at(time_str).do(job_func).tag(job_id)
        elif job_config['type'] == 'monthly':
            # Monthly scheduling requires custom logic
            schedule.every().day.at(time_str).do(self._check_monthly_job, job_config).tag(f"{job_id}_check")
        
        # Update next run time
        self._update_next_run_time(job_config)
    
    def _unschedule_job(self, job_id: str):
        """Remove a job from the schedule."""
        schedule.clear(job_id)
        schedule.clear(f"{job_id}_check")
    
    def _check_monthly_job(self, job_config: Dict[str, Any]):
        """Check if monthly job should run today."""
        today = datetime.now()
        if today.day == job_config['day_of_month']:
            self._execute_job(job_config)
    
    def _execute_job(self, job_config: Dict[str, Any]):
        """Execute a scheduled export job."""
        try:
            export_type = job_config['export_type']
            format = job_config['format']
            
            self.logger.info(f"Executing scheduled export: {job_config['id']}")
            
            # Determine date range for export
            now = datetime.now()
            if job_config['type'] == 'daily':
                start_date = now - timedelta(days=1)
            elif job_config['type'] == 'weekly':
                start_date = now - timedelta(days=7)
            elif job_config['type'] == 'monthly':
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=1)
            
            date_range = (start_date, now)
            
            # Execute export based on type
            output_path = None
            
            if export_type == 'chamber_data':
                output_path = self.data_exporter.export_chamber_data(
                    date_range=date_range,
                    format=format
                )
            elif export_type == 'telemetry':
                # Export telemetry for all chambers
                chambers = self.app.get_chambers()
                for chamber in chambers:
                    try:
                        path = self.data_exporter.export_telemetry_data(
                            chamber.id,
                            date_range=date_range,
                            format=format
                        )
                        if not output_path:
                            output_path = path
                    except Exception as e:
                        self.logger.error(f"Error exporting telemetry for {chamber.id}: {e}")
            
            elif export_type == 'work_requests':
                output_path = self.report_generator.generate_work_requests_report(
                    date_range=date_range,
                    format=format
                )
            elif export_type == 'report':
                if format == 'pdf':
                    output_path = self.report_generator.generate_chamber_status_report(
                        date_range=date_range,
                        format=format
                    )
                else:
                    output_path = self.data_exporter.export_chamber_data(
                        date_range=date_range,
                        format=format
                    )
            
            # Update job status
            job_config['last_run'] = now.isoformat()
            self._update_next_run_time(job_config)
            
            # Clean up old exports
            self._cleanup_old_exports(job_config)
            
            if output_path:
                self.logger.info(f"Scheduled export completed: {output_path}")
            else:
                self.logger.warning(f"Scheduled export completed but no output file generated")
                
        except Exception as e:
            self.logger.error(f"Error executing scheduled export {job_config['id']}: {e}")
    
    def _update_next_run_time(self, job_config: Dict[str, Any]):
        """Update the next run time for a job."""
        try:
            # Get next scheduled run from schedule library
            jobs = schedule.get_jobs(job_config['id'])
            if jobs:
                next_run = jobs[0].next_run
                job_config['next_run'] = next_run.isoformat() if next_run else None
            else:
                # Calculate next run manually for monthly jobs
                if job_config['type'] == 'monthly':
                    now = datetime.now()
                    target_day = job_config['day_of_month']
                    time_parts = job_config['time'].split(':')
                    target_hour = int(time_parts[0])
                    target_minute = int(time_parts[1])
                    
                    # Find next occurrence
                    if now.day <= target_day:
                        # This month
                        next_run = now.replace(day=target_day, hour=target_hour, minute=target_minute, second=0, microsecond=0)
                        if next_run <= now:
                            # Next month
                            if now.month == 12:
                                next_run = next_run.replace(year=now.year + 1, month=1)
                            else:
                                next_run = next_run.replace(month=now.month + 1)
                    else:
                        # Next month
                        if now.month == 12:
                            next_run = now.replace(year=now.year + 1, month=1, day=target_day, hour=target_hour, minute=target_minute, second=0, microsecond=0)
                        else:
                            next_run = now.replace(month=now.month + 1, day=target_day, hour=target_hour, minute=target_minute, second=0, microsecond=0)
                    
                    job_config['next_run'] = next_run.isoformat()
        except Exception as e:
            self.logger.error(f"Error updating next run time for {job_config['id']}: {e}")
    
    def _cleanup_old_exports(self, job_config: Dict[str, Any]):
        """Clean up old export files based on retention policy."""
        try:
            retention_days = job_config.get('retention_days', 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            export_dirs = [
                Path("exports"),
                Path("reports"),
                Path("data")
            ]
            
            deleted_count = 0
            for export_dir in export_dirs:
                if export_dir.exists():
                    for file_path in export_dir.glob("*"):
                        if file_path.is_file():
                            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_time < cutoff_date:
                                try:
                                    file_path.unlink()
                                    deleted_count += 1
                                except Exception as e:
                                    self.logger.error(f"Error deleting old export file {file_path}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old export files")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old exports: {e}")
    
    def _worker_loop(self):
        """Main worker loop for scheduled exports."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in scheduled export worker loop: {e}")
                time.sleep(60)
    
    def _load_scheduled_exports(self):
        """Load scheduled exports from configuration."""
        config_file = Path("data/scheduled_exports.json")
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    saved_jobs = json.load(f)
                
                for job_config in saved_jobs:
                    self.scheduled_jobs.append(job_config)
                    self._schedule_job(job_config)
                
                self.logger.info(f"Loaded {len(saved_jobs)} scheduled export jobs")
                
            except Exception as e:
                self.logger.error(f"Error loading scheduled exports: {e}")
    
    def _save_scheduled_exports(self):
        """Save scheduled exports to configuration."""
        try:
            config_file = Path("data/scheduled_exports.json")
            config_file.parent.mkdir(exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_jobs, f, indent=2, default=str)
            
            self.logger.info("Saved scheduled export configuration")
            
        except Exception as e:
            self.logger.error(f"Error saving scheduled exports: {e}")


class APIEndpointManager:
    """
    Manages REST API endpoints for external integrations.
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        self.api_server = None
        self.port = 8080
        
        # API endpoint handlers
        self.handlers = {
            '/api/chambers': self._handle_chambers,
            '/api/chambers/{chamber_id}': self._handle_chamber_detail,
            '/api/chambers/{chamber_id}/state': self._handle_chamber_state,
            '/api/chambers/{chamber_id}/status': self._handle_chamber_status,
            '/api/chambers/{chamber_id}/telemetry': self._handle_chamber_telemetry,
            '/api/chambers/{chamber_id}/work_requests': self._handle_work_requests,
            '/api/work_requests': self._handle_all_work_requests,
            '/api/export/chambers': self._handle_export_chambers,
            '/api/export/telemetry/{chamber_id}': self._handle_export_telemetry,
            '/api/reports/status': self._handle_status_report,
            '/api/reports/utilization': self._handle_utilization_report,
            '/api/health': self._handle_health_check
        }
    
    def start_api_server(self, port: int = 8080):
        """Start the API server."""
        try:
            from flask import Flask, request, jsonify
            from flask_cors import CORS
            
            self.port = port
            app = Flask(__name__)
            CORS(app)  # Enable CORS for all routes
            
            # Register routes
            for endpoint, handler in self.handlers.items():
                # Convert {param} to <param> for Flask
                flask_endpoint = endpoint.replace('{', '<').replace('}', '>')
                app.add_url_rule(flask_endpoint, endpoint=endpoint, view_func=handler, methods=['GET', 'POST', 'PUT', 'DELETE'])
            
            # Start server in background thread
            def run_server():
                app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
            
            import threading
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            self.logger.info(f"API server started on port {port}")
            return True
            
        except ImportError:
            self.logger.error("Flask not available - cannot start API server")
            return False
        except Exception as e:
            self.logger.error(f"Error starting API server: {e}")
            return False
    
    def _handle_chambers(self):
        """Handle chambers endpoint."""
        from flask import request, jsonify
        
        if request.method == 'GET':
            chambers = self.app.get_chambers()
            chamber_data = []
            
            for chamber in chambers:
                data = {
                    'id': chamber.id,
                    'name': chamber.name,
                    'type': chamber.chamber_type.value,
                    'state': chamber.state_manager.current_state.value,
                    'status': chamber.state_manager.current_status.value,
                    'is_connected': chamber.is_connected,
                    'last_update': chamber.last_update.isoformat() if chamber.last_update else None,
                    'work_requests_count': len(chamber.work_requests)
                }
                
                # Add latest telemetry if available
                if chamber.latest_telemetry:
                    data['telemetry'] = {
                        'temperature': chamber.latest_telemetry.temperature,
                        'pressure': chamber.latest_telemetry.pressure,
                        'humidity': chamber.latest_telemetry.humidity,
                        'vacuum_level': chamber.latest_telemetry.vacuum_level,
                        'timestamp': chamber.latest_telemetry.timestamp.isoformat()
                    }
                
                chamber_data.append(data)
            
            return jsonify({
                'chambers': chamber_data,
                'count': len(chamber_data)
            })
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_chamber_detail(self, chamber_id: str):
        """Handle individual chamber endpoint."""
        from flask import request, jsonify
        
        chamber = self.app.get_chamber(chamber_id)
        if not chamber:
            return jsonify({'error': 'Chamber not found'}), 404
        
        if request.method == 'GET':
            data = {
                'id': chamber.id,
                'name': chamber.name,
                'type': chamber.chamber_type.value,
                'state': chamber.state_manager.current_state.value,
                'status': chamber.state_manager.current_status.value,
                'is_connected': chamber.is_connected,
                'last_update': chamber.last_update.isoformat() if chamber.last_update else None,
                'created_at': chamber.created_at.isoformat(),
                'work_requests': []
            }
            
            # Add work requests
            for wr in chamber.work_requests:
                wr_data = {
                    'id': wr.id,
                    'title': wr.title,
                    'description': wr.description,
                    'status': wr.status,
                    'priority': wr.priority,
                    'created_at': wr.created_at.isoformat(),
                    'assigned_to': wr.assigned_to,
                    'estimated_hours': wr.estimated_hours
                }
                data['work_requests'].append(wr_data)
            
            # Add latest telemetry
            if chamber.latest_telemetry:
                data['telemetry'] = {
                    'temperature': chamber.latest_telemetry.temperature,
                    'pressure': chamber.latest_telemetry.pressure,
                    'humidity': chamber.latest_telemetry.humidity,
                    'vacuum_level': chamber.latest_telemetry.vacuum_level,
                    'elapsed_time': chamber.latest_telemetry.elapsed_time,
                    'timestamp': chamber.latest_telemetry.timestamp.isoformat()
                }
            
            return jsonify(data)
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_chamber_state(self, chamber_id: str):
        """Handle chamber state endpoint."""
        from flask import request, jsonify
        
        chamber = self.app.get_chamber(chamber_id)
        if not chamber:
            return jsonify({'error': 'Chamber not found'}), 404
        
        if request.method == 'GET':
            return jsonify({
                'chamber_id': chamber_id,
                'state': chamber.state_manager.current_state.value,
                'timestamp': chamber.state_manager.last_state_change.isoformat() if chamber.state_manager.last_state_change else None
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            if not data or 'state' not in data:
                return jsonify({'error': 'State required'}), 400
            
            try:
                from ..core.chamber_state import ChamberState
                new_state = ChamberState(data['state'])
                reason = data.get('reason', 'API update')
                
                success = self.app.update_chamber_state(chamber_id, new_state, reason)
                if success:
                    return jsonify({
                        'success': True,
                        'chamber_id': chamber_id,
                        'new_state': new_state.value
                    })
                else:
                    return jsonify({'error': 'Failed to update state'}), 500
                    
            except ValueError as e:
                return jsonify({'error': f'Invalid state: {e}'}), 400
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_chamber_status(self, chamber_id: str):
        """Handle chamber status endpoint."""
        from flask import request, jsonify
        
        chamber = self.app.get_chamber(chamber_id)
        if not chamber:
            return jsonify({'error': 'Chamber not found'}), 404
        
        if request.method == 'GET':
            return jsonify({
                'chamber_id': chamber_id,
                'status': chamber.state_manager.current_status.value,
                'timestamp': chamber.state_manager.last_status_change.isoformat() if chamber.state_manager.last_status_change else None
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            if not data or 'status' not in data:
                return jsonify({'error': 'Status required'}), 400
            
            try:
                from ..core.chamber_state import ChamberStatus
                new_status = ChamberStatus(data['status'])
                reason = data.get('reason', 'API update')
                
                success = self.app.update_chamber_status(chamber_id, new_status, reason)
                if success:
                    return jsonify({
                        'success': True,
                        'chamber_id': chamber_id,
                        'new_status': new_status.value
                    })
                else:
                    return jsonify({'error': 'Failed to update status'}), 500
                    
            except ValueError as e:
                return jsonify({'error': f'Invalid status: {e}'}), 400
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_chamber_telemetry(self, chamber_id: str):
        """Handle chamber telemetry endpoint."""
        from flask import request, jsonify
        
        chamber = self.app.get_chamber(chamber_id)
        if not chamber:
            return jsonify({'error': 'Chamber not found'}), 404
        
        if request.method == 'GET':
            # Get query parameters for filtering
            hours = request.args.get('hours', 24, type=int)
            limit = request.args.get('limit', 1000, type=int)
            
            # Get telemetry from database
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            db = self.app.database
            query = """
            SELECT timestamp, temperature, pressure, humidity, vacuum_level, elapsed_time
            FROM telemetry_data 
            WHERE chamber_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
            LIMIT ?
            """
            
            results = db.execute_query(query, (chamber_id, start_time, end_time, limit))
            
            telemetry_data = []
            for row in results:
                record = {
                    'timestamp': row[0],
                    'temperature': row[1],
                    'pressure': row[2],
                    'humidity': row[3],
                    'vacuum_level': row[4],
                    'elapsed_time': row[5]
                }
                telemetry_data.append(record)
            
            return jsonify({
                'chamber_id': chamber_id,
                'telemetry': telemetry_data,
                'count': len(telemetry_data),
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            })
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_work_requests(self, chamber_id: str):
        """Handle chamber work requests endpoint."""
        from flask import request, jsonify
        
        chamber = self.app.get_chamber(chamber_id)
        if not chamber:
            return jsonify({'error': 'Chamber not found'}), 404
        
        if request.method == 'GET':
            work_requests = []
            for wr in chamber.work_requests:
                wr_data = {
                    'id': wr.id,
                    'title': wr.title,
                    'description': wr.description,
                    'status': wr.status,
                    'priority': wr.priority,
                    'created_at': wr.created_at.isoformat(),
                    'assigned_to': wr.assigned_to,
                    'estimated_hours': wr.estimated_hours,
                    'created_by': wr.created_by,
                    'notes_count': len(wr.notes)
                }
                work_requests.append(wr_data)
            
            return jsonify({
                'chamber_id': chamber_id,
                'work_requests': work_requests,
                'count': len(work_requests)
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            if not data or 'title' not in data:
                return jsonify({'error': 'Title required'}), 400
            
            try:
                from ..core.chamber import WorkRequest
                work_request = WorkRequest(
                    title=data['title'],
                    description=data.get('description', ''),
                    priority=data.get('priority', 'medium'),
                    assigned_to=data.get('assigned_to'),
                    estimated_hours=data.get('estimated_hours', 0.0),
                    created_by=data.get('created_by', 'api_user')
                )
                
                success = self.app.add_work_request(chamber_id, work_request)
                if success:
                    return jsonify({
                        'success': True,
                        'work_request_id': work_request.id,
                        'chamber_id': chamber_id
                    }), 201
                else:
                    return jsonify({'error': 'Failed to create work request'}), 500
                    
            except Exception as e:
                return jsonify({'error': f'Error creating work request: {e}'}), 400
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_all_work_requests(self):
        """Handle all work requests endpoint."""
        from flask import request, jsonify
        
        if request.method == 'GET':
            all_work_requests = []
            chambers = self.app.get_chambers()
            
            for chamber in chambers:
                for wr in chamber.work_requests:
                    wr_data = {
                        'id': wr.id,
                        'title': wr.title,
                        'description': wr.description,
                        'status': wr.status,
                        'priority': wr.priority,
                        'created_at': wr.created_at.isoformat(),
                        'assigned_to': wr.assigned_to,
                        'estimated_hours': wr.estimated_hours,
                        'created_by': wr.created_by,
                        'chamber_id': chamber.id,
                        'chamber_name': chamber.name
                    }
                    all_work_requests.append(wr_data)
            
            # Apply filters
            status_filter = request.args.get('status')
            priority_filter = request.args.get('priority')
            
            if status_filter:
                all_work_requests = [wr for wr in all_work_requests if wr['status'] == status_filter]
            
            if priority_filter:
                all_work_requests = [wr for wr in all_work_requests if wr['priority'] == priority_filter]
            
            return jsonify({
                'work_requests': all_work_requests,
                'count': len(all_work_requests)
            })
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_export_chambers(self):
        """Handle chamber data export endpoint."""
        from flask import request, jsonify
        
        if request.method == 'GET':
            format = request.args.get('format', 'json')
            hours = request.args.get('hours', 24, type=int)
            
            try:
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=hours)
                
                from .data_export import DataExporter
                exporter = DataExporter(self.app)
                
                output_path = exporter.export_chamber_data(
                    date_range=(start_time, end_time),
                    format=format
                )
                
                return jsonify({
                    'success': True,
                    'export_path': output_path,
                    'format': format,
                    'time_range': {
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat()
                    }
                })
                
            except Exception as e:
                return jsonify({'error': f'Export failed: {e}'}), 500
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_export_telemetry(self, chamber_id: str):
        """Handle telemetry data export endpoint."""
        from flask import request, jsonify
        
        chamber = self.app.get_chamber(chamber_id)
        if not chamber:
            return jsonify({'error': 'Chamber not found'}), 404
        
        if request.method == 'GET':
            format = request.args.get('format', 'csv')
            hours = request.args.get('hours', 24, type=int)
            
            try:
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=hours)
                
                from .data_export import DataExporter
                exporter = DataExporter(self.app)
                
                output_path = exporter.export_telemetry_data(
                    chamber_id,
                    date_range=(start_time, end_time),
                    format=format
                )
                
                return jsonify({
                    'success': True,
                    'export_path': output_path,
                    'chamber_id': chamber_id,
                    'format': format,
                    'time_range': {
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat()
                    }
                })
                
            except Exception as e:
                return jsonify({'error': f'Export failed: {e}'}), 500
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_status_report(self):
        """Handle status report generation endpoint."""
        from flask import request, jsonify
        
        if request.method == 'GET':
            format = request.args.get('format', 'pdf')
            days = request.args.get('days', 30, type=int)
            
            try:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)
                
                from .report_generator import ReportGenerator
                report_gen = ReportGenerator(self.app)
                
                output_path = report_gen.generate_chamber_status_report(
                    date_range=(start_time, end_time),
                    format=format
                )
                
                return jsonify({
                    'success': True,
                    'report_path': output_path,
                    'format': format,
                    'time_range': {
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat()
                    }
                })
                
            except Exception as e:
                return jsonify({'error': f'Report generation failed: {e}'}), 500
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_utilization_report(self):
        """Handle utilization report generation endpoint."""
        from flask import request, jsonify
        
        if request.method == 'GET':
            format = request.args.get('format', 'pdf')
            days = request.args.get('days', 30, type=int)
            
            try:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)
                
                from .report_generator import ReportGenerator
                report_gen = ReportGenerator(self.app)
                
                output_path = report_gen.generate_utilization_report(
                    date_range=(start_time, end_time),
                    format=format
                )
                
                return jsonify({
                    'success': True,
                    'report_path': output_path,
                    'format': format,
                    'time_range': {
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat()
                    }
                })
                
            except Exception as e:
                return jsonify({'error': f'Report generation failed: {e}'}), 500
        
        return jsonify({'error': 'Method not allowed'}), 405
    
    def _handle_health_check(self):
        """Handle health check endpoint."""
        from flask import jsonify
        
        chambers = self.app.get_chambers()
        connected_chambers = sum(1 for c in chambers if c.is_connected)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'chambers': {
                'total': len(chambers),
                'connected': connected_chambers,
                'disconnected': len(chambers) - connected_chambers
            },
            'services': {
                'database': self.app.database.is_connected() if hasattr(self.app.database, 'is_connected') else True,
                'telemetry_manager': self.app.telemetry_manager.is_running if hasattr(self.app.telemetry_manager, 'is_running') else True,
                'multi_user_manager': self.app.multi_user_manager.is_running if hasattr(self.app.multi_user_manager, 'is_running') else True
            }
        })
