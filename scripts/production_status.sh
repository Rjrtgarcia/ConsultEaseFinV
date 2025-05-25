#!/bin/bash

# ConsultEase Production Status Dashboard
# Real-time system monitoring and status display

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} ${CYAN}$1${NC} ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
}

print_section() {
    echo -e "\n${MAGENTA}▶ $1${NC}"
    echo -e "${MAGENTA}────────────────────────────────────────────────────────────────────────────${NC}"
}

print_status() {
    local status=$1
    local message=$2
    case $status in
        "ONLINE"|"ACTIVE"|"HEALTHY"|"CONNECTED")
            echo -e "  ${GREEN}●${NC} $message"
            ;;
        "OFFLINE"|"INACTIVE"|"UNHEALTHY"|"DISCONNECTED")
            echo -e "  ${RED}●${NC} $message"
            ;;
        "WARNING"|"DEGRADED")
            echo -e "  ${YELLOW}●${NC} $message"
            ;;
        *)
            echo -e "  ${BLUE}●${NC} $message"
            ;;
    esac
}

print_metric() {
    local label=$1
    local value=$2
    local unit=$3
    printf "  %-25s: ${CYAN}%s${NC} %s\n" "$label" "$value" "$unit"
}

# Function to get service status
get_service_status() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        echo "ACTIVE"
    else
        echo "INACTIVE"
    fi
}

# Function to get memory usage
get_memory_usage() {
    free | awk 'NR==2{printf "%.1f", $3*100/$2}'
}

# Function to get CPU usage
get_cpu_usage() {
    top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}'
}

# Function to get disk usage
get_disk_usage() {
    df / | awk 'NR==2 {print $5}' | sed 's/%//'
}

# Function to get uptime
get_uptime() {
    uptime -p | sed 's/up //'
}

# Function to get load average
get_load_average() {
    uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//'
}

# Function to get database status
get_database_status() {
    if sudo -u postgres psql -d consulteasedb -c "SELECT 1;" >/dev/null 2>&1; then
        echo "CONNECTED"
    else
        echo "DISCONNECTED"
    fi
}

# Function to get web interface status
get_web_status() {
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/" 2>/dev/null || echo "000")
    if [ "$response_code" = "200" ]; then
        echo "ONLINE"
    else
        echo "OFFLINE"
    fi
}

# Function to get MQTT status
get_mqtt_status() {
    if pgrep -f "run_mqtt_service" > /dev/null; then
        echo "ACTIVE"
    else
        echo "INACTIVE"
    fi
}

# Function to count connected faculty units
count_faculty_units() {
    # This would need to be customized based on your MQTT broker setup
    mosquitto_sub -h localhost -t "consultease/faculty/+/heartbeat" -W 2 2>/dev/null | wc -l || echo "0"
}

# Function to get recent consultation requests
get_recent_consultations() {
    # This would query your database for recent consultation requests
    sudo -u postgres psql -d consulteasedb -t -c "SELECT COUNT(*) FROM consultations WHERE created_at > NOW() - INTERVAL '1 hour';" 2>/dev/null | xargs || echo "0"
}

# Function to get system temperature (Raspberry Pi specific)
get_system_temperature() {
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        local temp=$(cat /sys/class/thermal/thermal_zone0/temp)
        echo "scale=1; $temp/1000" | bc
    else
        echo "N/A"
    fi
}

# Function to get network interface status
get_network_status() {
    local interface=$1
    if ip link show "$interface" 2>/dev/null | grep -q "state UP"; then
        echo "UP"
    else
        echo "DOWN"
    fi
}

# Function to display real-time dashboard
display_dashboard() {
    clear
    
    print_header "CONSULTEEASE PRODUCTION STATUS DASHBOARD"
    
    echo -e "${BLUE}System Information${NC}"
    print_metric "Hostname" "$(hostname)" ""
    print_metric "IP Address" "$(hostname -I | awk '{print $1}')" ""
    print_metric "Timestamp" "$(date '+%Y-%m-%d %H:%M:%S')" ""
    print_metric "Uptime" "$(get_uptime)" ""
    
    print_section "CORE SERVICES"
    print_status "$(get_service_status nginx)" "Nginx Web Server"
    print_status "$(get_service_status postgresql)" "PostgreSQL Database"
    print_status "$(get_service_status redis-server)" "Redis Cache"
    print_status "$(get_service_status consulteasecentral)" "ConsultEase Central"
    print_status "$(get_service_status consulteasemqtt)" "MQTT Service"
    
    print_section "SYSTEM RESOURCES"
    local cpu_usage=$(get_cpu_usage)
    local mem_usage=$(get_memory_usage)
    local disk_usage=$(get_disk_usage)
    local load_avg=$(get_load_average)
    local temperature=$(get_system_temperature)
    
    print_metric "CPU Usage" "${cpu_usage}%" ""
    print_metric "Memory Usage" "${mem_usage}%" ""
    print_metric "Disk Usage" "${disk_usage}%" ""
    print_metric "Load Average" "$load_avg" ""
    print_metric "Temperature" "${temperature}°C" ""
    
    print_section "NETWORK CONNECTIVITY"
    print_status "$(get_network_status eth0)" "Ethernet Interface (eth0)"
    print_status "$(get_network_status wlan0)" "WiFi Interface (wlan0)"
    print_status "$(get_web_status)" "Web Interface (HTTP)"
    print_status "$(get_database_status)" "Database Connection"
    print_status "$(get_mqtt_status)" "MQTT Service"
    
    print_section "APPLICATION STATUS"
    local web_response_time=$(curl -o /dev/null -s -w "%{time_total}" "http://localhost/" 2>/dev/null || echo "N/A")
    local db_connections=$(sudo -u postgres psql -d consulteasedb -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='consulteasedb';" 2>/dev/null | xargs || echo "N/A")
    local recent_consultations=$(get_recent_consultations)
    local connected_units=$(count_faculty_units)
    
    print_metric "Web Response Time" "${web_response_time}s" ""
    print_metric "Database Connections" "$db_connections" ""
    print_metric "Recent Consultations" "$recent_consultations" "(last hour)"
    print_metric "Connected Faculty Units" "$connected_units" ""
    
    print_section "SECURITY STATUS"
    local firewall_status="INACTIVE"
    if ufw status | grep -q "Status: active"; then
        firewall_status="ACTIVE"
    fi
    
    local fail2ban_status=$(get_service_status fail2ban)
    local ssl_status="DISABLED"
    if [ -f "/etc/letsencrypt/live/$(hostname)/fullchain.pem" ]; then
        ssl_status="ENABLED"
    fi
    
    print_status "$firewall_status" "UFW Firewall"
    print_status "$fail2ban_status" "Fail2Ban Protection"
    print_status "$ssl_status" "SSL/TLS Encryption"
    
    print_section "STORAGE INFORMATION"
    echo -e "  ${CYAN}Filesystem Usage:${NC}"
    df -h | grep -E '^/dev/' | awk '{printf "    %-20s %5s %5s %5s %s\n", $1, $2, $3, $4, $5}'
    
    print_section "RECENT LOG ACTIVITY"
    echo -e "  ${CYAN}Last 5 system events:${NC}"
    journalctl --no-pager -n 5 --output=short | sed 's/^/    /'
    
    print_section "PERFORMANCE METRICS"
    echo -e "  ${CYAN}Top Processes by CPU:${NC}"
    ps aux --sort=-%cpu | head -6 | tail -5 | awk '{printf "    %-12s %5s%% %5s%% %s\n", $1, $3, $4, $11}'
    
    echo -e "\n  ${CYAN}Top Processes by Memory:${NC}"
    ps aux --sort=-%mem | head -6 | tail -5 | awk '{printf "    %-12s %5s%% %5s%% %s\n", $1, $3, $4, $11}'
    
    print_section "QUICK ACTIONS"
    echo -e "  ${YELLOW}Available Commands:${NC}"
    echo -e "    ${GREEN}r${NC} - Refresh dashboard"
    echo -e "    ${GREEN}h${NC} - Run health check"
    echo -e "    ${GREEN}l${NC} - View logs"
    echo -e "    ${GREEN}s${NC} - Service management"
    echo -e "    ${GREEN}q${NC} - Quit"
    
    # Overall system health indicator
    local health_score=0
    
    # Check critical services
    [ "$(get_service_status nginx)" = "ACTIVE" ] && ((health_score++))
    [ "$(get_service_status postgresql)" = "ACTIVE" ] && ((health_score++))
    [ "$(get_service_status consulteasecentral)" = "ACTIVE" ] && ((health_score++))
    [ "$(get_service_status consulteasemqtt)" = "ACTIVE" ] && ((health_score++))
    [ "$(get_web_status)" = "ONLINE" ] && ((health_score++))
    
    # Check resource usage
    [ "${cpu_usage%.*}" -lt 80 ] && ((health_score++))
    [ "${mem_usage%.*}" -lt 80 ] && ((health_score++))
    [ "$disk_usage" -lt 80 ] && ((health_score++))
    
    local health_percentage=$((health_score * 100 / 8))
    
    echo -e "\n${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    if [ "$health_percentage" -ge 90 ]; then
        echo -e "${BLUE}║${NC} ${GREEN}SYSTEM HEALTH: EXCELLENT (${health_percentage}%)${NC} ${BLUE}║${NC}"
    elif [ "$health_percentage" -ge 70 ]; then
        echo -e "${BLUE}║${NC} ${YELLOW}SYSTEM HEALTH: GOOD (${health_percentage}%)${NC} ${BLUE}║${NC}"
    else
        echo -e "${BLUE}║${NC} ${RED}SYSTEM HEALTH: NEEDS ATTENTION (${health_percentage}%)${NC} ${BLUE}║${NC}"
    fi
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
}

# Function to handle user input
handle_input() {
    local choice
    echo -e "\n${CYAN}Enter command (r/h/l/s/q):${NC} "
    read -t 30 -n 1 choice
    
    case $choice in
        'r'|'R')
            return 0  # Refresh
            ;;
        'h'|'H')
            echo -e "\n${YELLOW}Running health check...${NC}"
            ./scripts/health_check.sh
            echo -e "\n${CYAN}Press any key to continue...${NC}"
            read -n 1
            return 0
            ;;
        'l'|'L')
            echo -e "\n${YELLOW}Recent logs:${NC}"
            journalctl --no-pager -n 20 --output=short
            echo -e "\n${CYAN}Press any key to continue...${NC}"
            read -n 1
            return 0
            ;;
        's'|'S')
            echo -e "\n${YELLOW}Service Management:${NC}"
            echo -e "1) Restart ConsultEase Central"
            echo -e "2) Restart MQTT Service"
            echo -e "3) Restart Nginx"
            echo -e "4) Restart All Services"
            echo -e "5) Back to dashboard"
            echo -e "\n${CYAN}Enter choice (1-5):${NC} "
            read -n 1 service_choice
            
            case $service_choice in
                '1') systemctl restart consulteasecentral ;;
                '2') systemctl restart consulteasemqtt ;;
                '3') systemctl restart nginx ;;
                '4') 
                    systemctl restart consulteasecentral
                    systemctl restart consulteasemqtt
                    systemctl restart nginx
                    ;;
                '5') return 0 ;;
            esac
            
            echo -e "\n${GREEN}Service operation completed.${NC}"
            echo -e "\n${CYAN}Press any key to continue...${NC}"
            read -n 1
            return 0
            ;;
        'q'|'Q')
            echo -e "\n${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            return 0  # Auto-refresh on timeout or invalid input
            ;;
    esac
}

# Main loop
main() {
    # Check if running as root for service management
    if [[ $EUID -ne 0 ]]; then
        echo -e "${YELLOW}Note: Running without root privileges. Some features may be limited.${NC}"
        echo -e "${YELLOW}For full functionality, run with: sudo $0${NC}\n"
        sleep 2
    fi
    
    # Install bc if not available
    command -v bc >/dev/null 2>&1 || { 
        echo "Installing bc for calculations..."
        apt-get update && apt-get install -y bc
    }
    
    while true; do
        display_dashboard
        handle_input
        sleep 1  # Brief pause before refresh
    done
}

# Trap Ctrl+C to exit gracefully
trap 'echo -e "\n${GREEN}Goodbye!${NC}"; exit 0' INT

# Run the main function
main "$@"
