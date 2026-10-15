#!/usr/bin/env bash
# Installs or updates the oversee payload locally or from GitHub.
set -euo pipefail

profile_root="${HOME:?HOME is not set}"
fetch_dir=""
stage=""
dest=""
old_skill=0 old_refs=0 new_skill=0 new_refs=0

rollback() {
  [ -n "${stage}" ] || return 0
  local failed=0
  if [ "${new_skill}" = 1 ]; then rm -f "${dest}/SKILL.md" || failed=1; fi
  if [ "${new_refs}" = 1 ]; then rm -rf "${dest}/references" || failed=1; fi
  if [ "${old_skill}" = 1 ]; then mv "${stage}/old-skill" "${dest}/SKILL.md" || failed=1; fi
  if [ "${old_refs}" = 1 ]; then mv "${stage}/old-references" "${dest}/references" || failed=1; fi
  if [ "${failed}" = 1 ]; then
    echo "Error: restore failed; recovery files retained at ${stage}" >&2
    stage=""
    return 1
  fi
  rm -rf "${stage}"
  stage=""
}

cleanup() {
  rollback || true
  if [ -n "${fetch_dir}" ]; then rm -rf "${fetch_dir}"; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

script_path="${BASH_SOURCE[0]:-}"
src_dir=""
if [ -n "${script_path}" ]; then
  src_dir="$(cd "$(dirname "${script_path}")" && pwd -P)"
fi
if [ -z "${src_dir}" ] || [ ! -f "${src_dir}/SKILL.md" ]; then
  fetch_dir="$(mktemp -d)"
  repo="${OVERSEE_REPO:-https://github.com/BurntToasters/oversee}"
  branch="${OVERSEE_BRANCH:-main}"
  echo "Fetching the skill from ${repo} (${branch})" >&2
  if ! curl -fsSL "${repo}/archive/refs/heads/${branch}.tar.gz" | tar -xz -C "${fetch_dir}" --strip-components=1; then
    echo "Error: download or extraction failed." >&2
    exit 1
  fi
  src_dir="${fetch_dir}"
fi
if [ ! -s "${src_dir}/SKILL.md" ] || [ ! -s "${src_dir}/references/harnesses.md" ]; then
  echo "Error: incomplete skill payload (SKILL.md and references/harnesses.md required)." >&2
  exit 1
fi

install_to() {
  dest="$1"
  old_skill=0 old_refs=0 new_skill=0 new_refs=0
  if [ -L "${dest}" ] || [ -L "${dest}/SKILL.md" ] || [ -L "${dest}/references" ]; then
    echo "Error: refusing linked installation target: ${dest}" >&2
    return 1
  fi
  if [ -d "${dest}" ] && [ "$(cd "${dest}" && pwd -P)" = "${src_dir}" ]; then
    echo "Skipped: ${dest} is this folder."
    return 0
  fi
  mkdir -p "${dest}" || return 1
  stage="$(mktemp -d "$(dirname "${dest}")/.oversee-stage.XXXXXX")" || return 1
  cp "${src_dir}/SKILL.md" "${stage}/SKILL.md" || return 1
  cp -R "${src_dir}/references" "${stage}/references" || return 1
  if [ -e "${dest}/SKILL.md" ]; then
    [ -f "${dest}/SKILL.md" ] || return 1
    mv "${dest}/SKILL.md" "${stage}/old-skill" || return 1
    old_skill=1
  fi
  if [ -e "${dest}/references" ]; then
    [ -d "${dest}/references" ] || return 1
    mv "${dest}/references" "${stage}/old-references" || return 1
    old_refs=1
  fi
  mv "${stage}/SKILL.md" "${dest}/SKILL.md" || return 1
  new_skill=1
  mv "${stage}/references" "${dest}/references" || return 1
  new_refs=1
  old_skill=0 old_refs=0 new_skill=0 new_refs=0
  rm -rf "${stage}" || return 1
  stage=""
  echo "Installed/updated: ${dest}"
}

for relative in .agents/skills .claude/skills .gemini/config/skills .gemini/antigravity-cli/skills; do
  if ! install_to "${profile_root}/${relative}/oversee"; then
    echo "Error: could not install to ${dest}" >&2
    exit 1
  fi
done
echo "Start a new agent session to load the skill."
