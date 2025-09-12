#!/usr/bin/env python3
"""
Comprehensive Logging Integration Example for grimoire-context

This example demonstrates how to integrate grimoire-context with grimoire-logging
for flexible logging configuration in your applications.
"""

import json
import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from io import StringIO

from grimoire_context import GrimoireContext
from grimoire_context.logging import clear_logger_injection, inject_logger


def example_basic_logging():
    """Basic logging integration with standard Python logging."""
    print("=== Basic Logging Integration ===")
    
    # Configure standard Python logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        stream=sys.stdout
    )
    
    # Create contexts - logging happens automatically
    context = GrimoireContext({"config": {"debug": True}, "app_name": "MyApp"})
    print(f"Created context with {len(context)} variables")
    
    # Child context creation is logged
    child = context.create_child_context({"user_id": 123})
    print(f"Child context has {len(child)} total variables")
    
    # Variable access warnings are logged when variables are missing
    missing_value = child.get("config.missing_setting")
    print(f"Missing value result: {missing_value}")


def example_json_logging():
    """JSON structured logging for production environments."""
    print("\n=== JSON Structured Logging ===")
    
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "service": "context_system",
                "version": "0.2.0"
            }
            return json.dumps(log_entry)
    
    # Setup JSON logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    json_logger = logging.getLogger("grimoire_context")
    json_logger.handlers.clear()
    json_logger.addHandler(handler)
    json_logger.setLevel(logging.INFO)
    
    # Use contexts with JSON logging
    context = GrimoireContext({"environment": "production", "service": "api"})
    child = context.create_child_context({"request_id": "req-789"})
    
    # Try to access a missing configuration
    missing_config = child.get("database.connection.url")
    print(f"Database config: {missing_config}")


def example_logger_injection():
    """Custom logger injection for testing and mocking."""
    print("\n=== Logger Injection for Testing ===")
    
    # Create a mock logger that captures log messages
    class MockLogger:
        def __init__(self):
            self.messages = []
            
        def info(self, msg: str, *args, **kwargs):
            self.messages.append(("INFO", msg % args if args else msg))
            
        def debug(self, msg: str, *args, **kwargs):
            self.messages.append(("DEBUG", msg % args if args else msg))
            
        def warning(self, msg: str, *args, **kwargs):
            self.messages.append(("WARNING", msg % args if args else msg))
            
        def error(self, msg: str, *args, **kwargs):
            self.messages.append(("ERROR", msg % args if args else msg))
            
        def critical(self, msg: str, *args, **kwargs):
            self.messages.append(("CRITICAL", msg % args if args else msg))
    
    # Inject the mock logger
    mock_logger = MockLogger()
    inject_logger(mock_logger)
    
    try:
        # Perform operations that generate log messages
        context = GrimoireContext({"test": True})
        child = context.create_child_context({"child_test": "value"})
        
        # Try parallel operations to see merge logging
        operations = [
            lambda ctx: ctx.set_variable("op1", "result1"),
            lambda ctx: ctx.set_variable("op2", "result2"),
        ]
        
        results = context.execute_parallel(operations)
        
        # Display captured messages
        print("Captured log messages:")
        for level, message in mock_logger.messages:
            print(f"  [{level}] {message}")
            
    finally:
        # Clean up logger injection
        clear_logger_injection()


def example_concurrent_logging():
    """Thread-safe logging in concurrent environments."""
    print("\n=== Concurrent Logging ===")
    
    # Configure logging with thread info
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(levelname)s] [%(threadName)s] %(message)s',
        stream=sys.stdout,
        force=True
    )
    
    def worker_task(worker_id, base_context):
        """Simulate work that creates contexts and performs operations."""
        thread_name = f"ContextWorker_{worker_id}"
        threading.current_thread().name = thread_name
        
        print(f"Worker {worker_id} starting...")
        
        # Create worker-specific context
        worker_context = base_context.create_child_context({
            "worker_id": worker_id,
            "task_type": "data_processing"
        })
        
        # Simulate multiple operations
        for i in range(3):
            worker_context = worker_context.set_variable(f"task_{i}", f"completed_by_worker_{worker_id}")
            time.sleep(0.01)  # Small delay to show concurrent logging
        
        # Try to access a missing configuration
        missing_config = worker_context.get(f"missing_config_for_worker_{worker_id}")
        
        print(f"Worker {worker_id} completed.")
        return worker_context
    
    # Create base context
    base_context = GrimoireContext({"app": "concurrent_demo", "version": "1.0"})
    
    print("Starting concurrent context operations...")
    
    # Run multiple workers concurrently
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="ContextWorker") as executor:
        futures = [
            executor.submit(worker_task, i, base_context)
            for i in range(3)
        ]
        
        # Wait for all workers to complete
        results = [future.result() for future in futures]
    
    print(f"All {len(results)} workers completed successfully.")


def example_performance_monitoring():
    """Performance-oriented logging with metrics."""
    print("\n=== Performance Monitoring ===")
    
    # Custom formatter with timing
    class PerformanceFormatter(logging.Formatter):
        def format(self, record):
            return f"[{time.strftime('%H:%M:%S.%f')[:-3]}] [{record.levelname}] {record.getMessage()}"
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(PerformanceFormatter())
    
    perf_logger = logging.getLogger("grimoire_context")
    perf_logger.handlers.clear()
    perf_logger.addHandler(handler)
    perf_logger.setLevel(logging.DEBUG)
    
    print("Creating contexts with performance logging...")
    
    # Simulate a performance scenario
    start_time = time.time()
    
    # Create increasingly complex contexts
    contexts = []
    for i in range(6):
        if i == 0:
            context = GrimoireContext({f"test_key_{j}": f"value_{j}" for j in range(i + 1)})
        else:
            context = contexts[-1].set_variable(f"test_key_{i}", f"value_{i}")
        contexts.append(context)
    
    # Bulk update for performance testing  
    bulk_data = {f"bulk_key_{i}": f"bulk_value_{i}" for i in range(10)}
    final_context = contexts[-1].update(bulk_data)
    
    # Create child contexts to test hierarchy performance
    child_contexts = []
    for i in range(3):
        child = final_context.create_child_context({f"child_{i}": f"child_value_{i}"})
        child_contexts.append(child)
    
    elapsed = time.time() - start_time
    print(f"Total benchmark time: {elapsed * 1000:.2f}ms")


def main():
    """Run all logging integration examples."""
    print("Grimoire Context - Logging Integration Examples")
    print("=" * 50)
    
    try:
        example_basic_logging()
        example_json_logging()
        example_logger_injection() 
        example_concurrent_logging()
        example_performance_monitoring()
        
        print("\nAll logging integration examples completed!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
