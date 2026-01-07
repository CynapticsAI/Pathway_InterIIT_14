#!/bin/bash

# --- 1. Load connection details from your LOCAL .env file ---
if [ -f .env ]; then
    set -o allexport
    source .env
    set +o allexport
else
    echo "Error: Local .env file not found."
    exit 1
fi

# Sanitize variables (Remove Windows \r characters)
EC2_HOST=$(echo "$EC2_HOST" | tr -d '\r')
KEY_FILE=$(echo "$KEY_FILE" | tr -d '\r')

echo "Deploying to $EC2_HOST..."

# --- 2. Prepare Directories ---
echo "Creating directories on server..."
ssh -i "$KEY_FILE" "$EC2_HOST" "mkdir -p ~/technical_analysis"

# --- 3. Copy Project Files ---
echo "Copying project files..."
scp -i "$KEY_FILE" -r \
  news_producer \
  pnl \
  reader \
  market_breadth \
  sarimax_api \
  finnhub_producer \
  sarimaxConsumer \
  spike_detector \
  k8s \
  docker-compose.yml \
  "$EC2_HOST":~/technical_analysis/

# --- 4. Configure Server ---
ssh -i "$KEY_FILE" "$EC2_HOST" << 'ENDSSH'
    set -e
    cd ~/technical_analysis

    echo "Setting up EC2 Environment..."

    # STEP A: Install Docker
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        sudo apt-get update
        sudo apt-get install -y docker.io docker-compose-v2
        sudo usermod -aG docker $USER
    fi

    # STEP B: Install K3s
    if ! command -v k3s &> /dev/null; then
        echo "Installing K3s..."
        curl -sfL https://get.k3s.io | sh -
    fi

    # STEP C: Configure Kubeconfig
    echo "Configuring Kubernetes access for Docker..."
    mkdir -p /home/ubuntu/.kube

    # Copy config
    sudo cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
    sudo chown ubuntu:ubuntu /home/ubuntu/.kube/config
    sudo chmod 644 /home/ubuntu/.kube/config

    # --- NETWORK & SECURITY FIXES ---
    # 1. Point to Docker Gateway IP (172.17.0.1) instead of localhost
    sed -i 's/127.0.0.1/172.17.0.1/g' /home/ubuntu/.kube/config

    # 2. Disable Certificate Checking
    sed -i '/certificate-authority-data/d' /home/ubuntu/.kube/config
    sed -i '/server:/i \    insecure-skip-tls-verify: true' /home/ubuntu/.kube/config

    # STEP D: Create .env
    cat > .env <<EOF
KUBE_CONFIG_PATH=/home/ubuntu/.kube
KUBECONFIG=/home/ubuntu/.kube/config
EC2_HOST=localhost
FINNHUB_API_KEY=d49072pr01qshn3k09dgd49072pr01qshn3k09e0
EOF
    export KUBECONFIG=/home/ubuntu/.kube/config

    # --- STEP E: Build and Transfer Image to K3s (THE FIX) ---
    echo " Building and Importing K8s Image..."

    # 1. Build the image locally
    sudo docker build -t technical_analysis-sarimax:latest ./sarimaxConsumer

    # 2. Save to disk (Prevents RAM crash)
    echo "Saving image to buffer..."
    sudo rm -f /tmp/sarimax_preload.tar
    sudo docker save -o /tmp/sarimax_preload.tar technical_analysis-sarimax:latest

    # 3. Import to K3s
    echo "Importing into K3s..."
    sudo k3s ctr images import /tmp/sarimax_preload.tar

    # 4. Cleanup
    sudo rm -f /tmp/sarimax_preload.tar
    echo "Image successfully loaded into K3s."


    # STEP F: Restart Services
    echo "Restarting Services..."
    sudo docker compose down
    sudo docker compose build
    sudo docker compose up -d

    echo "Deployment successful!"
    sudo k3s kubectl get nodes

    # Verification Check
    echo "--- K3s Image List (Should include sarimax) ---"
    sudo k3s ctr images list | grep sarimax
ENDSSH