#!/usr/bin/env python3
"""
MCP Server Management Script for JIA application.

This script helps start, stop, and manage the mcp-atlassian server
for the JIA application.
"""

import subprocess
import sys
import time
import requests
import argparse
import signal
import os
from pathlib import Path

class MCPServerManager:
    def __init__(self, port=8080, host="localhost"):
        self.port = port
        self.host = host
        self.server_url = f"http://{host}:{port}"
        self.process = None
        self.pid_file = Path("mcp_server.pid")
    
    def is_server_running(self):
        """Check if the MCP server is running."""
        try:
            # Try the MCP endpoint - should return error about content type but server is running
            response = requests.get(f"{self.server_url}/mcp", timeout=5)
            # If we get any response (even error), server is running
            return True
        except requests.exceptions.ConnectionError:
            # Connection refused means server is not running
            return False
        except:
            # Any other response means server is running
            return True
    
    def start_server(self):
        """Start the MCP server."""
        if self.is_server_running():
            print(f"✅ MCP server is already running at {self.server_url}")
            return True
        
        print(f"🚀 Starting MCP server at {self.server_url}...")
        
        try:
            # Start the mcp-atlassian server with streamable-HTTP transport
            cmd = [
                sys.executable, "-c", 
                f"import sys; sys.argv = ['mcp-atlassian', '--transport', 'streamable-http', '--port', '{self.port}', '--host', '{self.host}']; import mcp_atlassian; mcp_atlassian.main()"
            ]
            
            print(f"🔧 Command: {' '.join(cmd)}")
            
            # Start server in background
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True
            )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(self.process.pid))
            
            # Wait for server to start
            max_retries = 15
            for i in range(max_retries):
                time.sleep(1)
                if self.is_server_running():
                    print(f"✅ MCP server started successfully at {self.server_url}")
                    print(f"📝 Server PID: {self.process.pid}")
                    return True
                print(f"⏳ Waiting for server to start... ({i+1}/{max_retries})")
                
                # Check if process is still running
                if self.process.poll() is not None:
                    print("❌ Server process exited unexpectedly")
                    # Get the output
                    stdout, _ = self.process.communicate()
                    if stdout:
                        print(f"Server output:\n{stdout}")
                    break
            
            print("❌ Failed to start MCP server")
            self.stop_server()
            return False
            
        except Exception as e:
            print(f"❌ Error starting MCP server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server."""
        stopped = False
        
        # Try to stop using PID file
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                print(f"🛑 Stopping MCP server (PID: {pid})...")
                os.kill(pid, signal.SIGTERM)
                
                # Wait for process to stop
                for i in range(10):
                    time.sleep(0.5)
                    try:
                        os.kill(pid, 0)  # Check if process exists
                    except OSError:
                        stopped = True
                        break
                
                if not stopped:
                    print("⚠️ Process didn't stop gracefully, forcing...")
                    try:
                        # On Windows, use SIGTERM instead of SIGKILL
                        if os.name == 'nt':
                            os.kill(pid, signal.SIGTERM)
                        else:
                            os.kill(pid, signal.SIGKILL)
                        stopped = True
                    except:
                        pass
                
                self.pid_file.unlink()
                
            except Exception as e:
                print(f"⚠️ Error stopping server via PID: {e}")
        
        # Try to stop current process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                stopped = True
            except:
                try:
                    self.process.kill()
                    stopped = True
                except:
                    pass
        
        if stopped:
            print("✅ MCP server stopped")
        else:
            print("⚠️ Could not confirm server was stopped")
        
        return stopped
    
    def restart_server(self):
        """Restart the MCP server."""
        print("🔄 Restarting MCP server...")
        self.stop_server()
        time.sleep(2)
        return self.start_server()
    
    def status(self):
        """Check server status."""
        if self.is_server_running():
            print(f"✅ MCP server is running at {self.server_url}")
            
            # Check PID file
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    pid = f.read().strip()
                print(f"📝 Server PID: {pid}")
            
            return True
        else:
            print(f"❌ MCP server is not running")
            return False


def main():
    parser = argparse.ArgumentParser(description="Manage MCP Atlassian server for JIA")
    parser.add_argument("action", choices=["start", "stop", "restart", "status"], 
                       help="Action to perform")
    parser.add_argument("--port", type=int, default=8080, 
                       help="Server port (default: 8080)")
    parser.add_argument("--host", default="localhost", 
                       help="Server host (default: localhost)")
    
    args = parser.parse_args()
    
    manager = MCPServerManager(port=args.port, host=args.host)
    
    if args.action == "start":
        success = manager.start_server()
        sys.exit(0 if success else 1)
    elif args.action == "stop":
        success = manager.stop_server()
        sys.exit(0 if success else 1)
    elif args.action == "restart":
        success = manager.restart_server()
        sys.exit(0 if success else 1)
    elif args.action == "status":
        success = manager.status()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()