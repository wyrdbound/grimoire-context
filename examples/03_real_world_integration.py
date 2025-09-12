#!/usr/bin/env python3
"""
Real-World Integration Examples

This example demonstrates practical integration patterns for grimoire-context:
- Integration with web frameworks
- Database context patterns
- Configuration management
- Testing strategies
- Performance considerations
"""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from grimoire_context import GrimoireContext


def example_web_request_context():
    """Simulate web application request context pattern."""
    print("=== Web Application Request Context ===")
    
    # Application-level context (shared across requests)
    app_context = GrimoireContext({
        "app_name": "MyWebApp",
        "version": "2.1.0",
        "environment": "production",
        "database_url": "postgresql://localhost:5432/myapp",
        "cache_enabled": True,
        "debug_mode": False
    })
    
    def simulate_request(request_id: str, user_data: Dict[str, Any], route_params: Dict[str, Any]):
        """Simulate processing a web request with context inheritance."""
        
        # Request-level context inherits from application
        request_context = app_context.create_child_context({
            "request_id": request_id,
            "timestamp": time.time(),
            "method": "GET",
            "path": "/api/users/profile"
        })
        
        # User authentication context
        user_context = request_context.create_child_context({
            "user_id": user_data["id"],
            "username": user_data["username"], 
            "roles": user_data["roles"],
            "is_authenticated": True
        })
        
        # Route-specific context
        route_context = user_context.create_child_context(route_params)
        
        print(f"Processing request {request_id}:")
        print(f"  User: {route_context['username']} (ID: {route_context['user_id']})")
        print(f"  App: {route_context['app_name']} v{route_context['version']}")
        print(f"  Environment: {route_context['environment']}")
        print(f"  Route params: {route_params}")
        print(f"  Total context size: {len(route_context)} variables")
        
        return route_context
    
    # Simulate different requests
    user1 = {"id": 123, "username": "alice", "roles": ["user", "premium"]}
    user2 = {"id": 456, "username": "bob", "roles": ["user", "admin"]}
    
    req1_ctx = simulate_request("req_001", user1, {"profile_view": "public"})
    req2_ctx = simulate_request("req_002", user2, {"profile_view": "admin", "include_sensitive": True})
    
    # Contexts are independent
    print(f"Request 1 has admin role: {'admin' in req1_ctx['roles']}")
    print(f"Request 2 has admin role: {'admin' in req2_ctx['roles']}")


def example_configuration_management():
    """Demonstrate configuration management patterns."""
    print("\n=== Configuration Management ===")
    
    # Base configuration
    base_config = GrimoireContext({
        "database": {
            "host": "localhost", 
            "port": 5432,
            "name": "myapp",
            "pool_size": 10
        },
        "cache": {
            "type": "redis",
            "host": "localhost",
            "port": 6379,
            "ttl": 3600
        },
        "logging": {
            "level": "INFO",
            "format": "json"
        },
        "features": {
            "new_ui": False,
            "beta_features": False
        }
    })
    
    # Environment-specific overrides
    def create_environment_config(base: GrimoireContext, env: str) -> GrimoireContext:
        """Create environment-specific configuration."""
        
        if env == "development":
            return base.update({
                "database": {**base["database"], "host": "dev-db.local", "name": "myapp_dev"},
                "logging": {**base["logging"], "level": "DEBUG"},
                "features": {**base["features"], "new_ui": True, "beta_features": True}
            })
        elif env == "staging":
            return base.update({
                "database": {**base["database"], "host": "staging-db.company.com", "name": "myapp_staging"},
                "cache": {**base["cache"], "host": "staging-redis.company.com"},
                "logging": {**base["logging"], "level": "WARN"}
            })
        elif env == "production":
            return base.update({
                "database": {
                    **base["database"],
                    "host": "prod-db-cluster.company.com",
                    "name": "myapp_prod",
                    "pool_size": 50
                },
                "cache": {**base["cache"], "host": "prod-redis-cluster.company.com"},
                "logging": {**base["logging"], "level": "ERROR"}
            })
        else:
            return base
    
    # Show configuration for different environments
    for env in ["development", "staging", "production"]:
        config = create_environment_config(base_config, env)
        print(f"\n{env.upper()} configuration:")
        print(f"  Database: {config.get_variable('database.host')}:{config.get_variable('database.port')}")
        print(f"  DB Name: {config.get_variable('database.name')}")
        print(f"  Log Level: {config.get_variable('logging.level')}")
        print(f"  Beta Features: {config.get_variable('features.beta_features')}")


def example_testing_patterns():
    """Demonstrate testing patterns with contexts."""
    print("\n=== Testing Patterns ===")
    
    def create_test_context(test_name: str, **overrides) -> GrimoireContext:
        """Create a standardized test context."""
        base_test_data = {
            "test_name": test_name,
            "environment": "test",
            "database_url": "sqlite:///:memory:",
            "external_services": {"mock": True},
            "user": {
                "id": 999,
                "username": "test_user",
                "roles": ["user"]
            }
        }
        
        if overrides:
            return GrimoireContext(base_test_data).update(overrides)
        return GrimoireContext(base_test_data)
    
    def test_user_permissions():
        """Test user permission logic.""" 
        print("Running test_user_permissions:")
        
        # Test regular user
        regular_user_ctx = create_test_context(
            "test_regular_user",
            user={"id": 100, "username": "regular", "roles": ["user"]}
        )
        
        # Test admin user  
        admin_user_ctx = create_test_context(
            "test_admin_user", 
            user={"id": 200, "username": "admin", "roles": ["user", "admin"]}
        )
        
        def can_access_admin_panel(ctx: GrimoireContext) -> bool:
            return "admin" in ctx.get_variable("user.roles", [])
        
        regular_access = can_access_admin_panel(regular_user_ctx)
        admin_access = can_access_admin_panel(admin_user_ctx)
        
        print(f"  Regular user can access admin: {regular_access}")
        print(f"  Admin user can access admin: {admin_access}")
        
        assert not regular_access, "Regular user should not have admin access"
        assert admin_access, "Admin user should have admin access"
        print("  ✅ Permission tests passed!")
    
    def test_feature_flags():
        """Test feature flag functionality."""
        print("Running test_feature_flags:")
        
        # Test with feature enabled
        feature_enabled_ctx = create_test_context(
            "test_feature_enabled",
            features={"experimental_ui": True}
        )
        
        # Test with feature disabled
        feature_disabled_ctx = create_test_context(
            "test_feature_disabled",
            features={"experimental_ui": False}
        )
        
        enabled = feature_enabled_ctx.get_variable("features.experimental_ui", False)
        disabled = feature_disabled_ctx.get_variable("features.experimental_ui", False)
        
        print(f"  Feature enabled context: {enabled}")
        print(f"  Feature disabled context: {disabled}")
        
        assert enabled, "Feature should be enabled in test context"
        assert not disabled, "Feature should be disabled in test context"
        print("  ✅ Feature flag tests passed!")
    
    # Run tests
    test_user_permissions()
    test_feature_flags()


def example_performance_patterns():
    """Demonstrate performance optimization patterns."""
    print("\n=== Performance Optimization Patterns ===")
    
    def benchmark_context_operations(operation_count: int = 1000):
        """Benchmark context operations."""
        print(f"Benchmarking {operation_count} context operations...")
        
        # Test context creation performance
        start_time = time.time()
        contexts = []
        for i in range(operation_count):
            ctx = GrimoireContext({"iteration": i, "data": f"value_{i}"})
            contexts.append(ctx)
        creation_time = time.time() - start_time
        
        # Test variable access performance
        start_time = time.time()
        for ctx in contexts[:100]:  # Test subset for access
            _ = ctx["iteration"]
            _ = ctx.get_variable("data")
        access_time = time.time() - start_time
        
        # Test immutable operations performance
        start_time = time.time()
        base_ctx = contexts[0]
        for i in range(100):
            base_ctx = base_ctx.set_variable(f"key_{i}", f"value_{i}")
        mutation_time = time.time() - start_time
        
        print(f"  Creation: {creation_time:.3f}s ({operation_count} contexts)")
        print(f"  Access: {access_time:.4f}s (200 operations)")
        print(f"  Mutations: {mutation_time:.4f}s (100 operations)")
        print(f"  Final context size: {len(base_ctx)} variables")
    
    def benchmark_hierarchical_access():
        """Benchmark hierarchical context access patterns."""
        print("Benchmarking hierarchical access...")
        
        # Create deep hierarchy
        root = GrimoireContext({"level": 0, "root_data": "base"})
        current = root
        
        # Build 10-level deep hierarchy
        for i in range(1, 11):
            current = current.create_child_context({
                "level": i,
                f"level_{i}_data": f"data_at_level_{i}"
            })
        
        # Benchmark access to different levels
        start_time = time.time()
        for _ in range(1000):
            # Access data from different hierarchy levels
            _ = current["root_data"]  # From root (level 0)
            _ = current.get_variable("level_5_data")  # From middle level
            _ = current["level"]  # From current level
        hierarchy_time = time.time() - start_time
        
        print(f"  Hierarchy depth: 10 levels")
        print(f"  Access time: {hierarchy_time:.4f}s (3000 operations)")
        print(f"  Context chain length: {len(current)} variables")
    
    def benchmark_concurrent_contexts():
        """Benchmark concurrent context operations."""
        print("Benchmarking concurrent operations...")
        
        def worker_task(worker_id: int, operation_count: int = 100):
            """Worker that creates and modifies contexts."""
            base_ctx = GrimoireContext({"worker_id": worker_id})
            
            for i in range(operation_count):
                base_ctx = base_ctx.set_variable(f"operation_{i}", f"result_{i}")
                
                if i % 10 == 0:
                    # Periodic child context creation
                    child = base_ctx.create_child_context({"checkpoint": i})
            
            return len(base_ctx)
        
        start_time = time.time()
        
        # Run concurrent workers
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(worker_task, i, 50)
                for i in range(4)
            ]
            
            results = [future.result() for future in futures]
        
        concurrent_time = time.time() - start_time
        
        print(f"  Workers: 4")
        print(f"  Operations per worker: 50")
        print(f"  Total time: {concurrent_time:.3f}s")
        print(f"  Final context sizes: {results}")
    
    # Run benchmarks
    benchmark_context_operations(500)  # Reduced count for demo
    benchmark_hierarchical_access()
    benchmark_concurrent_contexts()


def example_integration_best_practices():
    """Demonstrate integration best practices."""
    print("\n=== Integration Best Practices ===")
    
    # 1. Context factory pattern
    class ContextFactory:
        """Factory for creating standardized contexts."""
        
        def __init__(self, base_config: GrimoireContext):
            self.base_config = base_config
        
        def create_request_context(self, request_id: str, user_id: Optional[int] = None) -> GrimoireContext:
            """Create a request context with standard fields."""
            ctx_data = {
                "request_id": request_id,
                "timestamp": time.time(),
                "session_id": f"session_{request_id}"
            }
            
            if user_id:
                ctx_data["user_id"] = user_id
                ctx_data["is_authenticated"] = True
            
            return self.base_config.create_child_context(ctx_data)
        
        def create_background_job_context(self, job_id: str, job_type: str) -> GrimoireContext:
            """Create a background job context."""
            return self.base_config.create_child_context({
                "job_id": job_id,
                "job_type": job_type,
                "started_at": time.time(),
                "is_background_job": True
            })
    
    # 2. Context middleware pattern  
    def logging_middleware(ctx: GrimoireContext, operation: str) -> GrimoireContext:
        """Middleware that adds logging context."""
        return ctx.set_variable("last_operation", {
            "name": operation,
            "timestamp": time.time()
        })
    
    def security_middleware(ctx: GrimoireContext) -> GrimoireContext:
        """Middleware that adds security context."""
        is_secure = ctx.get("is_authenticated", False) and "admin" in ctx.get("user.roles", [])
        return ctx.set_variable("security", {
            "is_secure_context": is_secure,
            "requires_audit": is_secure
        })
    
    # Demonstrate factory usage
    base_config = GrimoireContext({
        "app_name": "BestPracticesApp",
        "version": "1.0.0",
        "environment": "production"
    })
    
    factory = ContextFactory(base_config)
    
    # Create different context types
    request_ctx = factory.create_request_context("req_123", user_id=456)
    job_ctx = factory.create_background_job_context("job_789", "data_processing")
    
    # Apply middleware
    enhanced_request = logging_middleware(request_ctx, "user_profile_fetch")
    enhanced_request = security_middleware(enhanced_request)
    
    print("Factory-created contexts:")
    print(f"  Request context: {request_ctx['request_id']} (user: {request_ctx.get('user_id')})")
    print(f"  Job context: {job_ctx['job_id']} (type: {job_ctx['job_type']})")
    print(f"  Enhanced context has {len(enhanced_request)} variables")
    print(f"  Security context: {enhanced_request.get_variable('security.is_secure_context')}")


def main():
    """Run all integration examples."""
    print("GrimoireContext - Real-World Integration Examples")
    print("=" * 55)
    
    try:
        example_web_request_context()
        example_configuration_management()
        example_testing_patterns()
        example_performance_patterns()
        example_integration_best_practices()
        
        print("\n✅ All integration examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in integration examples: {e}")
        raise


if __name__ == "__main__":
    main()
