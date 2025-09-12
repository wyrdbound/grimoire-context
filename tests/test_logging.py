"""Tests for logging injection functionality."""

import logging
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from grimoire_context import GrimoireContext
from grimoire_context.exceptions import (
    ContextMergeError,
    PathResolutionError,
    TemplateError,
)
from grimoire_context.logging import get_logger, inject_logger


class MockLogger:
    """Mock logger for testing."""

    def __init__(self):
        self.debug_calls = []
        self.info_calls = []
        self.warning_calls = []
        self.error_calls = []
        self.critical_calls = []

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.debug_calls.append(msg % args if args and "%" in msg else msg)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.info_calls.append(msg % args if args and "%" in msg else msg)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.warning_calls.append(msg % args if args and "%" in msg else msg)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.error_calls.append(msg % args if args and "%" in msg else msg)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self.critical_calls.append(msg % args if args and "%" in msg else msg)


class TestLoggingInjection:
    """Test logging injection and configuration."""

    def test_default_logger_creation(self):
        """Test that get_logger returns a logger that implements the protocol."""
        logger = get_logger("test_module")

        # Verify it has the required methods
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")

    def test_logger_injection(self):
        """Test injecting a custom logger."""
        mock_logger = MockLogger()

        # Inject the custom logger
        inject_logger(mock_logger)

        # Get logger should work with injected logger
        logger = get_logger("test_module")

        # Test that the logger delegates to our injected logger
        logger.debug("test message")
        assert "test message" in mock_logger.debug_calls

        # Reset to default
        inject_logger(None)

    def test_logger_protocol_compliance(self):
        """Test that mock logger implements the protocol correctly."""
        mock_logger = MockLogger()

        # Should have all required methods
        assert hasattr(mock_logger, "debug")
        assert hasattr(mock_logger, "info")
        assert hasattr(mock_logger, "warning")
        assert hasattr(mock_logger, "error")

        # Test method calls
        mock_logger.debug("debug message")
        mock_logger.info("info message")
        mock_logger.warning("warning message")
        mock_logger.error("error message")

        assert "debug message" in mock_logger.debug_calls
        assert "info message" in mock_logger.info_calls
        assert "warning message" in mock_logger.warning_calls
        assert "error message" in mock_logger.error_calls

    def test_context_creation_logging(self):
        """Test that context creation generates appropriate log messages."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        try:
            # Create a context
            context = GrimoireContext({"key1": "value1", "key2": "value2"})

            # Should have logged context creation
            assert len(mock_logger.debug_calls) >= 1

            # Check that the log message contains expected content
            creation_log = mock_logger.debug_calls[0]
            assert "Created GrimoireContext" in creation_log
            assert "2 local keys" in creation_log
            assert context.context_id in creation_log

        finally:
            # Reset logger
            inject_logger(None)

    def test_child_context_logging(self):
        """Test logging when creating child contexts."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        try:
            # Create parent context
            parent = GrimoireContext({"parent_key": "parent_value"})
            mock_logger.debug_calls.clear()  # Clear creation logs

            # Create child context
            parent.create_child_context({"child_key": "child_value"})

            # Should have logged child creation
            assert len(mock_logger.debug_calls) >= 1
            creation_log = mock_logger.debug_calls[0]
            assert "Created GrimoireContext" in creation_log
            assert "with parent" in creation_log

        finally:
            inject_logger(None)

    def test_template_resolution_logging(self):
        """Test logging during template resolution."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        try:
            # Create a mock template resolver
            mock_resolver = Mock()
            mock_resolver.resolve_template.return_value = "resolved_value"

            context = GrimoireContext({"var": "test"}, template_resolver=mock_resolver)
            mock_logger.debug_calls.clear()  # Clear creation logs

            # Resolve a template
            context.resolve_template("Hello {{var}}")

            # Should have logged template resolution
            debug_logs = [
                log for log in mock_logger.debug_calls if "Resolving template" in log
            ]
            assert len(debug_logs) >= 1
            assert "Hello {{var}}" in debug_logs[0]

        finally:
            inject_logger(None)

    def test_template_resolution_error_logging(self):
        """Test logging when template resolution fails."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        try:
            # Create a mock template resolver that raises an error
            mock_resolver = Mock()
            mock_resolver.resolve_template.side_effect = Exception("Template error")

            context = GrimoireContext({"var": "test"}, template_resolver=mock_resolver)
            mock_logger.debug_calls.clear()
            mock_logger.error_calls.clear()

            # Try to resolve template (should fail)
            with pytest.raises(TemplateError):
                context.resolve_template("Hello {{var}}")

            # Should have logged the error
            assert len(mock_logger.error_calls) >= 1
            error_log = mock_logger.error_calls[0]
            assert "Template resolution failed" in error_log
            assert context.context_id in error_log

        finally:
            inject_logger(None)

    def test_no_template_resolver_error_logging(self):
        """Test that missing template resolver doesn't log errors (just raises)."""
        mock_logger = MockLogger()
        inject_logger(mock_logger)

        try:
            context = GrimoireContext({"var": "test"})
            mock_logger.error_calls.clear()

            # Try to resolve template without resolver
            with pytest.raises(TemplateError):
                context.resolve_template("Hello {{var}}")

            # Should not have logged an error (just raised exception)
            assert len(mock_logger.error_calls) == 0

        finally:
            inject_logger(None)

    def test_merge_conflict_logging(self):
        """Test logging when merge conflicts are detected."""
        from grimoire_context.merge import ContextMerger

        mock_logger = MockLogger()
        inject_logger(mock_logger)

        try:
            # Create contexts that will conflict
            base_context = GrimoireContext({"shared_key": "original"})
            context1 = base_context.set("shared_key", "value1")
            context2 = base_context.set("shared_key", "value2")

            mock_logger.warning_calls.clear()

            # Try to merge conflicting contexts
            with pytest.raises(ContextMergeError):
                ContextMerger.merge_contexts_with_base(
                    [context1, context2], base_context
                )

            # Should have logged the conflict
            assert len(mock_logger.warning_calls) >= 1
            warning_log = mock_logger.warning_calls[0]
            assert "Path conflicts detected" in warning_log

        finally:
            inject_logger(None)

    def test_path_resolution_error_logging(self):
        """Test logging when path resolution fails."""
        from pyrsistent import pmap

        from grimoire_context.path_resolver import set_nested_path

        mock_logger = MockLogger()
        inject_logger(mock_logger)

        try:
            mock_logger.error_calls.clear()

            # Create a scenario that will cause a path resolution error
            # This is a bit tricky since the path resolver is quite robust
            # Let's patch something to force an error
            with patch("grimoire_context.path_resolver.pmap") as mock_pmap:
                mock_pmap.side_effect = Exception("Forced error")

                with pytest.raises(PathResolutionError):
                    set_nested_path(pmap({}), "test.path", "value")

                # Should have logged the error
                assert len(mock_logger.error_calls) >= 1
                error_log = mock_logger.error_calls[0]
                assert "Failed to set nested path 'test.path'" in error_log

        finally:
            inject_logger(None)

    def test_standard_logging_integration(self):
        """Test that standard Python logging works properly."""
        # Create a string stream to capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.DEBUG)

        # Create a logger and add our handler
        test_logger = logging.getLogger("grimoire_context.test")
        test_logger.setLevel(logging.DEBUG)
        test_logger.addHandler(handler)

        try:
            # Inject the standard logger (should work fine)
            inject_logger(None)  # Use standard logging

            # Create context which should log via standard logging
            context = GrimoireContext({"test": "value"})

            # The actual logging goes to the module's logger, not our test logger
            # So we can't easily capture it, but we can verify no exceptions occur
            assert context.context_id is not None

        finally:
            test_logger.removeHandler(handler)
            inject_logger(None)


class TestLoggingThreadSafety:
    """Test that logging injection is thread-safe."""

    def test_concurrent_logger_access(self):
        """Test that logger access is thread-safe with grimoire-logging."""
        import threading

        results = []
        errors = []

        def worker(worker_id: int):
            try:
                # Access logger from multiple threads
                logger = get_logger(f"worker_{worker_id}")

                # Perform logging operations
                for i in range(100):
                    logger.debug(f"Worker {worker_id} message {i}")
                    logger.info(f"Worker {worker_id} info {i}")

                results.append(worker_id)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # Use multiple threads
        threads = []
        for i in range(20):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 20

    def test_logger_injection_race_condition(self):
        """Test for race conditions during logger injection."""
        import threading

        mock_logger1 = MockLogger()
        mock_logger2 = MockLogger()
        mock_logger3 = MockLogger()

        injection_results = []
        access_results = []
        errors = []

        def rapid_injector(logger, injector_id):
            """Rapidly inject loggers to create race conditions."""
            try:
                for _i in range(1000):
                    inject_logger(logger)
                    # Just do the injection, don't check immediately
                    # (other threads will change it concurrently)
                injection_results.append(injector_id)
            except Exception as e:
                errors.append(f"Injector {injector_id}: {str(e)}")

        def rapid_accessor(accessor_id):
            """Rapidly access logger state to detect inconsistencies."""
            try:
                logger_proxy = get_logger(f"accessor_{accessor_id}")
                for i in range(1000):
                    # This should always work, even during injection changes
                    # Test actual logging calls which use _get_current_logger internally
                    logger_proxy.debug(f"Test message {i}")
                access_results.append(accessor_id)
            except Exception as e:
                errors.append(f"Accessor {accessor_id}: {str(e)}")

        # Start multiple threads doing rapid injections and access
        threads = []

        # Multiple injector threads with different loggers
        for i, logger in enumerate([mock_logger1, mock_logger2, mock_logger3]):
            thread = threading.Thread(target=rapid_injector, args=(logger, i))
            threads.append(thread)

        # Multiple accessor threads
        for i in range(10):
            thread = threading.Thread(target=rapid_accessor, args=(i,))
            threads.append(thread)

        # Start all threads simultaneously (no delays)
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Clean up
        inject_logger(None)

        assert len(errors) == 0, f"Race conditions detected: {errors[:10]}"
        assert len(injection_results) == 3
        assert len(access_results) == 10

    def test_concurrent_logger_injection(self):
        """Test that logger injection works safely in concurrent environment."""
        import threading

        mock_logger = MockLogger()
        errors = []
        results = []

        def worker(worker_id: int):
            """Worker that performs logging operations."""
            try:
                logger = get_logger(f"concurrent_worker_{worker_id}")

                # Perform logging operations
                for i in range(10):
                    logger.info(f"Worker {worker_id} operation {i}")
                    logger.debug(f"Worker {worker_id} debug {i}")

                results.append(worker_id)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # Inject logger before starting threads
        inject_logger(mock_logger)

        try:
            # Start multiple threads
            threads = []
            for i in range(10):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            assert len(errors) == 0, f"Concurrent errors: {errors}"
            assert len(results) == 10

            # Should have captured messages from all workers
            assert len(mock_logger.info_calls) > 0
            assert len(mock_logger.debug_calls) > 0

        finally:
            inject_logger(None)
