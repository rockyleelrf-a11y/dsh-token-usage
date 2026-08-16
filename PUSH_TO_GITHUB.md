# 上传到 GitHub 开源

本仓库已经初始化为本地 Git 仓库，并包含以下内容：

- `README.md` — 项目说明
- `FEATURES.md` — 功能介绍
- `install.sh` / `uninstall.sh` — 一键安装/卸载
- `lib/client.js` — 客户端插件
- `lib/index.js` — 宿主侧空实现
- `LICENSE` — MIT 协议
- `package.json` — DSH 插件元数据

## 第一步：在 GitHub 上创建仓库

打开 https://github.com/new

- Repository name 建议：`dsh-token-usage`
- Description 建议：`DeepSeek Harness Token usage & cost dashboard plugin`
- Visibility：`Public`
- 不要勾选 “Add a README file”（仓库里已有）

## 第二步：推送到 GitHub

```bash
cd ~/Desktop/DeepSeekAgent/token-usage-plugin
git remote add origin https://github.com/<你的用户名>/dsh-token-usage.git
git branch -M main
git push -u origin main
```

如果你使用 SSH：

```bash
git remote add origin git@github.com:<你的用户名>/dsh-token-usage.git
git branch -M main
git push -u origin main
```

## 第三步：可选完善

- 在 GitHub 仓库 Settings 中打开 Issues / Discussions
- 添加 release 标签：
  ```bash
  git tag v0.1.0
  git push origin v0.1.0
  ```
- 可将 `dsh-token-usage-plugin-v0.1.0.zip` 作为 GitHub Release 附件上传

## 说明

当前沙箱环境没有 GitHub 凭据/网络权限，因此无法代替你实际创建远程仓库。以上命令在你的本机终端中运行即可完成开源发布。
