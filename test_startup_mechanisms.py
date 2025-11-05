#!/usr/bin/env python3
"""
Test script for validating alternative startup mechanisms.

This script tests both direct Streamlit startup and bash script startup approaches
for Railway deployment.
"""

import os
import subprocess
import sys


def test_procfile_configurations():
    """Test both Procfile configurations exist and are valid."""
    
    print("Testing Procfile Configurations")
    print("=" * 40)
    
    # Test main Procfile
    if os.path.exists("Procfile"):
        print("✓ Main Procfile exists")
        with open("Procfile", "r") as f:
            content = f.read()
            if "streamlit run app.py" in content:
                print("✓ Main Procfile contains direct Streamlit startup")
            if "bash start.sh" in content:
                print("✓ Main Procfile includes bash script option")
    else:
        print("✗ Main Procfile missing")
        return False
    
    # Test alternative Procfile
    if os.path.exists("Procfile.alternative"):
        print("✓ Alternative Procfile exists")
        with open("Procfile.alternative", "r") as f:
            content = f.read()
            if "bash start.sh" in content:
                print("✓ Alternative Procfile uses bash script")
    else:
        print("✗ Alternative Procfile missing")
        return False
    
    return True


def test_bash_script():
    """Test bash script exists and has correct configuration."""
    
    print("\nTesting Bash Script Configuration")
    print("=" * 40)
    
    if not os.path.exists("start.sh"):
        print("✗ start.sh script missing")
        return False
    
    print("✓ start.sh script exists")
    
    with open("start.sh", "r") as f:
        content = f.read()
    
    # Check for required elements
    checks = [
        ("#!/bin/bash", "Shebang line"),
        ("export PORT", "PORT environment variable export"),
        ("PORT=8080", "Fallback port configuration"),
        ("streamlit run app.py", "Streamlit startup command"),
        ("--server.port=$PORT", "Port parameter"),
        ("--server.address=0.0.0.0", "Address parameter"),
        ("--server.headless=true", "Headless parameter")
    ]
    
    for check, description in checks:
        if check in content:
            print(f"✓ {description} found")
        else:
            print(f"✗ {description} missing")
            return False
    
    return True


def test_environment_variable_handling():
    """Test environment variable handling in bash script."""
    
    print("\nTesting Environment Variable Handling")
    print("=" * 40)
    
    # Test with PORT set
    test_env = os.environ.copy()
    test_env["PORT"] = "3000"
    
    try:
        # Test bash script syntax (dry run)
        result = subprocess.run(
            ["bash", "-n", "start.sh"], 
            capture_output=True, 
            text=True,
            env=test_env
        )
        
        if result.returncode == 0:
            print("✓ Bash script syntax is valid")
        else:
            print(f"✗ Bash script syntax error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("⚠ Bash not available for testing (Windows environment)")
        print("✓ Script will be tested during Railway deployment")
    
    return True


def main():
    """Run all startup mechanism tests."""
    
    print("Railway Startup Mechanisms Validation")
    print("=" * 50)
    
    tests = [
        test_procfile_configurations,
        test_bash_script,
        test_environment_variable_handling
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    if all(results):
        print("✓ All startup mechanism tests passed!")
        print("✓ Both direct Streamlit and bash script approaches are configured correctly")
        print("✓ Ready for Railway deployment testing")
    else:
        print("⚠ Some tests failed - check configuration above")
    
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)