"""
Deployment Configuration Validation System

This module provides comprehensive validation for Vercel deployment configuration files,
ensuring all required files exist and contain proper configuration for Streamlit deployment.
"""

import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import re
from packaging import version


@dataclass
class ValidationResult:
    """Result of a validation check"""
    component: str
    status: str  # "pass", "fail", "warning"
    message: str
    fix_applied: bool = False


@dataclass
class DeploymentConfig:
    """Overall deployment configuration status"""
    vercel_json_valid: bool
    procfile_exists: bool
    vercelignore_exists: bool
    runtime_txt_exists: bool
    dependencies_valid: bool
    streamlit_config_valid: bool
    overall_ready: bool


@dataclass
class DependencyInfo:
    """Information about a dependency"""
    name: str
    version: Optional[str] = None
    extras: Optional[List[str]] = None
    
    def __str__(self) -> str:
        """String representation for requirements.txt format"""
        result = self.name
        if self.extras:
            result += f"[{','.join(self.extras)}]"
        if self.version:
            result += f"=={self.version}"
        return result


class DeploymentConfigValidator:
    """
    Validates and manages Vercel deployment configuration files for Streamlit applications.
    
    This class provides methods to validate each configuration file type required for
    successful Vercel deployment, including vercel.json, Procfile, .vercelignore,
    runtime.txt, and requirements.txt.
    """
    
    def __init__(self, project_root: str = "."):
        """
        Initialize the validator with the project root directory.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = project_root
        self.validation_results: List[ValidationResult] = []
    
    def validate_vercel_json(self) -> ValidationResult:
        """
        Validate vercel.json configuration file.
        
        Checks for:
        - File existence
        - Valid JSON syntax
        - Required version field
        - Proper builds configuration
        - Correct routing configuration
        - Environment variables for headless operation
        
        Returns:
            ValidationResult: Result of the validation
        """
        file_path = os.path.join(self.project_root, "vercel.json")
        
        if not os.path.exists(file_path):
            return ValidationResult(
                component="vercel.json",
                status="fail",
                message="vercel.json file does not exist"
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(
                component="vercel.json",
                status="fail",
                message=f"Invalid JSON syntax in vercel.json: {str(e)}"
            )
        except Exception as e:
            return ValidationResult(
                component="vercel.json",
                status="fail",
                message=f"Error reading vercel.json: {str(e)}"
            )
        
        # Validate required fields
        issues = []
        
        # Check version
        if "version" not in config or config["version"] != 2:
            issues.append("Missing or incorrect version field (should be 2)")
        
        # Check builds configuration
        if "builds" not in config:
            issues.append("Missing builds configuration")
        else:
            builds = config["builds"]
            if not isinstance(builds, list) or len(builds) == 0:
                issues.append("Builds configuration should be a non-empty list")
            else:
                app_build = None
                for build in builds:
                    if build.get("src") == "app.py":
                        app_build = build
                        break
                
                if not app_build:
                    issues.append("Missing build configuration for app.py")
                elif app_build.get("use") != "@vercel/python":
                    issues.append("Build configuration should use @vercel/python")
        
        # Check routes configuration
        if "routes" not in config:
            issues.append("Missing routes configuration")
        else:
            routes = config["routes"]
            if not isinstance(routes, list) or len(routes) == 0:
                issues.append("Routes configuration should be a non-empty list")
            else:
                catch_all_route = None
                for route in routes:
                    if route.get("src") == "/(.*)" and route.get("dest") == "app.py":
                        catch_all_route = route
                        break
                
                if not catch_all_route:
                    issues.append("Missing catch-all route configuration")
        
        # Check environment variables (recommended but not required)
        env_warnings = []
        if "env" not in config:
            env_warnings.append("Missing environment variables for headless operation")
        else:
            env = config["env"]
            if "STREAMLIT_SERVER_HEADLESS" not in env:
                env_warnings.append("Missing STREAMLIT_SERVER_HEADLESS environment variable")
            if "STREAMLIT_SERVER_PORT" not in env:
                env_warnings.append("Missing STREAMLIT_SERVER_PORT environment variable")
            if "STREAMLIT_SERVER_ADDRESS" not in env:
                env_warnings.append("Missing STREAMLIT_SERVER_ADDRESS environment variable")
        
        if issues:
            return ValidationResult(
                component="vercel.json",
                status="fail",
                message=f"Configuration issues: {'; '.join(issues)}"
            )
        elif env_warnings:
            return ValidationResult(
                component="vercel.json",
                status="warning",
                message=f"Recommendations: {'; '.join(env_warnings)}"
            )
        else:
            return ValidationResult(
                component="vercel.json",
                status="pass",
                message="vercel.json configuration is valid"
            )
    
    def validate_procfile(self) -> ValidationResult:
        """
        Validate Procfile configuration.
        
        Checks for:
        - File existence
        - Proper web process definition
        - Correct Streamlit command
        - Required flags for headless operation
        
        Returns:
            ValidationResult: Result of the validation
        """
        file_path = os.path.join(self.project_root, "Procfile")
        
        # Check both Procfile and procfile (case variations)
        if not os.path.exists(file_path):
            file_path = os.path.join(self.project_root, "procfile")
            if not os.path.exists(file_path):
                return ValidationResult(
                    component="Procfile",
                    status="fail",
                    message="Procfile does not exist"
                )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception as e:
            return ValidationResult(
                component="Procfile",
                status="fail",
                message=f"Error reading Procfile: {str(e)}"
            )
        
        if not content:
            return ValidationResult(
                component="Procfile",
                status="fail",
                message="Procfile is empty"
            )
        
        # Validate web process definition
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        web_process = None
        
        for line in lines:
            if line.startswith("web:"):
                web_process = line
                break
        
        if not web_process:
            return ValidationResult(
                component="Procfile",
                status="fail",
                message="Missing web process definition"
            )
        
        # Validate Streamlit command
        command = web_process[4:].strip()  # Remove "web:" prefix
        
        issues = []
        
        if "streamlit run" not in command:
            issues.append("Missing 'streamlit run' command")
        
        if "app.py" not in command:
            issues.append("Missing app.py target file")
        
        # Check for required flags
        if "--server.port" not in command and "--server.port=$PORT" not in command:
            issues.append("Missing --server.port configuration")
        
        if "--server.address=0.0.0.0" not in command:
            issues.append("Missing --server.address=0.0.0.0 configuration")
        
        if "--server.headless=true" not in command:
            issues.append("Missing --server.headless=true flag")
        
        if issues:
            return ValidationResult(
                component="Procfile",
                status="fail",
                message=f"Configuration issues: {'; '.join(issues)}"
            )
        else:
            return ValidationResult(
                component="Procfile",
                status="pass",
                message="Procfile configuration is valid"
            )
    
    def validate_vercelignore(self) -> ValidationResult:
        """
        Validate .vercelignore file for deployment optimization.
        
        Checks for:
        - File existence
        - Common exclusion patterns
        - Proper syntax
        
        Returns:
            ValidationResult: Result of the validation
        """
        file_path = os.path.join(self.project_root, ".vercelignore")
        
        if not os.path.exists(file_path):
            return ValidationResult(
                component=".vercelignore",
                status="warning",
                message=".vercelignore file does not exist (recommended for deployment optimization)"
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception as e:
            return ValidationResult(
                component=".vercelignore",
                status="fail",
                message=f"Error reading .vercelignore: {str(e)}"
            )
        
        if not content:
            return ValidationResult(
                component=".vercelignore",
                status="warning",
                message=".vercelignore file is empty"
            )
        
        # Check for recommended exclusion patterns
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        
        recommended_patterns = [
            "__pycache__/",
            "*.pyc",
            ".env",
            ".git/",
            ".vscode/",
            "test_*.py"
        ]
        
        missing_patterns = []
        for pattern in recommended_patterns:
            if pattern not in lines:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            return ValidationResult(
                component=".vercelignore",
                status="warning",
                message=f"Missing recommended patterns: {', '.join(missing_patterns)}"
            )
        else:
            return ValidationResult(
                component=".vercelignore",
                status="pass",
                message=".vercelignore configuration is optimal"
            )
    
    def validate_runtime_txt(self) -> ValidationResult:
        """
        Validate runtime.txt file for Python version specification.
        
        Checks for:
        - File existence
        - Valid Python version format
        - Supported Python version
        
        Returns:
            ValidationResult: Result of the validation
        """
        file_path = os.path.join(self.project_root, "runtime.txt")
        
        if not os.path.exists(file_path):
            return ValidationResult(
                component="runtime.txt",
                status="fail",
                message="runtime.txt file does not exist"
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception as e:
            return ValidationResult(
                component="runtime.txt",
                status="fail",
                message=f"Error reading runtime.txt: {str(e)}"
            )
        
        if not content:
            return ValidationResult(
                component="runtime.txt",
                status="fail",
                message="runtime.txt file is empty"
            )
        
        # Validate Python version format
        python_version_pattern = r'^python-3\.\d+(\.\d+)?$'
        
        if not re.match(python_version_pattern, content):
            return ValidationResult(
                component="runtime.txt",
                status="fail",
                message=f"Invalid Python version format: {content}. Expected format: python-3.x or python-3.x.y"
            )
        
        # Extract version number
        version_match = re.search(r'python-3\.(\d+)(?:\.(\d+))?', content)
        if version_match:
            major_minor = int(version_match.group(1))
            
            # Check if version is supported (Python 3.8+)
            if major_minor < 8:
                return ValidationResult(
                    component="runtime.txt",
                    status="fail",
                    message=f"Python version {content} is not supported. Use Python 3.8 or higher"
                )
            elif major_minor > 12:
                return ValidationResult(
                    component="runtime.txt",
                    status="warning",
                    message=f"Python version {content} may not be supported yet. Consider using a stable version"
                )
        
        return ValidationResult(
            component="runtime.txt",
            status="pass",
            message=f"Python version {content} is valid"
        )
    
    def parse_requirements_txt(self) -> List[DependencyInfo]:
        """
        Parse requirements.txt file and extract dependency information.
        
        Returns:
            List[DependencyInfo]: List of parsed dependencies
        """
        file_path = os.path.join(self.project_root, "requirements.txt")
        dependencies = []
        
        if not os.path.exists(file_path):
            return dependencies
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            return dependencies
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse dependency line
            dependency = self._parse_dependency_line(line)
            if dependency:
                dependencies.append(dependency)
        
        return dependencies
    
    def _parse_dependency_line(self, line: str) -> Optional[DependencyInfo]:
        """
        Parse a single dependency line from requirements.txt.
        
        Args:
            line: Single line from requirements.txt
            
        Returns:
            DependencyInfo: Parsed dependency information or None if invalid
        """
        # Remove inline comments
        if '#' in line:
            line = line.split('#')[0].strip()
        
        if not line:
            return None
        
        # Pattern to match package[extras]==version
        pattern = r'^([a-zA-Z0-9_-]+)(?:\[([^\]]+)\])?(?:==([^\s]+))?'
        match = re.match(pattern, line)
        
        if not match:
            return None
        
        name = match.group(1)
        extras_str = match.group(2)
        version_str = match.group(3)
        
        extras = None
        if extras_str:
            extras = [extra.strip() for extra in extras_str.split(',')]
        
        return DependencyInfo(
            name=name,
            version=version_str,
            extras=extras
        )
    
    def get_required_dependencies(self) -> List[DependencyInfo]:
        """
        Get the list of required dependencies for Streamlit Vercel deployment.
        
        Returns:
            List[DependencyInfo]: Required dependencies with versions
        """
        return [
            DependencyInfo(name="streamlit", version="1.38.0"),
            DependencyInfo(name="python-dotenv", version="1.0.1"),
            DependencyInfo(name="psycopg", version="3.2.10", extras=["binary"]),
            DependencyInfo(name="requests", version="2.32.3"),
            DependencyInfo(name="gunicorn")  # No specific version required
        ]
    
    def validate_dependencies(self) -> ValidationResult:
        """
        Validate that all required dependencies are present in requirements.txt.
        
        Checks for:
        - File existence
        - Required packages presence
        - Version compatibility
        - Proper formatting
        
        Returns:
            ValidationResult: Result of the dependency validation
        """
        file_path = os.path.join(self.project_root, "requirements.txt")
        
        if not os.path.exists(file_path):
            return ValidationResult(
                component="requirements.txt",
                status="fail",
                message="requirements.txt file does not exist"
            )
        
        current_deps = self.parse_requirements_txt()
        required_deps = self.get_required_dependencies()
        
        # Create lookup dictionary for current dependencies
        current_deps_dict = {dep.name.lower(): dep for dep in current_deps}
        
        issues = []
        warnings = []
        
        for required_dep in required_deps:
            dep_name_lower = required_dep.name.lower()
            
            if dep_name_lower not in current_deps_dict:
                issues.append(f"Missing required package: {required_dep.name}")
                continue
            
            current_dep = current_deps_dict[dep_name_lower]
            
            # Check version if specified
            if required_dep.version and current_dep.version:
                try:
                    if version.parse(current_dep.version) != version.parse(required_dep.version):
                        warnings.append(
                            f"Version mismatch for {required_dep.name}: "
                            f"found {current_dep.version}, expected {required_dep.version}"
                        )
                except Exception:
                    warnings.append(f"Invalid version format for {required_dep.name}: {current_dep.version}")
            elif required_dep.version and not current_dep.version:
                warnings.append(f"No version specified for {required_dep.name}, expected {required_dep.version}")
            
            # Check extras if specified
            if required_dep.extras:
                if not current_dep.extras:
                    issues.append(f"Missing extras for {required_dep.name}: {required_dep.extras}")
                else:
                    missing_extras = set(required_dep.extras) - set(current_dep.extras)
                    if missing_extras:
                        issues.append(
                            f"Missing extras for {required_dep.name}: {list(missing_extras)}"
                        )
        
        if issues:
            return ValidationResult(
                component="requirements.txt",
                status="fail",
                message=f"Dependency issues: {'; '.join(issues)}"
            )
        elif warnings:
            return ValidationResult(
                component="requirements.txt",
                status="warning",
                message=f"Dependency warnings: {'; '.join(warnings)}"
            )
        else:
            return ValidationResult(
                component="requirements.txt",
                status="pass",
                message="All required dependencies are present and valid"
            )
    
    def get_missing_dependencies(self) -> List[DependencyInfo]:
        """
        Get list of missing required dependencies.
        
        Returns:
            List[DependencyInfo]: Dependencies that need to be added
        """
        current_deps = self.parse_requirements_txt()
        required_deps = self.get_required_dependencies()
        
        # Create lookup set for current dependency names
        current_names = {dep.name.lower() for dep in current_deps}
        
        missing_deps = []
        for required_dep in required_deps:
            if required_dep.name.lower() not in current_names:
                missing_deps.append(required_dep)
        
        return missing_deps
    
    def add_missing_dependencies(self) -> ValidationResult:
        """
        Automatically add missing required dependencies to requirements.txt.
        
        Returns:
            ValidationResult: Result of the dependency addition operation
        """
        missing_deps = self.get_missing_dependencies()
        
        if not missing_deps:
            return ValidationResult(
                component="requirements.txt",
                status="pass",
                message="No missing dependencies to add",
                fix_applied=False
            )
        
        file_path = os.path.join(self.project_root, "requirements.txt")
        
        try:
            # Read current content
            current_content = ""
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
            
            # Ensure content ends with newline if it exists
            if current_content and not current_content.endswith('\n'):
                current_content += '\n'
            
            # Add missing dependencies
            new_lines = []
            for dep in missing_deps:
                new_lines.append(str(dep))
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(current_content)
                for line in new_lines:
                    f.write(f"{line}\n")
            
            added_deps = [dep.name for dep in missing_deps]
            return ValidationResult(
                component="requirements.txt",
                status="pass",
                message=f"Added missing dependencies: {', '.join(added_deps)}",
                fix_applied=True
            )
            
        except Exception as e:
            return ValidationResult(
                component="requirements.txt",
                status="fail",
                message=f"Failed to add dependencies: {str(e)}",
                fix_applied=False
            )
    
    def ensure_gunicorn_dependency(self) -> ValidationResult:
        """
        Ensure gunicorn package is present for WSGI compatibility.
        
        Returns:
            ValidationResult: Result of gunicorn dependency check/addition
        """
        current_deps = self.parse_requirements_txt()
        current_names = {dep.name.lower() for dep in current_deps}
        
        if "gunicorn" in current_names:
            return ValidationResult(
                component="gunicorn",
                status="pass",
                message="gunicorn dependency is already present",
                fix_applied=False
            )
        
        # Add gunicorn if missing
        file_path = os.path.join(self.project_root, "requirements.txt")
        
        try:
            # Read current content
            current_content = ""
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
            
            # Ensure content ends with newline if it exists
            if current_content and not current_content.endswith('\n'):
                current_content += '\n'
            
            # Add gunicorn
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(current_content)
                f.write("gunicorn\n")
            
            return ValidationResult(
                component="gunicorn",
                status="pass",
                message="Added gunicorn dependency for WSGI compatibility",
                fix_applied=True
            )
            
        except Exception as e:
            return ValidationResult(
                component="gunicorn",
                status="fail",
                message=f"Failed to add gunicorn dependency: {str(e)}",
                fix_applied=False
            )
    
    def fix_dependency_issues(self) -> List[ValidationResult]:
        """
        Automatically fix dependency issues by adding missing packages.
        
        Returns:
            List[ValidationResult]: Results of all fix operations
        """
        results = []
        
        # Add missing dependencies
        results.append(self.add_missing_dependencies())
        
        # Ensure gunicorn is present (this is handled by add_missing_dependencies, 
        # but keeping separate method for explicit WSGI compatibility check)
        gunicorn_result = self.ensure_gunicorn_dependency()
        if not any(r.component == "requirements.txt" and r.fix_applied for r in results):
            results.append(gunicorn_result)
        
        return results
    
    def validate_all_files(self) -> List[ValidationResult]:
        """
        Run validation on all deployment configuration files.
        
        Returns:
            List[ValidationResult]: Results for all validation checks
        """
        self.validation_results = []
        
        # Validate each configuration file
        self.validation_results.append(self.validate_vercel_json())
        self.validation_results.append(self.validate_procfile())
        self.validation_results.append(self.validate_vercelignore())
        self.validation_results.append(self.validate_runtime_txt())
        self.validation_results.append(self.validate_dependencies())
        self.validation_results.append(self.validate_streamlit_config())
        
        return self.validation_results
    
    def get_deployment_config_status(self) -> DeploymentConfig:
        """
        Get overall deployment configuration status.
        
        Returns:
            DeploymentConfig: Summary of all configuration file statuses
        """
        if not self.validation_results:
            self.validate_all_files()
        
        # Determine status for each component
        vercel_json_valid = any(r.component == "vercel.json" and r.status == "pass" for r in self.validation_results)
        procfile_exists = any(r.component == "Procfile" and r.status in ["pass", "warning"] for r in self.validation_results)
        vercelignore_exists = any(r.component == ".vercelignore" and r.status in ["pass", "warning"] for r in self.validation_results)
        runtime_txt_exists = any(r.component == "runtime.txt" and r.status == "pass" for r in self.validation_results)
        dependencies_valid = any(r.component == "requirements.txt" and r.status in ["pass", "warning"] for r in self.validation_results)
        
        # Check streamlit configuration status
        streamlit_config_valid = any(r.component == "streamlit_config" and r.status in ["pass", "warning"] for r in self.validation_results)
        
        # Overall readiness requires all critical components to be valid
        overall_ready = (
            vercel_json_valid and
            procfile_exists and
            runtime_txt_exists and
            dependencies_valid and
            streamlit_config_valid
        )
        
        return DeploymentConfig(
            vercel_json_valid=vercel_json_valid,
            procfile_exists=procfile_exists,
            vercelignore_exists=vercelignore_exists,
            runtime_txt_exists=runtime_txt_exists,
            dependencies_valid=dependencies_valid,
            streamlit_config_valid=streamlit_config_valid,
            overall_ready=overall_ready
        )
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.
        
        Returns:
            Dict[str, Any]: Detailed validation report
        """
        if not self.validation_results:
            self.validate_all_files()
        
        config_status = self.get_deployment_config_status()
        
        report = {
            "timestamp": "2024-11-03",  # Current date from system info
            "overall_status": "ready" if config_status.overall_ready else "needs_attention",
            "summary": {
                "total_checks": len(self.validation_results),
                "passed": len([r for r in self.validation_results if r.status == "pass"]),
                "warnings": len([r for r in self.validation_results if r.status == "warning"]),
                "failed": len([r for r in self.validation_results if r.status == "fail"])
            },
            "configuration_status": {
                "vercel_json": config_status.vercel_json_valid,
                "procfile": config_status.procfile_exists,
                "vercelignore": config_status.vercelignore_exists,
                "runtime_txt": config_status.runtime_txt_exists,
                "dependencies": config_status.dependencies_valid,
                "streamlit_config": config_status.streamlit_config_valid
            },
            "detailed_results": [
                {
                    "component": result.component,
                    "status": result.status,
                    "message": result.message,
                    "fix_applied": result.fix_applied
                }
                for result in self.validation_results
            ],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on validation results.
        
        Returns:
            List[str]: List of actionable recommendations
        """
        recommendations = []
        
        for result in self.validation_results:
            if result.status == "fail":
                if result.component == "vercel.json":
                    recommendations.append("Fix vercel.json configuration issues")
                elif result.component == "Procfile":
                    recommendations.append("Create or fix Procfile with proper Streamlit command")
                elif result.component == "runtime.txt":
                    recommendations.append("Create runtime.txt with supported Python version")
                elif result.component == "requirements.txt":
                    recommendations.append("Fix requirements.txt dependency issues")
            elif result.status == "warning":
                if result.component == ".vercelignore":
                    recommendations.append("Create .vercelignore file to optimize deployment")
                elif result.component == "vercel.json":
                    recommendations.append("Add environment variables to vercel.json for better configuration")
                elif result.component == "requirements.txt":
                    recommendations.append("Review dependency version warnings")
                elif result.component == "streamlit_config":
                    recommendations.append("Review Streamlit configuration warnings")
            elif result.status == "fail":
                if result.component == "streamlit_config":
                    recommendations.append("Fix Streamlit headless configuration in app.py")
        
        return recommendations
    
    def validate_streamlit_config(self) -> ValidationResult:
        """
        Validate Streamlit headless configuration in app.py.
        
        Checks for:
        - Presence of STREAMLIT_SERVER_HEADLESS environment variable
        - Presence of STREAMLIT_SERVER_PORT environment variable
        - Presence of STREAMLIT_SERVER_ADDRESS environment variable
        - Proper configuration placement before Streamlit imports
        
        Returns:
            ValidationResult: Result of the Streamlit configuration validation
        """
        file_path = os.path.join(self.project_root, "app.py")
        
        if not os.path.exists(file_path):
            return ValidationResult(
                component="streamlit_config",
                status="fail",
                message="app.py file does not exist"
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return ValidationResult(
                component="streamlit_config",
                status="fail",
                message=f"Error reading app.py: {str(e)}"
            )
        
        # Parse the file to check for configuration
        config_analysis = self._analyze_streamlit_config(content)
        
        issues = []
        warnings = []
        
        # Check for required environment variables
        if not config_analysis['has_headless']:
            issues.append("Missing STREAMLIT_SERVER_HEADLESS configuration")
        
        if not config_analysis['has_port']:
            issues.append("Missing STREAMLIT_SERVER_PORT configuration")
        
        if not config_analysis['has_address']:
            issues.append("Missing STREAMLIT_SERVER_ADDRESS configuration")
        
        # Check configuration placement
        if config_analysis['has_config'] and not config_analysis['config_before_imports']:
            warnings.append("Streamlit configuration should be set before imports")
        
        # Check configuration values
        if config_analysis['has_headless'] and not config_analysis['headless_correct']:
            issues.append("STREAMLIT_SERVER_HEADLESS should be set to 'true'")
        
        if config_analysis['has_address'] and not config_analysis['address_correct']:
            issues.append("STREAMLIT_SERVER_ADDRESS should be set to '0.0.0.0'")
        
        if config_analysis['has_port'] and not config_analysis['port_correct']:
            warnings.append("STREAMLIT_SERVER_PORT should use PORT environment variable with default")
        
        if issues:
            return ValidationResult(
                component="streamlit_config",
                status="fail",
                message=f"Configuration issues: {'; '.join(issues)}"
            )
        elif warnings:
            return ValidationResult(
                component="streamlit_config",
                status="warning",
                message=f"Configuration warnings: {'; '.join(warnings)}"
            )
        else:
            return ValidationResult(
                component="streamlit_config",
                status="pass",
                message="Streamlit headless configuration is valid"
            )
    
    def _analyze_streamlit_config(self, content: str) -> Dict[str, bool]:
        """
        Analyze app.py content for Streamlit configuration.
        
        Args:
            content: Content of app.py file
            
        Returns:
            Dict[str, bool]: Analysis results for various configuration aspects
        """
        lines = content.split('\n')
        
        # Track configuration presence and values
        has_headless = False
        has_port = False
        has_address = False
        headless_correct = False
        port_correct = False
        address_correct = False
        
        # Track import positions
        streamlit_import_line = -1
        config_lines = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check for Streamlit imports
            if ('import streamlit' in line_stripped or 
                'from streamlit' in line_stripped):
                if streamlit_import_line == -1:
                    streamlit_import_line = i
            
            # Check for environment variable configurations
            if 'STREAMLIT_SERVER_HEADLESS' in line_stripped:
                has_headless = True
                config_lines.append(i)
                # Check if set to "true"
                if '"true"' in line_stripped or "'true'" in line_stripped:
                    headless_correct = True
            
            if 'STREAMLIT_SERVER_PORT' in line_stripped:
                has_port = True
                config_lines.append(i)
                # Check if uses PORT environment variable
                if ('os.getenv("PORT"' in line_stripped or 
                    "os.getenv('PORT'" in line_stripped or
                    'os.environ.get("PORT"' in line_stripped or
                    "os.environ.get('PORT'" in line_stripped):
                    port_correct = True
            
            if 'STREAMLIT_SERVER_ADDRESS' in line_stripped:
                has_address = True
                config_lines.append(i)
                # Check if set to "0.0.0.0"
                if '"0.0.0.0"' in line_stripped or "'0.0.0.0'" in line_stripped:
                    address_correct = True
        
        # Check if configuration is before imports
        config_before_imports = True
        if config_lines and streamlit_import_line != -1:
            config_before_imports = all(line_num < streamlit_import_line for line_num in config_lines)
        
        has_config = has_headless or has_port or has_address
        
        return {
            'has_headless': has_headless,
            'has_port': has_port,
            'has_address': has_address,
            'headless_correct': headless_correct,
            'port_correct': port_correct,
            'address_correct': address_correct,
            'has_config': has_config,
            'config_before_imports': config_before_imports,
            'streamlit_import_line': streamlit_import_line,
            'config_lines': config_lines
        }
    
    def inject_streamlit_config(self) -> ValidationResult:
        """
        Inject missing Streamlit configuration into app.py.
        
        Adds missing environment variable configurations before Streamlit imports.
        Ensures proper values and format for headless operation.
        
        Returns:
            ValidationResult: Result of the configuration injection operation
        """
        file_path = os.path.join(self.project_root, "app.py")
        
        if not os.path.exists(file_path):
            return ValidationResult(
                component="streamlit_config_injection",
                status="fail",
                message="app.py file does not exist",
                fix_applied=False
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return ValidationResult(
                component="streamlit_config_injection",
                status="fail",
                message=f"Error reading app.py: {str(e)}",
                fix_applied=False
            )
        
        # Analyze current configuration
        config_analysis = self._analyze_streamlit_config(content)
        
        # Determine what needs to be added or fixed
        configs_to_add = []
        configs_to_fix = []
        
        if not config_analysis['has_headless']:
            configs_to_add.append('os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"')
        elif not config_analysis['headless_correct']:
            configs_to_fix.append(('STREAMLIT_SERVER_HEADLESS', 'os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"'))
        
        if not config_analysis['has_port']:
            configs_to_add.append('os.environ["STREAMLIT_SERVER_PORT"] = os.getenv("PORT", "8080")')
        elif not config_analysis['port_correct']:
            configs_to_fix.append(('STREAMLIT_SERVER_PORT', 'os.environ["STREAMLIT_SERVER_PORT"] = os.getenv("PORT", "8080")'))
        
        if not config_analysis['has_address']:
            configs_to_add.append('os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"')
        elif not config_analysis['address_correct']:
            configs_to_fix.append(('STREAMLIT_SERVER_ADDRESS', 'os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"'))
        
        if not configs_to_add and not configs_to_fix:
            return ValidationResult(
                component="streamlit_config_injection",
                status="pass",
                message="No Streamlit configuration injection needed",
                fix_applied=False
            )
        
        lines = content.split('\n')
        
        try:
            # First, fix existing incorrect configurations
            if configs_to_fix:
                lines = self._fix_existing_config_lines(lines, configs_to_fix)
            
            # Then, add missing configurations
            if configs_to_add:
                lines = self._add_missing_config_lines(lines, configs_to_add)
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            changes_made = len(configs_to_add) + len(configs_to_fix)
            return ValidationResult(
                component="streamlit_config_injection",
                status="pass",
                message=f"Updated Streamlit configuration: {changes_made} settings modified",
                fix_applied=True
            )
            
        except Exception as e:
            return ValidationResult(
                component="streamlit_config_injection",
                status="fail",
                message=f"Failed to inject configuration: {str(e)}",
                fix_applied=False
            )
    
    def _find_config_insertion_point(self, lines: List[str]) -> int:
        """
        Find the best insertion point for Streamlit configuration.
        
        Args:
            lines: Lines of the app.py file
            
        Returns:
            int: Line number where configuration should be inserted
        """
        # Look for existing import statements
        import_end = 0
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Skip comments and empty lines at the beginning
            if not line_stripped or line_stripped.startswith('#'):
                continue
            
            # If we find an import, update the end position
            if (line_stripped.startswith('import ') or 
                line_stripped.startswith('from ') or
                line_stripped == 'import os'):
                import_end = i + 1
            else:
                # If we hit non-import code, stop looking
                break
        
        # Insert after imports but before other code
        return import_end
    
    def _fix_existing_config_lines(self, lines: List[str], configs_to_fix: List[Tuple[str, str]]) -> List[str]:
        """
        Fix existing incorrect Streamlit configuration lines.
        
        Args:
            lines: Lines of the app.py file
            configs_to_fix: List of (config_name, correct_line) tuples
            
        Returns:
            List[str]: Updated lines with fixed configurations
        """
        new_lines = []
        
        for line in lines:
            line_modified = False
            
            # Check if this line contains any configuration that needs fixing
            for config_name, correct_line in configs_to_fix:
                if config_name in line and 'os.environ' in line:
                    # Replace the entire line with the correct configuration
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * indent + correct_line)
                    line_modified = True
                    break
            
            if not line_modified:
                new_lines.append(line)
        
        return new_lines
    
    def _add_missing_config_lines(self, lines: List[str], configs_to_add: List[str]) -> List[str]:
        """
        Add missing Streamlit configuration lines at the appropriate location.
        
        Args:
            lines: Lines of the app.py file
            configs_to_add: List of configuration lines to add
            
        Returns:
            List[str]: Updated lines with added configurations
        """
        insertion_point = self._find_config_insertion_point(lines)
        
        # Insert configuration at the appropriate location
        new_lines = lines[:insertion_point]
        
        # Add import os if not present
        if not any('import os' in line for line in new_lines):
            new_lines.append('import os')
            new_lines.append('')
        
        # Add missing configurations
        for config in configs_to_add:
            new_lines.append(config)
        
        new_lines.append('')  # Add blank line after config
        new_lines.extend(lines[insertion_point:])
        
        return new_lines