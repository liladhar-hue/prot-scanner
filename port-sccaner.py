import socket
import sys
from datetime import datetime
import threading
from queue import Queue

# A thread-safe queue to manage the ports to be scanned.
q = Queue()
# A list to store the open ports found by the threads.
open_ports = []
# A threading.Event to signal a graceful stop for all threads if an error occurs.
stop_event = threading.Event()

def worker(target):
    """
    Worker function for each thread.
    Pulls a port from the queue and scans it.
    """
    while not stop_event.is_set():
        try:
            # Use a timeout on get() to avoid blocking indefinitely if the queue is empty
            # and a fatal error has occurred in another thread.
            port = q.get(timeout=1)
            port_scanner(target, port)
            q.task_done()
        except Queue.Empty:
            # Continue looping if the queue is empty until the stop event is set.
            continue
        except Exception as e:
            # If any other error occurs, set the stop event to gracefully exit all threads.
            print(f"An error occurred in a worker thread: {e}", file=sys.stderr)
            stop_event.set()
            break

def port_scanner(target, port):
    """
    Attempts to connect to a specific port on the target host.
    This function will be run by each worker thread.
    """
    try:
        # Create a new socket object.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Set a short timeout for the connection attempt.
        # A shorter timeout will make the scan much faster.
        s.settimeout(0.5)
        
        # Attempt to connect to the target host and port.
        result = s.connect_ex((target, port))
        
        # Check the result of the connection attempt.
        if result == 0:
            # If the port is open, add it to the list.
            open_ports.append(port)
            
    finally:
        s.close()

def main():
    """
    Main function to handle user input and run the port scan.
    """
    print("-" * 50)
    print("Simple Port Scanner (Multithreaded)")
    print("-" * 50)
    
    # Get the target host from the user.
    target = input("Enter the target host to scan (e.g., example.com): ")
    
    # Resolve the hostname to an IP address before starting the threads.
    # This prevents worker threads from failing and causing the program to hang.
    try:
        host_ip = socket.gethostbyname(target)
    except socket.gaierror:
        print("Hostname could not be resolved. Exiting.")
        sys.exit()

    # Get the port range from the user.
    try:
        start_port = int(input("Enter the starting port: "))
        end_port = int(input("Enter the ending port: "))
    except ValueError:
        print("Invalid port number. Please enter a valid integer.")
        sys.exit()
        
    print(f"Scanning target: {target} ({host_ip})")
    
    # Record the start time of the scan.
    start_time = datetime.now()

    # Create worker threads.
    for _ in range(200):
        t = threading.Thread(target=worker, args=(target,))
        # Set the thread as a daemon so it exits when the main program exits.
        t.daemon = True
        t.start()
        
    # Populate the queue with all the ports in the range.
    for port in range(start_port, end_port + 1):
        q.put(port)

    # Wait for all tasks in the queue to be completed.
    q.join()
            
    # Record the end time and calculate the total duration.
    end_time = datetime.now()
    total_time = end_time - start_time
    
    print("-" * 50)
    print("Scan completed.")
    print(f"Scan duration: {total_time}")
    
    if open_ports:
        # Sort the open ports for a cleaner summary.
        open_ports.sort()
        print("\nSummary of open ports:")
        for port in open_ports:
            print(f"- {port}")
    else:
        print("\nNo open ports found in the specified range.")

if __name__ == "__main__":
    main()
