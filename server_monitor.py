#!/usr/bin/env python3
"""
Server Monitor and Auto-Restart System
Ensures server is always active with automatic recovery
"""

import subprocess
import time
import sys
import os
import signal
import logging
import json
from datetime import datetime
from threading import Thread, Event
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_monitor.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


class ServerMonitor:
    """
    Monitors production server and automatically restarts if it crashes.
    Ensures 99.9% uptime for the AI debate system.
    """
    
    def __init__(self, 
                 server_script: str = "production_server.py",
                 backup_script: str = "backup_server.py",
                 primary_port: int = 5000,
                 backup_port: int = 5001,
                 health_check_interval: int = 30,
                 restart_delay: int = 5):
        
        self.server_script = server_script
        self.backup_script = backup_script
        self.primary_port = primary_port
        self.backup_port = backup_port
        self.health_check_interval = health_check_interval
        self.restart_delay = restart_delay
        
        self.primary_process = None
        self.backup_process = None
        self.running = Event()
        self.restart_count = 0
        self.last_restart = None
        self.health_history = []
        
    def start(self):
        """Start monitoring both primary and backup servers"""
        log.info("=" * 60)
        log.info("🔍 SERVER MONITOR STARTING")
        log.info("=" * 60)
        log.info(f"Primary: {self.server_script}:{self.primary_port}")
        log.info(f"Backup: {self.backup_script}:{self.backup_port}")
        log.info(f"Health check interval: {self.health_check_interval}s")
        
        self.running.set()
        
        # Start primary server
        self._start_primary()
        
        # Wait for primary to initialize
        time.sleep(3)
        
        # Start monitoring thread
        monitor_thread = Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Start health check thread
        health_thread = Thread(target=self._health_check_loop)
        health_thread.daemon = True
        health_thread.start()
        
        log.info("✅ Monitor active - servers under supervision")
        
        try:
            while self.running.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("🛑 Shutting down monitor...")
            self.stop()
    
    def _start_primary(self):
        """Start primary server"""
        log.info(f"🚀 Starting primary server: {self.server_script}")
        
        try:
            # Kill any existing process on the port
            self._kill_port_processes(self.primary_port)
            
            # Start new process
            env = os.environ.copy()
            env['PORT'] = str(self.primary_port)
            env['HOST'] = '0.0.0.0'
            
            self.primary_process = subprocess.Popen(
                [sys.executable, self.server_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            log.info(f"✅ Primary server started (PID: {self.primary_process.pid})")
            
        except Exception as e:
            log.error(f"❌ Failed to start primary server: {e}")
            self._start_backup()
    
    def _start_backup(self):
        """Start backup server"""
        log.info(f"🚀 Starting backup server: {self.backup_script}")
        
        try:
            self._kill_port_processes(self.backup_port)
            
            env = os.environ.copy()
            env['BACKUP_PORT'] = str(self.backup_port)
            env['PRIMARY_PORT'] = str(self.primary_port)
            
            self.backup_process = subprocess.Popen(
                [sys.executable, self.backup_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            log.info(f"✅ Backup server started (PID: {self.backup_process.pid})")
            
        except Exception as e:
            log.error(f"❌ Failed to start backup server: {e}")
    
    def _kill_port_processes(self, port: int):
        """Kill any processes using the specified port"""
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :{port}\') do taskkill /F /PID %a',
                             shell=True, capture_output=True)
            else:  # Unix
                subprocess.run(f"lsof -ti:{port} | xargs kill -9 2>/dev/null",
                             shell=True, capture_output=True)
        except:
            pass
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running.is_set():
            try:
                # Check if primary is running
                if self.primary_process:
                    ret_code = self.primary_process.poll()
                    
                    if ret_code is not None:
                        # Primary crashed
                        log.error(f"💥 Primary server crashed (exit code: {ret_code})")
                        self._handle_primary_crash()
                
                # Check if backup is running (if active)
                if self.backup_process:
                    ret_code = self.backup_process.poll()
                    
                    if ret_code is not None:
                        log.warning(f"⚠️ Backup server stopped (exit code: {ret_code})")
                        # Restart backup after delay
                        time.sleep(self.restart_delay)
                        self._start_backup()
                
                time.sleep(5)
                
            except Exception as e:
                log.error(f"Monitor loop error: {e}")
                time.sleep(10)
    
    def _handle_primary_crash(self):
        """Handle primary server crash"""
        log.info("🔄 Initiating failover sequence...")
        
        # Promote backup to primary
        if self.backup_process and self.backup_process.poll() is None:
            log.info("📡 Backup server already active - continuing")
        else:
            log.info("🚀 Starting backup server as emergency primary")
            self._start_backup()
        
        # Restart primary after delay
        time.sleep(self.restart_delay)
        self.restart_count += 1
        self.last_restart = datetime.now().isoformat()
        
        log.info(f"🔄 Restarting primary server (restart #{self.restart_count})")
        self._start_primary()
    
    def _health_check_loop(self):
        """Health check loop"""
        import urllib.request
        
        while self.running.is_set():
            try:
                # Check primary health
                primary_healthy = self._check_health(
                    f"http://localhost:{self.primary_port}/health"
                )
                
                health_status = {
                    "timestamp": datetime.now().isoformat(),
                    "primary_healthy": primary_healthy,
                    "backup_active": self.backup_process is not None and 
                                    self.backup_process.poll() is None,
                    "restart_count": self.restart_count
                }
                
                self.health_history.append(health_status)
                
                # Keep only last 1000 records
                if len(self.health_history) > 1000:
                    self.health_history = self.health_history[-1000:]
                
                if not primary_healthy and self.primary_process:
                    log.warning("⚠️ Primary server health check failed")
                    # Kill and restart primary
                    self._kill_process(self.primary_process)
                    time.sleep(self.restart_delay)
                    self._start_primary()
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                log.error(f"Health check error: {e}")
                time.sleep(self.health_check_interval)
    
    def _check_health(self, url: str, timeout: int = 5) -> bool:
        """Check server health"""
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.status == 200
        except:
            return False
    
    def _kill_process(self, process):
        """Kill a process safely"""
        try:
            if os.name != 'nt':
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()
            
            process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass
    
    def stop(self):
        """Stop all servers and monitoring"""
        log.info("🛑 Stopping all servers...")
        self.running.clear()
        
        if self.primary_process:
            self._kill_process(self.primary_process)
            log.info("✅ Primary server stopped")
        
        if self.backup_process:
            self._kill_process(self.backup_process)
            log.info("✅ Backup server stopped")
        
        # Save health history
        self._save_health_history()
        
        log.info("👋 Monitor shutdown complete")
    
    def _save_health_history(self):
        """Save health history to file"""
        try:
            with open('health_history.json', 'w') as f:
                json.dump({
                    "health_history": self.health_history,
                    "restart_count": self.restart_count,
                    "last_restart": self.last_restart,
                    "shutdown_time": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            log.error(f"Error saving health history: {e}")
    
    def get_status(self) -> dict:
        """Get current monitor status"""
        return {
            "primary_running": self.primary_process is not None and 
                              self.primary_process.poll() is None,
            "backup_running": self.backup_process is not None and 
                             self.backup_process.poll() is None,
            "primary_port": self.primary_port,
            "backup_port": self.backup_port,
            "restart_count": self.restart_count,
            "last_restart": self.last_restart,
            "uptime_checks": len(self.health_history)
        }


def create_systemd_service():
    """Create systemd service file for automatic startup"""
    service_content = """[Unit]
Description=AI Debate System Server Monitor
After=network.target

[Service]
Type=simple
User=%s
WorkingDirectory=%s
ExecStart=%s server_monitor.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
""" % (os.environ.get('USER', 'root'), 
      os.path.abspath('.'),
      sys.executable)
    
    service_path = "/etc/systemd/system/ai-debate-monitor.service"
    
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        log.info(f"Systemd service created: {service_path}")
        log.info("Run: sudo systemctl enable ai-debate-monitor && sudo systemctl start ai-debate-monitor")
    except PermissionError:
        log.warning(f"Permission denied creating systemd service. Run with sudo or create manually.")
        print("\n" + "=" * 60)
        print("SYSTEMD SERVICE CONFIGURATION")
        print("=" * 60)
        print(service_content)
        print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Server Monitor for AI Debate System")
    parser.add_argument('--status', action='store_true', help='Check monitor status')
    parser.add_argument('--install-service', action='store_true', help='Install systemd service')
    args = parser.parse_args()
    
    if args.install_service:
        create_systemd_service()
        sys.exit(0)
    
    if args.status:
        try:
            with open('health_history.json', 'r') as f:
                data = json.load(f)
                print(json.dumps(data, indent=2))
        except:
            print("No health history available")
        sys.exit(0)
    
    # Start monitoring
    monitor = ServerMonitor()
    
    try:
        monitor.start()
    except Exception as e:
        log.error(f"Monitor error: {e}")
        sys.exit(1)
