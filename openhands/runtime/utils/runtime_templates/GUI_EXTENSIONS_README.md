# GUI Extensions for OpenHands Runtime

本文档说明如何在 OpenHands 运行时镜像中启用 GUI 扩展功能。

## 概述

GUI 扩展功能为 OpenHands 运行时环境添加了完整的桌面环境支持，包括：

- X11 显示服务器 (Xvfb)
- VNC 服务器 (x11vnc)
- Web 浏览器访问 (noVNC)
- 窗口管理器 (Mutter/Openbox)
- 桌面应用程序 (LibreOffice, 图像查看器, 文本编辑器等)
- 任务栏 (tint2)

## 使用方法

### 1. 启用 GUI 扩展

在构建 Dockerfile 时，设置 `enable_gui` 变量为 `true`：

```dockerfile
# 在模板变量中设置
{% set enable_gui = true %}
```

或者在 Jinja2 渲染时传递参数：

```python
from jinja2 import Template

template = Template(open('Dockerfile.j2').read())
dockerfile_content = template.render(
    base_image='nikolaik/python-nodejs:python3.12-nodejs24',
    build_from_scratch=True,
    enable_gui=True,  # 启用 GUI 扩展
    # ... 其他参数
)
```

### 2. 构建镜像

```bash
# 确保 gui-extensions 目录存在于构建上下文中
docker build -t openhands-gui .
```

### 3. 运行容器

```bash
# 运行容器并暴露 VNC 端口
docker run -d \
  --name openhands-gui \
  -p 6080:6080 \
  -p 5900:5900 \
  openhands-gui
```

### 4. 访问 GUI

- **Web 浏览器访问**: http://localhost:6080 (noVNC Web 界面)
- **VNC 客户端访问**: localhost:5900

## 配置选项

### 显示设置

可以通过构建参数自定义显示配置：

```dockerfile
ARG DISPLAY_NUM=1      # 显示编号
ARG HEIGHT=768         # 屏幕高度
ARG WIDTH=1024         # 屏幕宽度
```

### 用户设置

GUI 扩展会使用统一的用户管理：

- **用户名**: `openhands` (如果已存在) 或新创建的用户
- **主目录**: `/home/openhands`
- **权限**: 具有 sudo 权限

## 启动流程

GUI 扩展的启动流程如下：

1. **Docker ENTRYPOINT**: 容器启动时执行 `entrypoint.sh`
2. **服务启动**: `entrypoint.sh` 调用 `start_all.sh` 启动所有 GUI 服务
3. **noVNC 启动**: 单独启动 `novnc_startup.sh` 提供 Web 访问

### 启动脚本说明

- `entrypoint.sh`: 容器的主入口点，由 Docker 自动执行
- `start_all.sh`: 启动所有 GUI 服务的主脚本
- `xvfb_startup.sh`: 启动 X11 虚拟显示服务器 (DISPLAY :1)
- `x11vnc_startup.sh`: 启动 VNC 服务器 (端口 5900)
- `novnc_startup.sh`: 启动 noVNC Web 服务 (端口 6080)
- `mutter_startup.sh`: 启动窗口管理器
- `tint2_startup.sh`: 启动任务栏

## 端口配置

### 默认端口

- **VNC 服务器**: 5900 (x11vnc)
- **noVNC Web 界面**: 6080 (websocket 代理)
- **内部显示**: :1 (DISPLAY_NUM=1)

### 端口映射示例

```bash
# 标准端口映射
docker run -p 6080:6080 -p 5900:5900 openhands-gui

# 自定义端口映射
docker run -p 8080:6080 -p 5901:5900 openhands-gui
# 访问: http://localhost:8080 (Web) 或 localhost:5901 (VNC客户端)
```

## 包含的应用程序

### 办公软件
- LibreOffice (文档编辑)
- PDF 查看器 (xpdf)

### 图形工具
- 图像编辑器 (xpaint)
- 截图工具 (scrot)
- 图像处理 (imagemagick)

### 系统工具
- 文件管理器 (pcmanfm)
- 文本编辑器 (gedit)
- 计算器 (galculator)
- 终端 (xterm)

### 开发工具
- X11 应用程序集合 (x11-apps)
- 鼠标/键盘控制工具 (xdotool)

## 架构说明

GUI 扩展功能通过 `setup_gui_extensions()` 宏实现，该宏：

1. **安装必要的包**: X11、VNC、桌面环境和应用程序
2. **设置 noVNC**: 用于 Web 浏览器访问
3. **智能用户管理**: 复用现有的 `openhands` 用户或创建新用户
4. **复制配置文件**: 启动脚本和配置文件
5. **设置权限**: 确保脚本可执行和用户权限正确

## 与其他功能的兼容性

GUI 扩展与以下构建模式兼容：

- ✅ `build_from_scratch`: 从头构建时启用
- ✅ `build_from_versioned`: 基于版本化镜像构建时启用
- ✅ VSCode Server: 可与 VSCode Server 共存
- ✅ Extra Dependencies: 可与额外依赖项共存

## 故障排除

### 常见问题

1. **VNC 连接失败**
   - 检查端口映射是否正确 (5900:5900)
   - 确保容器正在运行

2. **Web 界面无法访问**
   - 检查 6080 端口是否被占用或正确映射
   - 确认 noVNC 服务是否启动: `ps aux | grep novnc_proxy`

3. **显示问题**
   - 检查 DISPLAY 环境变量设置 (应为 :1)
   - 确认 Xvfb 服务是否正常运行: `ps aux | grep Xvfb`

### 调试命令

```bash
# 进入容器检查服务状态
docker exec -it openhands-gui bash

# 检查 X11 服务
ps aux | grep Xvfb

# 检查 VNC 服务
ps aux | grep x11vnc

# 检查 noVNC 服务
ps aux | grep novnc_proxy

# 检查端口监听状态
netstat -tuln | grep -E "(5900|6080)"

# 查看 noVNC 日志
cat /tmp/novnc.log
```

## 性能考虑

启用 GUI 扩展会增加：

- **镜像大小**: 约 +500MB (桌面环境和应用程序)
- **内存使用**: 约 +200-400MB (运行时开销)
- **CPU 使用**: 图形渲染和 VNC 编码的额外开销

建议在需要图形界面功能时才启用此扩展。 