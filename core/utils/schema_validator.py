import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class SchemaValidator:
    """
    Utility class responsible for enforcing a canonical JSON schema
    for all system health metrics retrieved within TwisterLab.
    Prevents runtime data errors by standardizing structure and type casting.
    """
    SCHEMA_VERSION = "1.0"

    @staticmethod
    def _validate_metric(raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validates a single raw metric dict against the canonical schema."""
        required_keys = ["metric_id", "description", "unit", "value"]
        if not all(key in raw_data for key in required_keys):
            print(f"Validation failed: Metric data missing one or more required keys. Data received: {raw_data}")
            return None

        try:
            # Type Casting and Standardization: Assume 'value' can be float/int based on context, default to str if complex.
            # This handles both numeric (e.g., 45.2) and string values safely.
            standardized_metric = {
                "metric_id": str(raw_data['metric_id']),
                "description": str(raw_data['description']),
                "unit": str(raw_data['unit']),
                "type": str(raw_data.get('expected_type', 'string')), # Fallback to string type check if missing
                "value": float(raw_data['value']) if isinstance(raw_data['value'], (int, float)) else raw_data['value'],
                "is_critical": bool(raw_data.get('is_critical', True))
            }
            return standardized_metric
        except (ValueError, TypeError) as e:
            print(f"Validation failed during casting for metric {raw_data.get('metric_id')}: {e}")
            return None

    @staticmethod
    def validate_and_standardize(raw_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processes a raw dictionary of metrics and returns a list of strictly
        schema-compliant metric dictionaries. Only valid entries are included.

        Args:
            raw_metrics (Dict[str, Any]): Dictionary containing unsanitized metric data.

        Returns:
            List[Dict[str, Any]]: A list of standardized metrics ready for API/UI consumption.
        """
        standardized_list = []
        print("--- Starting Metric Standardization Process ---")
        for key, raw_data in raw_metrics.items():
            # We assume the raw dictionary keys are our metric IDs or names
            validated_metric = SchemaValidator._validate_metric(raw_data)
            if validated_metric:
                standardized_list.append(validated_metric)

        print("--- Standardization Complete ---")
        return standardized_list

# Helper function to generate a consistent top-level report payload structure
def create_health_report_payload(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Creates the final wrapper object for system health."""
    return {
        "system_health_report": {
            "schema_version": SchemaValidator.SCHEMA_VERSION,
            "timestamp": datetime.now().isoformat() + 'Z',
            "metrics": metrics # Contains the list of standardized metric dicts
        }
    }

# Example Usage (for internal testing/documentation):
if __name__ == "__main__":
    print("--- SchemaValidator Test Run ---")
    # Simulating raw, messy input data from different sources
    messy_data = {
        "CPU_LOAD": {
            "metric_id": "cpu_utilization",
            "description": "Current CPU usage.",
            "unit": "percent",
            "value": 45.2,
            "expected_type": "number",
            "is_critical": False
        },
        "UPTIME": {
            "metric_id": "uptime",
            "description": "System operational uptime.",
            "unit": "s",
            "value": 86400,
            "expected_type": "number",
            "is_critical": True
        },
        # Example of bad data (missing 'unit')
        "BAD_DATA_SAMPLE": {
             "metric_id": "bad_test",
             "description": "This one is intentionally broken.",
             "value": "should fail", # Wrong type, missing unit
             "is_critical": False
        }
    }

    standardized = SchemaValidator.validate_and_standardize(messy_data)
    final_payload = create_health_report_payload(standardized)
    print("\n--- Final Validated Payload (JSON Dump): ---")
    print(json.dumps(final_payload, indent=2))