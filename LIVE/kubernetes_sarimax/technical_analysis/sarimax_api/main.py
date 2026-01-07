import json
import os
import subprocess
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

import yaml
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

app = FastAPI(
    title="SARIMAX Forecasting API",
    description="API wrapper for Kubernetes-based SARIMAX stock forecasting",
    version="1.0.7"
)


class StockListRequest(BaseModel):
    stocks: List[str] = Field(..., description="List of stock tickers (e.g., ['AAPL', 'GOOGL', 'MSFT'])")
    forecast_horizon: Optional[int] = Field(7, description="Number of days to forecast")
    run_immediately: Optional[bool] = Field(True, description="Run forecast immediately or wait for cron")


class ForecastResponse(BaseModel):
    job_name: str
    status: str
    pod_name: Optional[str] = None
    message: str
    stocks: List[str]
    timestamp: str


class PodStatus(BaseModel):
    pod_name: str
    status: str
    phase: str
    logs: Optional[str] = None


# --- PATH CONFIGURATION ---
PROJECT_ROOT = Path("/technical_analysis")
FINNHUB_PRODUCER_PATH = PROJECT_ROOT / "finnhub_producer"
FINNHUB_ENV_PATH = FINNHUB_PRODUCER_PATH / ".env"
SARIMAX_PATH = PROJECT_ROOT / "sarimaxConsumer"
K8S_PATH = PROJECT_ROOT / "k8s"
K8S_STOCK_LIST_PATH = K8S_PATH / "stock-list.yaml"
K8S_CRONJOB_PATH = K8S_PATH / "market-cronjob.yaml"

# --- KUBERNETES CONFIGURATION ---
if "KUBECONFIG" not in os.environ:
    if os.path.exists("/root/.kube/config"):
        os.environ["KUBECONFIG"] = "/root/.kube/config"
        print("✓ Set KUBECONFIG to /root/.kube/config")
    else:
        print("! Warning: /root/.kube/config not found. Kubectl may fail.")


def run_command(cmd: str, shell: bool = True, cwd: Optional[str] = None) -> tuple[str, str, int]:
    """Execute shell command and return output"""
    try:
        if cwd is None:
            cwd = str(PROJECT_ROOT)

        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=cwd
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1


def update_finnhub_env(stocks: List[str]) -> bool:
    """Update Finnhub producer .env file with new stock list"""
    try:
        env_dict = {}
        if FINNHUB_ENV_PATH.exists():
            with open(FINNHUB_ENV_PATH, 'r') as f:
                for line in f:
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        env_dict[k] = v

        if "FINNHUB_API_KEY" not in env_dict:
            env_dict["FINNHUB_API_KEY"] = os.getenv("FINNHUB_API_KEY", "")
        if "KAFKA_BOOTSTRAP_SERVERS" not in env_dict:
            env_dict["KAFKA_BOOTSTRAP_SERVERS"] = "13.50.238.243:9090"
        if "KAFKA_TOPIC" not in env_dict:
            env_dict["KAFKA_TOPIC"] = "stock_data"

        env_dict["STOCK_LIST"] = ",".join(stocks)

        with open(FINNHUB_ENV_PATH, 'w') as f:
            for k, v in env_dict.items():
                f.write(f"{k}={v}\n")

        print(f"✓ Updated {FINNHUB_ENV_PATH} with stocks: {env_dict['STOCK_LIST']}")
        return True
    except Exception as e:
        print(f"✗ Error updating Finnhub .env: {e}")
        return False


def update_k8s_stock_list(stocks: List[str]) -> bool:
    """Update Kubernetes ConfigMap using Atomic File Swap (No Deletion)"""
    try:
        K8S_PATH.mkdir(parents=True, exist_ok=True)

        class LiteralStr(str):
            pass

        def literal_presenter(dumper, data):
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

        yaml.add_representer(LiteralStr, literal_presenter)

        stock_list_yaml = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "stock-tickers-config",
                "namespace": "default"
            },
            "data": {
                "STOCK_LIST": json.dumps(stocks),
                "stocks.txt": LiteralStr("\n".join(stocks))
            }
        }

        # 1. CREATE TEMP CONFIGMAP FILE
        # We write to a temporary file first to avoid partial reads
        temp_path = K8S_STOCK_LIST_PATH.with_suffix('.tmp')

        with open(temp_path, 'w') as f:
            yaml.dump(stock_list_yaml, f, default_flow_style=False)

        # 2. MOVE (MV) TO ORIGINAL CONFIG
        # atomic replace ensures the file is never empty/corrupt
        os.replace(temp_path, K8S_STOCK_LIST_PATH)
        print(f"✓ Atomic write to {K8S_STOCK_LIST_PATH} complete")

        # 3. APPLY WITHOUT DELETING
        # Kubernetes handles the update in-place, avoiding 'MountVolume' errors
        stdout, stderr, code = run_command(f"kubectl apply -f {K8S_STOCK_LIST_PATH}")
        if code != 0:
            print(f"Error applying ConfigMap: {stderr}")
            return False

        print(f"✓ ConfigMap updated in Kubernetes")
        return True
    except Exception as e:
        print(f"✗ Error updating K8s stock list: {e}")
        return False


def rebuild_docker_services() -> tuple[bool, str]:
    """Rebuild specific Docker services that depend on stock list"""
    try:
        project_root = str(PROJECT_ROOT)
        print("Stopping affected services...")
        services = ["finnhub_producer", "spike_detector", "market_breadth"]

        for service in services:
            run_command(f"docker compose rm -s -f {service}", cwd=project_root)

        print("⏳ Rebuilding finnhub_producer...")
        stdout, stderr, code = run_command("docker compose build finnhub_producer", cwd=project_root)
        if code != 0:
            return False, f"Failed to rebuild finnhub_producer: {stderr}"

        print("⏳ Starting services...")
        stdout, stderr, code = run_command(f"docker compose up -d {' '.join(services)}", cwd=project_root)
        if code != 0:
            return False, f"Failed to start services: {stderr}"

        print("✓ Docker services rebuilt successfully")
        return True, "Docker services rebuilt successfully"
    except Exception as e:
        return False, str(e)


def build_sarimax_image() -> tuple[bool, str]:
    """Build SARIMAX Docker image AND safely import into K3s via File Buffer"""
    try:
        IMAGE_NAME = "docker.io/library/technical_analysis-sarimax:latest"

        print(f"Building SARIMAX image ({IMAGE_NAME})...")

        if not SARIMAX_PATH.exists():
            return False, f"Path not found: {SARIMAX_PATH}"

        cmd = f"docker build -t {IMAGE_NAME} {SARIMAX_PATH}"
        stdout, stderr, code = run_command(cmd)

        if code != 0:
            return False, f"Failed to build SARIMAX image: {stderr}"

        print("✓ Image built in Docker. Saving to shared disk...")

        container_tar_path = "/technical_analysis/temp_sarimax.tar"
        host_tar_path = "/home/ubuntu/technical_analysis/temp_sarimax.tar"

        try:
            if os.path.exists(container_tar_path):
                os.remove(container_tar_path)

            save_cmd = f"docker save -o {container_tar_path} {IMAGE_NAME}"
            stdout, stderr, code = run_command(save_cmd)
            if code != 0:
                return False, f"Failed to save image to disk: {stderr}"

            print("✓ Image saved to disk. Importing to K3s...")

            importer_cmd = [
                "docker", "run", "--rm", "--privileged", "--pid=host",
                "alpine", "nsenter", "-t", "1", "-m", "-u", "-n", "-i", "--",
                "/usr/local/bin/k3s", "ctr", "images", "import", host_tar_path
            ]

            result = subprocess.run(importer_cmd, capture_output=True, text=True)

            if os.path.exists(container_tar_path):
                os.remove(container_tar_path)

            if result.returncode != 0:
                print(f"Import Error: {result.stderr}")
                return False, f"Failed to import to K3s: {result.stderr}"

            print("✓ SARIMAX image imported to K3s successfully")
            return True, "SARIMAX image built and imported"

        except Exception as transfer_error:
            if os.path.exists(container_tar_path):
                os.remove(container_tar_path)
            return False, f"Image transfer failed: {str(transfer_error)}"

    except Exception as e:
        return False, str(e)


def deploy_k8s_resources() -> tuple[bool, str]:
    """Deploy Kubernetes resources"""
    try:
        print("Applying Kubernetes resources...")

        # We already applied the Stock List in update_k8s_stock_list
        if K8S_CRONJOB_PATH.exists():
            stdout, stderr, code = run_command(f"kubectl apply -f {K8S_CRONJOB_PATH} --validate=false")
            if code != 0:
                return False, f"Failed to apply market-cronjob.yaml: {stderr}"
            print("✓ Applied market-cronjob")

        return True, "Kubernetes resources deployed successfully"
    except Exception as e:
        return False, str(e)


def trigger_manual_job() -> tuple[bool, str, Optional[str]]:
    """Trigger manual Kubernetes job and return pod name"""
    try:
        print(f"Triggering manual forecast job...")

        # 1. Cleanup old jobs/pods
        run_command("kubectl delete jobs --all --ignore-not-found=true")
        run_command("kubectl delete pods --all --ignore-not-found=true --force --grace-period=0")
        time.sleep(3)

        # 2. Create the job (Standard, no dynamic patching)
        stdout, stderr, code = run_command(
            "kubectl create job --from=cronjob/daily-stock-forecast manual-test-run"
        )
        if code != 0:
            return False, f"Failed to create job: {stderr}", None

        print("Job created, waiting for pod...")

        pod_name = ""
        for _ in range(10):
            time.sleep(3)
            stdout, stderr, code = run_command(
                "kubectl get pods --selector=job-name=manual-test-run --output=jsonpath='{.items[0].metadata.name}'"
            )
            if code == 0 and stdout:
                pod_name = stdout.strip().strip("'")
                if pod_name:
                    break

        if not pod_name:
            return True, "Job created but pod name lookup timed out.", "pending-pod-lookup"

        print(f"Pod created: {pod_name}")
        return True, "Job triggered successfully", pod_name
    except Exception as e:
        return False, str(e), None


# ... [API Endpoints] ...

@app.get("/")
async def root():
    return {"service": "SARIMAX Forecasting API", "status": "running"}


@app.post("/forecast", response_model=ForecastResponse)
async def run_forecast(request: StockListRequest, background_tasks: BackgroundTasks):
    timestamp = datetime.now().isoformat()
    try:
        print(f"\n{'=' * 60}\nStarting forecast for: {', '.join(request.stocks)}\n{'=' * 60}")

        if not update_finnhub_env(request.stocks): raise HTTPException(500, "Failed to update Finnhub .env")
        if not update_k8s_stock_list(request.stocks): raise HTTPException(500, "Failed to update K8s stock list")

        success, msg = rebuild_docker_services()
        if not success: raise HTTPException(500, msg)

        # Build and Auto-Import to K3s (Ensures new code is used)
        success, msg = build_sarimax_image()
        if not success: raise HTTPException(500, msg)

        success, msg = deploy_k8s_resources()
        if not success: raise HTTPException(500, msg)

        pod_name = None
        status = "scheduled"
        response_msg = f"Configured {len(request.stocks)} stocks"

        if request.run_immediately:
            success, msg, pod_name = trigger_manual_job()
            if success:
                status = "running"
                response_msg = f"Forecast triggered for {len(request.stocks)} stocks"
            else:
                response_msg = f"Configured but trigger failed: {msg}"

        print(f"\n{'=' * 60}\nComplete!\n{'=' * 60}")
        return ForecastResponse(
            job_name="manual-test-run" if request.run_immediately else "daily-stock-forecast",
            status=status, pod_name=pod_name, message=response_msg, stocks=request.stocks, timestamp=timestamp
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


# [Remaining GET endpoints same as before]
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8888)