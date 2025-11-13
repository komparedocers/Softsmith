"""
Web Agent Runner - Playwright-based web UI testing service.
"""
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import logging
from typing import Dict, List, Any
from pathlib import Path

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Screenshots directory
SCREENSHOTS_DIR = Path("/app/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


class WebTestRunner:
    """Runs web tests using Playwright."""

    def __init__(self):
        self.playwright = None
        self.browser = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def run_scenario(self, scenario: Dict[str, Any], base_url: str, project_id: str) -> Dict[str, Any]:
        """Run a single test scenario."""
        logger.info(f"Running scenario: {scenario['name']}")

        result = {
            "name": scenario["name"],
            "status": "pending",
            "steps": [],
            "screenshots": [],
            "errors": [],
        }

        try:
            context = self.browser.new_context()
            page = context.new_page()

            for step_idx, step in enumerate(scenario.get("steps", [])):
                step_result = self._execute_step(page, step, base_url, project_id, scenario["name"], step_idx)
                result["steps"].append(step_result)

                if step_result["status"] == "failed":
                    result["status"] = "failed"
                    break

            if result["status"] == "pending":
                result["status"] = "passed"

            context.close()

        except Exception as e:
            logger.error(f"Scenario failed: {str(e)}")
            result["status"] = "failed"
            result["errors"].append(str(e))

        return result

    def _execute_step(
        self,
        page,
        step: Dict[str, Any],
        base_url: str,
        project_id: str,
        scenario_name: str,
        step_idx: int
    ) -> Dict[str, Any]:
        """Execute a single test step."""
        action = step.get("action")
        step_result = {
            "action": action,
            "status": "passed",
            "error": None,
        }

        try:
            if action == "goto":
                url = step.get("url", "/")
                if url.startswith("/"):
                    url = base_url + url
                logger.info(f"Navigating to {url}")
                page.goto(url, timeout=30000)

            elif action == "click":
                selector = step.get("selector")
                logger.info(f"Clicking {selector}")
                page.click(selector, timeout=10000)

            elif action == "fill":
                selector = step.get("selector")
                value = step.get("value")
                logger.info(f"Filling {selector} with {value}")
                page.fill(selector, value, timeout=10000)

            elif action == "wait":
                if "selector" in step:
                    selector = step["selector"]
                    logger.info(f"Waiting for {selector}")
                    page.wait_for_selector(selector, timeout=10000)
                elif "timeout" in step:
                    timeout = step["timeout"]
                    logger.info(f"Waiting for {timeout}ms")
                    page.wait_for_timeout(timeout)

            elif action == "screenshot":
                name = step.get("name", f"step_{step_idx}")
                screenshot_path = SCREENSHOTS_DIR / f"{project_id}_{scenario_name}_{name}.png"
                logger.info(f"Taking screenshot: {screenshot_path}")
                page.screenshot(path=str(screenshot_path))
                step_result["screenshot"] = str(screenshot_path)

            elif action == "assert_text":
                selector = step.get("selector")
                expected_text = step.get("text")
                element = page.locator(selector)
                actual_text = element.inner_text()
                if expected_text not in actual_text:
                    raise AssertionError(f"Expected '{expected_text}' but got '{actual_text}'")

            else:
                logger.warning(f"Unknown action: {action}")

        except PlaywrightTimeout as e:
            logger.error(f"Step timeout: {str(e)}")
            step_result["status"] = "failed"
            step_result["error"] = f"Timeout: {str(e)}"

        except Exception as e:
            logger.error(f"Step failed: {str(e)}")
            step_result["status"] = "failed"
            step_result["error"] = str(e)

        return step_result


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "web-agent"})


@app.route("/run-tests", methods=["POST"])
def run_tests():
    """Run web tests for a project."""
    data = request.json
    project_id = data.get("project_id")
    app_url = data.get("app_url")
    scenarios = data.get("scenarios", [])

    logger.info(f"Running web tests for project {project_id}")
    logger.info(f"App URL: {app_url}")
    logger.info(f"Scenarios: {len(scenarios)}")

    results = {
        "project_id": project_id,
        "app_url": app_url,
        "scenarios": [],
        "passed": 0,
        "failed": 0,
        "total": len(scenarios),
    }

    try:
        with WebTestRunner() as runner:
            for scenario in scenarios:
                scenario_result = runner.run_scenario(scenario, app_url, project_id)
                results["scenarios"].append(scenario_result)

                if scenario_result["status"] == "passed":
                    results["passed"] += 1
                else:
                    results["failed"] += 1

        logger.info(f"Tests completed: {results['passed']} passed, {results['failed']} failed")

    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
