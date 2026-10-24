"""
CineMatch AI - Automatic Grafana Alert Provisioner
Configures the contact point and alert rule via Grafana REST API directly,
bypassing the buggy Grafana 10.3 UI.
"""
import requests
import json
import sys

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GRAFANA_URL = "http://localhost:3001"
AUTH = ("admin", "admin")
HEADERS = {"Content-Type": "application/json"}

def setup_grafana_alerting():
    print("=" * 60)
    print(" CineMatch AI - Provisioning Grafana Alert via REST API")
    print("=" * 60)

    # 1. Update Contact Point to point to backend:8000/api/model/retrain
    cp_resp = requests.get(f"{GRAFANA_URL}/api/v1/provisioning/contact-points", auth=AUTH)
    cp_list = cp_resp.json()
    retrain_cp_uid = None
    for cp in cp_list:
        if cp.get("name") == "Jenkins-Retrain-Webhook" or "retrain" in cp.get("name", "").lower():
            retrain_cp_uid = cp["uid"]
            break

    cp_payload = {
        "name": "Jenkins-Retrain-Webhook",
        "type": "webhook",
        "settings": {
            "httpMethod": "POST",
            "url": "http://backend:8000/api/model/retrain",
        },
        "disableResolveMessage": False,
    }

    if retrain_cp_uid:
        print(f"🔄 Updating existing contact point {retrain_cp_uid}...")
        res = requests.put(
            f"{GRAFANA_URL}/api/v1/provisioning/contact-points/{retrain_cp_uid}",
            auth=AUTH,
            headers=HEADERS,
            data=json.dumps(cp_payload),
        )
        print(f"   Status: {res.status_code}")
    else:
        print("➕ Creating contact point 'Jenkins-Retrain-Webhook'...")
        res = requests.post(
            f"{GRAFANA_URL}/api/v1/provisioning/contact-points",
            auth=AUTH,
            headers=HEADERS,
            data=json.dumps(cp_payload),
        )
        print(f"   Status: {res.status_code}")
        retrain_cp_uid = res.json().get("uid")

    # 2. Get Folder UID
    folder_resp = requests.get(f"{GRAFANA_URL}/api/folders", auth=AUTH)
    folders = folder_resp.json()
    folder_uid = folders[0]["uid"] if folders else None
    if not folder_uid:
        f_create = requests.post(
            f"{GRAFANA_URL}/api/folders",
            auth=AUTH,
            headers=HEADERS,
            data=json.dumps({"title": "CineMatch AI"}),
        )
        folder_uid = f_create.json().get("uid", "c6cd88f6-c320-431e-9c46-5038740a5bea")

    print(f"📁 Using Folder UID: {folder_uid}")

    # 3. Create or Update Alert Rule
    alert_rule_payload = {
        "title": "Data Drift Retrain Trigger",
        "ruleGroup": "drift-eval",
        "folderUID": folder_uid,
        "for": "10s",
        "condition": "B",
        "noDataState": "OK",
        "execErrState": "OK",
        "data": [
            {
                "refId": "A",
                "relativeTimeRange": {"from": 600, "to": 0},
                "datasourceUid": "prometheus",
                "model": {
                    "editorMode": "code",
                    "expr": "max(cinematch_data_drift_detected)",
                    "instant": True,
                    "intervalMs": 1000,
                    "maxDataPoints": 43200,
                    "refId": "A",
                },
            },
            {
                "refId": "B",
                "datasourceUid": "__expr__",
                "model": {
                    "type": "math",
                    "expression": "$A > 0",
                    "refId": "B",
                },
            },
        ],
        "annotations": {
            "summary": "Model Data Drift Detected in Production",
            "description": "Production ratings significantly differ from training baseline. Automated retraining pipeline triggered.",
        },
        "labels": {
            "alertname": "DataDriftDetected",
            "severity": "critical",
        },
    }

    print("🚀 Registering Alert Rule in Grafana...")
    # Check if rule exists
    existing_rules = requests.get(f"{GRAFANA_URL}/api/v1/provisioning/alert-rules", auth=AUTH).json()
    rule_uid = None
    for r in existing_rules:
        if r.get("title") == "Data Drift Retrain Trigger":
            rule_uid = r["uid"]
            break

    if rule_uid:
        print(f"🔄 Updating existing alert rule {rule_uid}...")
        rule_res = requests.put(
            f"{GRAFANA_URL}/api/v1/provisioning/alert-rules/{rule_uid}",
            auth=AUTH,
            headers=HEADERS,
            data=json.dumps(alert_rule_payload),
        )
    else:
        print("➕ Creating alert rule...")
        rule_res = requests.post(
            f"{GRAFANA_URL}/api/v1/provisioning/alert-rules",
            auth=AUTH,
            headers=HEADERS,
            data=json.dumps(alert_rule_payload),
        )

    print(f"   Alert Rule Response: {rule_res.status_code}")
    if rule_res.status_code in [200, 201]:
        print("✅ Alert rule saved successfully!")
    else:
        print(f"   Response Body: {rule_res.text}")

    # 4. Configure Notification Policy so this alert routes to Jenkins-Retrain-Webhook.
    print("🔀 Updating Notification Policy root route...")
    policy_resp = requests.get(f"{GRAFANA_URL}/api/v1/provisioning/policies", auth=AUTH)
    if policy_resp.status_code == 200:
        policy = policy_resp.json()
        policy["receiver"] = "Jenkins-Retrain-Webhook."
        pol_res = requests.put(
            f"{GRAFANA_URL}/api/v1/provisioning/policies",
            auth=AUTH,
            headers=HEADERS,
            data=json.dumps(policy),
        )
        print(f"🎯 Default notification policy set to 'Jenkins-Retrain-Webhook.': {pol_res.status_code}")

    print("\n🎉 Done! The alert rule and webhook are fully provisioned and active.")

if __name__ == "__main__":
    setup_grafana_alerting()
