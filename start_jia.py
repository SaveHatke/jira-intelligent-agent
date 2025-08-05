#!/usr/bin/env python3
"""
JIA Application Startup Script

This script starts both the MCP server and the Flask application.
"""

import subprocess
import sys
import time
import os
import signal
import argparse
from pathlib import Path

def start_mcp_server():
    """Start the MCP server in the background."""
    print("🚀 Starting MCP Atlassian server...")
    
    try:
        # Start MCP server
        mcp_process = subprocess.Popen([
            sys.executable, "manage_mcp_server.py", "start"
        ])
        
        # Wait for it to complete startup
        mcp_process.wait()
        
        if mcp_process.returncode == 0:
            print("✅ MCP server started successfully")
            return True
        else:
            print("❌ Failed to start MCP server")
            return False
            
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        return False

def start_flask_app():
    """Start the Flask application."""
    print("🌐 Starting JIA Flask application...")
    
    try:
        # Start Flask app
        flask_process = subprocess.Popen([
            sys.executable, "jia.py"
        ])
        
        return flask_process
        
    except Exception as e:
        print(f"❌ Error starting Flask app: {e}")
        return None

def stop_all_services():
    """Stop all services."""
    print("🛑 Stopping all services...")
    
    # Stop MCP server
    subprocess.run([sys.executable, "manage_mcp_server.py", "stop"])
    
    print("✅ All services stopped")

def main():
    parser = argparse.ArgumentParser(description="Start JIA application with MCP server")
    parser.add_argument("--mcp-only", action="store_true", 
                       help="Start only MCP server")
    parser.add_argument("--flask-only", action="store_true", 
                       help="Start only Flask app (assumes MCP server is running)")
    parser.add_argument("--stop", action="store_true", 
                       help="Stop all services")
    
    args = parser.parse_args()
    
    if args.stop:
        stop_all_services()
        return
    
    flask_process = None
    
    try:
        if args.flask_only:
            # Start only Flask app
            flask_process = start_flask_app()
        elif args.mcp_only:
            # Start only MCP server
            start_mcp_server()
        else:
            # Start both (default)
            print("🚀 Starting JIA Application Suite...")
            print("=" * 50)
            
            # Start MCP server first
            if start_mcp_server():
                # Start Flask app
                flask_process = start_flask_app()
                
                if flask_process:
                    print("=" * 50)
                    print("✅ JIA Application Suite started successfully!")
                    print("🌐 Flask app: http://localhost:5000")
                    print("🔧 MCP server: http://localhost:8080")
                    print("=" * 50)
                    print("Press Ctrl+C to stop all services")
                    
                    # Wait for Flask app to finish
                    flask_process.wait()
                else:
                    print("❌ Failed to start Flask app")
                    stop_all_services()
                    sys.exit(1)
            else:
                print("❌ Failed to start MCP server")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal...")
        
        # Stop Flask app
        if flask_process:
            print("🛑 Stopping Flask app...")
            flask_process.terminate()
            try:
                flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                flask_process.kill()
        
        # Stop MCP server
        stop_all_services()
        
        print("✅ All services stopped gracefully")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        stop_all_services()
        sys.exit(1)

if __name__ == "__main__":
    main()