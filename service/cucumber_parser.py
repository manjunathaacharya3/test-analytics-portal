# cucumber_parser.py - Cucumber JSON Parser
from typing import Dict, List, Any


class CucumberParser:
    """Parse Cucumber JSON reports into structured data"""

    def parse_cucumber_json(self, cucumber_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse cucumber JSON and extract structured information"""

        if not isinstance(cucumber_data, list):
            raise ValueError("Cucumber JSON should be a list of features")

        parsed_features = []
        summary = {
            'total_features': 0,
            'total_scenarios': 0,
            'passed_scenarios': 0,
            'failed_scenarios': 0,
            'skipped_scenarios': 0,
            'total_steps': 0,
            'passed_steps': 0,
            'failed_steps': 0,
            'skipped_steps': 0,
            'execution_start_time': None,
            'execution_end_time': None,
            'duration_ms': 0
        }

        for feature_json in cucumber_data:
            feature_info, scenarios_data = self._parse_feature(feature_json)

            parsed_features.append({
                'feature_info': feature_info,
                'scenarios': scenarios_data
            })

            summary['total_features'] += 1

            for scenario_data in scenarios_data:
                scenario_info = scenario_data['scenario_info']
                summary['total_scenarios'] += 1

                if scenario_info['status'] == 'passed':
                    summary['passed_scenarios'] += 1
                elif scenario_info['status'] == 'failed':
                    summary['failed_scenarios'] += 1
                else:
                    summary['skipped_scenarios'] += 1

                summary['total_steps'] += len(scenario_data['steps'])

                for step in scenario_data['steps']:
                    if step['status'] == 'passed':
                        summary['passed_steps'] += 1
                    elif step['status'] == 'failed':
                        summary['failed_steps'] += 1
                    else:
                        summary['skipped_steps'] += 1

                summary['duration_ms'] += scenario_info.get('duration_ms', 0)

        return {
            'summary': summary,
            'features': parsed_features
        }

    def _parse_feature(self, feature_json: Dict[str, Any]) -> tuple:
        """Parse a single feature"""
        feature_info = {
            'name': feature_json.get('name', ''),
            'description': feature_json.get('description', ''),
            'uri': feature_json.get('uri', ''),
            'line': feature_json.get('line', 0),
            'keyword': feature_json.get('keyword', 'Feature'),
            'tags': [tag.get('name', '') for tag in feature_json.get('tags', [])],
            'status': 'passed',
            'duration_ms': 0
        }

        scenarios_data = []
        feature_status = 'passed'
        feature_duration = 0

        for element in feature_json.get('elements', []):
            if element.get('type') == 'scenario':
                scenario_info, steps_data = self._parse_scenario(element)
                scenarios_data.append({
                    'scenario_info': scenario_info,
                    'steps': steps_data
                })

                if scenario_info['status'] == 'failed':
                    feature_status = 'failed'
                elif scenario_info['status'] == 'skipped' and feature_status == 'passed':
                    feature_status = 'skipped'

                feature_duration += scenario_info.get('duration_ms', 0)

        feature_info['status'] = feature_status
        feature_info['duration_ms'] = feature_duration

        return feature_info, scenarios_data

    def _parse_scenario(self, scenario_json: Dict[str, Any]) -> tuple:
        """Parse a single scenario"""
        scenario_info = {
            'name': scenario_json.get('name', ''),
            'description': scenario_json.get('description', ''),
            'line': scenario_json.get('line', 0),
            'keyword': scenario_json.get('keyword', 'Scenario'),
            'tags': [tag.get('name', '') for tag in scenario_json.get('tags', [])],
            'status': 'passed',
            'duration_ms': 0,
            'error_message': None
        }

        steps_data = []
        scenario_status = 'passed'
        scenario_duration = 0
        error_message = None

        for i, step_json in enumerate(scenario_json.get('steps', [])):
            step_info = self._parse_step(step_json, i)
            steps_data.append(step_info)

            if step_info['status'] == 'failed':
                scenario_status = 'failed'
                if not error_message and step_info.get('error_message'):
                    error_message = step_info['error_message']
            elif step_info['status'] == 'skipped' and scenario_status == 'passed':
                scenario_status = 'skipped'

            scenario_duration += step_info.get('duration_ms', 0)

        scenario_info['status'] = scenario_status
        scenario_info['duration_ms'] = scenario_duration
        scenario_info['error_message'] = error_message

        return scenario_info, steps_data

    def _parse_step(self, step_json: Dict[str, Any], order: int) -> Dict[str, Any]:
        """Parse a single step"""
        result = step_json.get('result', {})

        step_info = {
            'name': step_json.get('name', ''),
            'keyword': step_json.get('keyword', '').strip(),
            'line': step_json.get('line', 0),
            'status': result.get('status', 'undefined'),
            'duration_ms': int(result.get('duration', 0) / 1000000) if result.get('duration') else 0,
            'error_message': result.get('error_message'),
            'step_order': order
        }

        return step_info
