#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Skills Graph — Install Script
# ═══════════════════════════════════════════════════════════════════════════
# Repository: github.com/AbhishekSharma-17/skills-graph
#
# Usage:
#   ./install/install-skills.sh                  # Interactive menu
#   ./install/install-skills.sh --all            # Install all skills
#   ./install/install-skills.sh --skill agno     # Install specific skill
#   ./install/install-skills.sh --list           # List available skills
#   ./install/install-skills.sh --global         # Install all globally
#   ./install/install-skills.sh --help           # Show help
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

REPO="AbhishekSharma-17/skills-graph"
SKILLS=(
    "agno"
    "ms-agent-framework"
    "remotion-prompt-generator"
    "trigger-dev"
    "drizzle-orm"
    "hono"
    "zod"
    "claude-agent-sdk"
)

# Descriptions for the interactive menu
declare -A SKILL_DESC
SKILL_DESC[agno]="AI agent framework (Python) — v1.2.0 — 116 files, 23K lines"
SKILL_DESC[ms-agent-framework]="Microsoft Agent Framework (Python) — v2.0.0 — 61 files, 14K lines"
SKILL_DESC[remotion-prompt-generator]="Remotion video prompt generator (React) — v1.1.0 — 15 files, 2.7K lines"
SKILL_DESC[trigger-dev]="Background jobs & workflows (TypeScript) — v1.0.0 — 11 files, 3.5K lines"
SKILL_DESC[drizzle-orm]="Type-safe ORM (TypeScript) — v1.0.0 — 12 files, 3.5K lines"
SKILL_DESC[hono]="Ultrafast web framework (TypeScript) — v1.0.0 — 12 files, 3.4K lines"
SKILL_DESC[zod]="Schema validation (TypeScript) — v1.0.0 — 13 files, 3.7K lines"
SKILL_DESC[claude-agent-sdk]="Claude Agent SDK (Python + TypeScript) — v1.1.0 — 16 files, 5.8K lines"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  Skills Graph — Skill Installer${NC}"
    echo -e "${BOLD}${CYAN}  Repository: ${REPO}${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_help() {
    print_header
    echo -e "${BOLD}Usage:${NC}"
    echo "  ./install/install-skills.sh                  # Interactive menu"
    echo "  ./install/install-skills.sh --all            # Install all skills"
    echo "  ./install/install-skills.sh --skill <name>   # Install specific skill"
    echo "  ./install/install-skills.sh --list           # List available skills"
    echo "  ./install/install-skills.sh --global         # Install all globally"
    echo "  ./install/install-skills.sh --search <query> # Search skills ecosystem"
    echo "  ./install/install-skills.sh --help           # Show this help"
    echo ""
    echo -e "${BOLD}Available skills:${NC}"
    for skill in "${SKILLS[@]}"; do
        echo -e "  ${GREEN}${skill}${NC} — ${SKILL_DESC[$skill]}"
    done
    echo ""
    echo -e "${BOLD}Quick install (copy-paste):${NC}"
    echo ""
    echo "  # Via npx (recommended)"
    echo "  npx skills add ${REPO} --skill <skill-name>"
    echo ""
    echo "  # Via smithery"
    echo "  smithery install <skill-name>"
    echo ""
    echo -e "${BOLD}Manual install:${NC}"
    echo "  Copy the skill folder to your platform's skill directory."
    echo "  See README.md for platform-specific paths."
    echo ""
}

list_skills() {
    print_header
    echo -e "${BOLD}Available Skills (${#SKILLS[@]} total):${NC}"
    echo ""
    printf "  ${BOLD}%-30s %-60s${NC}\n" "SKILL" "DESCRIPTION"
    printf "  %-30s %-60s\n" "-----" "-----------"
    for skill in "${SKILLS[@]}"; do
        printf "  ${GREEN}%-30s${NC} %s\n" "$skill" "${SKILL_DESC[$skill]}"
    done
    echo ""
    echo -e "${BOLD}Install commands:${NC}"
    echo ""
    for skill in "${SKILLS[@]}"; do
        echo "  npx skills add ${REPO} --skill ${skill}"
    done
    echo ""
    echo -e "  ${YELLOW}# Or install all at once:${NC}"
    echo "  npx skills add ${REPO}"
    echo ""
}

install_skill() {
    local skill="$1"
    local global_flag="${2:-}"

    echo -e "${BLUE}Installing ${BOLD}${skill}${NC}${BLUE}...${NC}"

    if [ "$global_flag" = "--global" ] || [ "$global_flag" = "-g" ]; then
        npx skills add "${REPO}" --skill "${skill}" -g
    else
        npx skills add "${REPO}" --skill "${skill}"
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Successfully installed ${skill}${NC}"
    else
        echo -e "${RED}Failed to install ${skill}${NC}"
        return 1
    fi
}

install_all() {
    local global_flag="${1:-}"

    print_header
    echo -e "${BOLD}Installing all ${#SKILLS[@]} skills...${NC}"
    echo ""

    if [ "$global_flag" = "--global" ] || [ "$global_flag" = "-g" ]; then
        echo -e "${YELLOW}Installing globally...${NC}"
        npx skills add "${REPO}" -g
    else
        npx skills add "${REPO}"
    fi
}

interactive_menu() {
    print_header
    echo -e "${BOLD}Select skills to install:${NC}"
    echo ""

    for i in "${!SKILLS[@]}"; do
        local num=$((i + 1))
        echo -e "  ${BOLD}${num})${NC} ${GREEN}${SKILLS[$i]}${NC} — ${SKILL_DESC[${SKILLS[$i]}]}"
    done

    echo ""
    echo -e "  ${BOLD}a)${NC} Install ALL skills"
    echo -e "  ${BOLD}q)${NC} Quit"
    echo ""

    read -p "Enter choice (number, 'a' for all, or 'q' to quit): " choice

    case "$choice" in
        a|A)
            install_all
            ;;
        q|Q)
            echo "Bye!"
            exit 0
            ;;
        [1-8])
            local idx=$((choice - 1))
            if [ $idx -lt ${#SKILLS[@]} ]; then
                install_skill "${SKILLS[$idx]}"
            else
                echo -e "${RED}Invalid choice${NC}"
                exit 1
            fi
            ;;
        *)
            echo -e "${RED}Invalid choice: ${choice}${NC}"
            exit 1
            ;;
    esac
}

# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

case "${1:-}" in
    --help|-h)
        print_help
        ;;
    --list|-l)
        list_skills
        ;;
    --all|-a)
        install_all "${2:-}"
        ;;
    --global|-g)
        install_all "--global"
        ;;
    --skill|-s)
        if [ -z "${2:-}" ]; then
            echo -e "${RED}Error: --skill requires a skill name${NC}"
            echo "Usage: ./install/install-skills.sh --skill <skill-name>"
            exit 1
        fi
        install_skill "$2" "${3:-}"
        ;;
    --search)
        npx skills find "${2:-}"
        ;;
    "")
        interactive_menu
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        print_help
        exit 1
        ;;
esac
