# Sunlit 项目 DXF 输入路径 Spike 任务

> 目标：在 30 分钟内验证"用户按规范整理的 DXF 文件"能否被可靠解析
> 输出：一个能运行的 Python 脚本 + 一份技术可行性回执
> 这是 Sunlit 项目第二个 spike（第一个是 CityJSON 核心算法验证）

---

## 背景

Sunlit 是一个基于建筑体块数据的地面日照分析工具。经过产品讨论，我们确定了极简的输入策略：

**用户负责把 CAD 总图整理成符合 Sunlit 约定的 DXF 文件，Sunlit 负责解析和分析**。

用户需要按约定做三件事：

1. 把建筑外轮廓（闭合多段线）放到名为 `SUNLIT_BUILDING` 的图层
2. 在每栋建筑附近打一个纯数字文字表示高度（米），放到 `SUNLIT_HEIGHT` 图层
3. 用一个闭合多段线框出评估区域，放到 `SUNLIT_BOUNDARY` 图层

其他所有内容（道路、绿化、标注、图框）用户自行删除或忽略。

**本 spike 的目标**：验证 `ezdxf` 库能否可靠地从这种约定的 DXF 中提取出我们需要的三要素。

---

## 纪律（必读）

- ❌ 不要实现日照计算、不要调用 AI、不要做 CLI、不要做可视化（matplotlib 的简单散点图除外，用于肉眼核验）
- ❌ 不要尝试兼容"不规范"的 DXF（那不是 spike 的目的）
- ❌ 遇到问题不要花超过 10 分钟死磕，记录在回执里继续
- ✅ 只测试"约定明确的 DXF 能否被正确读懂"这一件事
- ✅ 过程中的所有阻力、版本问题、API 怪异之处，全部记录

---

## 技术栈

- `ezdxf`（>=1.0.0）：Python 的 DXF 读写库
- `matplotlib`（仅用于 spike 的肉眼验证绘图）
- `shapely`（用于判断"高度文字"落在哪栋建筑里）

**运行环境**：Python 3.9+ / macOS

---

## Spike 具体任务

### Step 1：环境准备（约 3 分钟）

1. 创建干净的虚拟环境
2. 安装 `ezdxf`、`matplotlib`、`shapely`
3. 记录版本号和安装过程中的任何异常

### Step 2：生成一份符合规范的测试 DXF（约 8 分钟）

**不要去找真实 CAD 图纸**——真实图纸的杂质会淹没 spike 的验证目标。

用 `ezdxf` 直接**写出**一份符合 Sunlit 约定的测试 DXF，命名 `test_sunlit.dxf`。内容：

**3 栋建筑**（放在 `SUNLIT_BUILDING` 图层）：

- 建筑 A：矩形，左下角 (0, 0)，右上角 (30, 15)
- 建筑 B：矩形，左下角 (50, 0)，右上角 (70, 25)
- 建筑 C：L 形多边形（自己构造合理坐标），位于 (0, 30) 附近区域

**3 个高度文字**（放在 `SUNLIT_HEIGHT` 图层）：

- 在建筑 A 内部（大约 (15, 7)）打文字 `"18"`
- 在建筑 B 内部（大约 (60, 12)）打文字 `"54"`
- 在建筑 C 内部（选合适点）打文字 `"24"`

**1 个评估区域**（放在 `SUNLIT_BOUNDARY` 图层）：

- 一个包含上述 3 栋建筑的大矩形，比如 (-10, -10) 到 (80, 60)

**额外的干扰项**（故意加入，测试 spike 是否能正确忽略）：

- 在 `0` 图层（默认图层）随便画几条线或一个矩形
- 在 `ANNOTATIONS` 图层打一些文字如"北向"、"比例 1:500"
- 加一个图框（矩形加文字）

Spike 脚本必须正确忽略这些干扰项。

**保存 DXF 为 R2010 版本**（`doc.saveas("test_sunlit.dxf")`，ezdxf 默认就可以）。

### Step 3：编写 spike 解析脚本（约 15 分钟）

脚本名：`spike_dxf.py`
目标：**150 行以内**，从 `test_sunlit.dxf` 中提取三要素。

脚本必须完成以下步骤，每一步 print 确认信息：

```python
# Step A: 打开 DXF 文件
# import ezdxf; doc = ezdxf.readfile("test_sunlit.dxf")
# print 文件的 DXF 版本 和 总图层数

# Step B: 列出所有图层名
# print: "Layers: [...]"
# 确认 SUNLIT_BUILDING、SUNLIT_HEIGHT、SUNLIT_BOUNDARY 都在列表中

# Step C: 提取建筑轮廓
# 从 modelspace 中筛选 layer == "SUNLIT_BUILDING" 的 LWPolyline 实体
# 对每个实体:
#   - 确认 is_closed 为 True（若不是,记录警告但继续）
#   - 提取所有顶点坐标 (x, y)
# 输出: print 每栋建筑的顶点数和 Shapely Polygon 的 area
# 预期: 找到 3 栋建筑,面积分别约 450、500、和 L 形建筑的面积

# Step D: 提取高度文字
# 从 modelspace 中筛选 layer == "SUNLIT_HEIGHT" 的 Text 或 MText 实体
# 对每个实体:
#   - 提取 text 内容和 insert 位置
#   - 尝试 float(text),若失败记录并跳过
# 输出: print 每个高度文字的值和位置
# 预期: 找到 3 个高度文字,值分别为 18.0、54.0、24.0

# Step E: 高度与建筑的匹配
# 对每个高度文字,判断它的位置落在哪个建筑的 Shapely Polygon 内
# (用 shapely 的 contains 方法)
# 若落在某个建筑内,把该高度赋给该建筑
# 若不落在任何建筑内(用户可能把文字打在建筑外),退化为找最近的建筑
# 输出: print 每栋建筑及其匹配到的高度
# 预期: 3 栋建筑都有正确的高度

# Step F: 提取评估区域
# 从 modelspace 中筛选 layer == "SUNLIT_BOUNDARY" 的 LWPolyline 实体
# 确认只有一个(若多个,取第一个并警告)
# 提取顶点
# 输出: print 评估区域的顶点数和面积

# Step G: 确认正确忽略了干扰项
# 统计 modelspace 中 layer 不属于三个 SUNLIT_* 图层的实体数量
# 确认 spike 脚本完全没有读这些实体
# 输出: print "Ignored N entities on non-Sunlit layers"

# Step H: 肉眼验证(用 matplotlib 绘图)
# 画一张简单的 2D 图:
#   - 灰色填充: 评估区域
#   - 蓝色描边: 每栋建筑轮廓
#   - 红色文字: 每栋建筑的高度(标在建筑中心)
# 保存为 spike_dxf_preview.png
# 目的: 让 Leo 肉眼确认解析结果正确
```

### Step 4：边界测试（约 5 分钟）

生成一份**故意有问题**的 DXF `test_broken.dxf`，包含：

- 一个未闭合的多段线在 `SUNLIT_BUILDING` 图层
- 一个高度文字内容不是数字（如 `"18F"`）
- 高度文字位置落在所有建筑之外

用 spike 脚本解析它，确认：

- 未闭合的 polyline 被识别但产生明确的警告
- 非数字的高度文字被跳过并警告
- 位置不在建筑内的文字能通过"最近匹配"逻辑正确归属，或给出明确警告

**不要试图修复这些问题，只要求脚本能"明确报告问题"而不是崩溃**。

### Step 5：撰写技术可行性回执（约 3 分钟）

创建 `SPIKE_DXF_REPORT.md`：

```markdown
# Sunlit DXF Spike 回执

## 1. 环境信息

- Python 版本：
- 操作系统：
- 依赖实际版本：
  - ezdxf：
  - matplotlib：
  - shapely：

## 2. 安装过程

- 是否一次成功？
- 是否有任何平台相关的问题？

## 3. 脚本运行结果

### 正常流程（test_sunlit.dxf）
- [ ] Step A 通过
- [ ] Step B 通过
- [ ] Step C 通过，正确识别 3 栋建筑
- [ ] Step D 通过，正确识别 3 个高度文字
- [ ] Step E 通过，高度正确匹配到建筑
- [ ] Step F 通过，识别评估区域
- [ ] Step G 通过，正确忽略干扰项
- [ ] Step H 的图片在视觉上正确

### 异常流程（test_broken.dxf）
- [ ] 未闭合 polyline 被正确报警
- [ ] 非数字高度文字被正确跳过
- [ ] 位置错误的文字处理得当

## 4. ezdxf API 的使用观察

- 哪些 API 用起来顺手？
- 哪些 API 反直觉或文档不足？
- 对 LWPolyline 的顶点读取有没有坑？
- Text 和 MText 处理是否统一？（DXF 里文字有多种实体类型）

## 5. 踩到的坑

列出所有过程中遇到的非 trivial 问题。

## 6. 对 MVP 的技术建议

- DXF 解析模块的架构建议：
- "高度文字与建筑匹配"的策略是否合理？有什么更好的想法？
- 错误提示应该细化到什么程度？

## 7. 真实 CAD 图纸的风险预估

Spike 使用的是"ezdxf 生成的干净 DXF"。预估一下，当用户从真实 AutoCAD 导出时，可能出现哪些意料之外的问题？
（例如：中文图层名、TrueType 字体文字、块参照 BLOCK 包装的建筑、不同 DXF 版本的兼容性……）

## 8. 最终判断

- [ ] 技术路径完全畅通，可以把 DXF 定为 MVP 主输入
- [ ] 技术路径可行，但有以下需要提前约束：___
- [ ] 技术路径有阻塞，建议回退到 GeoJSON 或 CityJSON 作为主输入。阻塞在：___
```

---

## 时间盒

**总预算：30 分钟**。超时立即停止撰写回执。

单步卡住超过 10 分钟，记录后跳过。

---

## 交付物清单

1. `spike_dxf.py`（150 行以内的 spike 脚本）
2. `generate_test_dxf.py`（生成测试 DXF 的辅助脚本）
3. `test_sunlit.dxf` 和 `test_broken.dxf`（测试用 DXF）
4. `spike_dxf_preview.png`（肉眼验证图）
5. `SPIKE_DXF_REPORT.md`（技术可行性回执）
6. `requirements.txt`

---

## 不要做的事

- 不要处理真实 CAD 图纸（用 ezdxf 生成的测试 DXF 就够）
- 不要做日照计算（那是主 MVP 的事）
- 不要实现 GUI 或 CLI
- 不要优化性能
- 不要兼容任何非 Sunlit 约定的图层命名
- 不要处理块参照（BLOCK / INSERT）——MVP 不支持用户用块来包装建筑
- 不要处理曲线（Arc / Spline）——MVP 只支持多段线
- 不要处理 3D 实体——MVP 只从 2D footprint + 高度数字构建 3D

这些限制**不是因为未来不需要**，而是因为 **spike 的目的是验证"最简路径是否通畅"**。任何复杂情况都应该在 `SPIKE_DXF_REPORT.md` 第 7 节的"风险预估"里讨论，而不是在 spike 代码里实现。

---

## 最重要的输出

**不是 `spike_dxf.py`，而是 `SPIKE_DXF_REPORT.md` 的第 7 节和第 8 节**。

- 第 7 节"真实 CAD 图纸的风险预估"：这决定 MVP 开发时需要提前准备哪些 "用户教育" 和 "错误处理" 工作
- 第 8 节"最终判断"：直接影响 Leo 是否把 DXF 定为 MVP 主输入

其他步骤都是为这两节服务的。

Spike 的目的是**用 30 分钟换取对 3-4 周 MVP 的信心**。如果这个 spike 暴露了严重问题（比如 ezdxf 在 macOS 上装不上、中文 layer 名处理有坑），Leo 需要在投入大量工作前知道，并重新设计方案。
