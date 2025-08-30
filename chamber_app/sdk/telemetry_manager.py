"""
Telemetry management for chamber data collection.
Handles Grafana, Atlas SDK, Ethernet, and Serial connections.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from ..core.chamber_state import ChamberMetrics
from ..utils import get_logger


class TelemetrySource(ABC):
    """Abstract base class for telemetry data sources."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the telemetry source."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the telemetry source."""
        pass
    
    @abstractmethod
    async def get_metrics(self, chamber_id: str) -> Optional[ChamberMetrics]:
        """Get current metrics for a chamber."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the source."""
        pass


class GrafanaTelemetrySource(TelemetrySource):
    """Telemetry source using Grafana API."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.connected = False
        self.session = None
    
    async def connect(self) -> bool:
        """Connect to Grafana API."""
        try:
            import aiohttp
            
            grafana_url = self.config.get('GRAFANA_URL')
            api_key = self.config.get('GRAFANA_API_KEY')
            
            if not grafana_url or not api_key:
                self.logger.warning("Grafana URL or API key not configured")
                return False
            
            self.session = aiohttp.ClientSession(
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Test connection
            async with self.session.get(f"{grafana_url}/api/health") as response:
                if response.status == 200:
                    self.connected = True
                    self.logger.info("Connected to Grafana successfully")
                    return True
                else:
                    self.logger.error(f"Grafana connection failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to connect to Grafana: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Grafana."""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        self.logger.info("Disconnected from Grafana")
    
    async def get_metrics(self, chamber_id: str) -> Optional[ChamberMetrics]:
        """Get metrics from Grafana for a chamber."""
        if not self.connected or not self.session:
            return None
        
        try:
            # This is a simplified example - in real implementation,
            # you'd query specific Grafana dashboards/metrics
            query = f"chamber_temperature{{chamber_id=\"{chamber_id}\"}}"
            
            params = {
                'query': query,
                'time': datetime.now().isoformat()
            }
            
            grafana_url = self.config.get('GRAFANA_URL')
            async with self.session.get(
                f"{grafana_url}/api/datasources/proxy/1/api/v1/query",
                params=params
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse Grafana response and create ChamberMetrics
                    # This is a simplified parser - real implementation would be more complex
                    metrics = ChamberMetrics(
                        temperature=self._extract_metric(data, 'temperature', 20.0),
                        vacuum_level=self._extract_metric(data, 'vacuum', 1e-6),
                        humidity=self._extract_metric(data, 'humidity', 45.0),
                        pressure=self._extract_metric(data, 'pressure', 1013.25),
                        elapsed_time=self._extract_metric(data, 'elapsed_time', 0.0)
                    )
                    
                    return metrics
                    
        except Exception as e:
            self.logger.error(f"Failed to get Grafana metrics for chamber {chamber_id}: {e}")
        
        return None
    
    def _extract_metric(self, data: Dict, metric_name: str, default: float) -> float:
        """Extract a metric value from Grafana response."""
        # Simplified metric extraction - real implementation would parse Prometheus format
        try:
            # This would parse the actual Grafana/Prometheus response
            return default + (hash(metric_name) % 10)  # Dummy variation
        except:
            return default
    
    def is_connected(self) -> bool:
        """Check if connected to Grafana."""
        return self.connected


class EthernetTelemetrySource(TelemetrySource):
    """Telemetry source using Ethernet TCP/IP connection."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.connected = False
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
    
    async def connect(self) -> bool:
        """Connect to chamber via Ethernet."""
        try:
            # This would connect to the actual chamber IP
            # For now, simulate connection
            await asyncio.sleep(0.1)  # Simulate connection delay
            self.connected = True
            self.logger.info("Connected to chamber via Ethernet")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect via Ethernet: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Ethernet."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None
        self.reader = None
        self.connected = False
        self.logger.info("Disconnected from Ethernet")
    
    async def get_metrics(self, chamber_id: str) -> Optional[ChamberMetrics]:
        """Get metrics via Ethernet protocol."""
        if not self.connected:
            return None
        
        try:
            # Simulate reading from chamber via TCP
            # Real implementation would send protocol-specific commands
            metrics = ChamberMetrics(
                temperature=20.0 + (hash(chamber_id) % 100) / 10,
                vacuum_level=1e-6 * (1 + (hash(chamber_id) % 10) / 100),
                humidity=45.0 + (hash(chamber_id) % 20),
                pressure=1013.25 + (hash(chamber_id) % 50),
                elapsed_time=(hash(chamber_id) % 3600)
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get Ethernet metrics for chamber {chamber_id}: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if connected via Ethernet."""
        return self.connected


class SerialTelemetrySource(TelemetrySource):
    """Telemetry source using Serial/RS232 connection."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.connected = False
        self.serial_port = None
    
    async def connect(self) -> bool:
        """Connect to chamber via Serial."""
        try:
            # This would use pyserial to connect to actual port
            # For now, simulate connection
            await asyncio.sleep(0.1)
            self.connected = True
            self.logger.info("Connected to chamber via Serial")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect via Serial: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Serial."""
        if self.serial_port:
            self.serial_port.close()
        self.serial_port = None
        self.connected = False
        self.logger.info("Disconnected from Serial")
    
    async def get_metrics(self, chamber_id: str) -> Optional[ChamberMetrics]:
        """Get metrics via Serial protocol."""
        if not self.connected:
            return None
        
        try:
            # Simulate reading from serial port
            # Real implementation would send/receive serial commands
            metrics = ChamberMetrics(
                temperature=25.0 + (hash(chamber_id) % 50) / 10,
                vacuum_level=1e-7 * (1 + (hash(chamber_id) % 5)),
                humidity=40.0 + (hash(chamber_id) % 30),
                pressure=1000.0 + (hash(chamber_id) % 100),
                elapsed_time=(hash(chamber_id) % 7200)
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get Serial metrics for chamber {chamber_id}: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if connected via Serial."""
        return self.connected


class TelemetryManager:
    """
    Manages telemetry collection from multiple sources.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.sources: Dict[str, TelemetrySource] = {}
        self.chamber_source_mapping: Dict[str, str] = {}
        self.running = False
        
        # Initialize available sources
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Initialize available telemetry sources."""
        # Grafana source
        if self.config.get('GRAFANA_URL') and self.config.get('GRAFANA_API_KEY'):
            self.sources['grafana'] = GrafanaTelemetrySource(self.config)
        
        # Ethernet source
        self.sources['ethernet'] = EthernetTelemetrySource(self.config)
        
        # Serial source
        self.sources['serial'] = SerialTelemetrySource(self.config)
        
        self.logger.info(f"Initialized {len(self.sources)} telemetry sources")
    
    async def start(self):
        """Start telemetry collection."""
        self.running = True
        
        # Attempt to connect to all sources
        for source_name, source in self.sources.items():
            try:
                connected = await source.connect()
                if connected:
                    self.logger.info(f"Telemetry source '{source_name}' connected")
                else:
                    self.logger.warning(f"Telemetry source '{source_name}' failed to connect")
            except Exception as e:
                self.logger.error(f"Error connecting to source '{source_name}': {e}")
        
        self.logger.info("Telemetry manager started")
    
    def stop(self):
        """Stop telemetry collection."""
        self.running = False
        
        # Disconnect from all sources
        async def disconnect_all():
            for source in self.sources.values():
                try:
                    await source.disconnect()
                except Exception as e:
                    self.logger.error(f"Error disconnecting source: {e}")
        
        # Run disconnect in event loop if available
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(disconnect_all())
            else:
                loop.run_until_complete(disconnect_all())
        except:
            pass
        
        self.logger.info("Telemetry manager stopped")
    
    def assign_chamber_source(self, chamber_id: str, source_name: str):
        """Assign a telemetry source to a chamber."""
        if source_name in self.sources:
            self.chamber_source_mapping[chamber_id] = source_name
            self.logger.info(f"Chamber {chamber_id} assigned to source {source_name}")
        else:
            self.logger.error(f"Unknown telemetry source: {source_name}")
    
    async def get_chamber_metrics(self, chamber_id: str) -> Optional[ChamberMetrics]:
        """Get current metrics for a chamber."""
        if not self.running:
            return None
        
        # Get assigned source for chamber
        source_name = self.chamber_source_mapping.get(chamber_id)
        
        if not source_name:
            # Try to auto-assign a connected source
            for name, source in self.sources.items():
                if source.is_connected():
                    self.assign_chamber_source(chamber_id, name)
                    source_name = name
                    break
        
        if source_name and source_name in self.sources:
            source = self.sources[source_name]
            try:
                return await source.get_metrics(chamber_id)
            except Exception as e:
                self.logger.error(f"Error getting metrics from {source_name} for chamber {chamber_id}: {e}")
        
        return None
    
    def get_source_status(self) -> Dict[str, bool]:
        """Get connection status of all sources."""
        return {
            name: source.is_connected() 
            for name, source in self.sources.items()
        }
    
    def get_chamber_assignments(self) -> Dict[str, str]:
        """Get current chamber-to-source assignments."""
        return self.chamber_source_mapping.copy()
