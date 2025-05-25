#!/bin/bash

# ConsultEase System Health Check Script
# Comprehensive system validation and monitoring

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Function to print colored output
print_pass() {
    echo -e "${GREEN}✅ PASS${NC} $1"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_fail() {
    echo -e "${RED}❌ FAIL${NC} $1"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARN${NC} $1"
    ((WARNING_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_info() {
    echo -e "${BLUE}ℹ️  INFO${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to check if a service is running
check_service() {
    local service_name=$1
    if systemctl is-active --quiet "$service_name"; then
        print_pass "Service $service_name is running"
    else
        print_fail "Service $service_name is not running"
    fi
}

# Function to check if a port is listening
check_port() {
    local port=$1
    local description=$2
    if netstat -tuln | grep -q ":$port "; then
        print_pass "$description (port $port) is listening"
    else
        print_fail "$description (port $port) is not listening"
    fi
}

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local description=$2
    local expected_code=${3:-200}
    
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response_code" = "$expected_code" ]; then
        print_pass "$description responds with HTTP $response_code"
    else
        print_fail "$description responds with HTTP $response_code (expected $expected_code)"
    fi
}

# Function to check database connectivity
check_database() {
    local db_name=$1
    local db_user=$2
    
    if sudo -u postgres psql -d "$db_name" -U "$db_user" -c "SELECT 1;" >/dev/null 2>&1; then
        print_pass "Database $db_name is accessible"
    else
        print_fail "Database $db_name is not accessible"
    fi
}

# Function to check disk space
check_disk_space() {
    local mount_point=$1
    local threshold=${2:-80}
    
    local usage=$(df "$mount_point" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -lt "$threshold" ]; then
        print_pass "Disk usage for $mount_point is ${usage}% (< ${threshold}%)"
    elif [ "$usage" -lt 90 ]; then
        print_warning "Disk usage for $mount_point is ${usage}% (>= ${threshold}%)"
    else
        print_fail "Disk usage for $mount_point is ${usage}% (critical)"
    fi
}

# Function to check memory usage
check_memory() {
    local threshold=${1:-80}
    
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$mem_usage" -lt "$threshold" ]; then
        print_pass "Memory usage is ${mem_usage}% (< ${threshold}%)"
    elif [ "$mem_usage" -lt 90 ]; then
        print_warning "Memory usage is ${mem_usage}% (>= ${threshold}%)"
    else
        print_fail "Memory usage is ${mem_usage}% (critical)"
    fi
}

# Function to check CPU load
check_cpu_load() {
    local threshold=${1:-2.0}
    
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    
    if (( $(echo "$load_avg < $threshold" | bc -l) )); then
        print_pass "CPU load average is $load_avg (< $threshold)"
    elif (( $(echo "$load_avg < 4.0" | bc -l) )); then
        print_warning "CPU load average is $load_avg (>= $threshold)"
    else
        print_fail "CPU load average is $load_avg (critical)"
    fi
}

# Function to check file permissions
check_file_permissions() {
    local file_path=$1
    local expected_owner=$2
    local expected_perms=$3
    
    if [ -e "$file_path" ]; then
        local actual_owner=$(stat -c "%U:%G" "$file_path")
        local actual_perms=$(stat -c "%a" "$file_path")
        
        if [ "$actual_owner" = "$expected_owner" ] && [ "$actual_perms" = "$expected_perms" ]; then
            print_pass "File $file_path has correct permissions ($actual_owner $actual_perms)"
        else
            print_fail "File $file_path has incorrect permissions ($actual_owner $actual_perms, expected $expected_owner $expected_perms)"
        fi
    else
        print_fail "File $file_path does not exist"
    fi
}

# Function to check log files for errors
check_logs() {
    local log_file=$1
    local description=$2
    local time_window=${3:-"1 hour ago"}
    
    if [ -f "$log_file" ]; then
        local error_count=$(journalctl --since "$time_window" -u "$description" --no-pager | grep -i error | wc -l)
        
        if [ "$error_count" -eq 0 ]; then
            print_pass "No errors in $description logs (last hour)"
        elif [ "$error_count" -lt 5 ]; then
            print_warning "$error_count errors found in $description logs (last hour)"
        else
            print_fail "$error_count errors found in $description logs (last hour)"
        fi
    else
        print_warning "Log file $log_file not found"
    fi
}

# Main health check execution
main() {
    print_header "ConsultEase System Health Check"
    print_info "Starting comprehensive system validation..."
    print_info "Timestamp: $(date)"
    print_info "Hostname: $(hostname)"
    print_info "IP Address: $(hostname -I | awk '{print $1}')"
    
    print_header "System Resources"
    check_disk_space "/" 80
    check_disk_space "/opt" 80
    check_memory 80
    check_cpu_load 2.0
    
    print_header "Core Services"
    check_service "nginx"
    check_service "postgresql"
    check_service "redis-server"
    check_service "consulteasecentral"
    check_service "consulteasemqtt"
    
    print_header "Network Connectivity"
    check_port 80 "HTTP (Nginx)"
    check_port 443 "HTTPS (Nginx)"
    check_port 5432 "PostgreSQL"
    check_port 6379 "Redis"
    check_port 1883 "MQTT"
    check_port 8000 "Django Application"
    
    print_header "Web Interface"
    local server_ip=$(hostname -I | awk '{print $1}')
    check_http "http://localhost/" "Main web interface"
    check_http "http://localhost/health/" "Health endpoint"
    check_http "http://localhost/admin/" "Admin interface"
    check_http "http://localhost/api/v1/status/" "API status endpoint"
    
    print_header "Database Connectivity"
    check_database "consulteasedb" "consulteaseuser"
    
    # Check database tables exist
    if sudo -u postgres psql -d consulteasedb -c "\dt" | grep -q "faculty"; then
        print_pass "Database tables are present"
    else
        print_fail "Database tables are missing"
    fi
    
    print_header "File System Permissions"
    check_file_permissions "/opt/consulteasecentral" "www-data:www-data" "755"
    check_file_permissions "/var/log/consulteasecentral" "www-data:www-data" "755"
    check_file_permissions "/etc/nginx/sites-enabled/consulteasecentral" "root:root" "644"
    
    print_header "Security Checks"
    
    # Check firewall status
    if ufw status | grep -q "Status: active"; then
        print_pass "UFW firewall is active"
    else
        print_fail "UFW firewall is not active"
    fi
    
    # Check fail2ban status
    check_service "fail2ban"
    
    # Check SSL certificate (if exists)
    if [ -f "/etc/letsencrypt/live/$(hostname)/fullchain.pem" ]; then
        local cert_expiry=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$(hostname)/fullchain.pem" | cut -d= -f2)
        local expiry_epoch=$(date -d "$cert_expiry" +%s)
        local current_epoch=$(date +%s)
        local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        if [ "$days_until_expiry" -gt 30 ]; then
            print_pass "SSL certificate expires in $days_until_expiry days"
        elif [ "$days_until_expiry" -gt 7 ]; then
            print_warning "SSL certificate expires in $days_until_expiry days"
        else
            print_fail "SSL certificate expires in $days_until_expiry days (critical)"
        fi
    else
        print_warning "SSL certificate not found (HTTP only)"
    fi
    
    print_header "Application Health"
    
    # Check Django application
    if curl -s "http://localhost/api/v1/status/" | grep -q "healthy"; then
        print_pass "Django application is healthy"
    else
        print_fail "Django application is not responding correctly"
    fi
    
    # Check MQTT service
    if pgrep -f "run_mqtt_service" > /dev/null; then
        print_pass "MQTT service process is running"
    else
        print_fail "MQTT service process is not running"
    fi
    
    print_header "Log Analysis"
    check_logs "/var/log/nginx/error.log" "nginx"
    check_logs "" "consulteasecentral"
    check_logs "" "consulteasemqtt"
    check_logs "" "postgresql"
    
    print_header "Performance Metrics"
    
    # Check response times
    local response_time=$(curl -o /dev/null -s -w "%{time_total}" "http://localhost/")
    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        print_pass "Web interface response time: ${response_time}s (< 1.0s)"
    elif (( $(echo "$response_time < 3.0" | bc -l) )); then
        print_warning "Web interface response time: ${response_time}s (>= 1.0s)"
    else
        print_fail "Web interface response time: ${response_time}s (>= 3.0s)"
    fi
    
    # Check database connections
    local db_connections=$(sudo -u postgres psql -d consulteasedb -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='consulteasedb';" | xargs)
    if [ "$db_connections" -lt 10 ]; then
        print_pass "Database connections: $db_connections (< 10)"
    elif [ "$db_connections" -lt 20 ]; then
        print_warning "Database connections: $db_connections (>= 10)"
    else
        print_fail "Database connections: $db_connections (>= 20)"
    fi
    
    print_header "Faculty Desk Unit Connectivity"
    
    # Check for connected faculty desk units (this would need to be customized based on your MQTT broker)
    local connected_units=$(mosquitto_sub -h localhost -t "consultease/faculty/+/heartbeat" -W 5 2>/dev/null | wc -l || echo "0")
    if [ "$connected_units" -gt 0 ]; then
        print_pass "$connected_units faculty desk units are connected"
    else
        print_warning "No faculty desk units detected (may be normal if none are deployed)"
    fi
    
    print_header "Health Check Summary"
    
    local pass_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    
    print_info "Total Checks: $TOTAL_CHECKS"
    print_info "Passed: $PASSED_CHECKS"
    print_info "Failed: $FAILED_CHECKS"
    print_info "Warnings: $WARNING_CHECKS"
    print_info "Pass Rate: ${pass_rate}%"
    
    if [ "$FAILED_CHECKS" -eq 0 ]; then
        if [ "$WARNING_CHECKS" -eq 0 ]; then
            echo -e "\n${GREEN}🎉 EXCELLENT: All checks passed! System is healthy.${NC}"
            exit 0
        else
            echo -e "\n${YELLOW}✅ GOOD: System is operational with minor warnings.${NC}"
            exit 0
        fi
    elif [ "$FAILED_CHECKS" -lt 3 ]; then
        echo -e "\n${YELLOW}⚠️  WARNING: System has some issues that should be addressed.${NC}"
        exit 1
    else
        echo -e "\n${RED}❌ CRITICAL: System has significant issues requiring immediate attention.${NC}"
        exit 2
    fi
}

# Check if required tools are available
command -v curl >/dev/null 2>&1 || { echo "curl is required but not installed. Aborting." >&2; exit 1; }
command -v bc >/dev/null 2>&1 || { echo "bc is required but not installed. Installing..." >&2; apt-get update && apt-get install -y bc; }

# Run the main health check
main "$@"
