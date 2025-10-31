#!/usr/bin/env python3
"""
Comprehensive System Test for OrderPilot-AI Trading Application
This script performs a complete verification of all application components
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class ComprehensiveApplicationTester:
    """
    Complete application tester for OrderPilot-AI
    """

    def __init__(self):
        self.app_name = "OrderPilot-AI Trading Application"
        self.test_results = {
            "app_name": self.app_name,
            "test_date": datetime.now().isoformat(),
            "components_tested": [],
            "components_passed": [],
            "components_failed": [],
            "errors": [],
            "warnings": [],
            "test_coverage": 0.0
        }
        self.total_tests = 0
        self.passed_tests = 0

    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Execute a single test and record results"""
        self.total_tests += 1
        try:
            print(f"  ✓ Testing {test_name}...", end=" ")
            result = test_func(*args, **kwargs)
            if result:
                print("PASSED ✅")
                self.passed_tests += 1
                self.test_results["components_passed"].append(test_name)
                return True
            else:
                print("FAILED ❌")
                self.test_results["components_failed"].append(test_name)
                return False
        except Exception as e:
            print(f"ERROR ⚠️ - {str(e)}")
            self.test_results["errors"].append({
                "test": test_name,
                "error": str(e)
            })
            self.test_results["components_failed"].append(test_name)
            return False

    def test_imports(self) -> bool:
        """Test all module imports"""
        print("\n" + "="*60)
        print("📦 TESTING MODULE IMPORTS")
        print("="*60)

        modules_to_test = [
            ("Database Models", "src.database.models"),
            ("Database Manager", "src.database.database"),
            ("Configuration Loader", "config.loader"),
            ("Security Module", "src.common.security"),
            ("Event Bus", "common.event_bus"),
            ("OpenAI Service", "src.ai.openai_service"),
            ("Broker Base", "src.core.broker.base"),
            ("Mock Broker", "src.core.broker.mock_broker"),
            ("Main App UI", "src.ui.app"),
        ]

        all_passed = True
        for module_name, module_path in modules_to_test:
            try:
                print(f"  Importing {module_name}...", end=" ")
                exec(f"import {module_path}")
                print("✅")
                self.test_results["components_tested"].append(module_name)
            except Exception as e:
                print(f"❌ - {e}")
                all_passed = False
                self.test_results["errors"].append({
                    "module": module_name,
                    "error": str(e)
                })

        return all_passed

    def test_configuration(self) -> bool:
        """Test configuration system"""
        print("\n" + "="*60)
        print("⚙️ TESTING CONFIGURATION SYSTEM")
        print("="*60)

        from config.loader import ConfigManager

        tests_passed = True

        # Test 1: ConfigManager initialization
        config_manager = ConfigManager()
        if not self.run_test("ConfigManager Initialization",
                            lambda: config_manager is not None):
            tests_passed = False

        # Test 2: Default profile loading
        def load_default_profile():
            profile = config_manager.load_profile("paper")
            return profile.profile_name == "paper"

        if not self.run_test("Default Profile Loading", load_default_profile):
            tests_passed = False

        # Test 3: Profile list
        def list_profiles():
            profiles = config_manager.list_profiles()
            return isinstance(profiles, list)

        if not self.run_test("Profile Listing", list_profiles):
            tests_passed = False

        return tests_passed

    def test_database(self) -> bool:
        """Test database operations"""
        print("\n" + "="*60)
        print("🗄️ TESTING DATABASE SYSTEM")
        print("="*60)

        import tempfile
        from decimal import Decimal

        from src.config.loader import DatabaseConfig
        from src.database.database import DatabaseManager
        from src.database.models import (
            Order,
            OrderSide,
            OrderStatus,
            OrderType,
            Position,
            TimeInForce,
        )

        # Use temporary database for testing
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        config = DatabaseConfig(engine="sqlite", path=temp_db.name)

        db_manager = DatabaseManager(config)
        db_manager.initialize()

        tests_passed = True

        # Test 1: Database initialization
        if not self.run_test("Database Initialization",
                            lambda: db_manager is not None):
            tests_passed = False

        # Test 2: Create Order
        def create_order():
            with db_manager.session() as session:
                order = Order(
                    order_id="TEST_001",
                    symbol="AAPL",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=10,
                    time_in_force=TimeInForce.DAY,
                    status=OrderStatus.PENDING,
                    created_at=datetime.utcnow()
                )
                session.add(order)
                session.commit()
                return True

        if not self.run_test("Order Creation", create_order):
            tests_passed = False

        # Test 3: Query Order
        def query_order():
            with db_manager.session() as session:
                order = session.query(Order).filter_by(order_id="TEST_001").first()
                return order is not None and order.symbol == "AAPL"

        if not self.run_test("Order Query", query_order):
            tests_passed = False

        # Test 4: Create Position
        def create_position():
            with db_manager.session() as session:
                position = Position(
                    symbol="GOOGL",
                    quantity=Decimal('5'),
                    average_cost=Decimal('150.00'),
                    current_price=Decimal('155.00'),
                    market_value=Decimal('775.00'),
                    unrealized_pnl=Decimal('25.00'),
                    opened_at=datetime.utcnow()
                )
                session.add(position)
                session.commit()
                return True

        if not self.run_test("Position Creation", create_position):
            tests_passed = False

        temp_db.close()
        return tests_passed

    def test_security(self) -> bool:
        """Test security components"""
        print("\n" + "="*60)
        print("🔐 TESTING SECURITY SYSTEM")
        print("="*60)

        from src.common.security import (
            EncryptionManager,
            RateLimiter,
            SessionManager,
            generate_api_key,
            hash_password,
            validate_api_key,
            verify_password,
        )

        tests_passed = True

        # Test 1: Encryption
        def test_encryption():
            em = EncryptionManager("test_password")
            original = "sensitive_data"
            encrypted = em.encrypt(original)
            decrypted = em.decrypt(encrypted)
            return decrypted == original

        if not self.run_test("Encryption/Decryption", test_encryption):
            tests_passed = False

        # Test 2: Password hashing
        def test_password_hash():
            password = "SecurePass123!"
            hash_str, salt = hash_password(password)
            return verify_password(password, hash_str, salt)

        if not self.run_test("Password Hashing", test_password_hash):
            tests_passed = False

        # Test 3: API key generation and validation
        def test_api_key():
            key = generate_api_key()
            return validate_api_key(key)

        if not self.run_test("API Key Generation", test_api_key):
            tests_passed = False

        # Test 4: Session management
        def test_session():
            sm = SessionManager()
            session_id = sm.create_session("test_user")
            context = sm.validate_session(session_id)
            return context is not None and context.user_id == "test_user"

        if not self.run_test("Session Management", test_session):
            tests_passed = False

        # Test 5: Rate limiting
        def test_rate_limit():
            rl = RateLimiter()
            rl.set_limit("api", max_requests=2, time_window=60)
            # First two should succeed
            result1 = rl.check_limit("api", "user1")
            result2 = rl.check_limit("api", "user1")
            # Third should fail
            result3 = rl.check_limit("api", "user1")
            return result1 and result2 and not result3

        if not self.run_test("Rate Limiting", test_rate_limit):
            tests_passed = False

        return tests_passed

    def test_broker_adapter(self) -> bool:
        """Test broker adapter functionality"""
        print("\n" + "="*60)
        print("📈 TESTING BROKER ADAPTER")
        print("="*60)

        from decimal import Decimal

        from src.core.broker import MockBroker, OrderRequest
        from src.database.models import OrderSide, OrderType, TimeInForce

        tests_passed = True
        broker = MockBroker(initial_cash=Decimal('10000'))

        # Test 1: Broker initialization
        if not self.run_test("MockBroker Initialization",
                            lambda: broker is not None):
            tests_passed = False

        # Test 2: Connect to broker
        async def test_connect():
            await broker.connect()
            return await broker.is_connected()

        if not self.run_test("Broker Connection",
                            lambda: asyncio.run(test_connect())):
            tests_passed = False

        # Test 3: Get balance
        async def test_balance():
            balance = await broker.get_balance()
            return balance.cash == Decimal('10000')

        if not self.run_test("Get Balance",
                            lambda: asyncio.run(test_balance())):
            tests_passed = False

        # Test 4: Place order
        async def test_place_order():
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal('10'),
                time_in_force=TimeInForce.DAY
            )
            response = await broker.place_order(order)
            return response is not None

        if not self.run_test("Place Order",
                            lambda: asyncio.run(test_place_order())):
            tests_passed = False

        # Test 5: Get positions
        async def test_positions():
            positions = await broker.get_positions()
            return len(positions) > 0

        if not self.run_test("Get Positions",
                            lambda: asyncio.run(test_positions())):
            tests_passed = False

        return tests_passed

    def test_event_system(self) -> bool:
        """Test event bus system"""
        print("\n" + "="*60)
        print("📡 TESTING EVENT SYSTEM")
        print("="*60)

        from src.common.event_bus import Event, EventBus

        tests_passed = True
        event_bus = EventBus()

        # Test 1: Event bus initialization
        if not self.run_test("EventBus Initialization",
                            lambda: event_bus is not None):
            tests_passed = False

        # Test 2: Event creation
        def test_event_creation():
            event = Event("test_event", {"data": "test"})
            return event.event_type == "test_event" and event.data["data"] == "test"

        if not self.run_test("Event Creation", test_event_creation):
            tests_passed = False

        # Test 3: Subscribe and emit
        received_data = []

        def test_subscribe_emit():
            def handler(event):
                received_data.append(event.data)

            event_bus.subscribe("test_event", handler)
            event_bus.emit("test_event", {"message": "Hello"})
            time.sleep(0.1)  # Allow async processing
            return len(received_data) > 0 and received_data[0]["message"] == "Hello"

        if not self.run_test("Subscribe and Emit", test_subscribe_emit):
            tests_passed = False

        return tests_passed

    def test_ui_components(self) -> bool:
        """Test UI component imports and initialization"""
        print("\n" + "="*60)
        print("🖼️ TESTING UI COMPONENTS")
        print("="*60)

        tests_passed = True

        ui_components = [
            ("Dashboard Widget", "src.ui.widgets.dashboard"),
            ("Positions Widget", "src.ui.widgets.positions"),
            ("Orders Widget", "src.ui.widgets.orders"),
            ("Chart Widget", "src.ui.widgets.chart"),
            ("Alerts Widget", "src.ui.widgets.alerts"),
            ("Order Dialog", "src.ui.dialogs.order_dialog"),
            ("Settings Dialog", "src.ui.dialogs.settings_dialog"),
            ("Backtest Dialog", "src.ui.dialogs.backtest_dialog"),
        ]

        for component_name, module_path in ui_components:
            try:
                exec(f"import {module_path}")
                self.test_results["components_passed"].append(f"UI: {component_name}")
                print(f"  ✓ {component_name} - Importable ✅")
            except Exception as e:
                self.test_results["components_failed"].append(f"UI: {component_name}")
                self.test_results["errors"].append({
                    "component": component_name,
                    "error": str(e)
                })
                print(f"  ✗ {component_name} - Import Failed ❌")
                tests_passed = False

        return tests_passed

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📊 FINAL TEST REPORT")
        print("="*80)

        # Calculate test coverage
        self.test_results["test_coverage"] = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0

        # Save detailed JSON report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)

        # Print summary
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    OrderPilot-AI COMPREHENSIVE TEST REPORT                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Test Date:        {self.test_results['test_date']}                  ║
║ Total Tests Run:  {self.total_tests:>3}                                                         ║
║ Tests Passed:     {self.passed_tests:>3} ✅                                                      ║
║ Tests Failed:     {self.total_tests - self.passed_tests:>3} ❌                                                      ║
║ Test Coverage:    {self.test_results['test_coverage']:.1f}%                                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Components Tested: {len(self.test_results['components_passed']) + len(self.test_results['components_failed']):>3}                                                        ║
║ Components Passed: {len(self.test_results['components_passed']):>3}                                                        ║
║ Components Failed: {len(self.test_results['components_failed']):>3}                                                        ║
║ Errors Logged:     {len(self.test_results['errors']):>3}                                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)

        if self.test_results["components_failed"]:
            print("\n❌ FAILED COMPONENTS:")
            for component in self.test_results["components_failed"]:
                print(f"  • {component}")

        if self.test_results["errors"]:
            print("\n⚠️ ERROR DETAILS:")
            for error in self.test_results["errors"][:5]:  # Show first 5 errors
                print(f"  • {error}")

        print(f"\n📁 Detailed report saved to: {report_file}")

        # Return verdict
        if self.test_results["test_coverage"] >= 80:
            print("\n✅ VERDICT: Application is READY for production testing")
            return True
        elif self.test_results["test_coverage"] >= 60:
            print("\n⚠️ VERDICT: Application needs MINOR fixes before production")
            return False
        else:
            print("\n❌ VERDICT: Application has CRITICAL issues - NOT ready for production")
            return False

    def run_complete_test(self):
        """Run all tests"""
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║          STARTING COMPREHENSIVE TEST FOR ORDERPILOT-AI                        ║
║                    Trading Application System Test                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)

        # Run all test suites
        self.test_imports()
        self.test_configuration()
        self.test_database()
        self.test_security()
        self.test_broker_adapter()
        self.test_event_system()
        self.test_ui_components()

        # Generate report
        return self.generate_report()


def main():
    """Main test execution"""
    tester = ComprehensiveApplicationTester()
    success = tester.run_complete_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()