#!/bin/bash
#
# System Info Monitor - Comprehensive system information and diagnostics tool
# Provides detailed system metrics and performance information
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Platform detection
detect_platform() {
    case "$(uname -s)" in
        Darwin*)     echo "macOS" ;;
        Linux*)      echo "Linux" ;;
        MINGW*)      echo "Windows" ;;
        *)           echo "Unknown" ;;
    esac
}

# Get system uptime
get_uptime() {
    case "$(detect_platform)" in
        Linux)
            uptime | awk -F, '{print $1}'
            ;;
        macOS)
            uptime | sed 's/^.*up //' | sed 's/, [0-9]* users.*//'
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Get CPU count
get_cpu_count() {
    case "$(detect_platform)" in
        Linux)
            grep -c ^processor /proc/cpuinfo 2>/dev/null || echo "N/A"
            ;;
        macOS)
            sysctl -n hw.ncpu 2>/dev/null || echo "N/A"
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Get CPU model
get_cpu_model() {
    case "$(detect_platform)" in
        Linux)
            grep "model name" /proc/cpuinfo 2>/dev/null | head -n1 | cut -d: -f2 | xargs
            ;;
        macOS)
            sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "N/A"
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Get total memory
get_total_memory() {
    case "$(detect_platform)" in
        Linux)
            free -h 2>/dev/null | grep Mem | awk '{print $2}'
            ;;
        macOS)
            vm_stat 2>/dev/null | grep "Pages free" | awk '{print int($3 * 4096 / 1024 / 1024 / 1024)}' || echo "N/A"
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Get used memory
get_used_memory() {
    case "$(detect_platform)" in
        Linux)
            free -h 2>/dev/null | grep Mem | awk '{print $3}'
            ;;
        macOS)
            vm_stat 2>/dev/null | grep "Pages active" | awk '{print int($3 * 4096 / 1024 / 1024 / 1024)}' || echo "N/A"
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Get disk space
get_disk_space() {
    case "$(detect_platform)" in
        Linux)
            df -h / | awk 'NR==2 {print $2}'
            ;;
        macOS)
            df -h / | awk 'NR==2 {print $2}'
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Get disk used
get_disk_used() {
    case "$(detect_platform)" in
        Linux)
            df -h / | awk 'NR==2 {print $3}'
            ;;
        macOS)
            df -h / | awk 'NR==2 {print $3}'
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Get disk usage percentage
get_disk_usage_percent() {
    case "$(detect_platform)" in
        Linux)
            df -h / | awk 'NR==2 {print $5}'
            ;;
        macOS)
            df -h / | awk 'NR==2 {print $5}'
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Get OS version
get_os_version() {
    case "$(detect_platform)" in
        Linux)
            cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d '"'
            ;;
        macOS)
            sw_vers -productVersion 2>/dev/null
            ;;
        *)
            uname -r
            ;;
    esac
}

# Get kernel version
get_kernel_version() {
    uname -r
}

# Get current load average
get_load_average() {
    uptime | grep -o "load average.*" | cut -d: -f2 | xargs
}

# Count running processes
count_processes() {
    case "$(detect_platform)" in
        Linux)
            ps aux | wc -l
            ;;
        macOS)
            ps aux | wc -l
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Get network interfaces
get_network_interfaces() {
    case "$(detect_platform)" in
        Linux)
            ip link show 2>/dev/null | grep "^[0-9]" | grep -o "^\s*[0-9]*:\s*\w*" | grep -o "\w*$" | tr '\n' ', '
            ;;
        macOS)
            networksetup -listallhardwareports 2>/dev/null | grep Device | awk '{print $NF}' | tr '\n' ', '
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Get current user
get_current_user() {
    whoami
}

# Get logged in users count
get_logged_in_users() {
    who 2>/dev/null | wc -l
}

# Get shell information
get_shell_info() {
    echo $SHELL
}

# Main reporting function
print_system_report() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║      SYSTEM INFORMATION REPORT             ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${YELLOW}System Overview${NC}"
    echo "  Platform: $(detect_platform)"
    echo "  OS Version: $(get_os_version)"
    echo "  Kernel: $(get_kernel_version)"
    echo "  Hostname: $(hostname)"
    echo "  Current User: $(get_current_user)"
    echo "  Shell: $(get_shell_info)"
    echo ""

    echo -e "${YELLOW}CPU Information${NC}"
    echo "  Model: $(get_cpu_model)"
    echo "  CPU Cores: $(get_cpu_count)"
    echo "  Load Average: $(get_load_average)"
    echo ""

    echo -e "${YELLOW}Memory Information${NC}"
    echo "  Total Memory: $(get_total_memory)"
    echo "  Used Memory: $(get_used_memory)"
    echo ""

    echo -e "${YELLOW}Disk Information${NC}"
    echo "  Total Space: $(get_disk_space)"
    echo "  Used Space: $(get_disk_used)"
    echo "  Usage: $(get_disk_usage_percent)"
    echo ""

    echo -e "${YELLOW}Process Information${NC}"
    echo "  Total Processes: $(count_processes)"
    echo "  Logged In Users: $(get_logged_in_users)"
    echo ""

    echo -e "${YELLOW}Network Information${NC}"
    echo "  Interfaces: $(get_network_interfaces)"
    echo ""

    echo -e "${YELLOW}Uptime${NC}"
    echo "  $(get_uptime)"
    echo ""
}

# Main execution
main() {
    if [ -n "$1" ]; then
        echo "Error: No arguments expected"
        exit 1
    fi

    print_system_report
}

main "$@"
