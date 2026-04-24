# Lumen 算子开发文档：`cityjson-sunlight`

> 目标读者：vibe coding 助手（执行层）+ Leo（产品审阅）
> 文档版本：v0.2（明确了计算类型的边界，避免与专业报建软件混淆）
> 最后更新：2026-04-24
> 关联文档：`lumen-ifc-diff-operator.md`（同一垂直算子系列的第一个算子）

---

## 第一部分：产品叙事

### 1.1 这个算子解决的问题

日照分析是中国建筑项目**绕不开的强制性内容**：

- **前期阶段**：判断场地本身被周边遮挡的情况，影响方案定位和业态选择
- **方案阶段**：核算自己的体块会不会遮挡周边已有住宅、学校、医院
- **报建阶段**：必须提供日照分析报告，证明符合《城市居住区规划设计标准》GB 50180 以及各地方日照间距规定

当前行业现状：

- **主流做法一：众智日照、天正日照、斯维尔日照** ——专业但封闭。单机授权数千到上万元，学习曲线陡峭，界面停留在 2010 年代水平，且只能在 Windows 的 AutoCAD 上跑。
- **主流做法二：Rhino + Ladybug/Ladybug Tools** ——灵活但门槛极高。建筑师要会 Grasshopper，要理解气象数据格式（EPW），要自己处理周边体块建模。实际能用的建筑师不到 5%。
- **主流做法三：SketchUp + 插件** ——精度和严谨性不足以用于报建。

结果是：**日照分析这件在逻辑上很确定的计算任务，在实践中变成了专业软件厂商的垄断领地**。大部分建筑师要么外包给专门做日照分析的咨询公司（单项目几千到几万元），要么在设计院内部依赖少数会用专业软件的人。

**AI 时代这种垄断没有技术理由继续存在**。日照计算本质是：

```
太阳方位角 + 高度角（可精确计算）
+ 遮挡体几何（CityJSON 中的 LOD1 体块足够）
+ 被评估点位（红线内的网格或窗口位置）
= 投射几何运算（纯数学）
```

所有部分都是开放、公开、标准化的。缺的只是**一个建筑师真正能用、且能被 AI 工作流调用的工具**。

### 1.2 计算类型与边界（重要）

"日照分析"在建筑行业不是**一种**计算，而是**一组**完全不同的计算。它们的用户、输入、输出、精度要求都不同。开发前必须明确本算子做哪一种、不做哪一种，否则容易陷入"什么都想做、什么都做不好"的陷阱，也容易让用户误以为这是一个能替代报建软件的工具。

**日照分析的主要类型**：

| 类型 | 计算对象 | 典型用途 | 数据需求 |
|------|---------|---------|---------|
| ① 点位日照时长 | 单个点在指定日期的受晒时长 | 窗台/室外座椅评估 | 体块 LOD1 |
| ② **地面网格日照** | 场地地面切网格，每个格点的日照时长 | 景观布置、场地前期、方案自评 | 体块 LOD1 |
| ③ 建筑表面日照 | 建筑立面/屋顶切网格 | 光伏、热工、开窗策略 | 表面几何 LOD2+ |
| ④ 窗口满窗日照 | 每扇窗"整窗同时受晒"的最长连续时间 | 中国居住建筑报建核心指标 | 窗户信息（LOD1 无法满足） |
| ⑤ 阴影范围 | 指定时刻的地面阴影轮廓 | 规划示意图、可视化演示 | 体块 LOD1 |
| ⑥ 全年累计日照 | 8760 小时累计或年辐射量 | 光伏、被动式、LEED | 气象数据（EPW） |

**本 MVP 聚焦做类型 ②：地面网格日照**。

**为什么是类型 ②**：

- **数据前提匹配**：CityJSON LOD1（体块）就足够，与用户自带数据的能力范围一致
- **用户群清晰**：景观师、场地设计师、地产前期团队、做方案自评的建筑师——这些人当前没有好用的轻量工具（众智主打住宅报建、Ladybug 门槛过高）
- **不受规范绑架**：不涉及 GB 50180 的合规判定，不承担法律风险，设计阶段参考足矣
- **输出直观**：热力图视觉效果强，AI 摘要价值清晰，演示友好
- **架构可扩展**：为类型 ①（点位）留接口但不开发；类型 ③④ 留给未来更高 LOD 数据支持后的新算子

**本 MVP 明确不做的事**（也是产品定位的一部分，用于管理用户期待）：

- ❌ **不做类型 ④（窗口满窗日照）**：这是中国居住建筑报建的核心指标，涉及 GB 50180 的合规判定。报建级精度需要窗户几何信息、可能涉及法律责任——留给专业软件（众智、天正、斯维尔）。用户若需报建，请继续使用专业软件。
- ❌ **不做类型 ③（建筑表面日照）**：涉及 BIPV、被动式设计领域，用户画像和工具链不同，属于未来独立算子。
- ❌ **不做类型 ⑥(全年累计/辐射量）**：需要气象数据（EPW）+ 大气辐射模型，属于 Ladybug 的地盘，MVP 不涉足。
- ❌ **不做专业级日照阴影分析动画**：类型 ⑤ 可作为副产品（某一时刻的阴影多边形），但不是核心输出。

**预留接口但不开发**：

- `evaluation_points` 参数：允许用户传入自定义点位（GeoJSON 点集合），按类型 ① 的逻辑计算每个点的日照时长。MVP 保留接口定义，**但不实现**——调用时返回"Not implemented in MVP"提示。这是为未来扩展留路径，同时避免用户误以为可以用于"窗口日照评估"。

**对用户的明确沟通**：

在 README 和算子运行完的报告底部都应该有一段明确提示：

> **本工具的定位**：面向设计阶段的参考工具，帮助建筑师快速理解场地的日照分布特征。**不用于报建**。如需用于居住建筑报建或法律用途的满窗日照分析，请使用专业日照软件（众智、天正、斯维尔等）。

### 1.3 关键产品洞察：用户自带两种 CityJSON

这是本算子区别于任何现有日照软件的**核心设计决策**。

大部分人想到 CityJSON，第一反应是"政府公开数据"——于是担心"中国城市没几个开放数据集，做了也没人能用"。这个担心在"纯周边分析"的场景下成立，但**不成立于本算子的设计**。

本算子接受两种 CityJSON 输入，并且**任一种都可以独立使用**：

**类型 A：周边环境 CityJSON**
- 来源：政府公开数据、OSM + 高度推算、倾斜摄影导出、用户手动在 Rhino/SketchUp 里搓的周边体块
- 内容：项目周边的现状建筑、地形、其他环境要素
- 作用：判断**周边对我的遮挡**

**类型 B：方案体块 CityJSON**
- 来源：**用户自己的设计方案**。Rhino、SketchUp、Revit、Blender 都能导出体块，经过 `cjio` 或简单的 Python 脚本转换成 CityJSON
- 内容：待评估的建筑设计方案
- 作用：判断**我对周边的遮挡**，或**我自己各部分之间的自遮挡**

**战略含义**：

即便用户**没有任何周边环境数据**，只要他有自己的设计方案，这个算子就能用——用于分析方案内部的自遮挡（如 L 型住宅一翼对另一翼的遮挡、塔楼对裙房屋顶花园的遮挡、连廊对庭院的影响）。

即便用户**没有复杂的设计方案**，只要他有一块地 + 周边数据，这个算子也能用——用于前期场地评估。

**两种数据都有时，才是完整的日照报告场景**。但只有一种也能独立产生价值，**这让算子对"数据稀缺"的耐受度大幅提升**，不再依赖政府开放数据的可得性。

### 1.4 最终用户体验

**场景一：方案自评地面影响（最高频）**

建筑师小张刚画完一个住宅小区方案。他在 Rhino 里选中所有楼栋，用 `Export Selected` 导出 OBJ。Lumen 提供的脚本把 OBJ + 每栋楼的层高属性转成 `scheme.cityjson`。

在 Lumen Canvas 上：
1. 拖入 `scheme.cityjson`（方案体块）
2. 拖入 `site-boundary.geojson`（场地红线）
3. 连接到 `cityjson-sunlight` 算子
4. 配置纬度和评估日期（默认大寒日 9:00-15:00），网格大小 2 米
5. 运行

输出：
- 红线内地面的有效日照时长热力图（颜色越深代表日照时间越长）
- 统计摘要：达标面积占比（如"日照 ≥ 2 小时的地面面积占 78%"）、主要遮挡源排序
- AI 生成的摘要："方案内院受 1# 楼遮挡严重，大寒日下午 1 点后整体进入阴影。东南侧人行入口区域全天日照条件良好，适合做公共活动空间。若希望中央庭院日照改善，建议将 1# 楼西移或降低层数。"

**场景二：场地前期评估（中频）**

建筑师小李拿到一块地，还没有方案。周边有 OSM 数据（国内质量不高但聊胜于无）加上他用倾斜摄影模型手动提取的几栋高层。Lumen 脚本把这些转成 `context.cityjson`。

在 Canvas 上：
1. 拖入 `context.cityjson`（仅周边，无方案）
2. 拖入 `site.geojson`（红线）
3. 连接到 `cityjson-sunlight`
4. 运行

输出：
- 空场地的日照潜力热力图（哪些位置有多少日照）
- AI 摘要："场地西北角受 200 米外 80 米高层遮挡，大寒日下午 2 点后进入阴影。东南约 2/3 区域全天日照条件良好，适合布置主要功能用房。"

**场景三：方案对周边的影响参考（低频）**

项目方案阶段想初步了解对北侧现状住宅的遮挡情况（**注意：不是报建用途**）。建筑师既有方案体块，也用 GeoJSON 快速画了周边现状住宅的 footprint + 高度。

在 Canvas 上：
1. 拖入 `scheme.cityjson`（自己的方案）
2. 拖入 `context.cityjson`（周边现状住宅）
3. 拖入 `affected-area.geojson`（想评估的周边地面区域，如现状住宅南侧地面）
4. 连接到 `cityjson-sunlight`
5. 运行

输出：
- 周边评估区域的地面日照热力图，显示方案投下的额外阴影分布
- AI 摘要："方案的 1# 楼对北侧现状住宅南侧地面产生额外遮挡，主要影响范围在大寒日 12:00-14:00。若需用于正式报建，请使用专业日照软件做满窗日照核验。"

**三个场景共用同一个算子的同一种计算（地面网格日照）**，只是输入组合不同。这是 MVP 保持简单的关键——不为不同场景做不同功能，而是提供一种通用能力让建筑师自己组合。

### 1.5 MVP 范围

**计算类型**：仅做类型 ② 地面网格日照（见 1.2 节）。不做其他任何类型。

| 功能模块 | MVP 必须 | 接口保留但不开发 | 后续版本 |
|---------|---------|---------|---------|
| CityJSON 解析 | ✅ LOD1 体块（建筑 footprint + 高度） | — | LOD2/LOD3 |
| 太阳位置计算 | ✅ 基于经纬度、日期、时刻的精确方位角/高度角 | — | 考虑大气折射 |
| 遮挡判定 | ✅ 射线相交法 | — | — |
| 时间维度 | ✅ 单日多时刻（如大寒日 9:00-15:00） | — | 多日对比、全年累计 |
| 评估对象 | ✅ 红线内地面网格 | `evaluation_points` 自定义点位参数（见 2.3） | 建筑立面、屋顶表面 |
| 输出形态 | ✅ Markdown 报告 + PNG 热力图 + JSON 原始数据 | — | 交互式 HTML、报建级图纸 |
| AI 摘要 | ✅ 中文自然语言分析 | — | 规范条款引用、优化方向 |
| 输入数据辅助 | ✅ `obj-to-cityjson`、`geojson-to-cityjson` 两个 helper 脚本 | — | OSM 导入、Revit 直连 |

**明确不在 MVP 范围（且近期不考虑）**：

- ❌ **窗口满窗日照（类型 ④）**：报建级指标，涉及 GB 50180 合规判定，留给专业软件
- ❌ **建筑表面日照（类型 ③）**：光伏/被动式设计场景，未来独立算子
- ❌ **全年累计日照 / 年辐射量（类型 ⑥）**：需要气象数据和辐射模型，Ladybug 地盘
- ❌ 风环境、天空开阔度、视线等其他城市尺度分析（独立算子）
- ❌ 植被、玻璃幕墙反射等二次效应
- ❌ 国标规范的完整内置判定（仅接受用户配置数值阈值）

**关于 `evaluation_points` 参数的特别说明**：

- `skill.yaml` 和 `scripts/analyze.py` 的签名中**保留**此参数
- 调用时检测到此参数非空，直接返回"Not implemented in MVP. This interface is reserved for future point-level analysis."
- **不要实现**点位日照计算逻辑，即使它看起来只是"地面网格的简化版"
- 理由：避免用户误以为可以用于窗口日照评估；保持 MVP 聚焦

### 1.6 为什么这是 Lumen 的算子

和 `ifc-diff` 同构的理由：

- **Canvas 作为工作流编排界面**：日照分析很少是孤立的，它往往要和场地区位、方案变更、规范核查联动。Canvas 让这些连接可视化
- **Light Skills 作为算子封装**：`cityjson-sunlight` 和 `ifc-diff`、未来的 `cityjson-view-corridor`、`cityjson-svf` 共享同一套调用和缓存机制
- **Memory Index 作为项目档案**：方案迭代过程中每一次日照分析都是一个节点，可被未来的 AI 追问（"上周那版方案和这周的日照差异在哪里？"）
- **AI 叙事层通用**：所有垂直算子共享同一个 LLM adapter，保持语气和格式的一致性

更关键的战略意义：**IFC diff 证明 Lumen 能处理单体建筑，cityjson-sunlight 证明 Lumen 能处理城市尺度**。两者共同建立起 "Lumen = 建筑师的跨尺度项目大脑" 这个独特定位。

---

## 第二部分：技术规格

### 2.1 架构决策

**运行方式：Python 子进程调用**（与 `ifc-diff` 保持一致）

**核心依赖**：

- `cjio`：CityJSON 官方 Python 库，解析和几何操作
- `shapely`：2D 几何运算（红线、投影、相交）
- `numpy`：网格化和矩阵运算
- `pvlib`：太阳位置计算（比自己写公式更可靠，已经过学术验证）
- `matplotlib`：热力图输出
- `trimesh`（可选，用于 LOD1 体块的射线相交加速）

**不使用**：
- 不引入任何 GIS 专业软件（QGIS、ArcGIS）的依赖
- 不使用 Ladybug/Honeybee（太重，且依赖 Rhino）
- 不使用 Three.js 或前端渲染（MVP 不做 3D 可视化）

### 2.2 文件结构

```
lumen/
├── skills/
│   └── cityjson-sunlight/
│       ├── skill.yaml
│       ├── README.md
│       ├── scripts/
│       │   ├── analyze.py          # 主算子入口
│       │   ├── sun_position.py     # 太阳位置计算
│       │   ├── geometry.py         # CityJSON → 几何体 + 射线相交
│       │   ├── grid.py             # 红线网格化
│       │   ├── render.py           # matplotlib 热力图
│       │   ├── requirements.txt
│       │   └── __init__.py
│       ├── helpers/                # 辅助转换脚本,面向用户
│       │   ├── obj_to_cityjson.py  # Rhino/SketchUp OBJ → CityJSON
│       │   ├── geojson_to_cityjson.py  # footprint + 高度 → CityJSON
│       │   └── README.md
│       ├── prompts/
│       │   └── summary.md
│       ├── schemas/
│       │   └── analysis-result.json
│       ├── templates/              # 输入数据示例
│       │   ├── sample-site.geojson
│       │   ├── sample-context.cityjson
│       │   └── sample-scheme.cityjson
│       └── tests/
│           ├── fixtures/
│           └── test_analyze.py
```

### 2.3 Light Skill 定义（skill.yaml）

```yaml
name: cityjson-sunlight
version: 0.1.0
category: architecture
display_name: "日照分析（CityJSON）"
display_name_en: "Sunlight Analysis (CityJSON)"
description: |
  基于 CityJSON 体块数据进行地面网格日照分析。支持三种使用模式：
  1. 场地前期评估（仅周边环境 + 红线）
  2. 方案自评（仅方案体块 + 红线，含自遮挡）
  3. 方案对周边影响参考（方案 + 周边 + 评估区域）
  
  本算子仅做地面日照时长计算，不做窗口满窗日照、建筑表面日照、年累计辐射等。
  不用于居住建筑报建或法律用途——如需报建级分析，请使用专业软件。

inputs:
  - name: scheme_cityjson
    type: file
    accept: [".cityjson", ".json"]
    required: false
    display_name: "方案体块"
    description: "待评估的设计方案 CityJSON。可选——不提供则仅做场地前期评估。"
  - name: context_cityjson
    type: file
    accept: [".cityjson", ".json"]
    required: false
    display_name: "周边环境"
    description: "项目周边的现状建筑、地形。可选——不提供则不考虑外部遮挡。"
  - name: site_boundary
    type: file
    accept: [".geojson", ".json"]
    required: true
    display_name: "评估区域"
    description: "要计算日照时长的地面区域边界（通常是场地红线，也可以是场地外的地面区域）。"
  - name: evaluation_points
    type: file
    accept: [".geojson", ".json"]
    required: false
    display_name: "评估点位（MVP 不实现）"
    description: |
      自定义评估点（GeoJSON 点集合）。
      ⚠️ MVP 阶段此接口保留但不实现：检测到非空值时直接返回 "Not implemented in MVP" 错误。
      保留此接口是为未来点位级分析扩展，不代表可以用于窗口日照评估。
  - name: config
    type: object
    required: true
    schema:
      latitude:
        type: number
        description: "场地纬度（十进制度数）"
      longitude:
        type: number
        description: "场地经度（十进制度数）"
      date:
        type: string
        format: date
        default: "2026-01-20"  # 大寒日
      time_range:
        type: array
        items: { type: string }
        default: ["09:00", "15:00"]
      time_step_minutes:
        type: integer
        default: 15
      min_sunlight_hours:
        type: number
        default: 2.0
        description: "满足日照的最低小时数（用于判定合格面积）"
      grid_size_meters:
        type: number
        default: 2.0
        description: "评估网格的边长"
      language:
        type: string
        enum: ["zh", "en"]
        default: "zh"

outputs:
  - name: report
    type: markdown
    display_name: "日照分析报告"
  - name: heatmap
    type: image
    format: png
    display_name: "日照时长热力图"
  - name: raw_data
    type: json
    display_name: "结构化分析数据"
    schema_ref: "schemas/analysis-result.json"

execution:
  runtime: python
  entry: scripts/analyze.py
  timeout_seconds: 300

requirements:
  python: ">=3.9"
  packages:
    - "cjio>=0.9.0"
    - "shapely>=2.0.0"
    - "numpy>=1.24.0"
    - "pvlib>=0.10.0"
    - "matplotlib>=3.7.0"
    - "trimesh>=4.0.0"

extension_points:
  additional_analyses:
    description: "后续可挂载视线、风环境、SVF 等其他城市分析算子"
    signature: "(geometry_cache: GeometryCache, config: dict) -> AnalysisResult"

ui:
  icon: "sun"
  color: "#E8A44C"  # 日照主题的暖色
  canvas_node_template: "templates/sunlight-node.html"
```

### 2.4 核心算法

**数据结构**：

```python
from typing import TypedDict, Literal, Optional

class SunPosition(TypedDict):
    timestamp: str         # ISO 格式
    azimuth: float         # 方位角（度，北为 0，顺时针）
    altitude: float        # 高度角（度，地平为 0）

class EvaluationPoint(TypedDict):
    x: float
    y: float
    z: float
    sunlit_minutes: float  # 总受晒时长
    sunlit_intervals: list[tuple[str, str]]  # 连续受晒时段
    meets_threshold: bool  # 是否满足 min_sunlight_hours

class AnalysisResult(TypedDict):
    metadata: dict
    summary: dict
    sun_positions: list[SunPosition]
    evaluation_points: list[EvaluationPoint]
    grid_bounds: dict      # 热力图的地理边界
    statistics: dict       # 合格率、最小最大时长等
```

**核心流程**：

```python
def analyze(inputs: dict, config: dict) -> AnalysisResult:
    # 1. 加载几何
    obstacles = []
    if inputs.get("context_cityjson"):
        obstacles.extend(load_cityjson_as_meshes(inputs["context_cityjson"]))
    if inputs.get("scheme_cityjson"):
        obstacles.extend(load_cityjson_as_meshes(inputs["scheme_cityjson"]))
    
    # 2. 构建红线内评估网格
    boundary = load_geojson_polygon(inputs["site_boundary"])
    if inputs.get("evaluation_points"):
        eval_points = load_custom_points(inputs["evaluation_points"])
    else:
        eval_points = generate_grid_inside(
            boundary, 
            spacing=config["grid_size_meters"]
        )
    
    # 3. 计算时间序列内的太阳位置
    sun_positions = compute_sun_positions(
        latitude=config["latitude"],
        longitude=config["longitude"],
        date=config["date"],
        start_time=config["time_range"][0],
        end_time=config["time_range"][1],
        step_minutes=config["time_step_minutes"],
    )
    
    # 4. 对每个评估点 × 每个时刻做射线相交判定
    results = []
    for pt in eval_points:
        sunlit_slots = []
        for sun in sun_positions:
            ray_direction = sun_vector_from(sun["azimuth"], sun["altitude"])
            if not any_intersection(pt, ray_direction, obstacles):
                sunlit_slots.append(sun["timestamp"])
        
        results.append(EvaluationPoint(
            x=pt.x, y=pt.y, z=pt.z,
            sunlit_minutes=len(sunlit_slots) * config["time_step_minutes"],
            sunlit_intervals=compress_to_intervals(sunlit_slots),
            meets_threshold=len(sunlit_slots) * config["time_step_minutes"] 
                            >= config["min_sunlight_hours"] * 60,
        ))
    
    # 5. 统计 + 生成热力图 + 组装报告
    return assemble_result(results, sun_positions, config)
```

**性能关键点**：

- 射线与建筑的相交判定用 `trimesh` 的 BVH 加速结构（`ray.intersects_any`）
- 所有评估点 × 所有时刻的遍历可以向量化（一次性生成所有射线，批量相交）
- 典型规模：100m × 100m 地块，2m 网格 ≈ 2500 个评估点；大寒日 9-15 点 15 分钟步长 ≈ 25 个时刻。总计 62,500 次射线测试，在普通笔记本上应在 30 秒内完成

### 2.5 输入数据辅助脚本（关键产品决策）

**重要**：MVP 必须交付两个 helper 脚本，否则用户拿不到 CityJSON 数据，算子就没法用。

**helper 脚本 1：`obj_to_cityjson.py`**

接受 Rhino/SketchUp/Blender 导出的 OBJ 文件和一个配置 JSON，输出 CityJSON。

```bash
python helpers/obj_to_cityjson.py \
    --obj scheme.obj \
    --meta meta.json \
    --output scheme.cityjson
```

`meta.json` 示例：

```json
{
  "crs": "EPSG:4326",
  "origin": {"lat": 39.9042, "lon": 116.4074, "elevation": 0},
  "buildings": [
    {"obj_group": "Building_A", "name": "1号楼", "floors": 18, "floor_height": 3.0},
    {"obj_group": "Building_B", "name": "2号楼", "floors": 6, "floor_height": 3.3}
  ]
}
```

该脚本：
- 读取 OBJ 中的每个 group / mesh 作为一栋建筑
- 按 `meta.json` 赋予名称、高度等属性
- 转换到 CityJSON 的 LOD1 结构
- 处理坐标系转换（OBJ 的局部坐标 → CityJSON 要求的地理坐标）

**helper 脚本 2：`geojson_to_cityjson.py`**

用户用 QGIS 或手绘 GeoJSON 画了建筑 footprint，每个 feature 带 `height` 属性，脚本自动 extrude 成 LOD1 体块。

```bash
python helpers/geojson_to_cityjson.py \
    --input buildings.geojson \
    --height-field height \
    --output context.cityjson
```

这两个脚本是**降低使用门槛的关键**。没有它们，用户面对 CityJSON 三个字会直接劝退。

### 2.6 AI 摘要生成

**Prompt 模板（prompts/summary.md）**：

```markdown
你是一位资深建筑师，正在帮建筑师同事审阅一份地面日照分析结果。

# 分析类型说明

本次分析计算的是**地面网格上每一点在指定日期的有效日照时长**。
不是窗口满窗日照、不是建筑立面日照、不是年累计辐射，仅限于地面。
结果用于设计阶段参考，不用于报建或法律判定。

# 输入数据

**分析模式**：{mode}  # "场地前期评估" / "方案自评" / "方案对周边影响参考"
**项目位置**：纬度 {lat}，经度 {lon}
**评估日期**：{date}（{date_name}，如"大寒日"）
**评估时段**：{start_time} - {end_time}
**达标阈值**：地面点日照 ≥ {min_sunlight_hours} 小时视为达标（用户自定义）

**统计结果**：
- 评估点位总数：{total_points}
- 达标点位：{qualified_points}（{qualified_pct}%）
- 达标面积：约 {qualified_area} m²
- 最大日照时长：{max_hours} 小时
- 最小日照时长：{min_hours} 小时
- 平均日照时长：{avg_hours} 小时

**空间分布特征**：
{spatial_patterns_json}
（包括：哪个方位的地面受影响最严重、主要遮挡源是哪栋建筑、等等）

# 你的任务

用建筑师熟悉的语言，生成一份简洁的 Markdown 日照分析摘要。要求：

1. **开篇用 1-2 句说清楚总体情况**（地面达标面积占比、主要遮挡方位）
2. **指出主要问题区域**（方位 + 受影响程度 + 主要遮挡源建筑）
3. **提出可行的改进方向**（降低某建筑高度、调整位置、改变朝向等）
4. **结尾提醒用户本分析的定位和局限**：如用户明显在准备报建材料，提示使用专业软件
5. 避免 AI 腔，语气专业克制
6. 不要使用"合规""符合规范""满足国标"等判定性表述

# 输出格式

```markdown
## 地面日照分析摘要

[2-3 句总体情况]

### 达标情况
[定量描述：达标面积、占比、最小/最大时长]

### 主要问题区域
[按严重程度列出 2-3 个问题区域]

### 改进方向
[2-3 条可操作的建议]

### 分析局限
[提示：本分析为地面日照参考，不含窗口满窗、表面辐射等。如需报建，请用专业软件。]
```
```

### 2.7 Canvas 集成

**节点形态**（复用 `ifc-diff` 的模式）：

- CityJSON 文件节点、GeoJSON 文件节点：标准文件节点
- `cityjson-sunlight` 算子节点：有多个输入孔（两个 CityJSON、两个 GeoJSON），一个配置参数区，三个输出孔（report/heatmap/raw_data）
- 热力图输出节点：特殊的图片节点，点击可放大查看

**交互增强**：

- 算子配置面板内置"快速预设"按钮：
  - "北京 · 大寒日 · 2 小时"
  - "上海 · 大寒日 · 2 小时"
  - "广州 · 冬至日 · 1 小时"
  - 等等
- 用户一键选中，算子自动填入纬度、日期、规范阈值

这是一个很小但很重要的产品细节——降低建筑师查阅规范的成本。

### 2.8 扩展点

`skill.yaml` 中声明的 `additional_analyses` 钩子意味着：

- `cityjson-view-corridor`（视线分析）可以复用本算子加载的几何
- `cityjson-svf`（天空开阔度）同上
- `cityjson-noise`（噪声初估）同上

所有城市尺度算子共享一个 `GeometryCache` 对象，避免重复加载大文件。这是 Lumen 垂直算子生态的一个关键架构决策。

### 2.9 测试要求

**单元测试**：

- `test_sun_position_accuracy`：对已知日期/地点的太阳位置，与 NOAA 公开数据对比，误差 < 0.5 度
- `test_ray_intersection`：单个建筑挡单个点，验证遮挡判定正确
- `test_grid_inside_boundary`：凹形红线也能正确生成内部网格
- `test_no_context_mode`：仅有方案体块时的自遮挡分析
- `test_no_scheme_mode`：仅有周边时的空场地评估
- `test_evaluation_points_returns_not_implemented`：传入 `evaluation_points` 时返回明确的 "Not implemented in MVP" 错误而非崩溃或静默忽略
- `test_no_compliance_language_in_output`：扫描 AI 摘要输出和所有用户可见文本，不应包含"合规""符合国标""满足规范"等判定性措辞

**集成测试**：

- 一个包含 5 栋楼、1 块红线的典型小区案例，对比输出和手工计算结果
- 性能测试：2500 点 × 25 时刻，要求 30 秒内完成

**Leo 手动验收**：

- [ ] 用自己 Rhino 里的某个旧方案，导出 OBJ → CityJSON → 跑日照分析，时间 < 10 分钟
- [ ] 输出的热力图在视觉上合理（北侧暗、南侧亮）
- [ ] AI 摘要指出了至少 1 个真实存在的设计问题
- [ ] 切换"大寒日"和"冬至日"预设，结果变化符合直觉
- [ ] 在 Lumen Canvas 上完成完整的工作流，不需要离开 Obsidian
- [ ] README 和报告底部出现定位声明（"不用于报建"）
- [ ] 尝试传入 `evaluation_points`，得到清晰的"暂未实现"提示而非崩溃

### 2.10 交付物

1. `lumen/skills/cityjson-sunlight/` 完整目录，可集成到 Lumen 主工程
2. 两个 helper 脚本（`obj_to_cityjson.py`、`geojson_to_cityjson.py`）及其独立 README
3. 面向建筑师用户的 README，包含："如何把你的 Rhino 模型变成可分析的 CityJSON"完整 step-by-step 指南
4. 一个 Rhino 方案的 demo 素材包（OBJ + meta.json），用户照着跑就能跑通
5. 30 秒 demo 视频录制脚本

---

## 第三部分：开发约束与风格

### 3.1 代码风格

- Python 代码遵循 PEP 8，全面使用 type hints
- 所有面向用户的文本支持 i18n，默认中文
- 不在算子内调用 LLM，AI 调用经过 Lumen 的 provider 抽象层
- 几何计算和 AI 摘要的逻辑严格分离，便于后续单独测试

### 3.2 与 `ifc-diff` 保持架构一致

本算子必须复用 `ifc-diff` 已经建立的 Lumen 算子基础设施：

- Light Skill 的 YAML schema 字段
- 缓存路径规则（`{vault}/.lumen/cache/`）
- 错误处理和日志规范
- Canvas 节点基类
- LLM provider 调用接口

**任何需要修改 Lumen 核心代码的地方，单独列出 PR 说明**。本算子不应该反向要求主工程做大量适配。

### 3.3 不要做的事

- **不要实现 `evaluation_points` 的点位日照计算**——即使它看起来只是"地面网格的简化版"。保留接口定义,收到非空输入时返回 "Not implemented in MVP"。详见 1.5 节说明。
- **不要实现窗口满窗日照（类型 ④）**——这是 GB 50180 的核心报建指标,涉及法律责任,MVP 绝不碰。
- **不要实现建筑表面日照、年累计辐射**——见 1.2 节类型表。
- **不要自己实现太阳位置公式**——用 `pvlib`,学术验证过
- **不要自己实现射线相交**——用 `trimesh` 或 `shapely`
- **不要做 3D 可视化**——MVP 只出 2D 热力图
- **不要内置中国日照规范条款**——只接受数值阈值（如 2 小时）,规范判定交给未来的 `cityjson-code-check` 算子
- **不要在任何面向用户的文本中使用"合规""符合规范""满足国标"等判定性表述**——包括报告模板、错误信息、README。一律表述为"达到用户设定阈值"或"达标"。
- **不要假设用户有政府数据**——所有流程必须在"用户自带数据"前提下可用
- **不要和现有日照软件（众智、天正）兼容**——保持轻量和独立,不为兼容性妥协
- **README 和报告底部必须有定位声明**:"本工具为设计阶段参考工具,不用于居住建筑报建或法律用途的日照分析。如需报建,请使用专业软件。"

### 3.4 开发节奏

- Day 1-2：几何加载 + 太阳位置 + 射线相交（核心计算链路）
- Day 3：网格化 + 热力图渲染
- Day 4：两个 helper 脚本（obj_to_cityjson、geojson_to_cityjson）
- Day 5：AI 摘要集成 + prompt 调优
- Day 6：Light Skill 封装 + Canvas 集成
- Day 7：端到端测试 + 文档 + demo 录制
- Day 8：Leo 审阅 + 迭代

总计约两周工作量（留出 buffer）。

---

## 第四部分：与其他算子的关系

### 4.1 在 Lumen 垂直算子地图中的位置

```
Lumen 垂直算子生态
├── 单体建筑尺度（IFC 系列）
│   ├── ifc-diff                       ← 已交付（第一个算子）
│   ├── ifc-compliance-check           ← 下一步
│   ├── ifc-quantity-takeoff
│   └── ifc-to-markdown-spec
├── 城市尺度（CityJSON 系列）
│   ├── cityjson-sunlight              ← 本算子
│   ├── cityjson-view-corridor
│   ├── cityjson-svf
│   └── cityjson-noise
├── 参数化设计（GH 系列）
│   └── gh-node-graph                  ← Leo 已有雏形
└── 图纸与其他
    ├── dwg-extract
    └── pdf-spec-extract
```

**本算子的战略意义**：

- 跨尺度证明：Lumen 不仅能处理一栋楼（IFC），还能处理一座城市（CityJSON）
- 用户群扩展：从设计院建筑师延伸到规划师、景观师、地产前期团队
- 市场教育：把"CityJSON"这个冷门概念通过一个建筑师刚需场景推广出去

### 4.2 与 `ifc-diff` 的协同

未来可以做一个组合算子：**方案变更前后的日照影响对比**。

用户在 Canvas 上：
1. 两个版本的 IFC（或方案 CityJSON）
2. 周边环境 CityJSON 不变
3. 分别跑 cityjson-sunlight，输出两份热力图
4. 再接一个新算子 `sunlight-diff`，对比两份结果
5. AI 摘要："本次方案调整使北侧住宅的日照合格率从 78% 提升至 89%，主要是因为 3# 楼高度降低 3 层。"

**这就是 Lumen 的真正价值**——单个算子都不稀奇，但算子的组合产生了新的产品形态。

---

## 附录 A：关键术语

- **CityJSON**：城市尺度的开放数据格式，基于 JSON，是 CityGML（XML 格式）的轻量化版本。由代尔夫特理工主导。
- **LOD**（Level of Detail）：CityJSON 的细节层级。LOD0 = 仅底面轮廓；LOD1 = 体块（extrusion）；LOD2 = 带屋顶；LOD3 = 含立面细节。
- **`cjio`**：CityJSON 的官方 Python 命令行工具和库。
- **大寒日**：中国日照规范常用的评估日期，约 1 月 20 日。
- **有效日照时长**：建筑窗口或地面点在规定时段内连续受日照的时长。
- **射线相交法**：从评估点向太阳方向投射射线，判断是否被障碍物遮挡的几何算法。

## 附录 B：参考资料

- CityJSON 官方规范：https://www.cityjson.org/specs/
- `cjio` GitHub：https://github.com/cityjson/cjio
- `pvlib` 文档：https://pvlib-python.readthedocs.io/
- 《城市居住区规划设计标准》GB 50180-2018（日照相关条款 § 4.0.9）
- Lumen Light Skill 规范（内部文档，参阅 `/docs/light-skills.md`）
- 姊妹算子文档：`lumen-ifc-diff-operator.md`

---

*文档结束。架构或范围层面的疑问，联系 Leo 后再启动编码。*
