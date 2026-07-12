#!/bin/bash
# 将本仓库的 skill 以目录软链接方式安装到指定工具的 skills 目录

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── 终端颜色 ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ─── 工具函数 ──────────────────────────────────────────────────────────────────
print_header() {
    echo -e "\n${BOLD}${CYAN}=== Skill 链接安装工具 ===${RESET}\n"
}

print_step() {
    echo -e "${BOLD}▶ $1${RESET}"
}

print_ok()   { echo -e "  ${GREEN}✔${RESET} $1"; }
print_warn() { echo -e "  ${YELLOW}⚠${RESET}  $1"; }
print_err()  { echo -e "  ${RED}✘${RESET} $1"; }

# ─── 第一步：选择目标工具目录 ──────────────────────────────────────────────────
select_target_dir() {
    print_step "选择目标工具"
    echo "  1) claude      → ${HOME}/.claude/skills"
    echo "  2) openclaw    → ${HOME}/.openclaw/skills"
    echo "  3) 自定义路径"
    echo ""

    local choice
    while true; do
        read -rp "  请输入选项 [1-3]: " choice
        case "$choice" in
            1) TARGET_DIR="${HOME}/.claude/skills"; break ;;
            2) TARGET_DIR="${HOME}/.openclaw/skills"; break ;;
            3)
                read -rp "  请输入目标目录路径: " custom_path
                # 展开 ~ 并去除尾部斜杠
                custom_path="${custom_path/#\~/$HOME}"
                custom_path="${custom_path%/}"
                if [[ -z "$custom_path" ]]; then
                    print_err "路径不能为空，请重新输入"
                    continue
                fi
                TARGET_DIR="$custom_path"
                break
                ;;
            *) print_err "无效选项，请输入 1、2 或 3" ;;
        esac
    done

    echo ""
    echo -e "  目标目录: ${CYAN}${TARGET_DIR}${RESET}"
}

# ─── 扫描 skill（含 SKILL.md 的目录）─────────────────────────────────────────
scan_skills() {
    SKILL_PATHS=()   # skill 的绝对路径
    SKILL_NAMES=()   # skill 的目录名（用于显示和链接名）

    # 找所有包含 SKILL.md 的目录，排除脚本自身所在层（若有）
    while IFS= read -r skill_md; do
        local skill_dir
        skill_dir="$(dirname "$skill_md")"
        # 跳过根目录本身（若根目录也有 SKILL.md）
        [[ "$skill_dir" == "$SCRIPT_DIR" ]] && continue
        SKILL_PATHS+=("$skill_dir")
        SKILL_NAMES+=("$(basename "$skill_dir")")
    done < <(find "$SCRIPT_DIR" -name "SKILL.md" | sort)
}

# ─── 纯 Bash 多选 UI ───────────────────────────────────────────────────────────
# 用法: multiselect "item1" "item2" ...
# 结果写入全局数组 SELECTED_INDICES
SELECTED_INDICES=()
multiselect() {
    local items=("$@")
    local count=${#items[@]}
    local cursor=0
    local -a selected
    for ((i=0; i<count; i++)); do selected[i]=0; done

    # 隐藏光标
    tput civis 2>/dev/null || true
    trap 'tput cnorm 2>/dev/null; echo ""; exit 130' INT

    _render_menu() {
        for ((i=0; i<count; i++)); do
            local prefix="  "
            local check="[ ]"
            [[ ${selected[i]} -eq 1 ]] && check="[${GREEN}✔${RESET}]"
            if [[ $i -eq $cursor ]]; then
                echo -e "${CYAN}▶ ${check} ${items[i]}${RESET}"
            else
                echo -e "  ${check} ${items[i]}"
            fi
        done
        echo ""
        echo -e "  ${YELLOW}↑↓${RESET} 移动  ${YELLOW}Space${RESET} 选择/取消  ${YELLOW}a${RESET} 全选  ${YELLOW}Enter${RESET} 确认"
    }

    # 首次渲染
    _render_menu
    local rendered_lines=$((count + 2))

    while true; do
        # 回到菜单顶部重绘
        tput cuu "$rendered_lines" 2>/dev/null || true
        _render_menu

        # 读取按键（|| true 防止 read 返回非零被 set -e 终止）
        local key key2 key3
        IFS= read -rsn1 key || true
        if [[ $key == $'\x1b' ]]; then
            IFS= read -rsn1 -t 0.1 key2 || true
            IFS= read -rsn1 -t 0.1 key3 || true
            key="${key}${key2-}${key3-}"
        fi

        case "$key" in
            $'\x1b[A')             # 上箭头
                if [[ $cursor -gt 0 ]]; then
                    cursor=$(( cursor - 1 ))
                else
                    cursor=$(( count - 1 ))
                fi
                ;;
            $'\x1b[B')             # 下箭头
                if [[ $cursor -lt $(( count - 1 )) ]]; then
                    cursor=$(( cursor + 1 ))
                else
                    cursor=0
                fi
                ;;
            ' ')                   # 空格：切换选中
                if [[ ${selected[cursor]} -eq 0 ]]; then
                    selected[cursor]=1
                else
                    selected[cursor]=0
                fi
                ;;
            'a'|'A')               # 全选 / 取消全选
                local all_selected=1
                for ((i=0; i<count; i++)); do
                    [[ ${selected[i]} -eq 0 ]] && all_selected=0 && break
                done
                if [[ $all_selected -eq 1 ]]; then
                    for ((i=0; i<count; i++)); do selected[i]=0; done
                else
                    for ((i=0; i<count; i++)); do selected[i]=1; done
                fi
                ;;
            ''|$'\n'|$'\r')        # Enter：确认（终端可能发 \r 或 \n 或空串）
                break
                ;;
        esac
    done

    tput cnorm 2>/dev/null || true
    trap - INT

    SELECTED_INDICES=()
    for ((i=0; i<count; i++)); do
        if [[ ${selected[i]} -eq 1 ]]; then
            SELECTED_INDICES+=("$i")
        fi
    done
}

# ─── 第二步：选择 skill ────────────────────────────────────────────────────────
select_skills() {
    print_step "选择要安装的 Skill"
    echo ""

    if [[ ${#SKILL_NAMES[@]} -eq 0 ]]; then
        print_err "未在 ${SCRIPT_DIR} 下找到任何包含 SKILL.md 的目录"
        exit 1
    fi

    multiselect "${SKILL_NAMES[@]}"

    if [[ ${#SELECTED_INDICES[@]} -eq 0 ]]; then
        echo ""
        print_warn "未选择任何 skill，退出"
        exit 0
    fi
}

# ─── 第三步：创建软链接 ────────────────────────────────────────────────────────
create_links() {
    echo ""
    print_step "创建软链接"

    # 确保目标目录存在
    if [[ ! -d "$TARGET_DIR" ]]; then
        mkdir -p "$TARGET_DIR"
        print_ok "已创建目标目录: ${TARGET_DIR}"
    fi

    local success=0 skipped=0 failed=0

    for idx in "${SELECTED_INDICES[@]}"; do
        local src="${SKILL_PATHS[$idx]}"
        local name="${SKILL_NAMES[$idx]}"
        local dest="${TARGET_DIR}/${name}"

        if [[ -L "$dest" ]]; then
            local existing_target
            existing_target="$(readlink -f "$dest")"
            if [[ "$existing_target" == "$src" ]]; then
                print_warn "已存在相同链接，跳过: ${name}"
            else
                print_warn "已存在指向其他路径的链接，跳过: ${name}  (当前→ ${existing_target})"
            fi
            skipped=$(( skipped + 1 ))
        elif [[ -e "$dest" ]]; then
            print_warn "目标位置已存在同名文件/目录（非链接），跳过: ${name}"
            skipped=$(( skipped + 1 ))
        else
            if ln -s "$src" "$dest"; then
                print_ok "已链接: ${name}  →  ${src}"
                success=$(( success + 1 ))
            else
                print_err "链接失败: ${name}"
                failed=$(( failed + 1 ))
            fi
        fi
    done

    echo ""
    echo -e "  完成：${GREEN}${success} 个成功${RESET}，${YELLOW}${skipped} 个跳过${RESET}，${RED}${failed} 个失败${RESET}"
}

# ─── 主流程 ───────────────────────────────────────────────────────────────────
main() {
    print_header
    select_target_dir
    echo ""
    scan_skills
    select_skills
    create_links
    echo ""
}

main
