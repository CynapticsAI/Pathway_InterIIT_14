#!/bin/bash
# =============================================================================
# MASTER DEPLOYMENT SCRIPT
# =============================================================================
# Deploys the trading system across 4 AWS EC2 instances:
#   - Server 1: Kafka Cluster + All Shared Producers
#   - Server 2: AWS Macro Deployment
#   - Server 3: Chronos Deployment
#   - Server 4: Portfolio Deployment
#
# Usage:
#   ./deploy-all.sh servers.env
#   ./deploy-all.sh                 # Uses servers.env by default
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# ALL_DEPLOYMENTS directory (parent of scripts/aws-deploy)
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# =============================================================================
# LOAD CONFIGURATION FROM ENV FILE
# =============================================================================

ENV_FILE="${1:-$SCRIPT_DIR/servers.env}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}ERROR: Configuration file not found: $ENV_FILE${NC}"
    echo -e "${YELLOW}Usage: ./deploy-all.sh servers.env${NC}"
    echo -e ""
    echo -e "Create servers.env from template:"
    echo -e "  cp servers.env.example servers.env"
    echo -e "  nano servers.env"
    exit 1
fi

echo -e "${BLUE}Loading configuration from: $ENV_FILE${NC}"
source "$ENV_FILE"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_server() {
    local server=$1
    local name=$2
    if [ -z "$server" ]; then
        echo -e "${RED}ERROR: $name server IP not set in $ENV_FILE${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ $name: $server${NC}"
}

run_remote() {
    local server=$1
    local command=$2
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$server" "$command"
}

copy_to_remote() {
    local server=$1
    local source=$2
    local dest=$3
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$source" "$SSH_USER@$server:$dest"
}

copy_dir_to_remote() {
    local server=$1
    local source=$2
    local dest=$3
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r "$source" "$SSH_USER@$server:$dest"
}

create_env_file() {
    local server=$1
    echo "Creating .env file on $server..."
    
    # Create temp file locally
    local temp_env=$(mktemp)
    cat > "$temp_env" << EOF
# API Keys
FINNHUB_API_KEY=$FINNHUB_API_KEY
FRED_API_KEY=$FRED_API_KEY
FINVIZ_API_KEY=$FINVIZ_API_KEY

# Producer Settings
FINNHUB_SYMBOLS=$FINNHUB_SYMBOLS
NEWS_TICKERS=$NEWS_TICKERS
SENTIMENT_TICKERS=$SENTIMENT_TICKERS

# Kafka Settings
KAFKA_BOOTSTRAP_SERVERS=kafka:9090
EOF
    
    # Copy to remote server
    copy_to_remote "$server" "$temp_env" "~/trading-system-main/ALL_DEPLOYMENTS/.env"
    rm -f "$temp_env"
}

upload_project() {
    local server=$1
    echo "Uploading project files to $server..."
    
    # Remove old directory and create new one
    run_remote "$server" "rm -rf ~/trading-system-main && mkdir -p ~/trading-system-main"
    
    # Copy ALL_DEPLOYMENTS directory
    copy_dir_to_remote "$server" "$PROJECT_DIR" "~/trading-system-main/"
    
    echo -e "${GREEN}✓ Project files uploaded${NC}"
}

# Track which servers have been set up (for single-server mode)
# declare -A SETUP_DONE

# =============================================================================
# MAIN
# =============================================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   AWS MULTI-SERVER DEPLOYMENT${NC}"
echo -e "${BLUE}========================================${NC}"

# Check configuration
print_header "Checking Configuration"

if [ ! -f "$SSH_KEY" ]; then
    # Expand ~ in path
    SSH_KEY="${SSH_KEY/#\~/$HOME}"
    if [ ! -f "$SSH_KEY" ]; then
        echo -e "${RED}ERROR: SSH key not found at $SSH_KEY${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ SSH Key: $SSH_KEY${NC}"

check_server "$KAFKA_SERVER" "Kafka"
check_server "$MACRO_SERVER" "Macro"
check_server "$CHRONOS_SERVER" "Chronos"
check_server "$PORTFOLIO_SERVER" "Portfolio"

# Check API keys
if [ -z "$FINNHUB_API_KEY" ] || [ "$FINNHUB_API_KEY" = "your_finnhub_api_key" ]; then
    echo -e "${RED}ERROR: FINNHUB_API_KEY not configured in $ENV_FILE${NC}"
    exit 1
fi
echo -e "${GREEN}✓ API Keys configured${NC}"

# Check project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}ERROR: Project directory not found: $PROJECT_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Project directory: $PROJECT_DIR${NC}"

# Detect single-server mode (all IPs are the same)
SINGLE_SERVER_MODE=false
if [ "$KAFKA_SERVER" = "$MACRO_SERVER" ] && \
   [ "$KAFKA_SERVER" = "$CHRONOS_SERVER" ] && \
   [ "$KAFKA_SERVER" = "$PORTFOLIO_SERVER" ]; then
    SINGLE_SERVER_MODE=true
fi

echo -e "\n${YELLOW}Configuration Summary:${NC}"
echo -e "  Kafka Server:     $KAFKA_SERVER"
echo -e "  Macro Server:     $MACRO_SERVER"
echo -e "  Chronos Server:   $CHRONOS_SERVER"
echo -e "  Portfolio Server: $PORTFOLIO_SERVER"
echo -e "  Local Project:    $PROJECT_DIR"

if [ "$SINGLE_SERVER_MODE" = true ]; then
    echo -e "\n${YELLOW}⚠️  SINGLE SERVER MODE DETECTED${NC}"
    echo -e "All services will be deployed to: $KAFKA_SERVER"
    echo -e "\n${YELLOW}Continue with single-server deployment? (y/N)${NC}"
else
    echo -e "\n${YELLOW}This will deploy to 4 servers. Continue? (y/N)${NC}"
fi

read -r response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# =============================================================================
# DEPLOY KAFKA SERVER (Server 1)
# =============================================================================

print_header "Deploying Kafka Server ($KAFKA_SERVER)"

echo "Installing Docker..."
run_remote "$KAFKA_SERVER" "
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker.io docker-compose git
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker \$USER
" || true

echo "Uploading project files..."
upload_project "$KAFKA_SERVER"
SETUP_DONE["$KAFKA_SERVER"]=1

echo "Creating environment file..."
create_env_file "$KAFKA_SERVER"

echo "Copying Kafka deployment script..."
copy_to_remote "$KAFKA_SERVER" "$SCRIPT_DIR/server-kafka.sh" "~/trading-system-main/deploy-kafka.sh"

echo "Starting Kafka cluster..."
run_remote "$KAFKA_SERVER" "
    chmod +x ~/trading-system-main/deploy-kafka.sh
    cd ~/trading-system-main && ./deploy-kafka.sh
"

KAFKA_INTERNAL_IP=$(run_remote "$KAFKA_SERVER" "hostname -I | awk '{print \$1}'")
echo -e "${GREEN}✓ Kafka deployed at internal IP: $KAFKA_INTERNAL_IP${NC}"

# =============================================================================
# DEPLOY MACRO SERVER (Server 2)
# =============================================================================

print_header "Deploying Macro Server ($MACRO_SERVER)"

if [ -z "${SETUP_DONE[$MACRO_SERVER]}" ]; then
    echo "Installing Docker..."
    run_remote "$MACRO_SERVER" "
        sudo apt-get update -qq
        sudo apt-get install -y -qq docker.io docker-compose git
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker \$USER
    " || true

    echo "Uploading project files..."
    upload_project "$MACRO_SERVER"
    SETUP_DONE["$MACRO_SERVER"]=1
else
    echo "Server already set up, skipping upload..."
fi

echo "Copying deployment script..."
copy_to_remote "$MACRO_SERVER" "$SCRIPT_DIR/server-macro.sh" "~/trading-system-main/deploy.sh"

echo "Starting Macro services..."
run_remote "$MACRO_SERVER" "
    chmod +x ~/trading-system-main/deploy.sh
    cd ~/trading-system-main && KAFKA_SERVER=$KAFKA_INTERNAL_IP ./deploy.sh
"

echo -e "${GREEN}✓ Macro API deployed${NC}"

# =============================================================================
# DEPLOY CHRONOS SERVER (Server 3)
# =============================================================================

print_header "Deploying Chronos Server ($CHRONOS_SERVER)"

if [ -z "${SETUP_DONE[$CHRONOS_SERVER]}" ]; then
    echo "Installing Docker..."
    run_remote "$CHRONOS_SERVER" "
        sudo apt-get update -qq
        sudo apt-get install -y -qq docker.io docker-compose git
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker \$USER
    " || true

    echo "Uploading project files..."
    upload_project "$CHRONOS_SERVER"
    SETUP_DONE["$CHRONOS_SERVER"]=1
else
    echo "Server already set up, skipping upload..."
fi

echo "Copying deployment script..."
copy_to_remote "$CHRONOS_SERVER" "$SCRIPT_DIR/server-chronos.sh" "~/trading-system-main/deploy.sh"

echo "Starting Chronos services..."
run_remote "$CHRONOS_SERVER" "
    chmod +x ~/trading-system-main/deploy.sh
    cd ~/trading-system-main && KAFKA_SERVER=$KAFKA_INTERNAL_IP ./deploy.sh
"

echo -e "${GREEN}✓ Chronos API deployed${NC}"

# =============================================================================
# DEPLOY PORTFOLIO SERVER (Server 4)
# =============================================================================

print_header "Deploying Portfolio Server ($PORTFOLIO_SERVER)"

if [ -z "${SETUP_DONE[$PORTFOLIO_SERVER]}" ]; then
    echo "Installing Docker..."
    run_remote "$PORTFOLIO_SERVER" "
        sudo apt-get update -qq
        sudo apt-get install -y -qq docker.io docker-compose git
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker \$USER
    " || true

    echo "Uploading project files..."
    upload_project "$PORTFOLIO_SERVER"
    SETUP_DONE["$PORTFOLIO_SERVER"]=1
else
    echo "Server already set up, skipping upload..."
fi

echo "Copying deployment script..."
copy_to_remote "$PORTFOLIO_SERVER" "$SCRIPT_DIR/server-portfolio.sh" "~/trading-system-main/deploy.sh"

echo "Starting Portfolio services..."
run_remote "$PORTFOLIO_SERVER" "
    chmod +x ~/trading-system-main/deploy.sh
    cd ~/trading-system-main && KAFKA_SERVER=$KAFKA_INTERNAL_IP MACRO_SERVER=$MACRO_SERVER ./deploy.sh
"

echo -e "${GREEN}✓ Portfolio API deployed${NC}"

# =============================================================================
# SUMMARY
# =============================================================================

print_header "DEPLOYMENT COMPLETE"

echo -e "
${GREEN}All services deployed successfully!${NC}

${BLUE}Service URLs:${NC}
┌──────────────────┬─────────────────────────────────────────┐
│ Service          │ URL                                     │
├──────────────────┼─────────────────────────────────────────┤
│ Kafka UI         │ http://$KAFKA_SERVER:8090               │
│ Macro API        │ http://$MACRO_SERVER:8000               │
│ Chronos API      │ http://$CHRONOS_SERVER:9000             │
│ Portfolio API    │ http://$PORTFOLIO_SERVER:8080           │
└──────────────────┴─────────────────────────────────────────┘

${BLUE}Kafka Internal:${NC} $KAFKA_INTERNAL_IP:9090

${BLUE}Test commands:${NC}
  curl http://$MACRO_SERVER:8000/predict/Energy
  curl http://$CHRONOS_SERVER:9000/
  curl http://$PORTFOLIO_SERVER:8080/

${BLUE}Configuration used:${NC} $ENV_FILE
"
