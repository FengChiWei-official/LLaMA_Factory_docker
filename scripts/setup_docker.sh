#!/bin/bash
# setup_docker.sh - Docker 环境初始化脚本
# 支持 Ubuntu, CentOS, Arch Linux (yay/paru) 等发行版
# 用法: bash setup_docker.sh [包管理器]
# 示例:
#   bash setup_docker.sh                 # 自动检测
#   bash setup_docker.sh apt             # 使用 apt (Debian/Ubuntu)
#   bash setup_docker.sh yum             # 使用 yum (CentOS/RHEL)
#   bash setup_docker.sh pacman          # 使用 pacman (Arch Linux)
#   bash setup_docker.sh yay             # 使用 yay (Arch Linux AUR)
#   bash setup_docker.sh paru            # 使用 paru (Arch Linux AUR)

set -e

# ============================================================
# 辅助函数
# ============================================================

# 显示帮助信息
show_help() {
    cat << EOF
用法: bash setup_docker.sh [选项]

选项:
    -h, --help          显示此帮助信息
    apt                 使用 apt 包管理器 (Debian/Ubuntu)
    yum                 使用 yum 包管理器 (CentOS/RHEL)
    pacman              使用 pacman 包管理器 (Arch Linux)
    yay                 使用 yay AUR 助手 (Arch Linux)
    paru                使用 paru AUR 助手 (Arch Linux)
    (空)                自动检测发行版并使用相应包管理器

示例:
    bash setup_docker.sh                 # 自动检测
    bash setup_docker.sh apt             # 使用 apt
    bash setup_docker.sh yum             # 使用 yum
    bash setup_docker.sh pacman          # 使用 pacman
    bash setup_docker.sh yay             # 使用 yay
    bash setup_docker.sh paru            # 使用 paru
EOF
}

# 将包管理器名称转换为发行版类型
resolve_distro_from_pkgmgr() {
    local pkgmgr=$1
    case $pkgmgr in
        apt)
            echo "debian"
            ;;
        yum)
            echo "redhat"
            ;;
        pacman|yay|paru)
            echo "arch"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# 验证包管理器是否存在
check_pkgmgr_exists() {
    local pkgmgr=$1
    if command -v "$pkgmgr" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# 检测Linux发行版
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" =~ ^(ubuntu|debian)$ ]]; then
            echo "debian"
        elif [[ "$ID" == "centos" ]] || [[ "$ID_LIKE" =~ rhel ]]; then
            echo "redhat"
        elif [[ "$ID" == "arch" ]] || [[ "$ID" == "archlinux" ]]; then
            echo "arch"
        else
            echo "unknown"
        fi
    else
        echo "unknown"
    fi
}

# Ubuntu/Debian 系统依赖安装
install_deps_debian() {
    echo "检测到 Debian/Ubuntu 系统"
    echo "更新包管理器..."
    sudo apt-get update
    
    echo "安装必要依赖..."
    sudo apt-get install -y \
        docker.io \
        docker-compose \
        curl \
        wget \
        git \
        gnupg \
        lsb-release \
        software-properties-common
}

# CentOS/RHEL 系统依赖安装
install_deps_redhat() {
    echo "检测到 CentOS/RHEL 系统"
    echo "更新包管理器..."
    sudo yum update -y
    
    echo "安装必要依赖..."
    sudo yum install -y \
        yum-utils \
        device-mapper-persistent-data \
        lvm2 \
        docker \
        docker-compose \
        curl \
        wget \
        git \
        gnupg
    
    # 启动 Docker 服务
    echo "启动 Docker 服务..."
    sudo systemctl start docker
    sudo systemctl enable docker
}

# Arch Linux 系统依赖安装
install_deps_arch() {
    echo "检测到 Arch Linux 系统"
    
    # 检测 AUR 助手
    local aur_helper=""
    if command -v yay &> /dev/null; then
        aur_helper="yay"
        echo "检测到 AUR 助手: yay"
    elif command -v paru &> /dev/null; then
        aur_helper="paru"
        echo "检测到 AUR 助手: paru"
    else
        echo "⚠ 未检测到 AUR 助手 (yay/paru)"
        echo "请先安装 yay 或 paru:"
        echo "  # 安装 yay:"
        echo "  sudo pacman -S git base-devel && git clone https://aur.archlinux.org/yay.git && cd yay && makepkg -si"
        echo "  # 或安装 paru:"
        echo "  sudo pacman -S git base-devel && git clone https://aur.archlinux.org/paru.git && cd paru && makepkg -si"
        return 1
    fi
    
    echo "更新包管理器..."
    sudo pacman -Sy
    
    echo "安装必要依赖..."
    sudo pacman -S --noconfirm \
        docker \
        docker-compose \
        curl \
        wget \
        git \
        gnupg
    
    # 对于 nvidia-container-toolkit，使用 AUR
    if [ "$aur_helper" != "" ]; then
        echo "从 AUR 安装 nvidia-container-toolkit..."
        $aur_helper -S --noconfirm nvidia-container-toolkit
    fi
    
    # 启动 Docker 服务
    echo "启动 Docker 服务..."
    sudo systemctl start docker
    sudo systemctl enable docker
}

# 检查并安装 NVIDIA Container Toolkit
install_nvidia_container_toolkit_with_retry() {
    local distro=$1
    local max_retries=3
    local retry_count=0
    
    echo -e "\n正在安装 nvidia-container-toolkit..."
    
    while [ $retry_count -lt $max_retries ]; do
        case $distro in
            debian)
                echo "为 Debian/Ubuntu 安装 nvidia-container-toolkit（尝试 $((retry_count + 1))/$max_retries）..."
                if distribution=$(. /etc/os-release; echo $ID$VERSION_ID) && \
                   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - 2>/dev/null && \
                   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
                   sudo tee /etc/apt/sources.list.d/nvidia-docker.list > /dev/null && \
                   sudo apt-get update && \
                   sudo apt-get install -y nvidia-container-toolkit; then
                    echo "✓ nvidia-container-toolkit 安装成功"
                    return 0
                fi
                ;;
            redhat)
                echo "为 CentOS/RHEL 安装 nvidia-container-toolkit（尝试 $((retry_count + 1))/$max_retries）..."
                if distribution=$(. /etc/os-release; echo $ID$VERSION_ID) && \
                   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | \
                   sudo tee /etc/yum.repos.d/nvidia-docker.repo > /dev/null && \
                   sudo yum update -y && \
                   sudo yum install -y nvidia-container-toolkit; then
                    echo "✓ nvidia-container-toolkit 安装成功"
                    return 0
                fi
                ;;
            arch)
                echo "为 Arch Linux 安装 nvidia-container-toolkit（尝试 $((retry_count + 1))/$max_retries）..."
                
                # 检测 AUR 助手
                local aur_helper=""
                if command -v yay &> /dev/null; then
                    aur_helper="yay"
                elif command -v paru &> /dev/null; then
                    aur_helper="paru"
                fi
                
                if [ -z "$aur_helper" ]; then
                    echo "✗ 未检测到 AUR 助手（yay 或 paru）"
                    echo "请先安装 yay 或 paru:"
                    echo "  # 安装 yay:"
                    echo "  sudo pacman -S git base-devel"
                    echo "  git clone https://aur.archlinux.org/yay.git"
                    echo "  cd yay && makepkg -si"
                    echo "  # 或安装 paru:"
                    echo "  sudo pacman -S git base-devel"
                    echo "  git clone https://aur.archlinux.org/paru.git"
                    echo "  cd paru && makepkg -si"
                    return 1
                fi
                
                if $aur_helper -S --noconfirm nvidia-container-toolkit; then
                    echo "✓ nvidia-container-toolkit 安装成功"
                    return 0
                fi
                ;;
        esac
        
        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $max_retries ]; then
            echo "⚠ 安装失败，${retry_count} 秒后重试..."
            sleep 2
        fi
    done
    
    echo "✗ nvidia-container-toolkit 安装失败（已尝试 $max_retries 次）"
    return 1
}

# 配置 Docker 使用 NVIDIA Runtime
configure_docker_nvidia() {
    echo "配置 Docker 使用 NVIDIA Runtime..."
    
    # 检查 nvidia-ctk 命令
    if ! command -v nvidia-ctk &> /dev/null; then
        echo "✗ nvidia-ctk 命令不可用"
        echo "nvidia-container-toolkit 可能未正确安装"
        return 1
    fi
    
    if sudo nvidia-ctk runtime configure --runtime=docker; then
        sudo systemctl restart docker
        echo "✓ Docker NVIDIA Runtime 配置完成"
        return 0
    else
        echo "✗ Docker NVIDIA Runtime 配置失败"
        return 1
    fi
}

# ============================================================
# 主程序开始
# ============================================================

# 处理命令行参数
PKG_MGR="${1:-}"

# 显示帮助信息
if [ "$PKG_MGR" = "-h" ] || [ "$PKG_MGR" = "--help" ]; then
    show_help
    exit 0
fi

echo "================================"
echo "LLaMA-Factory Docker 环境检查与配置"
echo "================================"

# 确定使用的包管理器和发行版
if [ -z "$PKG_MGR" ]; then
    # 自动检测发行版
    echo -e "\n[步骤 0/5] 自动检测 Linux 发行版..."
    DISTRO=$(detect_distro)
    if [ "$DISTRO" = "unknown" ]; then
        echo "✗ 无法识别的 Linux 发行版"
        exit 1
    fi
    echo "✓ 检测到发行版: $DISTRO"
else
    # 使用指定的包管理器
    echo -e "\n[步骤 0/5] 使用指定的包管理器: $PKG_MGR"
    
    # 检查包管理器是否存在
    if ! check_pkgmgr_exists "$PKG_MGR"; then
        echo "✗ 包管理器 '$PKG_MGR' 不存在或未安装"
        echo "请先安装包管理器或选择其他包管理器"
        show_help
        exit 1
    fi
    
    # 将包管理器转换为发行版类型
    DISTRO=$(resolve_distro_from_pkgmgr "$PKG_MGR")
    if [ "$DISTRO" = "unknown" ]; then
        echo "✗ 无法识别的包管理器: $PKG_MGR"
        show_help
        exit 1
    fi
    
    echo "✓ 使用发行版类型: $DISTRO (包管理器: $PKG_MGR)"
fi

# 根据发行版安装基础依赖
echo -e "\n[步骤 1/5] 安装基础依赖..."
case $DISTRO in
    debian)
        install_deps_debian
        ;;
    redhat)
        install_deps_redhat
        ;;
    arch)
        if ! install_deps_arch; then
            echo "Arch Linux 依赖安装失败，请手动安装 AUR 助手"
            exit 1
        fi
        ;;
esac
echo "✓ 基础依赖安装完成"

# 检查 Docker
echo -e "\n[步骤 2/5] 检查 Docker..."
if command -v docker &> /dev/null; then
    echo "✓ Docker 已安装"
    docker --version
else
    echo "✗ Docker 安装失败"
    exit 1
fi

# 检查 NVIDIA 驱动
echo -e "\n[步骤 3/5] 检查 NVIDIA 驱动..."
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA 驱动已安装"
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
else
    echo "⚠ 未检测到 NVIDIA 驱动"
    echo "如需 GPU 支持，请先安装 NVIDIA 驱动"
    echo "安装指南:"
    echo "  Ubuntu: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html"
    echo "  CentOS: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html"
    echo "  Arch:   https://wiki.archlinux.org/title/NVIDIA"
fi

# 检查和安装 nvidia-container-toolkit
echo -e "\n[步骤 4/5] 检查 nvidia-container-toolkit..."
if command -v nvidia-container-toolkit &> /dev/null; then
    echo "✓ nvidia-container-toolkit 已安装"
    nvidia-container-toolkit --version
    
    # 如果 NVIDIA 驱动已安装，确保配置也已完成
    if command -v nvidia-smi &> /dev/null; then
        echo "正在验证 Docker NVIDIA Runtime 配置..."
        configure_docker_nvidia
    fi
else
    # 如果已安装 NVIDIA 驱动，则必须安装 nvidia-container-toolkit
    if command -v nvidia-smi &> /dev/null; then
        echo "检测到 NVIDIA 驱动已安装，必须安装 nvidia-container-toolkit..."
        if install_nvidia_container_toolkit_with_retry "$DISTRO"; then
            echo "✓ nvidia-container-toolkit 安装成功"
            configure_docker_nvidia
        else
            echo "✗ nvidia-container-toolkit 安装失败"
            echo "请手动安装 nvidia-container-toolkit"
            echo "参考文档: https://github.com/NVIDIA/nvidia-container-toolkit"
            exit 1
        fi
    else
        echo "⚠ 未检测到 NVIDIA 驱动，跳过 nvidia-container-toolkit 安装"
        echo "如需 GPU 支持，请先安装 NVIDIA 驱动后重新运行此脚本"
    fi
fi

# 配置用户权限
echo -e "\n[步骤 5/5] 配置 Docker 用户权限..."
if ! groups $USER | grep -q docker; then
    echo "添加当前用户到 docker 组..."
    sudo usermod -aG docker $USER
    echo "✓ 用户权限配置完成"
    echo "⚠ 请运行: newgrp docker 或重新登录以应用权限"
else
    echo "✓ 用户已在 docker 组中"
fi

echo -e "\n================================"
echo "✓ 所有依赖检查与配置完成！"
echo "================================"
echo -e "\n下一步: 运行 bash scripts/start_docker.sh"
