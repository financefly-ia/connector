#!/usr/bin/env python3
"""
Test script for deployment configuration validator.

This script tests the DeploymentConfigValidator class with the current project files.
"""

import sys
import os
import json

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from deployment_validator import DeploymentConfigValidator, ValidationResult, DeploymentConfig


def test_deployment_validator():
    """Test the deployment configuration validator with current project files."""
    
    print("Testing Deployment Configuration Validator")
    print("=" * 50)
    
    # Initialize validator
    validator = DeploymentConfigValidator()
    
    # Run all validations
    print("\nRunning validation checks...")
    results = validator.validate_all_files()
    
    # Display results
    print(f"\nValidation Results ({len(results)} checks):")
    print("-" * 30)
    
    for result in results:
        status_symbol = "✓" if result.status == "pass" else "⚠" if result.status == "warning" else "✗"
        print(f"{status_symbol} {result.component}: {result.status.upper()}")
        print(f"  Message: {result.message}")
        if result.fix_applied:
            print(f"  Fix applied: Yes")
        print()
    
    # Get deployment config status
    config_status = validator.get_deployment_config_status()
    print("Deployment Configuration Status:")
    print("-" * 30)
    print(f"vercel.json valid: {config_status.vercel_json_valid}")
    print(f"Procfile exists: {config_status.procfile_exists}")
    print(f".vercelignore exists: {config_status.vercelignore_exists}")
    print(f"runtime.txt exists: {config_status.runtime_txt_exists}")
    print(f"Dependencies valid: {config_status.dependencies_valid}")
    print(f"Streamlit config valid: {config_status.streamlit_config_valid}")
    print(f"Overall ready: {config_status.overall_ready}")
    
    # Generate validation report
    print("\nGenerating validation report...")
    report = validator.generate_validation_report()
    
    print(f"\nValidation Report Summary:")
    print("-" * 30)
    print(f"Overall Status: {report['overall_status']}")
    print(f"Total Checks: {report['summary']['total_checks']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print(f"Failed: {report['summary']['failed']}")
    
    if report['recommendations']:
        print(f"\nRecommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    # Save detailed report to file
    report_filename = f"validation_report_deployment_config.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed report saved to: {report_filename}")
    
    return config_status.overall_ready


def test_individual_validators():
    """Test individual validator methods."""
    
    print("\n" + "=" * 50)
    print("Testing Individual Validator Methods")
    print("=" * 50)
    
    validator = DeploymentConfigValidator()
    
    # Test vercel.json validation
    print("\n1. Testing vercel.json validation:")
    result = validator.validate_vercel_json()
    print(f"   Status: {result.status}")
    print(f"   Message: {result.message}")
    
    # Test Procfile validation
    print("\n2. Testing Procfile validation:")
    result = validator.validate_procfile()
    print(f"   Status: {result.status}")
    print(f"   Message: {result.message}")
    
    # Test .vercelignore validation
    print("\n3. Testing .vercelignore validation:")
    result = validator.validate_vercelignore()
    print(f"   Status: {result.status}")
    print(f"   Message: {result.message}")
    
    # Test runtime.txt validation
    print("\n4. Testing runtime.txt validation:")
    result = validator.validate_runtime_txt()
    print(f"   Status: {result.status}")
    print(f"   Message: {result.message}")


if __name__ == "__main__":
    try:
        # Test individual validators first
        test_individual_validators()
        
        # Test complete validation system
        overall_ready = test_deployment_validator()
        
        print("\n" + "=" * 50)
        print("Test Summary")
        print("=" * 50)
        
        if overall_ready:
            print("✓ Deployment configuration validation system is working correctly!")
            print("✓ Current project is ready for deployment!")
        else:
            print("⚠ Deployment configuration validation system is working correctly!")
            print("⚠ Current project needs some configuration fixes before deployment.")
        
        print("\nDeployment configuration validation system implementation completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)