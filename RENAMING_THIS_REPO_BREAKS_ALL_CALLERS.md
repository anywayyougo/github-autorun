# 请勿更改本仓库名称

本仓库名 `github-autorun` 已被调用方硬编码引用：

```yaml
uses: anywayyougo/github-autorun/.github/workflows/run-and-notify.yml@v1
```

一旦在 GitHub 上重命名仓库，或迁移到其他账号/组织，**所有调用方的工作流会立即报错中断**。

## 如果确实需要改名

1. 先在 GitHub 设置里重命名，GitHub 通常会保留旧名的重定向；
2. 尽快逐一修改所有调用方的 `uses:` 路径为新名字；
3. 注意重定向对未来新建的同名仓库无效，存在旧名被他人占用的风险。

## 更安全的做法

保持本仓库名称不变。需要新版本时改 tag（如 `v1`、`v1.x`）即可，无需改仓库名。

## 相关

- 可复用工作流入口：`.github/workflows/run-and-notify.yml`
- 调用方模板：`examples/caller.yml`
- 版本策略：调用方引用 `@v1`（浮动 tag）
