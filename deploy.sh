#!/bin/bash
# =============================================
# UnstressVN — Deploy Script
# Commit, push → Coolify auto-deploys via webhook
#
# Usage:
#   ./deploy.sh                          # Commit all changes + push
#   ./deploy.sh "fix: sửa lỗi XYZ"      # Commit with custom message
#   ./deploy.sh --status                 # Show git status only
#   ./deploy.sh --diff                   # Show git diff only
# =============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Always work from the repo root (where this script lives)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRANCH="main"

cd "$PROJECT_DIR"

# =============================================
# Parse arguments
# =============================================
MODE="deploy"
COMMIT_MSG=""

for arg in "$@"; do
    case "$arg" in
        --status)
            MODE="status"
            ;;
        --diff)
            MODE="diff"
            ;;
        --help|-h)
            echo "Usage: ./deploy.sh [OPTIONS] [COMMIT_MESSAGE]"
            echo ""
            echo "Options:"
            echo "  --status   Show git status"
            echo "  --diff     Show git diff"
            echo "  -h, --help Show this help"
            echo ""
            echo "Examples:"
            echo "  ./deploy.sh                       # Auto commit + push"
            echo "  ./deploy.sh \"fix: sửa lỗi XYZ\"   # Commit with message + push"
            echo "  ./deploy.sh --diff                # Preview changes"
            exit 0
            ;;
        *)
            COMMIT_MSG="$arg"
            ;;
    esac
done

# =============================================
# Verify git repo
# =============================================
if [ ! -d ".git" ]; then
    echo -e "${RED}✗ Not a git repository: $PROJECT_DIR${NC}"
    exit 1
fi

# =============================================
# Status / Diff modes
# =============================================
if [ "$MODE" = "status" ]; then
    git status
    exit 0
fi

if [ "$MODE" = "diff" ]; then
    git diff
    exit 0
fi

# =============================================
# Deploy mode: commit + push
# =============================================
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  UnstressVN — Deploy${NC}"
echo -e "${CYAN}========================================${NC}"

# Check for changes
CHANGES=$(git status --short 2>/dev/null)

if [ -z "$CHANGES" ]; then
    echo -e "${GREEN}✓ No changes to deploy.${NC}"
    exit 0
fi

# Count changes
MODIFIED=$(echo "$CHANGES" | grep -c "^ M\| M " 2>/dev/null || echo 0)
ADDED=$(echo "$CHANGES" | grep -c "^??" 2>/dev/null || echo 0)
DELETED=$(echo "$CHANGES" | grep -c "^ D\| D " 2>/dev/null || echo 0)
TOTAL=$(echo "$CHANGES" | wc -l)

echo -e "${YELLOW}  Changes: ${TOTAL} files${NC}"
echo -e "  Modified: ${MODIFIED}"
echo -e "  New:      ${ADDED}"
echo -e "  Deleted:  ${DELETED}"
echo ""

# Show files (max 20)
echo -e "${BLUE}Files:${NC}"
echo "$CHANGES" | head -20
if [ "$TOTAL" -gt 20 ]; then
    echo -e "  ${YELLOW}... and $((TOTAL - 20)) more${NC}"
fi
echo ""

# =============================================
# Commit
# =============================================
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="deploy: $(date '+%Y-%m-%d %H:%M') — ${TOTAL} files changed"
fi

echo -e "${BLUE}Committing...${NC}"
git add -A
git commit -m "$COMMIT_MSG"

echo -e "${GREEN}✓ Committed: \"$COMMIT_MSG\"${NC}"

# =============================================
# Push → Coolify auto-deploys
# =============================================
REMOTE=$(git remote 2>/dev/null | head -1)

if [ -z "$REMOTE" ]; then
    echo -e "${RED}✗ No git remote configured.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Pushing to ${REMOTE}/${BRANCH}...${NC}"

git push "$REMOTE" "$BRANCH" 2>&1

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Deploy successful!${NC}"
echo -e "${GREEN}  → Coolify will auto build & deploy${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  ${BLUE}Coolify:${NC}  http://45.88.223.89:9000"
echo -e "  ${BLUE}Website:${NC}  https://unstressvn.com"
