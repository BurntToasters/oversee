#!/usr/bin/env bash
# Removes the oversee skill from the same folders install.sh writes to.
set -eu

skill_name="oversee"
src_dir="$(cd "$(dirname "$0")" && pwd)"
home="${HOME:?HOME is not set}"

dest_dirs=(
  "${home}/.agents/skills/${skill_name}"
  "${home}/.claude/skills/${skill_name}"
  "${home}/.gemini/config/skills/${skill_name}"
  "${home}/.gemini/antigravity-cli/skills/${skill_name}"
)

for dest_dir in "${dest_dirs[@]}"; do
  if [ "${src_dir}" = "${dest_dir}" ]; then
    echo "Error: this script is inside an installed copy of the skill. Run uninstall.sh from your repo copy instead." >&2
    exit 1
  fi
done

for dest_dir in "${dest_dirs[@]}"; do
  if [ -e "${dest_dir}" ]; then
    rm -rf "${dest_dir}"
    echo "Removed: ${dest_dir}"
  else
    echo "Not installed: ${dest_dir}"
  fi
done
