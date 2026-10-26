"""
Trigger Jenkins Pipeline on Data Drift
"""
import os
import requests

JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
JENKINS_JOB = os.getenv("JENKINS_JOB", "cinematch")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN", "cinematch_retrain_token")
JENKINS_USER = os.getenv("JENKINS_USER", "")
JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN", "")


def trigger_jenkins_pipeline():
    """Trigger the Jenkins pipeline build immediately via Remote Token or API Token."""
    # Attempt 1: Remote Build Trigger with Token
    url = f"{JENKINS_URL}/job/{JENKINS_JOB}/build?token={JENKINS_TOKEN}"
    try:
        resp = requests.post(url, timeout=5)
        if resp.status_code in [200, 201]:
            print(f"✅ Successfully triggered Jenkins job '{JENKINS_JOB}' via build token!")
            return True
    except Exception as e:
        print(f"[NOTE] Remote token attempt: {e}")

    # Attempt 2: User API Token if provided
    if JENKINS_USER and JENKINS_API_TOKEN:
        try:
            crumb_url = f"{JENKINS_URL}/crumbIssuer/api/json"
            crumb_resp = requests.get(crumb_url, auth=(JENKINS_USER, JENKINS_API_TOKEN), timeout=5)
            headers = {}
            if crumb_resp.status_code == 200:
                crumb_data = crumb_resp.json()
                headers[crumb_data["crumbRequestField"]] = crumb_data["crumb"]

            build_url = f"{JENKINS_URL}/job/{JENKINS_JOB}/build"
            resp = requests.post(build_url, auth=(JENKINS_USER, JENKINS_API_TOKEN), headers=headers, timeout=5)
            if resp.status_code in [200, 201]:
                print(f"✅ Successfully triggered Jenkins job '{JENKINS_JOB}' via user API token!")
                return True
        except Exception as e:
            print(f"[NOTE] API token attempt: {e}")

    print("⚠️ Jenkins trigger requires Remote Token or API Token configured in Jenkins.")
    return False


if __name__ == "__main__":
    trigger_jenkins_pipeline()
