#!/usr/bin/env python3
"""
ATHintel Test Suite Runner
Comprehensive test execution script with reporting and quality gates
"""

import os
import sys
import argparse
import asyncio
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSuite(Enum):
    """Available test suites"""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    SECURITY = "security"
    PERFORMANCE = "performance"
    E2E = "e2e"
    ALL = "all"
    SMOKE = "smoke"
    REGRESSION = "regression"


class TestResult(Enum):
    """Test result status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestExecutionResult:
    """Result of test execution"""
    suite: str
    status: TestResult
    duration: float
    tests_run: int
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    coverage_percentage: float
    exit_code: int
    output_file: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class QualityGateResult:
    """Quality gate evaluation result"""
    passed: bool
    min_coverage_met: bool
    max_failures_met: bool
    security_issues_found: int
    performance_degradation: float
    overall_score: float
    recommendations: List[str]


class TestRunner:
    """Main test runner class"""
    
    def __init__(self, project_root: Path, output_dir: Path):
        self.project_root = project_root
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Configure logging
        self.logger = self._setup_logging()
        
        # Test configuration
        self.test_config = self._load_test_config()
        
        # Results storage
        self.results: List[TestExecutionResult] = []
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration"""
        logger = logging.getLogger('test_runner')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = self.output_dir / 'test_runner.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _load_test_config(self) -> Dict[str, Any]:
        """Load test configuration"""
        config_file = self.project_root / 'tests' / 'config.json'
        
        default_config = {
            'min_coverage': 85,
            'max_failed_tests': 0,
            'max_security_issues': 0,
            'max_performance_degradation': 20,
            'timeout_seconds': 300,
            'parallel_workers': 4,
            'retry_failed_tests': True,
            'generate_reports': True,
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load test config: {e}")
        
        return default_config
    
    async def run_test_suite(self, suite: TestSuite, **kwargs) -> TestExecutionResult:
        """Run a specific test suite"""
        
        self.logger.info(f"Starting {suite.value} test suite")
        start_time = time.perf_counter()
        
        # Prepare test command
        cmd = self._build_test_command(suite, **kwargs)
        
        # Set up output files
        output_file = self.output_dir / f"{suite.value}_output.txt"
        junit_file = self.output_dir / f"{suite.value}_junit.xml"
        coverage_file = self.output_dir / f"{suite.value}_coverage.xml"
        
        try:
            # Run tests
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.project_root
            )
            
            stdout, _ = await asyncio.wait_for(
                process.communicate(),
                timeout=self.test_config['timeout_seconds']
            )
            
            # Save output
            with open(output_file, 'w') as f:
                f.write(stdout.decode())
            
            # Parse results
            result = self._parse_test_results(
                suite=suite.value,
                exit_code=process.returncode,
                output_file=output_file,
                junit_file=junit_file,
                coverage_file=coverage_file,
                duration=time.perf_counter() - start_time
            )
            
            self.logger.info(f"Completed {suite.value} tests: {result.status.value}")
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Test suite {suite.value} timed out")
            return TestExecutionResult(
                suite=suite.value,
                status=TestResult.ERROR,
                duration=time.perf_counter() - start_time,
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                tests_skipped=0,
                coverage_percentage=0.0,
                exit_code=-1,
                error_message="Test suite timed out"
            )
        
        except Exception as e:
            self.logger.error(f"Error running {suite.value} tests: {e}")
            return TestExecutionResult(
                suite=suite.value,
                status=TestResult.ERROR,
                duration=time.perf_counter() - start_time,
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                tests_skipped=0,
                coverage_percentage=0.0,
                exit_code=-1,
                error_message=str(e)
            )
    
    def _build_test_command(self, suite: TestSuite, **kwargs) -> List[str]:
        """Build pytest command for specific test suite"""
        
        cmd = ['python', '-m', 'pytest']
        
        # Add test paths based on suite
        if suite == TestSuite.UNIT:
            cmd.append('tests/unit/')
        elif suite == TestSuite.INTEGRATION:
            cmd.append('tests/integration/')
        elif suite == TestSuite.FUNCTIONAL:
            cmd.append('tests/functional/')
        elif suite == TestSuite.SECURITY:
            cmd.append('tests/security/')
        elif suite == TestSuite.PERFORMANCE:
            cmd.extend(['tests/performance/', '-m', 'not slow'])
        elif suite == TestSuite.E2E:
            cmd.append('tests/e2e/')
        elif suite == TestSuite.SMOKE:
            cmd.extend(['-m', 'smoke'])
        elif suite == TestSuite.REGRESSION:
            cmd.extend(['-m', 'regression'])
        elif suite == TestSuite.ALL:
            cmd.append('tests/')
        
        # Add common options
        cmd.extend([
            '--verbose',
            '--tb=short',
            f'--junit-xml={self.output_dir}/{suite.value}_junit.xml',
            f'--cov-report=xml:{self.output_dir}/{suite.value}_coverage.xml',
            '--cov=src'
        ])
        
        # Add suite-specific options
        if suite == TestSuite.PERFORMANCE:
            cmd.extend(['--benchmark-only', '--benchmark-json=performance_results.json'])
        
        if suite == TestSuite.SECURITY:
            cmd.extend(['--cov-fail-under=90'])  # Higher coverage for security
        
        # Add parallel execution for suitable suites
        if suite in [TestSuite.UNIT, TestSuite.INTEGRATION] and 'no_parallel' not in kwargs:
            cmd.extend(['-n', str(self.test_config['parallel_workers'])])
        
        # Add custom options
        if kwargs.get('markers'):
            cmd.extend(['-m', kwargs['markers']])
        
        if kwargs.get('verbose'):
            cmd.append('-vv')
        
        if kwargs.get('no_coverage'):
            cmd = [c for c in cmd if not c.startswith('--cov')]
        
        return cmd
    
    def _parse_test_results(self, suite: str, exit_code: int, output_file: Path,
                           junit_file: Path, coverage_file: Path, duration: float) -> TestExecutionResult:
        """Parse test execution results"""
        
        # Default values
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        tests_skipped = 0
        coverage_percentage = 0.0
        
        # Parse JUnit XML if available
        if junit_file.exists():
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(junit_file)
                root = tree.getroot()
                
                # Parse test counts
                tests_run = int(root.get('tests', 0))
                tests_failed = int(root.get('failures', 0)) + int(root.get('errors', 0))
                tests_skipped = int(root.get('skipped', 0))
                tests_passed = tests_run - tests_failed - tests_skipped
                
            except Exception as e:
                self.logger.warning(f"Failed to parse JUnit results: {e}")
        
        # Parse coverage XML if available
        if coverage_file.exists():
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(coverage_file)
                root = tree.getroot()
                
                # Get line rate (coverage percentage)
                coverage_percentage = float(root.get('line-rate', 0)) * 100
                
            except Exception as e:
                self.logger.warning(f"Failed to parse coverage results: {e}")
        
        # Determine overall status
        if exit_code == 0 and tests_failed == 0:
            status = TestResult.PASSED
        elif exit_code != 0:
            status = TestResult.ERROR
        else:
            status = TestResult.FAILED
        
        return TestExecutionResult(
            suite=suite,
            status=status,
            duration=duration,
            tests_run=tests_run,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            tests_skipped=tests_skipped,
            coverage_percentage=coverage_percentage,
            exit_code=exit_code,
            output_file=str(output_file)
        )
    
    async def run_multiple_suites(self, suites: List[TestSuite], **kwargs) -> List[TestExecutionResult]:
        """Run multiple test suites"""
        
        results = []
        
        for suite in suites:
            result = await self.run_test_suite(suite, **kwargs)
            results.append(result)
            self.results.append(result)
            
            # Stop on first failure if requested
            if kwargs.get('fail_fast') and result.status in [TestResult.FAILED, TestResult.ERROR]:
                self.logger.warning(f"Stopping execution due to {suite.value} test failure")
                break
        
        return results
    
    def evaluate_quality_gates(self) -> QualityGateResult:
        """Evaluate quality gates based on test results"""
        
        # Calculate overall metrics
        total_tests = sum(r.tests_run for r in self.results)
        total_failed = sum(r.tests_failed for r in self.results)
        
        # Calculate weighted coverage (by number of tests)
        if total_tests > 0:
            weighted_coverage = sum(
                r.coverage_percentage * r.tests_run for r in self.results
            ) / total_tests
        else:
            weighted_coverage = 0.0
        
        # Check quality gates
        min_coverage_met = weighted_coverage >= self.test_config['min_coverage']
        max_failures_met = total_failed <= self.test_config['max_failed_tests']
        
        # Security issues (from security test suite)
        security_issues = 0
        security_result = next((r for r in self.results if r.suite == 'security'), None)
        if security_result:
            security_issues = security_result.tests_failed
        
        # Performance degradation (would be calculated from performance baseline)
        performance_degradation = 0.0  # Placeholder
        
        # Overall quality score (0-100)
        quality_score = min(100.0, (
            (weighted_coverage / 100) * 40 +  # 40% weight on coverage
            (1 - min(total_failed / max(total_tests, 1), 1)) * 30 +  # 30% weight on test success
            (1 - min(security_issues / 10, 1)) * 20 +  # 20% weight on security
            (1 - min(performance_degradation / 100, 1)) * 10  # 10% weight on performance
        ) * 100)
        
        # Generate recommendations
        recommendations = []
        if not min_coverage_met:
            recommendations.append(f"Increase test coverage to {self.test_config['min_coverage']}% (currently {weighted_coverage:.1f}%)")
        if not max_failures_met:
            recommendations.append(f"Fix {total_failed} failing tests")
        if security_issues > 0:
            recommendations.append(f"Address {security_issues} security issues")
        if performance_degradation > 20:
            recommendations.append(f"Address {performance_degradation:.1f}% performance degradation")
        
        # Overall pass/fail
        gates_passed = (
            min_coverage_met and
            max_failures_met and
            security_issues <= self.test_config['max_security_issues'] and
            performance_degradation <= self.test_config['max_performance_degradation']
        )
        
        return QualityGateResult(
            passed=gates_passed,
            min_coverage_met=min_coverage_met,
            max_failures_met=max_failures_met,
            security_issues_found=security_issues,
            performance_degradation=performance_degradation,
            overall_score=quality_score,
            recommendations=recommendations
        )
    
    def generate_report(self) -> Path:
        """Generate comprehensive test report"""
        
        report_file = self.output_dir / 'test_report.html'
        
        # Generate HTML report
        html_content = self._generate_html_report()
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        # Generate JSON report
        json_report = {
            'timestamp': datetime.now().isoformat(),
            'results': [asdict(r) for r in self.results],
            'quality_gate': asdict(self.evaluate_quality_gates()),
            'config': self.test_config
        }
        
        json_file = self.output_dir / 'test_report.json'
        with open(json_file, 'w') as f:
            json.dump(json_report, f, indent=2)
        
        self.logger.info(f"Generated test report: {report_file}")
        return report_file
    
    def _generate_html_report(self) -> str:
        """Generate HTML test report"""
        
        quality_gate = self.evaluate_quality_gates()
        
        # Calculate summary metrics
        total_tests = sum(r.tests_run for r in self.results)
        total_passed = sum(r.tests_passed for r in self.results)
        total_failed = sum(r.tests_failed for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ATHintel Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
                .container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 40px; }
                .status-pass { color: #28a745; }
                .status-fail { color: #dc3545; }
                .status-error { color: #ffc107; }
                .metric-card { display: inline-block; margin: 10px; padding: 20px; border-radius: 5px; text-align: center; min-width: 150px; }
                .metric-card.pass { background-color: #d4edda; border: 1px solid #c3e6cb; }
                .metric-card.fail { background-color: #f8d7da; border: 1px solid #f5c6cb; }
                .metric-card.warning { background-color: #fff3cd; border: 1px solid #ffeaa7; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f8f9fa; }
                .progress-bar { width: 100%; height: 20px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; }
                .progress-fill { height: 100%; background-color: #28a745; }
                .recommendations { background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ATHintel Test Report</h1>
                    <p>Generated on {timestamp}</p>
                    <h2 class="{quality_status}">Quality Gate: {quality_gate_status}</h2>
                </div>
                
                <div class="metrics">
                    <div class="metric-card {total_status}">
                        <h3>Total Tests</h3>
                        <h2>{total_tests}</h2>
                    </div>
                    <div class="metric-card pass">
                        <h3>Passed</h3>
                        <h2>{total_passed}</h2>
                    </div>
                    <div class="metric-card fail">
                        <h3>Failed</h3>
                        <h2>{total_failed}</h2>
                    </div>
                    <div class="metric-card {coverage_status}">
                        <h3>Coverage</h3>
                        <h2>{coverage:.1f}%</h2>
                    </div>
                    <div class="metric-card warning">
                        <h3>Duration</h3>
                        <h2>{duration:.1f}s</h2>
                    </div>
                    <div class="metric-card {score_status}">
                        <h3>Quality Score</h3>
                        <h2>{quality_score:.1f}</h2>
                    </div>
                </div>
                
                <h3>Test Suite Results</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Suite</th>
                            <th>Status</th>
                            <th>Tests</th>
                            <th>Passed</th>
                            <th>Failed</th>
                            <th>Coverage</th>
                            <th>Duration</th>
                        </tr>
                    </thead>
                    <tbody>
                        {suite_rows}
                    </tbody>
                </table>
                
                {recommendations_section}
                
            </div>
        </body>
        </html>
        """
        
        # Generate suite rows
        suite_rows = ""
        for result in self.results:
            status_class = {
                TestResult.PASSED: "status-pass",
                TestResult.FAILED: "status-fail",
                TestResult.ERROR: "status-error",
                TestResult.SKIPPED: "status-warning"
            }.get(result.status, "")
            
            suite_rows += f"""
                <tr>
                    <td>{result.suite}</td>
                    <td class="{status_class}">{result.status.value.upper()}</td>
                    <td>{result.tests_run}</td>
                    <td>{result.tests_passed}</td>
                    <td>{result.tests_failed}</td>
                    <td>{result.coverage_percentage:.1f}%</td>
                    <td>{result.duration:.1f}s</td>
                </tr>
            """
        
        # Generate recommendations section
        recommendations_section = ""
        if quality_gate.recommendations:
            recommendations_section = f"""
                <div class="recommendations">
                    <h3>Recommendations</h3>
                    <ul>
                        {''.join(f'<li>{rec}</li>' for rec in quality_gate.recommendations)}
                    </ul>
                </div>
            """
        
        # Calculate weighted coverage
        if total_tests > 0:
            weighted_coverage = sum(r.coverage_percentage * r.tests_run for r in self.results) / total_tests
        else:
            weighted_coverage = 0.0
        
        return html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            quality_gate_status="PASSED" if quality_gate.passed else "FAILED",
            quality_status="status-pass" if quality_gate.passed else "status-fail",
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            total_status="pass" if total_failed == 0 else "fail",
            coverage=weighted_coverage,
            coverage_status="pass" if quality_gate.min_coverage_met else "fail",
            duration=total_duration,
            quality_score=quality_gate.overall_score,
            score_status="pass" if quality_gate.overall_score >= 80 else "warning" if quality_gate.overall_score >= 60 else "fail",
            suite_rows=suite_rows,
            recommendations_section=recommendations_section
        )


async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description="ATHintel Test Suite Runner")
    parser.add_argument(
        '--suite', '-s',
        type=str,
        choices=[s.value for s in TestSuite],
        default=TestSuite.ALL.value,
        help='Test suite to run'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default=Path('test_results'),
        help='Output directory for test results'
    )
    parser.add_argument(
        '--markers', '-m',
        type=str,
        help='Pytest markers to filter tests'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Skip coverage collection'
    )
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='Disable parallel test execution'
    )
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first test suite failure'
    )
    parser.add_argument(
        '--generate-report',
        action='store_true',
        default=True,
        help='Generate HTML test report'
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(
        project_root=project_root,
        output_dir=args.output_dir
    )
    
    # Determine suites to run
    if args.suite == TestSuite.ALL.value:
        suites = [TestSuite.SECURITY, TestSuite.UNIT, TestSuite.FUNCTIONAL, TestSuite.INTEGRATION]
    else:
        suites = [TestSuite(args.suite)]
    
    # Run tests
    print(f"🧪 Running {args.suite} test suite(s)...")
    
    results = await runner.run_multiple_suites(
        suites=suites,
        markers=args.markers,
        verbose=args.verbose,
        no_coverage=args.no_coverage,
        no_parallel=args.no_parallel,
        fail_fast=args.fail_fast
    )
    
    # Evaluate quality gates
    quality_gate = runner.evaluate_quality_gates()
    
    # Generate report
    if args.generate_report:
        report_file = runner.generate_report()
        print(f"📊 Test report generated: {report_file}")
    
    # Print summary
    total_tests = sum(r.tests_run for r in results)
    total_passed = sum(r.tests_passed for r in results)
    total_failed = sum(r.tests_failed for r in results)
    
    print(f"\n🏆 Test Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {total_failed}")
    print(f"   Quality Score: {quality_gate.overall_score:.1f}")
    print(f"   Quality Gate: {'✅ PASSED' if quality_gate.passed else '❌ FAILED'}")
    
    if quality_gate.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in quality_gate.recommendations:
            print(f"   • {rec}")
    
    # Exit with appropriate code
    exit_code = 0 if quality_gate.passed else 1
    print(f"\n🚪 Exiting with code: {exit_code}")
    return exit_code


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)