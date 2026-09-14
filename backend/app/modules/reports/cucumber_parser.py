"""Cucumber JSON report parser for extracting test metrics."""
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class CucumberParser:
    """Parser for Cucumber JSON reports."""
    
    @staticmethod
    def parse(cucumber_json: str) -> Dict[str, Any]:
        """Parse Cucumber JSON report and extract metrics.
        
        Args:
            cucumber_json: Cucumber JSON string
            
        Returns:
            Dictionary containing parsed metrics and scenarios
            
        Raises:
            ValueError: If JSON is invalid or malformed
        """
        try:
            data = json.loads(cucumber_json)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Cucumber JSON: {e}")
            raise ValueError(f"Invalid JSON format: {str(e)}")
        
        if not isinstance(data, list):
            raise ValueError("Cucumber JSON must be an array of features")
        
        scenarios = []
        total_scenarios = 0
        passed_scenarios = 0
        failed_scenarios = 0
        skipped_scenarios = 0
        total_duration = 0.0
        
        for feature in data:
            if not isinstance(feature, dict):
                continue
            
            feature_name = feature.get("name", "Unknown Feature")
            elements = feature.get("elements", [])
            
            for element in elements:
                if not isinstance(element, dict):
                    continue
                
                # Skip background elements
                if element.get("type") == "background":
                    continue
                
                scenario_name = element.get("name", "Unknown Scenario")
                scenario_tags = CucumberParser._extract_tags(element.get("tags", []))
                steps = element.get("steps", [])
                
                # Calculate scenario status and duration
                scenario_status, scenario_duration, error_info = CucumberParser._analyze_steps(steps)
                
                # Update counters
                total_scenarios += 1
                if scenario_status == "passed":
                    passed_scenarios += 1
                elif scenario_status == "failed":
                    failed_scenarios += 1
                elif scenario_status == "skipped":
                    skipped_scenarios += 1
                
                total_duration += scenario_duration
                
                # Create scenario data
                scenario_data = {
                    "name": scenario_name,
                    "status": scenario_status,
                    "duration": scenario_duration,
                    "error_message": error_info.get("message"),
                    "stack_trace": error_info.get("stack_trace"),
                    "tags": scenario_tags,
                    "feature": feature_name,
                }
                
                scenarios.append(scenario_data)
        
        return {
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_scenarios,
            "failed_scenarios": failed_scenarios,
            "skipped_scenarios": skipped_scenarios,
            "duration": total_duration,
            "scenarios": scenarios,
        }
    
    @staticmethod
    def _extract_tags(tags: List[Dict]) -> Optional[str]:
        """Extract tags from Cucumber tags array.
        
        Args:
            tags: List of tag dictionaries
            
        Returns:
            Comma-separated tag string or None
        """
        if not tags:
            return None
        
        tag_names = [tag.get("name", "") for tag in tags if isinstance(tag, dict)]
        tag_names = [t.strip() for t in tag_names if t.strip()]
        
        return ", ".join(tag_names) if tag_names else None
    
    @staticmethod
    def _analyze_steps(steps: List[Dict]) -> tuple[str, float, Dict[str, Optional[str]]]:
        """Analyze steps to determine scenario status, duration, and error info.
        
        Args:
            steps: List of step dictionaries
            
        Returns:
            Tuple of (status, duration, error_info)
        """
        if not steps:
            return "skipped", 0.0, {"message": None, "stack_trace": None}
        
        total_duration = 0.0
        status = "passed"
        error_message = None
        stack_trace = None
        
        for step in steps:
            if not isinstance(step, dict):
                continue
            
            # Get step result
            result = step.get("result", {})
            step_status = result.get("status", "skipped")
            step_duration = result.get("duration", 0) / 1_000_000_000  # Convert nanoseconds to seconds
            
            total_duration += step_duration
            
            # Determine overall status
            if step_status == "failed":
                status = "failed"
                error_message = result.get("error_message")
                
                # Try to extract stack trace from error_message
                if error_message:
                    # Split by newline and take first line as message, rest as stack trace
                    lines = error_message.split("\n")
                    if len(lines) > 1:
                        error_message = lines[0]
                        stack_trace = "\n".join(lines[1:])
            
            elif step_status == "skipped" and status == "passed":
                status = "skipped"
            
            elif step_status == "undefined" and status == "passed":
                status = "skipped"
        
        return status, total_duration, {
            "message": error_message,
            "stack_trace": stack_trace
        }
    
    @staticmethod
    def validate_format(cucumber_json: str) -> bool:
        """Validate if the JSON is in Cucumber format.
        
        Args:
            cucumber_json: JSON string to validate
            
        Returns:
            True if valid Cucumber format, False otherwise
        """
        try:
            data = json.loads(cucumber_json)
            
            # Must be an array
            if not isinstance(data, list):
                return False
            
            # Must have at least one feature
            if len(data) == 0:
                return False
            
            # First element should be a feature with required fields
            first_feature = data[0]
            if not isinstance(first_feature, dict):
                return False
            
            # Check for required Cucumber fields
            required_fields = ["elements"]
            for field in required_fields:
                if field not in first_feature:
                    return False
            
            return True
            
        except (json.JSONDecodeError, Exception):
            return False
