# Sunlit Spike 技术回执

## 1. 环境信息

- Python 版本: 3.12.4
- 操作系统: macOS-26.4.1-arm64-arm-64bit
- 各依赖库实际安装版本:
  - cjio: 0.10.1
  - trimesh: 4.12.0
  - shapely: 2.1.2
  - pvlib: 0.15.1
  - numpy: 2.4.4
  - rtree: 1.4.1

## 2. 安装过程

- 是否一次安装成功? 否。第一次在沙箱内安装失败,原因是网络访问被限制,报错为 `Operation not permitted` / `Could not find a version that satisfies the requirement cjio>=0.9.0`。
- 授权网络访问后是否安装成功? 是。所有核心依赖均通过 PyPI wheel 安装成功。
- 是否需要额外的系统依赖(brew install 等)? 没有。`shapely`、`rtree`、`scipy`、`h5py`、`trimesh` 均直接安装成功。
- 是否有库之间的版本冲突? 没有发现版本冲突。
- 额外观察: pip cache 目录不可写,安装时提示 cache disabled,但不影响安装。

## 3. 数据获取

- 使用的 CityJSON 文件来源: TU Delft 3D Geoinformation 公开数据 `geoRES_testdata_v1.0.0.city.json`
- 下载地址: `https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v1.1/geoRES_testdata_v1.0.0.city.json`
- 本地文件: `sample.cityjson`
- 文件大小: 537535 bytes,约 528 KB
- 文件中的建筑数量: 5 个 `Building`
- CityJSON schema 版本: v1.1
- 使用的坐标系(CRS): `https://www.opengis.net/def/crs/EPSG/0/31467`

## 4. 脚本运行结果

- 是否 7 个步骤全部跑通? 是。
- Step A: `cjio.cityjson.reader` 成功读取 `sample.cityjson`。
- Step B: 成功从 5 个 `Building` 提取面并合并为一个 `trimesh.Trimesh`。
- Step C: 测试点为 `(3499996.311, 5400012.882, 1.500)`。
- Step D: `pvlib` 计算 2026-01-20 12:00:00 Europe/Amsterdam 的太阳位置成功。
- Step E: 成功构造单位射线方向。
- Step F: 单条射线相交查询成功。
- Step G: 1000 条射线批量查询成功。
- 如果有步骤失败,失败在哪一步,具体错误信息? 无脚本步骤失败。
- 测试点是否符合"被遮挡"的预期? 是。测试点放在最高建筑北侧,大寒日代尔夫特中午太阳位于偏南方向,结果 `Shadowed: True` 符合预期。

脚本输出:

```text
Loaded 5 buildings from CityJSON
Combined mesh: 4718 vertices, 5299 faces
Test point: (3499996.311, 5400012.882, 1.500)
Sun azimuth: 166.86°, altitude: 17.04°
Ray direction: (0.217426, -0.931041, 0.293068)
Shadowed: True, ray intersection took 13.723 ms
Batch 1000 rays took 325.388 ms, 3073 rays/sec
```

## 5. 性能数据

- 单条射线查询耗时: 13.723 ms
- 1000 条射线批量查询耗时: 325.388 ms
- 1000 条射线吞吐: 3073 rays/sec
- 外推 62500 条射线预估耗时: 约 20.34 秒
- 是否满足"30 秒内完成典型 MVP 规模分析"的目标? 以此小样本和朴素实现估算,满足。

## 6. 踩到的坑

- 文档中推荐的 `https://3d.bk.tudelft.nl/opendata/cityjson/1.1/` 当前返回 404,实际可用目录是 `https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v1.1/`。
- 未授权网络环境下,`pip install` 和 `curl` 都会失败。`curl` 还暴露出本机代理 `127.0.0.1:7897` 不可连接的问题。
- `python -m cjio sample.cityjson info` 不可用,因为 `cjio` 包没有 `__main__`。
- `cjio` CLI 不接受 `.cityjson` 扩展名,提示只支持 `.json`、`.jsonl`、`.off`、`.poly`。但 `cjio.cityjson.reader` 可以正常读取 `sample.cityjson`。
- CityJSON 几何不一定是 LOD1 `Solid`; 本样本的建筑可从 `MultiSurface` / surface 边界中构建 mesh。MVP 不能只写死 LOD1 `Solid` 结构。
- 第一次运行 `trimesh` 射线查询时总耗时明显长于复跑,推测包含 scipy/pandas/trimesh import 与 ray index 初始化成本。正式性能测试应区分冷启动和热路径。

## 7. 对 MVP 的技术建议

- 正式 MVP 应将文件扩展名兼容性纳入输入层处理: `.cityjson`、`.city.json`、`.json` 都应可读,不要完全依赖 `cjio` CLI 的扩展名判断。
- CityJSON 读取建议直接使用 `cjio.cityjson.reader`,而不是 shell 调用 `cjio` CLI。
- 几何加载层需要支持 `MultiSurface`、`CompositeSurface`、`Solid`、`MultiSolid` 等结构,至少要能从 exterior ring 三角化出遮挡 mesh。
- 射线批量查询性能基本可接受,但正式 MVP 仍应缓存合并 mesh 与 ray acceleration 结构,避免每次分析重复构建。
- 坐标系不要在 spike 阶段处理是对的,但 MVP 必须认真处理 CRS 和米制坐标,尤其是 WGS84 经纬度输入。
- 性能测试应固定随机种子,同时记录建筑数量、face 数量、射线数量,否则不同样本之间没有可比性。

## 8. 最终判断

- [ ] 技术路径完全畅通,可以放心投入 MVP 开发
- [x] 技术路径基本畅通,但有以下需要注意的点: 数据下载 URL 与代理环境、`cjio` CLI 扩展名限制、CityJSON 几何类型多样性、冷启动性能和 CRS 处理。
- [ ] 技术路径有严重阻塞,需要重新评估方案。具体阻塞在: 无。

