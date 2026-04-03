#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM VERIFICATION
Checks all components for errors
"""

import sys
import os
import importlib
import traceback
from datetime import datetime

class SystemVerifier:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success = []
        
    def log(self, category, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {category}: {message}")
        if category == "❌ ERROR":
            self.errors.append(message)
        elif category == "⚠️ WARN":
            self.warnings.append(message)
        elif category == "✅ PASS":
            self.success.append(message)
    
    def check_import(self, module_name, package=None):
        """Check if a module can be imported"""
        try:
            if package:
                importlib.import_module(module_name, package=package)
            else:
                importlib.import_module(module_name)
            self.log("✅ PASS", f"Import: {module_name}")
            return True
        except Exception as e:
            self.log("❌ ERROR", f"Import: {module_name} - {str(e)[:100]}")
            return False
    
    def check_file_exists(self, filepath):
        """Check if a file exists"""
        if os.path.exists(filepath):
            self.log("✅ PASS", f"File exists: {filepath}")
            return True
        else:
            self.log("❌ ERROR", f"File missing: {filepath}")
            return False
    
    def verify_core_modules(self):
        """Verify all core modules can be imported"""
        self.log("🔍 INFO", "=== CHECKING CORE MODULES ===")
        
        modules = [
            "production_server",
            "preview_server",
            "orchestrator",
            "prediction_engine",
            "market_data_service",
        ]
        
        for mod in modules:
            self.check_import(mod)
    
    def verify_multi_domain_modules(self):
        """Verify multi_domain package"""
        self.log("🔍 INFO", "=== CHECKING MULTI_DOMAIN MODULES ===")
        
        modules = [
            "multi_domain.latex_renderer",
            "multi_domain.visualization_engine",
            "multi_domain.local_llm_engine",
            "multi_domain.ai_cache",
            "multi_domain.structured_logging",
            "multi_domain.ast_code_analyzer",
            "multi_domain.circuit_breaker",
            "multi_domain.rate_limiter",
            "multi_domain.d3_visualization",
            "multi_domain.performance_optimizer",
            "multi_domain.superior_ai_system",
        ]
        
        for mod in modules:
            try:
                module = importlib.import_module(mod)
                self.log("✅ PASS", f"Module: {mod}")
            except Exception as e:
                self.log("❌ ERROR", f"Module: {mod} - {str(e)[:150]}")
                traceback.print_exc()
    
    def verify_website_builder(self):
        """Verify website builder modules"""
        self.log("🔍 INFO", "=== CHECKING WEBSITE BUILDER ===")
        
        modules = [
            "website_builder.multi_agent_website_builder",
            "website_builder.autonomous_website_builder",
            "website_builder.powerful_builder",
            "website_builder.unified_ai_builder",
            "website_builder.base44_competitor",
        ]
        
        for mod in modules:
            self.check_import(mod)
    
    def verify_templates(self):
        """Verify all template files exist"""
        self.log("🔍 INFO", "=== CHECKING TEMPLATES ===")
        
        templates = [
            "templates/admin_autonomous_builder.html",
            "templates/admin_base44_builder.html",
            "templates/admin_unified_builder.html",
            "templates/fallback_indicator.html",
            "templates/visualization_dashboard.html",
            "templates/terminal.html",
        ]
        
        for template in templates:
            self.check_file_exists(template)
    
    def verify_quant_ecosystem(self):
        """Verify quant ecosystem agents"""
        self.log("🔍 INFO", "=== CHECKING QUANT ECOSYSTEM ===")
        
        agents = [
            "quant_ecosystem.agents.bullish_agent",
            "quant_ecosystem.agents.bearish_agent",
            "quant_ecosystem.agents.neutral_agent",
            "quant_ecosystem.agents.data_collection_agent",
        ]
        
        for agent in agents:
            self.check_import(agent)
    
    def check_syntax_errors(self):
        """Check for syntax errors in key files"""
        self.log("🔍 INFO", "=== CHECKING SYNTAX ===")
        
        import py_compile
        
        files_to_check = [
            "production_server.py",
            "preview_server.py",
            "orchestrator.py",
            "multi_domain/superior_ai_system.py",
        ]
        
        for filepath in files_to_check:
            try:
                py_compile.compile(filepath, doraise=True)
                self.log("✅ PASS", f"Syntax: {filepath}")
            except py_compile.PyCompileError as e:
                self.log("❌ ERROR", f"Syntax: {filepath} - {e}")
    
    def test_basic_functionality(self):
        """Test basic functionality of key components"""
        self.log("🔍 INFO", "=== TESTING BASIC FUNCTIONALITY ===")
        
        # Test Superior AI
        try:
            from multi_domain.superior_ai_system import SuperiorAI
            ai = SuperiorAI()
            result = ai.process("What is Python?")
            if result and "answer" in result:
                self.log("✅ PASS", "SuperiorAI: Basic query works")
            else:
                self.log("⚠️ WARN", "SuperiorAI: Response format unexpected")
        except Exception as e:
            self.log("❌ ERROR", f"SuperiorAI: {str(e)[:150]}")
        
        # Test Knowledge Graph
        try:
            from multi_domain.superior_ai_system import KnowledgeGraph
            kg = KnowledgeGraph()
            kg.add_fact("Test", "is_a", "Entity")
            results = kg.query(subject="Test")
            if results:
                self.log("✅ PASS", "KnowledgeGraph: Add/query works")
            else:
                self.log("⚠️ WARN", "KnowledgeGraph: Query returned no results")
        except Exception as e:
            self.log("❌ ERROR", f"KnowledgeGraph: {str(e)[:150]}")
        
        # Test AST Analyzer
        try:
            from multi_domain.ast_code_analyzer import analyze_code_intelligent
            code = "def hello(): pass"
            result = analyze_code_intelligent(code, "test.py")
            if result.get("success"):
                self.log("✅ PASS", "AST Analyzer: Code analysis works")
            else:
                self.log("⚠️ WARN", "AST Analyzer: Analysis returned errors")
        except Exception as e:
            self.log("❌ ERROR", f"AST Analyzer: {str(e)[:150]}")
    
    def check_dependencies(self):
        """Check if key dependencies are installed"""
        self.log("🔍 INFO", "=== CHECKING DEPENDENCIES ===")
        
        dependencies = [
            "flask",
            "numpy",
            "pandas",
            "requests",
            "yfinance",
        ]
        
        for dep in dependencies:
            try:
                importlib.import_module(dep)
                self.log("✅ PASS", f"Dependency: {dep}")
            except ImportError:
                self.log("❌ ERROR", f"Dependency missing: {dep}")
    
    def generate_report(self):
        """Generate final verification report"""
        self.log("🔍 INFO", "=== VERIFICATION REPORT ===")
        
        print("\n" + "="*70)
        print(f"PASSED: {len(self.success)}")
        print(f"WARNINGS: {len(self.warnings)}")
        print(f"ERRORS: {len(self.errors)}")
        print("="*70)
        
        if self.errors:
            print("\n❌ CRITICAL ERRORS FOUND:")
            for i, error in enumerate(self.errors[:10], 1):
                print(f"  {i}. {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")
            return False
        elif self.warnings:
            print("\n⚠️  System functional with warnings")
            return True
        else:
            print("\n✅ ALL CHECKS PASSED - SYSTEM READY")
            return True


def main():
    print("="*70)
    print("COMPREHENSIVE SYSTEM VERIFICATION")
    print("="*70)
    print()
    
    verifier = SystemVerifier()
    
    # Run all verification checks
    verifier.verify_core_modules()
    print()
    verifier.verify_multi_domain_modules()
    print()
    verifier.verify_website_builder()
    print()
    verifier.verify_templates()
    print()
    verifier.verify_quant_ecosystem()
    print()
    verifier.check_syntax_errors()
    print()
    verifier.test_basic_functionality()
    print()
    verifier.check_dependencies()
    print()
    
    # Generate report
    success = verifier.generate_report()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
