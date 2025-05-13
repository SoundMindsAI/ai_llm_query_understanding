#!/usr/bin/env python3
"""
Entry point script for the LLM Query Understanding Service.

This script starts the FastAPI application using Uvicorn ASGI server.
It can be run directly from the command line with automatic port conflict resolution.
"""
import uvicorn
import os
import sys
import argparse
import socket
import signal
import subprocess
import time
from typing import Optional, List, Tuple


def is_port_in_use(host: str, port: int) -> bool:
    """
    Check if the specified port is already in use.
    
    Args:
        host: The host to check
        port: The port to check
        
    Returns:
        True if the port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def find_processes_using_port(port: int) -> List[int]:
    """
    Find process IDs using the specified port on macOS/Linux.
    
    Args:
        port: The port to check
        
    Returns:
        List of process IDs using the port
    """
    try:
        # Run lsof command to find processes using the port
        cmd = f"lsof -i :{port} -t"
        output = subprocess.check_output(cmd, shell=True, text=True)
        pids = [int(pid.strip()) for pid in output.split('\n') if pid.strip()]
        return pids
    except subprocess.CalledProcessError:
        # No processes found or command failed
        return []


def kill_processes(pids: List[int], force: bool = False) -> Tuple[bool, List[int]]:
    """
    Kill the specified processes.
    
    Args:
        pids: List of process IDs to kill
        force: If True, use SIGKILL instead of SIGTERM
        
    Returns:
        Tuple of (success, remaining_pids)
    """
    if not pids:
        return True, []
        
    remaining = []
    sig = signal.SIGKILL if force else signal.SIGTERM
    
    for pid in pids:
        try:
            os.kill(pid, sig)
            print(f"Killed process {pid} using {'SIGKILL' if force else 'SIGTERM'}")
        except OSError:
            # Process might not exist anymore
            pass
    
    # Give processes a moment to terminate
    time.sleep(0.5)
    
    # Check if any processes are still alive
    for pid in pids:
        try:
            os.kill(pid, 0)  # Does not kill the process, just checks if it exists
            remaining.append(pid)
        except OSError:
            # Process no longer exists
            pass
    
    return len(remaining) == 0, remaining


def ensure_port_available(host: str, port: int, max_attempts: int = 3) -> bool:
    """
    Ensure the specified port is available by killing any processes using it.
    
    Args:
        host: The host to check
        port: The port to check
        max_attempts: Maximum number of attempts to free the port
        
    Returns:
        True if the port was freed successfully, False otherwise
    """
    # First check if the port is even in use
    if not is_port_in_use(host, port):
        return True
        
    print(f"Port {port} is already in use. Attempting to free it...")
    
    # More aggressive approach: kill all processes on this port immediately
    for attempt in range(max_attempts):
        # Use direct system commands to find and kill processes
        try:
            # Find processes using the specified port with lsof
            print(f"Finding processes using port {port}...")
            os.system(f"lsof -i :{port}")
            
            # Kill processes using the port with both methods to be thorough
            print(f"Killing all processes using port {port}...")
            os.system(f"lsof -ti :{port} | xargs kill -9 2>/dev/null || true")
            
            # Also try the alternate pkill approach as a backup
            os.system(f"pkill -f ':{port}' 2>/dev/null || true")
            
            # Give the system a moment to release the port
            time.sleep(1)
            
            # Check if the port is now available
            if not is_port_in_use(host, port):
                print(f"Successfully freed port {port}")
                return True
                
            # If we're still here, the port is still in use
            print(f"Port {port} is still in use after attempt {attempt + 1}/{max_attempts}")
            
        except Exception as e:
            print(f"Error trying to free port {port}: {e}")
        
        # Short delay before the next attempt
        time.sleep(1)
    
    print(f"WARNING: Failed to free port {port} after {max_attempts} attempts.")
    return False


def force_kill_port_processes(port: int) -> bool:
    """
    Forcefully kill any processes using the specified port using direct shell commands.
    This is more reliable than the Python-based approach.
    
    Args:
        port: The port to free up
        
    Returns:
        True if the command executed successfully (doesn't guarantee port is free)
    """
    # Print processes using the port
    print(f"\nProcesses using port {port}:")
    os.system(f"lsof -i :{port} 2>/dev/null || echo 'No processes found'")
    print()
    
    # Three different approaches to kill processes on the port
    try:
        # Method 1: Use lsof to find PIDs and kill -9 them directly
        os.system(f"lsof -ti :{port} | xargs kill -9 2>/dev/null || true")
        
        # Method 2: Use pkill to find processes by port in command line
        os.system(f"pkill -f ':{port}' 2>/dev/null || true")
        
        # Method 3: Use fuser to kill processes using the port (Linux-specific but worth trying)
        os.system(f"fuser -k {port}/tcp 2>/dev/null || true")
        
        # Wait a moment for OS to free the port
        time.sleep(2)
        
        return True
    except Exception as e:
        print(f"Error killing processes on port {port}: {e}")
        return False


def start_server(host: str = "0.0.0.0", port: int = 8000,
                reload: bool = True, log_level: str = "info",
                max_retries: int = 3) -> None:
    """
    Start the LLM Query Understanding Service using Uvicorn with automatic port conflict resolution.
    Aggressively kills any existing processes using the port before starting.
    
    Args:
        host: The host to bind the server to
        port: The port to bind the server to
        reload: Whether to enable auto-reload on code changes
        log_level: The log level for Uvicorn (debug, info, warning, error, critical)
        max_retries: Maximum number of retries if port conflicts occur
    """
    original_port = port
    
    # Always attempt to kill any processes on the port before starting
    print(f"Ensuring port {port} is available by killing any existing processes...")
    force_kill_port_processes(port)
    
    for attempt in range(max_retries):
        try:
            print(f"\nStarting LLM Query Understanding Service on {host}:{port}... (Attempt {attempt+1}/{max_retries})")
            uvicorn.run(
                "llm_query_understand.api.app:app",
                host=host,
                port=port,
                reload=reload,
                log_level=log_level
            )
            # If we get here, the server started successfully
            return
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {port} is still in use. Attempting to force-kill processes...")
                force_kill_port_processes(port)
                
                # If this isn't our last attempt, wait a moment and try again
                if attempt < max_retries - 1:
                    print("Waiting before retrying...")
                    time.sleep(2)
                    continue
                    
                # On the last attempt, try an alternate port if we haven't already
                if port == original_port:
                    port = original_port + 1
                    print(f"\nSwitching to alternate port {port}...")
                    force_kill_port_processes(port)  # Kill any processes on the new port too
                    attempt = 0  # Reset attempts for the new port
                    continue
            
            # If we get here, we've tried the original port and an alternate port
            print(f"\nError starting server: {e}")
            print("Could not start the server after multiple attempts.")
            sys.exit(1)
        except Exception as e:
            # Handle other exceptions
            print(f"\nUnexpected error starting server: {e}")
            sys.exit(1)


def main() -> None:
    """
    Command-line entry point with argument parsing.
    """
    parser = argparse.ArgumentParser(description="LLM Query Understanding Service")
    
    # Add command line arguments
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload on code changes")
    parser.add_argument("--log-level", default="info", 
                        choices=["debug", "info", "warning", "error", "critical"],
                        help="Log level for Uvicorn")
    
    args = parser.parse_args()
    
    # Start the server with the provided arguments
    start_server(
        host=args.host, 
        port=args.port,
        reload=not args.no_reload,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()
