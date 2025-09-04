# -*- coding: utf-8 -*-
"""
Report generation system for the Chamber Management Application.
Provides comprehensive reporting capabilities for chambers, telemetry, and operations.
"""

import os
import json
import csv
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors

from .logging_config import get_logger


class ReportGenerator:
    """
    Generates various types of reports for the chamber management system.
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_chamber_status_report(self, 
                                     date_range: Optional[Tuple[datetime, datetime]] = None,
                                     format: str = 'pdf',
                                     chamber_ids: Optional[List[str]] = None) -> str:
        """
        Generate a comprehensive chamber status report.
        
        Args:
            date_range: Tuple of (start_date, end_date) or None for last 30 days
            format: Report format ('pdf', 'html', 'csv', 'excel')
            chamber_ids: Specific chambers or None for all
            
        Returns:
            Path to generated report file
        """
        if not date_range:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            date_range = (start_date, end_date)
        
        # Collect data
        report_data = self._collect_chamber_status_data(date_range, chamber_ids)
        
        # Generate report based on format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chamber_status_report_{timestamp}.{format}"
        output_path = self.output_dir / filename
        
        if format == 'pdf':
            self._generate_pdf_report(output_path, report_data, "Chamber Status Report")
        elif format == 'html':
            self._generate_html_report(output_path, report_data, "Chamber Status Report")
        elif format == 'csv':
            self._generate_csv_report(output_path, report_data)
        elif format == 'excel':
            self._generate_excel_report(output_path, report_data)
        
        self.logger.info(f"Generated chamber status report: {output_path}")
        return str(output_path)
    
    def generate_telemetry_report(self,
                                chamber_id: str,
                                date_range: Optional[Tuple[datetime, datetime]] = None,
                                metrics: Optional[List[str]] = None,
                                format: str = 'pdf') -> str:
        """
        Generate a telemetry report for a specific chamber.
        
        Args:
            chamber_id: Chamber to generate report for
            date_range: Time range or None for last 24 hours
            metrics: Specific metrics or None for all
            format: Report format
            
        Returns:
            Path to generated report file
        """
        if not date_range:
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            date_range = (start_date, end_date)
        
        # Collect telemetry data
        telemetry_data = self._collect_telemetry_data(chamber_id, date_range, metrics)
        
        # Generate charts
        chart_paths = self._generate_telemetry_charts(chamber_id, telemetry_data, date_range)
        
        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"telemetry_report_{chamber_id}_{timestamp}.{format}"
        output_path = self.output_dir / filename
        
        if format == 'pdf':
            self._generate_telemetry_pdf(output_path, chamber_id, telemetry_data, chart_paths, date_range)
        elif format == 'html':
            self._generate_telemetry_html(output_path, chamber_id, telemetry_data, chart_paths, date_range)
        
        self.logger.info(f"Generated telemetry report for {chamber_id}: {output_path}")
        return str(output_path)
    
    def generate_work_requests_report(self,
                                    date_range: Optional[Tuple[datetime, datetime]] = None,
                                    status_filter: Optional[str] = None,
                                    priority_filter: Optional[str] = None,
                                    format: str = 'pdf') -> str:
        """
        Generate a work requests summary report.
        
        Args:
            date_range: Time range or None for all time
            status_filter: Filter by status or None for all
            priority_filter: Filter by priority or None for all
            format: Report format
            
        Returns:
            Path to generated report file
        """
        # Collect work request data
        work_requests_data = self._collect_work_requests_data(date_range, status_filter, priority_filter)
        
        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"work_requests_report_{timestamp}.{format}"
        output_path = self.output_dir / filename
        
        if format == 'pdf':
            self._generate_work_requests_pdf(output_path, work_requests_data, date_range)
        elif format == 'csv':
            self._generate_work_requests_csv(output_path, work_requests_data)
        elif format == 'excel':
            self._generate_work_requests_excel(output_path, work_requests_data)
        
        self.logger.info(f"Generated work requests report: {output_path}")
        return str(output_path)
    
    def generate_utilization_report(self,
                                  date_range: Optional[Tuple[datetime, datetime]] = None,
                                  format: str = 'pdf') -> str:
        """
        Generate a chamber utilization report.
        
        Args:
            date_range: Time range or None for last 30 days
            format: Report format
            
        Returns:
            Path to generated report file
        """
        if not date_range:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            date_range = (start_date, end_date)
        
        # Collect utilization data
        utilization_data = self._collect_utilization_data(date_range)
        
        # Generate charts
        chart_paths = self._generate_utilization_charts(utilization_data, date_range)
        
        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"utilization_report_{timestamp}.{format}"
        output_path = self.output_dir / filename
        
        if format == 'pdf':
            self._generate_utilization_pdf(output_path, utilization_data, chart_paths, date_range)
        
        self.logger.info(f"Generated utilization report: {output_path}")
        return str(output_path)
    
    def _collect_chamber_status_data(self, date_range: Tuple[datetime, datetime], 
                                   chamber_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Collect chamber status data for reporting."""
        chambers = self.app.get_chambers()
        
        if chamber_ids:
            chambers = [c for c in chambers if c.id in chamber_ids]
        
        data = {
            'chambers': [],
            'summary': {
                'total_chambers': len(chambers),
                'by_state': {},
                'by_status': {},
                'connected': 0,
                'disconnected': 0
            },
            'date_range': date_range
        }
        
        for chamber in chambers:
            chamber_data = {
                'id': chamber.id,
                'name': chamber.name,
                'type': chamber.chamber_type.value,
                'current_state': chamber.state_manager.current_state.value,
                'current_status': chamber.state_manager.current_status.value,
                'is_connected': chamber.is_connected,
                'last_update': chamber.last_update,
                'work_requests_count': len(chamber.work_requests),
                'active_work_requests': len(chamber.get_active_work_requests())
            }
            
            # Add latest telemetry if available
            if chamber.latest_telemetry:
                chamber_data['telemetry'] = {
                    'temperature': chamber.latest_telemetry.temperature,
                    'pressure': chamber.latest_telemetry.pressure,
                    'humidity': chamber.latest_telemetry.humidity,
                    'vacuum_level': chamber.latest_telemetry.vacuum_level
                }
            
            data['chambers'].append(chamber_data)
            
            # Update summary
            state = chamber.state_manager.current_state.value
            status = chamber.state_manager.current_status.value
            data['summary']['by_state'][state] = data['summary']['by_state'].get(state, 0) + 1
            data['summary']['by_status'][status] = data['summary']['by_status'].get(status, 0) + 1
            
            if chamber.is_connected:
                data['summary']['connected'] += 1
            else:
                data['summary']['disconnected'] += 1
        
        return data
    
    def _collect_telemetry_data(self, chamber_id: str, 
                              date_range: Tuple[datetime, datetime],
                              metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """Collect telemetry data for a specific chamber."""
        chamber = self.app.get_chamber(chamber_id)
        if not chamber:
            return {}
        
        # Get telemetry from database
        db = self.app.database
        query = """
        SELECT timestamp, temperature, pressure, humidity, vacuum_level, elapsed_time
        FROM telemetry_data 
        WHERE chamber_id = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
        """
        
        results = db.execute_query(query, (chamber_id, date_range[0], date_range[1]))
        
        telemetry_records = []
        for row in results:
            record = {
                'timestamp': datetime.fromisoformat(row[0]),
                'temperature': row[1],
                'pressure': row[2],
                'humidity': row[3],
                'vacuum_level': row[4],
                'elapsed_time': row[5]
            }
            telemetry_records.append(record)
        
        return {
            'chamber_id': chamber_id,
            'chamber_name': chamber.name,
            'date_range': date_range,
            'records': telemetry_records,
            'record_count': len(telemetry_records)
        }
    
    def _collect_work_requests_data(self, date_range: Optional[Tuple[datetime, datetime]],
                                  status_filter: Optional[str] = None,
                                  priority_filter: Optional[str] = None) -> Dict[str, Any]:
        """Collect work requests data for reporting."""
        chambers = self.app.get_chambers()
        work_requests = []
        
        for chamber in chambers:
            for wr in chamber.work_requests:
                # Apply filters
                if date_range:
                    if not (date_range[0] <= wr.created_at <= date_range[1]):
                        continue
                
                if status_filter and wr.status != status_filter:
                    continue
                
                if priority_filter and wr.priority != priority_filter:
                    continue
                
                wr_data = {
                    'id': wr.id,
                    'title': wr.title,
                    'description': wr.description,
                    'chamber_id': chamber.id,
                    'chamber_name': chamber.name,
                    'status': wr.status,
                    'priority': wr.priority,
                    'created_at': wr.created_at,
                    'assigned_to': wr.assigned_to,
                    'estimated_hours': wr.estimated_hours,
                    'notes_count': len(wr.notes)
                }
                work_requests.append(wr_data)
        
        # Generate summary
        summary = {
            'total_requests': len(work_requests),
            'by_status': {},
            'by_priority': {},
            'by_chamber': {}
        }
        
        for wr in work_requests:
            summary['by_status'][wr['status']] = summary['by_status'].get(wr['status'], 0) + 1
            summary['by_priority'][wr['priority']] = summary['by_priority'].get(wr['priority'], 0) + 1
            summary['by_chamber'][wr['chamber_name']] = summary['by_chamber'].get(wr['chamber_name'], 0) + 1
        
        return {
            'work_requests': work_requests,
            'summary': summary,
            'date_range': date_range,
            'filters': {
                'status': status_filter,
                'priority': priority_filter
            }
        }
    
    def _collect_utilization_data(self, date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Collect chamber utilization data."""
        chambers = self.app.get_chambers()
        utilization_data = []
        
        for chamber in chambers:
            # Calculate time spent in each state during the date range
            state_times = {}
            total_time = (date_range[1] - date_range[0]).total_seconds()
            
            # Get state transitions from database
            db = self.app.database
            query = """
            SELECT timestamp, from_state, to_state
            FROM state_transitions 
            WHERE chamber_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
            """
            
            transitions = db.execute_query(query, (chamber.id, date_range[0], date_range[1]))
            
            # Calculate utilization based on state transitions
            current_state = chamber.state_manager.current_state.value
            if transitions:
                # Process transitions to calculate time in each state
                for i, transition in enumerate(transitions):
                    timestamp = datetime.fromisoformat(transition[0])
                    to_state = transition[2]
                    
                    if i == 0:
                        # Time from start to first transition
                        duration = (timestamp - date_range[0]).total_seconds()
                        state_times[transition[1]] = state_times.get(transition[1], 0) + duration
                    
                    if i < len(transitions) - 1:
                        # Time between transitions
                        next_timestamp = datetime.fromisoformat(transitions[i + 1][0])
                        duration = (next_timestamp - timestamp).total_seconds()
                        state_times[to_state] = state_times.get(to_state, 0) + duration
                    else:
                        # Time from last transition to end
                        duration = (date_range[1] - timestamp).total_seconds()
                        state_times[to_state] = state_times.get(to_state, 0) + duration
            else:
                # No transitions, chamber was in current state the whole time
                state_times[current_state] = total_time
            
            # Convert to percentages
            state_percentages = {}
            for state, time_seconds in state_times.items():
                state_percentages[state] = (time_seconds / total_time) * 100 if total_time > 0 else 0
            
            utilization_data.append({
                'chamber_id': chamber.id,
                'chamber_name': chamber.name,
                'chamber_type': chamber.chamber_type.value,
                'state_times': state_times,
                'state_percentages': state_percentages,
                'total_work_requests': len(chamber.work_requests),
                'active_work_requests': len(chamber.get_active_work_requests())
            })
        
        return {
            'chambers': utilization_data,
            'date_range': date_range
        }
    
    def _generate_pdf_report(self, output_path: Path, data: Dict[str, Any], title: str):
        """Generate a PDF report."""
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(title, title_style))
        
        # Date range
        if 'date_range' in data:
            date_range = data['date_range']
            date_text = f"Report Period: {date_range[0].strftime('%Y-%m-%d %H:%M')} to {date_range[1].strftime('%Y-%m-%d %H:%M')}"
            story.append(Paragraph(date_text, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Summary section
        if 'summary' in data:
            story.append(Paragraph("Summary", styles['Heading2']))
            summary = data['summary']
            
            for key, value in summary.items():
                if isinstance(value, dict):
                    story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b>", styles['Normal']))
                    for sub_key, sub_value in value.items():
                        story.append(Paragraph(f"  • {sub_key}: {sub_value}", styles['Normal']))
                else:
                    story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", styles['Normal']))
            
            story.append(Spacer(1, 12))
        
        # Chambers section
        if 'chambers' in data:
            story.append(Paragraph("Chamber Details", styles['Heading2']))
            
            # Create table data
            table_data = [['Chamber', 'Type', 'State', 'Status', 'Connected', 'Work Requests']]
            
            for chamber in data['chambers']:
                table_data.append([
                    chamber['name'],
                    chamber['type'],
                    chamber['current_state'],
                    chamber['current_status'],
                    '✓' if chamber['is_connected'] else '✗',
                    str(chamber['work_requests_count'])
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        doc.build(story)
    
    def _generate_html_report(self, output_path: Path, data: Dict[str, Any], title: str):
        """Generate an HTML report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; text-align: center; }}
                h2 {{ color: #666; border-bottom: 2px solid #eee; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
        """
        
        # Add date range
        if 'date_range' in data:
            date_range = data['date_range']
            html_content += f"""
            <p><strong>Report Period:</strong> {date_range[0].strftime('%Y-%m-%d %H:%M')} to {date_range[1].strftime('%Y-%m-%d %H:%M')}</p>
            """
        
        # Add summary
        if 'summary' in data:
            html_content += "<h2>Summary</h2><div class='summary'>"
            summary = data['summary']
            
            for key, value in summary.items():
                if isinstance(value, dict):
                    html_content += f"<h3>{key.replace('_', ' ').title()}</h3><ul>"
                    for sub_key, sub_value in value.items():
                        html_content += f"<li>{sub_key}: {sub_value}</li>"
                    html_content += "</ul>"
                else:
                    html_content += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
            
            html_content += "</div>"
        
        # Add chambers table
        if 'chambers' in data:
            html_content += """
            <h2>Chamber Details</h2>
            <table>
                <tr>
                    <th>Chamber</th>
                    <th>Type</th>
                    <th>State</th>
                    <th>Status</th>
                    <th>Connected</th>
                    <th>Work Requests</th>
                </tr>
            """
            
            for chamber in data['chambers']:
                connected = '✓' if chamber['is_connected'] else '✗'
                html_content += f"""
                <tr>
                    <td>{chamber['name']}</td>
                    <td>{chamber['type']}</td>
                    <td>{chamber['current_state']}</td>
                    <td>{chamber['current_status']}</td>
                    <td>{connected}</td>
                    <td>{chamber['work_requests_count']}</td>
                </tr>
                """
            
            html_content += "</table>"
        
        html_content += "</body></html>"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_csv_report(self, output_path: Path, data: Dict[str, Any]):
        """Generate a CSV report."""
        if 'chambers' in data:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['chamber_name', 'chamber_type', 'current_state', 'current_status', 
                            'is_connected', 'work_requests_count', 'active_work_requests']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for chamber in data['chambers']:
                    row = {
                        'chamber_name': chamber['name'],
                        'chamber_type': chamber['type'],
                        'current_state': chamber['current_state'],
                        'current_status': chamber['current_status'],
                        'is_connected': chamber['is_connected'],
                        'work_requests_count': chamber['work_requests_count'],
                        'active_work_requests': chamber['active_work_requests']
                    }
                    writer.writerow(row)
    
    def _generate_excel_report(self, output_path: Path, data: Dict[str, Any]):
        """Generate an Excel report."""
        if 'chambers' in data:
            df_data = []
            for chamber in data['chambers']:
                row = {
                    'Chamber Name': chamber['name'],
                    'Type': chamber['type'],
                    'Current State': chamber['current_state'],
                    'Current Status': chamber['current_status'],
                    'Connected': chamber['is_connected'],
                    'Work Requests': chamber['work_requests_count'],
                    'Active Requests': chamber['active_work_requests']
                }
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            df.to_excel(output_path, index=False, sheet_name='Chamber Status')
    
    def _generate_telemetry_charts(self, chamber_id: str, telemetry_data: Dict[str, Any], 
                                 date_range: Tuple[datetime, datetime]) -> List[str]:
        """Generate telemetry charts and return file paths."""
        if not telemetry_data.get('records'):
            return []
        
        chart_paths = []
        records = telemetry_data['records']
        
        # Extract data for plotting
        timestamps = [r['timestamp'] for r in records]
        temperatures = [r['temperature'] for r in records if r['temperature'] is not None]
        pressures = [r['pressure'] for r in records if r['pressure'] is not None]
        humidities = [r['humidity'] for r in records if r['humidity'] is not None]
        
        # Temperature chart
        if temperatures:
            plt.figure(figsize=(12, 6))
            plt.plot(timestamps[:len(temperatures)], temperatures, 'r-', linewidth=2)
            plt.title(f'Temperature - {chamber_id}')
            plt.xlabel('Time')
            plt.ylabel('Temperature (°C)')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            temp_chart_path = self.output_dir / f"temp_chart_{chamber_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(temp_chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            chart_paths.append(str(temp_chart_path))
        
        # Pressure chart
        if pressures:
            plt.figure(figsize=(12, 6))
            plt.plot(timestamps[:len(pressures)], pressures, 'b-', linewidth=2)
            plt.title(f'Pressure - {chamber_id}')
            plt.xlabel('Time')
            plt.ylabel('Pressure (mbar)')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            pressure_chart_path = self.output_dir / f"pressure_chart_{chamber_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(pressure_chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            chart_paths.append(str(pressure_chart_path))
        
        return chart_paths
    
    def _generate_utilization_charts(self, utilization_data: Dict[str, Any], 
                                   date_range: Tuple[datetime, datetime]) -> List[str]:
        """Generate utilization charts and return file paths."""
        chart_paths = []
        
        if not utilization_data.get('chambers'):
            return chart_paths
        
        # Overall utilization pie chart
        all_states = {}
        for chamber_data in utilization_data['chambers']:
            for state, percentage in chamber_data['state_percentages'].items():
                all_states[state] = all_states.get(state, 0) + percentage
        
        # Normalize percentages
        total = sum(all_states.values())
        if total > 0:
            all_states = {k: (v / total) * 100 for k, v in all_states.items()}
        
        if all_states:
            plt.figure(figsize=(10, 8))
            plt.pie(all_states.values(), labels=all_states.keys(), autopct='%1.1f%%', startangle=90)
            plt.title('Overall Chamber State Distribution')
            plt.axis('equal')
            
            pie_chart_path = self.output_dir / f"utilization_pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(pie_chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            chart_paths.append(str(pie_chart_path))
        
        return chart_paths
    
    def _generate_telemetry_pdf(self, output_path: Path, chamber_id: str, 
                              telemetry_data: Dict[str, Any], chart_paths: List[str],
                              date_range: Tuple[datetime, datetime]):
        """Generate a telemetry PDF report."""
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = f"Telemetry Report - {telemetry_data.get('chamber_name', chamber_id)}"
        story.append(Paragraph(title, styles['Title']))
        
        # Date range
        date_text = f"Period: {date_range[0].strftime('%Y-%m-%d %H:%M')} to {date_range[1].strftime('%Y-%m-%d %H:%M')}"
        story.append(Paragraph(date_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Summary
        story.append(Paragraph("Summary", styles['Heading2']))
        story.append(Paragraph(f"Total Records: {telemetry_data.get('record_count', 0)}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Add charts
        for chart_path in chart_paths:
            if os.path.exists(chart_path):
                img = Image(chart_path, width=6*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 12))
        
        doc.build(story)
    
    def _generate_work_requests_pdf(self, output_path: Path, work_requests_data: Dict[str, Any],
                                  date_range: Optional[Tuple[datetime, datetime]]):
        """Generate a work requests PDF report."""
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph("Work Requests Report", styles['Title']))
        
        # Date range
        if date_range:
            date_text = f"Period: {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}"
            story.append(Paragraph(date_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Summary
        summary = work_requests_data['summary']
        story.append(Paragraph("Summary", styles['Heading2']))
        story.append(Paragraph(f"Total Requests: {summary['total_requests']}", styles['Normal']))
        
        # Status breakdown
        story.append(Paragraph("By Status:", styles['Heading3']))
        for status, count in summary['by_status'].items():
            story.append(Paragraph(f"  • {status}: {count}", styles['Normal']))
        
        # Priority breakdown
        story.append(Paragraph("By Priority:", styles['Heading3']))
        for priority, count in summary['by_priority'].items():
            story.append(Paragraph(f"  • {priority}: {count}", styles['Normal']))
        
        story.append(Spacer(1, 12))
        
        # Work requests table
        if work_requests_data['work_requests']:
            story.append(Paragraph("Work Requests Details", styles['Heading2']))
            
            table_data = [['Title', 'Chamber', 'Status', 'Priority', 'Created', 'Assigned To']]
            
            for wr in work_requests_data['work_requests']:
                table_data.append([
                    wr['title'][:30] + '...' if len(wr['title']) > 30 else wr['title'],
                    wr['chamber_name'],
                    wr['status'],
                    wr['priority'],
                    wr['created_at'].strftime('%Y-%m-%d'),
                    wr['assigned_to'] or 'Unassigned'
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            
            story.append(table)
        
        doc.build(story)
    
    def _generate_work_requests_csv(self, output_path: Path, work_requests_data: Dict[str, Any]):
        """Generate a work requests CSV report."""
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'chamber_name', 'status', 'priority', 'created_at', 
                         'assigned_to', 'estimated_hours', 'notes_count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for wr in work_requests_data['work_requests']:
                writer.writerow(wr)
    
    def _generate_work_requests_excel(self, output_path: Path, work_requests_data: Dict[str, Any]):
        """Generate a work requests Excel report."""
        df = pd.DataFrame(work_requests_data['work_requests'])
        df.to_excel(output_path, index=False, sheet_name='Work Requests')
    
    def _generate_utilization_pdf(self, output_path: Path, utilization_data: Dict[str, Any],
                                chart_paths: List[str], date_range: Tuple[datetime, datetime]):
        """Generate a utilization PDF report."""
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph("Chamber Utilization Report", styles['Title']))
        
        # Date range
        date_text = f"Period: {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}"
        story.append(Paragraph(date_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Add charts
        for chart_path in chart_paths:
            if os.path.exists(chart_path):
                img = Image(chart_path, width=6*inch, height=4*inch)
                story.append(img)
                story.append(Spacer(1, 12))
        
        # Utilization table
        if utilization_data.get('chambers'):
            story.append(Paragraph("Chamber Utilization Details", styles['Heading2']))
            
            table_data = [['Chamber', 'Type', 'Available %', 'Test %', 'Setup %', 'Other %']]
            
            for chamber_data in utilization_data['chambers']:
                percentages = chamber_data['state_percentages']
                table_data.append([
                    chamber_data['chamber_name'],
                    chamber_data['chamber_type'],
                    f"{percentages.get('available', 0):.1f}%",
                    f"{percentages.get('test_nominal', 0):.1f}%",
                    f"{percentages.get('setup', 0):.1f}%",
                    f"{sum(v for k, v in percentages.items() if k not in ['available', 'test_nominal', 'setup']):.1f}%"
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        doc.build(story)


# Chamber templates for quick setup
CHAMBER_TEMPLATES = {
    'TVAC_Standard': {
        'name': 'TVAC Chamber {number}',
        'chamber_type': 'TVAC',
        'description': 'Standard thermal vacuum chamber configuration',
        'default_settings': {
            'temperature_range': (-40, 85),
            'pressure_range': (1e-6, 1013.25),
            'humidity_range': (0, 95)
        },
        'telemetry_sources': ['ethernet'],
        'work_request_templates': [
            {
                'title': 'Pre-test Setup',
                'description': 'Prepare chamber for thermal vacuum testing',
                'priority': 'medium',
                'estimated_hours': 2.0
            },
            {
                'title': 'Post-test Cleanup',
                'description': 'Clean and reset chamber after testing',
                'priority': 'medium',
                'estimated_hours': 1.5
            }
        ]
    },
    'HASS_Standard': {
        'name': 'HASS Chamber {number}',
        'chamber_type': 'HASS',
        'description': 'Standard HASS (Highly Accelerated Stress Screening) chamber',
        'default_settings': {
            'temperature_range': (-40, 150),
            'vibration_range': (1, 100),
            'humidity_range': (10, 95)
        },
        'telemetry_sources': ['ethernet', 'serial'],
        'work_request_templates': [
            {
                'title': 'HASS Profile Setup',
                'description': 'Configure HASS stress profile parameters',
                'priority': 'high',
                'estimated_hours': 3.0
            }
        ]
    },
    'THERMAL_Standard': {
        'name': 'Thermal Chamber {number}',
        'chamber_type': 'THERMAL',
        'description': 'Standard thermal cycling chamber',
        'default_settings': {
            'temperature_range': (-65, 200),
            'humidity_range': (10, 98),
            'ramp_rate': 5.0
        },
        'telemetry_sources': ['ethernet'],
        'work_request_templates': [
            {
                'title': 'Temperature Calibration',
                'description': 'Calibrate temperature sensors and controls',
                'priority': 'high',
                'estimated_hours': 4.0
            }
        ]
    }
}


class ChamberTemplateManager:
    """
    Manages chamber templates for quick setup and configuration.
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        self.templates = CHAMBER_TEMPLATES.copy()
    
    def get_available_templates(self) -> List[str]:
        """Get list of available chamber templates."""
        return list(self.templates.keys())
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific chamber template."""
        return self.templates.get(template_name)
    
    def create_chamber_from_template(self, template_name: str, 
                                   chamber_name: Optional[str] = None,
                                   customizations: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a new chamber from a template.
        
        Args:
            template_name: Name of the template to use
            chamber_name: Custom name or None to use template default
            customizations: Additional customizations to apply
            
        Returns:
            Chamber ID if successful, None otherwise
        """
        template = self.get_template(template_name)
        if not template:
            self.logger.error(f"Template not found: {template_name}")
            return None
        
        try:
            # Determine chamber name
            if not chamber_name:
                # Find next available number
                existing_chambers = self.app.get_chambers()
                existing_names = [c.name for c in existing_chambers]
                counter = 1
                while True:
                    potential_name = template['name'].format(number=counter)
                    if potential_name not in existing_names:
                        chamber_name = potential_name
                        break
                    counter += 1
            
            # Create chamber
            from ..core.chamber import Chamber
            from ..core.chamber_state import ChamberType
            
            chamber = Chamber(
                name=chamber_name,
                chamber_type=ChamberType(template['chamber_type'])
            )
            
            # Apply template settings
            if 'description' in template:
                chamber.description = template['description']
            
            # Apply customizations
            if customizations:
                for key, value in customizations.items():
                    if hasattr(chamber, key):
                        setattr(chamber, key, value)
            
            # Add chamber to application
            success = self.app.add_chamber(chamber)
            if success:
                # Create default work requests from template
                if 'work_request_templates' in template:
                    self._create_template_work_requests(chamber.id, template['work_request_templates'])
                
                self.logger.info(f"Created chamber '{chamber_name}' from template '{template_name}'")
                return chamber.id
            else:
                self.logger.error(f"Failed to add chamber from template: {template_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating chamber from template {template_name}: {e}")
            return None
    
    def _create_template_work_requests(self, chamber_id: str, wr_templates: List[Dict[str, Any]]):
        """Create work requests from template."""
        from ..core.chamber import WorkRequest
        
        for wr_template in wr_templates:
            work_request = WorkRequest(
                title=wr_template['title'],
                description=wr_template['description'],
                priority=wr_template.get('priority', 'medium'),
                estimated_hours=wr_template.get('estimated_hours', 1.0),
                created_by='system_template'
            )
            
            self.app.add_work_request(chamber_id, work_request)
            self.logger.debug(f"Created template work request: {wr_template['title']}")
    
    def add_custom_template(self, name: str, template_data: Dict[str, Any]):
        """Add a custom chamber template."""
        self.templates[name] = template_data
        self.logger.info(f"Added custom template: {name}")
    
    def remove_template(self, name: str) -> bool:
        """Remove a chamber template."""
        if name in CHAMBER_TEMPLATES:
            self.logger.error(f"Cannot remove built-in template: {name}")
            return False
        
        if name in self.templates:
            del self.templates[name]
            self.logger.info(f"Removed template: {name}")
            return True
        
        return False
    
    def export_template(self, name: str, output_path: str) -> bool:
        """Export a template to a file."""
        template = self.get_template(name)
        if not template:
            return False
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, default=str)
            self.logger.info(f"Exported template '{name}' to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting template {name}: {e}")
            return False
    
    def import_template(self, name: str, input_path: str) -> bool:
        """Import a template from a file."""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            self.add_custom_template(name, template_data)
            self.logger.info(f"Imported template '{name}' from {input_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error importing template from {input_path}: {e}")
            return False
