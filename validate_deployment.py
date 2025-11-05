#!/usr/bin/env python3
"""
Standalone deployment validation script for Railway Streamlit application.

This script validates deployment readiness without starting the full Streamlit app.
"""

import os
import sys
from datetime import datetime

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

def main():
    """Run deployment validation."""
    
    print("🚀 Railway Streamlit Deployment Validation")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Import and run validation
        from deployment_validator import run_deployment_validation
        
        print("Starting comprehensive deployment validation...")
        print()
        
        # Run the validation
        results = run_deployment_validation()
        
        # Display final summary
        print()
        print("=" * 60)
        print("🏁 VALIDATION COMPLETE")
        print("=" * 60)
        
        overall_status = results.get("overall", False)
        duration = results.get("duration", 0)
        errors = results.get("errors", [])
        warnings = results.get("warnings", [])
        
        print(f"Overall Status: {'✅ READY' if overall_status else '❌ NOT READY'}")
        print(f"Validation Duration: {duration:.2f} seconds")
        print(f"Errors: {len(errors)}")
        print(f"Warnings: {len(warnings)}")
        
        if not overall_status:
            print()
            print("❌ Critical Issues Found:")
            for i, error in enumerate(errors[:10], 1):  # Show first 10 errors
                print(f"  {i}. {error}")
            
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
        
        if warnings:
            print()
            print("⚠️ Warnings:")
            for i, warning in enumerate(warnings[:5], 1):  # Show first 5 warnings
                print(f"  {i}. {warning}")
            
            if len(warnings) > 5:
                print(f"  ... and {len(warnings) - 5} more warnings")
        
        print()
        if overall_status:
            print("🎉 Deployment validation passed! Application is ready for Railway.")
            return 0
        else:
            print("⚠️ Deployment validation failed. Please fix the issues above.")
            return 1
            
    except ImportError as e:
        print(f"❌ Failed to import validation module: {e}")
        print("Make sure the modules/deployment_validator.py file exists and is valid.")
        return 1
        
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)