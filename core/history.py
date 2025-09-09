import os
import json
import shutil
from datetime import datetime


def load_test_history(app) -> None:
    """Load test execution history"""
    # Placeholder for loading test history
    app.add_log("📊 Ready to run tests", "info")


def load_history_data(app) -> None:
    """Load test history data from logs directory with detailed information"""
    # Read logs from project root (same place the runner writes to)
    logs_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(logs_dir):
        return

    # Clear existing data
    for item in app.history_tree.get_children():
        app.history_tree.delete(item)

    # Get all test directories
    test_dirs = []
    for item in os.listdir(logs_dir):
        item_path = os.path.join(logs_dir, item)
        if os.path.isdir(item_path) and item.endswith("-checkout"):
            test_dirs.append(item)

    # Sort by date/time (newest first)
    test_dirs.sort(reverse=True)

    for test_dir in test_dirs:
        summary_path = os.path.join(logs_dir, test_dir, "summary.json")
        if os.path.exists(summary_path):
            try:
                with open(summary_path, "r") as f:
                    summary = json.load(f)

                # Parse datetime from directory name (format: 20250821-203515-checkout)
                date_str = test_dir.replace("-checkout", "")
                date_obj = datetime.strptime(date_str, "%Y%m%d-%H%M%S")

                date = date_obj.strftime("%Y-%m-%d")
                time = date_obj.strftime("%H:%M:%S")

                # Extract test details from summary
                project = summary.get("project", "GOOGLE")
                mode = summary.get("mode", "headless")

                # Get status with proper mapping (support current runner values)
                raw_status = str(summary.get("status", "")).lower()
                if raw_status in {"passed", "success", "ok"}:
                    status = "Success"
                elif raw_status in {"aborted"}:
                    status = "Aborted"
                else:
                    status = "Failed"

                # Get duration (fallback to compute from steps if not provided)
                duration = summary.get("durationSec", 0)
                if not duration:
                    try:
                        steps = summary.get("steps", []) or []
                        if steps:
                            start_ts = steps[0].get("start")
                            end_ts = None
                            for s in reversed(steps):
                                end_ts = s.get("end") or end_ts
                                if end_ts:
                                    break
                            if start_ts and end_ts:
                                duration = max(0.0, float(end_ts) - float(start_ts))
                    except Exception:
                        duration = 0
                duration_str = f"{duration:.1f}s"

                # Create detailed error information
                details = ""
                if status == "Failed":
                    error = summary.get("error", "Unknown error")
                    if error:
                        # Truncate long error messages but keep important parts
                        if len(error) > 80:
                            details = error[:77] + "..."
                        else:
                            details = error
                    else:
                        details = "No error details available"
                else:
                    details = "Test completed successfully"

                # Insert into treeview
                app.history_tree.insert(
                    "",
                    "end",
                    values=(
                        date,
                        time,
                        project,
                        mode,
                        status,
                        duration_str,
                        details,
                    ),
                )

            except Exception as e:
                print(f"Error loading summary from {test_dir}: {e}")
                # Insert error row with more context
                try:
                    date_str = test_dir.replace("-checkout", "")
                    date_obj = datetime.strptime(date_str, "%Y%m%d-%H%M%S")
                    date = date_obj.strftime("%Y-%m-%d")
                    time = date_obj.strftime("%H:%M:%S")
                except:
                    date = test_dir[:10]
                    time = test_dir[11:19]

                app.history_tree.insert(
                    "",
                    "end",
                    values=(
                        date,
                        time,
                        "GOOGLE",
                        "headless",
                        "Error",
                        "0s",
                        f"Failed to load summary: {str(e)[:50]}",
                    ),
                )


def clear_all_logs(app) -> None:
    """Delete all files and folders under the logs directory and refresh UI."""
    try:
        # Use the same logs location as the runner/history loader
        logs_dir = os.path.join(os.getcwd(), "logs")
        if os.path.exists(logs_dir):
            for name in os.listdir(logs_dir):
                path = os.path.join(logs_dir, name)
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        try:
                            os.remove(path)
                        except Exception:
                            pass
                except Exception:
                    pass
            app.add_log("🧹 All logs cleared", "info")
        else:
            app.add_log("📁 Logs folder not found", "warning")
    except Exception as e:
        app.add_log(f"❌ Error clearing logs: {e}", "error")
    # Refresh History and Results tabs after clearing
    try:
        app.load_history_data()
        app.refresh_results()
    except Exception:
        pass
