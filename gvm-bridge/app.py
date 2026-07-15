from flask import Flask, jsonify
from gvm.connections import UnixSocketConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeCheckCommandTransform
from contextlib import contextmanager
from lxml import etree
import os

app = Flask(__name__)

SOCKET_PATH = "/run/gvmd/gvmd.sock"
GVM_USERNAME = os.environ.get("GVM_USERNAME", "admin")
GVM_PASSWORD = os.environ.get("GVM_PASSWORD")

if not GVM_PASSWORD:
    raise RuntimeError(
        "GVM_PASSWORD environment variable is not set. "
        "Start the container with -e GVM_PASSWORD=your_password"
    )

@contextmanager
def get_gmp():
    connection = UnixSocketConnection(path=SOCKET_PATH)
    with Gmp(connection=connection, transform=EtreeCheckCommandTransform()) as gmp:
        gmp.authenticate(GVM_USERNAME, GVM_PASSWORD)
        yield gmp

@app.route("/tasks", methods=["GET"])
def list_tasks():
    with get_gmp() as gmp:
        response = gmp.get_tasks()
        tasks = []
        for task in response.findall(".//task"):
            tasks.append({
                "id": task.get("id"),
                "name": task.find("name").text
            })
        return jsonify({"tasks": tasks})

@app.route("/start_scan/<task_id>", methods=["POST"])
def start_scan(task_id):
    with get_gmp() as gmp:
        try:
            response = gmp.start_task(task_id)
            report_id_elem = response.find("report_id")
            if report_id_elem is None:
                return jsonify({"error": "Task could not be started, possibly already running"}), 409
            report_id = report_id_elem.text
        except Exception as e:
            return jsonify({"error": str(e)}), 409
    return jsonify({"status": "started", "task_id": task_id, "report_id": report_id})

@app.route("/report/<task_id>", methods=["GET"])
def report(task_id):
    with get_gmp() as gmp:
        task = gmp.get_task(task_id)
        last_report = task.find(".//last_report/report")
        if last_report is None:
            return jsonify({"error": "No completed scan report exists for this task yet."}), 404
        report_id = last_report.get("id")
        rep = gmp.get_report(
            report_id,
            report_format_id="c1645568-627a-11e3-a660-406186ea4fc5"
        )
        return jsonify({"report_xml": etree.tostring(rep, pretty_print=True).decode()})

@app.route("/report_status/<report_id>", methods=["GET"])
def report_status(report_id):
    with get_gmp() as gmp:
        response = gmp.get_report(report_id, details=False)

        status_elem = response.find(".//scan_run_status")
        status = status_elem.text if status_elem is not None else None

        progress_elem = response.find(".//task/progress")
        progress = progress_elem.text if progress_elem is not None else None

        return jsonify({"scan_run_status": status, "progress": progress})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)