# Sunlit 项目技术 Spike 任务

> 目标:在 30 分钟内验证 CityJSON 日照分析的核心技术链路是否可行
> 输出:一个能运行的 Python 脚本 + 一份技术可行性回执
> 这不是产品代码,是风险前置验证

---

## 背景

我们即将开发一个基于 CityJSON 体块数据的地面日照分析工具,MVP 预计开发周期 3-4 周。
在正式投入之前,需要先验证**技术路径是否畅通**——确认核心依赖库能正常协作、数据格式没有隐藏的兼容性坑、性能大致可接受。

这就是本次 spike 的目的。

**请严格遵守以下纪律**,否则这个 spike 会失去意义:

- ❌ 不要做网格化、不要做热力图、不要调用 AI、不要做命令行包装、不要考虑用户友好性
- ❌ 不要"顺便完善一下"任何功能
- ❌ 遇到问题不要花超过 20 分钟尝试修复,直接记录在回执里
- ✅ 只做"一个固定点位在一个固定时刻是否被遮挡"这一件事
- ✅ 过程中遇到的所有阻力、版本冲突、平台差异,全部记录

---

## 技术栈

以下是本项目计划使用的核心库。spike 的任务就是验证它们能协作工作:

- `cjio`(>=0.9.0):CityJSON 的官方 Python 库
- `trimesh`(>=4.0.0):3D 几何和射线相交
- `shapely`(>=2.0.0):2D 几何运算
- `numpy`
- `pvlib`(>=0.10.0):太阳位置计算

**运行环境**:Python 3.9+ / macOS(Leo 的主开发环境)

---

## Spike 具体任务

### Step 1:环境准备(约 5 分钟)

1. 创建一个干净的虚拟环境(venv 或 conda 均可)
2. 安装上述所有依赖
3. 记录:每个库最终安装的版本号、是否遇到编译错误、macOS 上是否需要额外的系统依赖

### Step 2:获取一份真实的 CityJSON 数据(约 5 分钟)

从以下几个公开来源任选一个下载:

- **代尔夫特 3D**:https://3d.bk.tudelft.nl/opendata/cityjson/1.1/ (推荐)
- **Rotterdam LOD1.2**:https://www.cityjson.org/datasets/
- **Helsinki**:https://www.cityjson.org/datasets/

选一个**小于 50MB** 的文件即可,不需要大文件。
把文件保存到脚本同目录,命名为 `sample.cityjson` 或保持原名。

### Step 3:编写 spike 脚本(约 15 分钟)

脚本名:`spike.py`
目标:**100 行以内**,读 CityJSON → 建立 3D 几何 → 计算太阳位置 → 判断一个固定点是否被遮挡

脚本必须依次完成以下步骤,每一步完成后 print 一条确认信息:

```python
# Step A: 读取 CityJSON 文件
# 使用 cjio 加载 sample.cityjson
# print: "Loaded X buildings from CityJSON"

# Step B: 把 CityJSON 的建筑体块转换成 trimesh Mesh 对象
# 提取 LOD1 Solid,拼成一个合并的 trimesh.Trimesh 对象
# print: "Combined mesh: N vertices, M faces"

# Step C: 选一个固定测试点
# 在 CityJSON 数据的地理范围内,选一个看起来会被某栋建筑遮挡的点
# 点高度 z=1.5 米(模拟人眼高度)
# print: "Test point: (x, y, z)"

# Step D: 计算某个固定时刻的太阳位置
# 地点:用 CityJSON 文件对应城市的经纬度(代尔夫特约 52.0°N, 4.36°E)
# 时间:2026-01-20 12:00:00 本地时间(大寒日中午)
# 使用 pvlib.solarposition.get_solarposition
# print: "Sun azimuth: XX°, altitude: YY°"

# Step E: 构造从测试点指向太阳的射线方向
# 根据方位角和高度角,算出单位方向向量
# print: "Ray direction: (dx, dy, dz)"

# Step F: 用 trimesh 判断这条射线是否与建筑群相交
# 使用 mesh.ray.intersects_any(origins=[point], directions=[ray_direction])
# 计时:记录这次相交判定花了多少毫秒
# print: "Shadowed: True/False, ray intersection took X ms"

# Step G: 批量性能测试
# 随机生成 1000 个测试点,都指向同一个太阳方向,批量查询
# 计时:记录 1000 条射线批量查询花了多少毫秒
# print: "Batch 1000 rays took X ms, Y rays/sec"
```

### Step 4:性能粗测(约 3 分钟)

在 Step G 已经做了批量查询。
根据 1000 条射线的耗时,外推 62500 条射线(MVP 典型规模)大约需要多少时间。

### Step 5:撰写技术可行性回执(约 2 分钟)

在脚本同目录创建 `SPIKE_REPORT.md`,包含以下几节:

```markdown
# Sunlit Spike 技术回执

## 1. 环境信息

- Python 版本:
- 操作系统:
- 各依赖库实际安装版本:
  - cjio: 
  - trimesh: 
  - shapely:
  - pvlib:
  - numpy:

## 2. 安装过程

- 是否一次安装成功?
- 是否需要额外的系统依赖(brew install 等)?
- 是否有库之间的版本冲突?

## 3. 数据获取

- 使用的 CityJSON 文件来源:
- 文件大小:
- 文件中的建筑数量:
- CityJSON schema 版本(v1.0 / v1.1 / v2.0):
- 使用的坐标系(CRS):

## 4. 脚本运行结果

- 是否 7 个步骤全部跑通?
- 如果有步骤失败,失败在哪一步,具体错误信息?
- 测试点是否符合"被遮挡"的预期?

## 5. 性能数据

- 单条射线查询耗时:___ ms
- 1000 条射线批量查询耗时:___ ms
- 外推 62500 条射线预估耗时:___ 秒
- 是否满足"30 秒内完成典型 MVP 规模分析"的目标?

## 6. 踩到的坑

列出所有过程中遇到的非 trivial 问题:
- 
- 
- 

## 7. 对 MVP 的技术建议

基于 spike 的经验,对正式 MVP 开发有什么具体建议?
- 
- 

## 8. 最终判断

- [ ] 技术路径完全畅通,可以放心投入 MVP 开发
- [ ] 技术路径基本畅通,但有以下需要注意的点:___
- [ ] 技术路径有严重阻塞,需要重新评估方案。具体阻塞在:___
```

---

## 时间盒(非常重要)

**总预算:30 分钟**。超时后无论做到哪一步,都立即停止并撰写回执。

如果任何单独步骤卡住超过 10 分钟,**记录问题后跳过该步骤继续**,不要死磕。
spike 的价值是**暴露未知风险**,不是**解决所有风险**。

---

## 交付物清单

spike 结束后应该有:

1. `spike.py`(100 行以内的脚本)
2. `sample.cityjson`(使用的测试数据,或说明如何下载)
3. `SPIKE_REPORT.md`(技术可行性回执)
4. `requirements.txt`(实际跑通的依赖版本)

---

## 不要做的事

再重申一次:

- 不要做可视化(不要画图、不要热力图、不要 3D 预览)
- 不要做 AI 摘要(不要调用任何 LLM API)
- 不要做 CLI(不要用 argparse,脚本内硬编码参数就行)
- 不要写单元测试
- 不要做错误处理的完善(直接让异常抛出,暴露问题)
- 不要尝试支持多个 CityJSON 版本
- 不要做坐标系转换(所有运算都在文件原生 CRS 里进行)
- 不要优化性能(除了 Step G 的批量查询,其他都用最朴素写法)

**如果有"这里应该再做一下 X"的冲动,把它记在 SPIKE_REPORT.md 的第 7 节"对 MVP 的技术建议"里,而不是立刻动手**。

---

## 最重要的输出

不是 `spike.py` 本身,而是 `SPIKE_REPORT.md`。

代码能跑通只是第二重要的事。最重要的是**把过程中的所有阻力、惊讶、疑惑如实记录下来**,让 Leo 在决定是否投入 3-4 周 MVP 开发之前,完整掌握技术风险图景。

回执里**负面结果和正面结果同样有价值**。"cjio 读不了某些文件"、"trimesh 在 Apple Silicon 上需要特殊处理"、"pvlib 的时区处理反直觉"——这些都是宝贵的发现,越多越好。
