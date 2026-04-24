# `sunlit` MVP 开发文档

> 项目代号:`sunlit`(暂拟名,正式发布前可重新命名)
> 一句话定位:面向建筑师的开源命令行工具,基于 CityJSON 做设计阶段的地面日照分析
> 目标读者:vibe coding 助手(执行层)+ Leo(产品审阅)
> 文档版本:v1.0
> 最后更新:2026-04-24
> 仓库规划:github.com/leoyang1984/sunlit

---

## 第一部分:产品叙事

### 1.1 这个工具解决的问题

日照分析是中国建筑项目绕不开的内容。但当前行业的日照分析工具处在一个尴尬的状态:

- **众智日照、天正日照、斯维尔日照**:专业但封闭。单机授权数千到上万元,界面停留在 2010 年代水平,只能在 Windows 的 AutoCAD 上跑,不支持 Mac。主要服务于报建场景,对设计阶段的快速反馈不友好。
- **Rhino + Ladybug Tools**:灵活但门槛极高。建筑师要会 Grasshopper,要理解气象数据格式(EPW),要自己处理周边体块建模。实际能熟练使用的建筑师不到 5%。
- **SketchUp + 阴影插件**:精度和严谨性不足以支撑方案判断。

**结果是:大多数建筑师在方案阶段根本不做日照分析**,凭经验估计;到了报建阶段再外包给咨询公司,花几千到几万元、等几天时间拿到报告——此时方案早已定型,发现问题来不及改。

`sunlit` 要填的是这个缝:**一个建筑师在自己的 Mac 或 Windows 上,十分钟内可以对任何方案跑一次日照分析的工具**。不是替代众智做报建,而是让设计阶段的日照判断成为日常。

### 1.2 计算类型与边界(极其重要)

"日照分析"在建筑行业不是一种计算,而是一组完全不同的计算。每一种对应不同的用户、输入、输出、精度要求。**开发前必须明确 `sunlit` 做哪一种、不做哪一种**,否则容易陷入"什么都想做、什么都做不好"的陷阱,也容易让用户误以为这是一个能替代报建软件的工具。

**日照分析的主要类型**:

| 类型 | 计算对象 | 典型用途 | 数据需求 |
|------|---------|---------|---------|
| ① 点位日照时长 | 单个点在指定日期的受晒时长 | 窗台/室外座椅评估 | 体块 LOD1 |
| ② **地面网格日照** | 场地地面切网格,每个格点的日照时长 | 景观布置、场地前期、方案自评 | 体块 LOD1 |
| ③ 建筑表面日照 | 建筑立面/屋顶切网格 | 光伏、热工、开窗策略 | 表面几何 LOD2+ |
| ④ 窗口满窗日照 | 每扇窗"整窗同时受晒"的最长连续时间 | 中国居住建筑报建核心指标 | 窗户信息(LOD1 无法满足) |
| ⑤ 阴影范围 | 指定时刻的地面阴影轮廓 | 规划示意图、可视化演示 | 体块 LOD1 |
| ⑥ 全年累计日照 | 8760 小时累计或年辐射量 | 光伏、被动式、LEED | 气象数据(EPW) |

**`sunlit` 只做类型 ②:地面网格日照**。

**为什么是类型 ②**:

- **数据前提匹配**:CityJSON LOD1(体块)就足够,与用户自带数据的能力范围一致
- **用户群清晰**:景观师、场地设计师、地产前期团队、做方案自评的建筑师——这些人当前没有好用的轻量工具
- **不受规范绑架**:不涉及 GB 50180 的合规判定,不承担法律风险,设计阶段参考足矣
- **输出直观**:热力图视觉效果强,AI 摘要价值清晰
- **架构可扩展**:为类型 ①(点位)留接口但不开发;类型 ③④ 留给未来独立工具

**`sunlit` 明确不做的事**(产品定位的一部分,用于管理用户期待):

- ❌ **不做类型 ④(窗口满窗日照)**:这是中国居住建筑报建的核心指标,涉及 GB 50180 的合规判定。报建级精度需要窗户几何信息、可能涉及法律责任——留给专业软件(众智、天正、斯维尔)。
- ❌ **不做类型 ③(建筑表面日照)**:光伏/被动式设计场景,未来可能独立开发其他工具。
- ❌ **不做类型 ⑥(全年累计/辐射量)**:需要气象数据(EPW)+ 大气辐射模型,属于 Ladybug 的地盘。
- ❌ **不做专业级日照阴影动画**:类型 ⑤ 可作为副产品(某一时刻的阴影多边形),但不是核心输出。

**预留接口但不开发**:

- `--points` 参数:允许用户传入自定义点位(GeoJSON 点集合),按类型 ① 的逻辑计算每个点的日照时长。MVP 保留 CLI 参数定义,**但不实现**——调用时返回 "Not implemented in MVP" 提示。这是为未来扩展留路径,同时避免用户误以为可以用于"窗口日照评估"。

**对用户的明确沟通**:

在 README 和每次运行的输出底部都要有一段定位声明:

> **本工具的定位**:面向设计阶段的参考工具,帮助建筑师快速理解场地的地面日照分布特征。**不用于报建**。如需用于居住建筑报建或法律用途的满窗日照分析,请使用专业日照软件(众智、天正、斯维尔等)。

### 1.3 关键产品洞察:用户自带两种 CityJSON

这是 `sunlit` 区别于任何现有日照软件的核心设计决策。

大部分人想到 CityJSON,第一反应是"政府公开数据"——于是担心"中国城市没几个开放数据集,做了也没人能用"。这个担心在"纯周边分析"的场景下成立,但**不成立于 `sunlit` 的设计**。

`sunlit` 接受两种 CityJSON 输入,并且**任一种都可以独立使用**:

**类型 A:周边环境 CityJSON**
- 来源:政府公开数据、OSM + 高度推算、倾斜摄影导出、用户手动在 Rhino/SketchUp 里搓的周边体块
- 内容:项目周边的现状建筑、地形、其他环境要素
- 作用:判断**周边对我的遮挡**

**类型 B:方案体块 CityJSON**
- 来源:**用户自己的设计方案**。Rhino、SketchUp、Revit、Blender 都能导出体块,经过 `sunlit convert` 或简单的 Python 脚本转换成 CityJSON
- 内容:待评估的设计方案
- 作用:判断**我对周边的遮挡**,或**我自己各部分之间的自遮挡**

**战略含义**:

即便用户**没有任何周边环境数据**,只要他有自己的设计方案,`sunlit` 就能用——用于分析方案内部的自遮挡(如 L 型住宅一翼对另一翼的遮挡、塔楼对裙房屋顶花园的遮挡、连廊对庭院的影响)。

即便用户**没有复杂的设计方案**,只要他有一块地 + 周边数据,`sunlit` 也能用——用于前期场地评估。

**两种数据都有时,才是完整的方案影响评估场景**。但只有一种也能独立产生价值——这让 `sunlit` 对"数据稀缺"的耐受度大幅提升,不再依赖政府开放数据的可得性。

### 1.4 最终用户体验

**场景一:方案自评地面影响(最高频)**

建筑师小张刚画完一个住宅小区方案。他在 Rhino 里选中所有楼栋,导出 OBJ。用 `sunlit convert` 把 OBJ + 每栋楼的层高属性转成 CityJSON,再用 QGIS 或 geojson.io 画了红线。

```bash
# 1. 转换方案
sunlit convert obj scheme.obj --meta meta.json --output scheme.cityjson

# 2. 跑日照分析
sunlit analyze \
  --scheme scheme.cityjson \
  --boundary site.geojson \
  --lat 39.9 --lon 116.4 \
  --date 2026-01-20 \
  --output ./report/
```

输出 `./report/` 下:

- `heatmap.png`:红线内地面的有效日照时长热力图(颜色越深代表日照时间越长)
- `summary.md`:AI 生成的摘要报告,含统计和建议
- `analysis.json`:完整的结构化数据,供下游工具消费

**场景二:场地前期评估(中频)**

建筑师小李拿到一块地,还没有方案。从 OSM 拿了周边 building footprint,用 `sunlit convert` 把 GeoJSON + height 属性 extrude 成 CityJSON。

```bash
sunlit convert footprint osm-buildings.geojson \
  --height-field height \
  --output context.cityjson

sunlit analyze \
  --context context.cityjson \
  --boundary site.geojson \
  --lat 31.2 --lon 121.5 \
  --date 2026-01-20 \
  --output ./site-study/
```

输出:空场地的日照潜力热力图 + AI 摘要("场地西北角受 200 米外 80 米高层遮挡,大寒日下午 2 点后进入阴影。东南约 2/3 区域全天日照条件良好。")

**场景三:方案对周边的影响参考(低频)**

项目方案阶段想初步了解对北侧现状住宅的遮挡情况(**不是报建用途**)。建筑师既有方案体块,也用 GeoJSON 快速画了周边现状住宅的 footprint + 高度,以及想评估的地面区域(北侧现状住宅的南侧地面)。

```bash
sunlit analyze \
  --scheme scheme.cityjson \
  --context north-neighbors.cityjson \
  --boundary affected-area.geojson \
  --lat 39.9 --lon 116.4 \
  --date 2026-01-20 \
  --output ./impact-study/
```

输出:评估区域的地面日照热力图,显示方案投下的额外阴影分布 + AI 摘要。AI 摘要会主动提醒:"若需用于正式报建,请使用专业日照软件。"

**三个场景共用同一个 `sunlit analyze` 命令**,只是输入组合不同。这是 MVP 保持简单的关键——不为不同场景做不同子命令,而是提供一种通用能力让建筑师自己组合。

### 1.5 MVP 范围

**计算类型**:仅做类型 ② 地面网格日照(见 1.2 节)。不做其他任何类型。

| 功能模块 | MVP 必须 | 接口保留但不开发 | 未来版本 |
|---------|---------|---------|---------|
| CityJSON 解析 | ✅ LOD1 体块(建筑 footprint + 高度) | — | LOD2/LOD3 |
| 太阳位置计算 | ✅ 基于经纬度、日期、时刻的精确方位角/高度角 | — | 考虑大气折射 |
| 遮挡判定 | ✅ 射线相交法 | — | — |
| 时间维度 | ✅ 单日多时刻(如大寒日 9:00-15:00) | — | 多日对比、全年累计 |
| 评估对象 | ✅ 红线内地面网格 | `--points` 自定义点位参数 | 建筑立面、屋顶表面 |
| 输出形态 | ✅ Markdown 报告 + PNG 热力图 + JSON 原始数据 | — | 交互式 HTML |
| AI 摘要 | ✅ 中文自然语言分析,通过 Anthropic API | — | 本地模型 fallback |
| 输入数据辅助 | ✅ `sunlit convert obj`、`sunlit convert footprint` | — | OSM 直接导入、Revit 直连 |

**明确不在 MVP 范围**:

- ❌ 窗口满窗日照、建筑表面日照、年累计日照(见 1.2)
- ❌ 风环境、天空开阔度、视线等其他城市尺度分析
- ❌ 植被、玻璃幕墙反射等二次效应
- ❌ 国标规范的完整内置判定(仅接受用户配置数值阈值)
- ❌ GUI 桌面应用(MVP 仅命令行)
- ❌ Web 界面
- ❌ 云端 SaaS

**关于 `--points` 参数的特别说明**:

- CLI 参数定义中保留 `--points` 选项
- 调用时检测到此参数非空,直接输出 "Not implemented in MVP. This interface is reserved for future point-level analysis." 并退出
- **不要实现**点位日照计算逻辑,即使它看起来只是"地面网格的简化版"
- 理由:避免用户误以为可以用于窗口日照评估;保持 MVP 聚焦

### 1.6 为什么做成独立开源项目

**避开平台绑定**:`sunlit` 作为独立的 Python CLI,任何人都能 `pip install` 使用,不绑定任何更大的产品。这和"IFC 是开放格式、不绑定 Revit"的哲学一致。

**用户圈测试**:独立 CLI 的早期用户是愿意装 Python、跑命令行的技术型建筑师——他们对算法正确性很敏感,反馈质量高。先在这个圈子验证算法,再给普通建筑师用。

**生态拓展**:未来可以被集成到 Lumen(Obsidian 插件)、Rhino 插件、Web SaaS、Slack bot 等各种上层产品,而核心算法只维护一份。

**独立存活**:即使未来上层产品调整方向,`sunlit` 本身仍能持续服务建筑师社区。

### 1.7 未来的 Lumen 集成(不在本次开发范围)

`sunlit` 打磨稳定后,将被集成到 Lumen(Leo 开发的 Obsidian 建筑师工作台)作为一个 Light Skill:

- 用户在 Lumen Canvas 上拖拽 CityJSON 文件节点
- 通过 Light Skill 封装调用 `sunlit` 命令
- 输出 Markdown 报告自动落到 Canvas 上
- 可与 Lumen 的其他算子(IFC diff、项目笔记等)组合

**本次 MVP 开发不涉及任何 Lumen 集成代码**。但 `sunlit` 的设计要保证未来集成时 glue code 最小:

- 所有 CLI 输出可通过标准管道消费(JSON 结构化、退出码规范)
- 核心逻辑封装成 Python 包,可被其他 Python 程序 `import sunlit` 直接调用
- AI 摘要的 prompt 可通过配置文件覆盖,便于上层产品注入自己的 prompt

---

## 第二部分:技术规格

### 2.1 技术栈

**运行时**:Python 3.9+

**核心依赖**:

- `cjio`:CityJSON 官方 Python 库,解析和几何操作
- `shapely`:2D 几何运算(红线、投影、相交)
- `numpy`:网格化和矩阵运算
- `pvlib`:太阳位置计算(学术验证过,比自己写公式可靠)
- `trimesh`:3D 几何和射线相交加速(BVH)
- `matplotlib`:热力图输出
- `anthropic`:AI 摘要调用(通过 `ANTHROPIC_API_KEY` 环境变量)
- `click` 或 `typer`:CLI 框架(推荐 `typer`,类型提示友好)
- `pydantic`:配置和数据模型校验
- `rich`:终端输出美化(进度条、彩色日志)

**不使用**:

- 不引入任何 GIS 专业软件(QGIS、ArcGIS)依赖
- 不使用 Ladybug/Honeybee(太重,依赖 Rhino)
- 不使用 Three.js 或前端渲染框架(MVP 不做 3D/Web)

**打包发布**:

- PyPI 发布(`pip install sunlit`)
- 使用 `uv` 或 `poetry` 管理开发环境
- GitHub Actions 自动发布 + 跨平台测试(macOS、Windows、Ubuntu)

### 2.2 项目结构

```
sunlit/
├── README.md                      # 面向用户的主文档
├── LICENSE                        # MIT 或 Apache 2.0
├── pyproject.toml                 # 包配置
├── uv.lock                        # 依赖锁定
├── .github/
│   └── workflows/
│       ├── test.yml               # 跨平台测试
│       └── publish.yml            # PyPI 自动发布
├── src/
│   └── sunlit/
│       ├── __init__.py
│       ├── __main__.py            # 使 `python -m sunlit` 可用
│       ├── cli.py                 # CLI 入口(typer)
│       ├── analyze.py             # 分析主逻辑
│       ├── sun_position.py        # 太阳位置计算(封装 pvlib)
│       ├── geometry.py            # CityJSON → trimesh Mesh 加载 + 射线相交
│       ├── grid.py                # 红线网格化
│       ├── render.py              # matplotlib 热力图
│       ├── summarize.py           # AI 摘要(Anthropic SDK 调用)
│       ├── models.py              # pydantic 数据模型
│       ├── convert/
│       │   ├── __init__.py
│       │   ├── obj_to_cityjson.py
│       │   └── footprint_to_cityjson.py
│       └── prompts/
│           └── summary.md         # AI 摘要 prompt 模板
├── tests/
│   ├── test_sun_position.py
│   ├── test_geometry.py
│   ├── test_grid.py
│   ├── test_analyze.py
│   ├── test_convert.py
│   ├── test_cli.py
│   └── fixtures/
│       ├── simple-scheme.obj
│       ├── simple-scheme.cityjson
│       ├── simple-context.cityjson
│       ├── simple-site.geojson
│       └── meta-example.json
├── docs/
│   ├── getting-started.md         # 零基础入门
│   ├── preparing-data.md          # 如何从 Rhino/SketchUp 导出到 CityJSON
│   ├── cli-reference.md           # 完整 CLI 参数说明
│   ├── faq.md
│   └── data-sources.md            # 可用的公开 CityJSON 数据源列表
└── examples/
    ├── 01-self-assessment/        # 方案自评示例(含数据)
    ├── 02-site-study/             # 场地前期示例
    └── 03-neighbor-impact/        # 周边影响示例
```

### 2.3 CLI 设计

使用 `typer` 构建,有三个主命令:

**`sunlit analyze`** — 核心日照分析

```bash
sunlit analyze [OPTIONS]

Options:
  --scheme PATH                方案体块 CityJSON (可选,但 scheme 和 context 至少提供一个)
  --context PATH               周边环境 CityJSON (可选)
  --boundary PATH              评估区域 GeoJSON (必填)
  --points PATH                自定义评估点 GeoJSON (MVP 不实现,传入时报错退出)
  --lat FLOAT                  纬度 (必填,十进制度数)
  --lon FLOAT                  经度 (必填,十进制度数)
  --date TEXT                  评估日期 YYYY-MM-DD (默认 2026-01-20 大寒日)
  --time-start TEXT            开始时刻 HH:MM (默认 09:00)
  --time-end TEXT              结束时刻 HH:MM (默认 15:00)
  --time-step INTEGER          时间步长 分钟 (默认 15)
  --grid-size FLOAT            评估网格边长 米 (默认 2.0)
  --threshold FLOAT            达标阈值 小时 (默认 2.0)
  --output PATH                输出目录 (默认 ./sunlit-output/)
  --no-ai                      跳过 AI 摘要 (离线/无 API key 时使用)
  --language TEXT              输出语言 zh/en (默认 zh)
  --config PATH                可选的 YAML 配置文件 (覆盖上述选项)
  --verbose / --quiet          输出详细度
  --help                       显示帮助
```

**`sunlit convert`** — 输入数据辅助转换

```bash
sunlit convert obj [OPTIONS] OBJ_PATH

将 OBJ 文件转成 CityJSON LOD1 体块。

Options:
  --meta PATH                  元数据 JSON 文件 (必填,定义各 group 的名称、高度等)
  --output PATH                输出路径 (默认 <obj>.cityjson)
  --crs TEXT                   坐标参考系 (默认 EPSG:4326)
```

```bash
sunlit convert footprint [OPTIONS] GEOJSON_PATH

将带高度属性的 GeoJSON Polygon 集合 extrude 成 CityJSON LOD1 体块。

Options:
  --height-field TEXT          高度属性字段名 (默认 "height")
  --default-height FLOAT       无高度属性时的默认值 米 (默认 10.0)
  --output PATH                输出路径
  --crs TEXT                   坐标参考系
```

**`sunlit version`** — 版本信息和环境检查

```bash
sunlit version

输出:
  sunlit 0.1.0
  Python 3.11.7
  Dependencies: cjio 0.9.0, trimesh 4.0.5, ...
  Anthropic API: configured / not configured
```

### 2.4 核心数据模型(pydantic)

```python
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import date

class AnalysisConfig(BaseModel):
    latitude: float
    longitude: float
    date: date
    time_start: str  # "HH:MM"
    time_end: str
    time_step_minutes: int = 15
    grid_size_meters: float = 2.0
    threshold_hours: float = 2.0
    language: Literal["zh", "en"] = "zh"
    enable_ai_summary: bool = True

class SunPosition(BaseModel):
    timestamp: str      # ISO 格式
    azimuth: float      # 度,北为 0,顺时针
    altitude: float     # 度,地平为 0

class EvaluationPoint(BaseModel):
    x: float
    y: float
    z: float
    sunlit_minutes: float
    sunlit_intervals: list[tuple[str, str]]
    meets_threshold: bool

class AnalysisMode(BaseModel):
    has_scheme: bool
    has_context: bool
    # 计算得到的显示名
    display_name: str  # "场地前期评估" / "方案自评" / "方案对周边影响参考"

class Statistics(BaseModel):
    total_points: int
    qualified_points: int
    qualified_pct: float
    qualified_area_sqm: float
    max_hours: float
    min_hours: float
    avg_hours: float

class AnalysisResult(BaseModel):
    version: str
    mode: AnalysisMode
    config: AnalysisConfig
    sun_positions: list[SunPosition]
    evaluation_points: list[EvaluationPoint]
    statistics: Statistics
    grid_bounds: dict          # xmin/xmax/ymin/ymax
    spatial_patterns: dict     # 给 AI 摘要使用的空间特征
    disclaimer: str            # 固定的定位声明
```

### 2.5 核心算法

```python
# 伪代码,vibe coding 助手负责实现

def analyze(
    scheme_path: Optional[Path],
    context_path: Optional[Path],
    boundary_path: Path,
    config: AnalysisConfig,
) -> AnalysisResult:
    # 前置校验
    if not scheme_path and not context_path:
        raise ValueError("Must provide at least one of --scheme or --context")
    
    # 1. 加载几何
    obstacles = []
    if context_path:
        obstacles.extend(load_cityjson_as_meshes(context_path))
    if scheme_path:
        obstacles.extend(load_cityjson_as_meshes(scheme_path))
    
    # 2. 构建评估网格
    boundary = load_geojson_polygon(boundary_path)
    grid_points = generate_grid_inside(boundary, spacing=config.grid_size_meters)
    
    # 3. 计算时间序列的太阳位置
    sun_positions = compute_sun_positions(
        lat=config.latitude,
        lon=config.longitude,
        date=config.date,
        start=config.time_start,
        end=config.time_end,
        step_minutes=config.time_step_minutes,
    )
    
    # 4. 批量射线相交测试
    # 将所有点 × 所有时刻的射线向量化,用 trimesh 的 BVH 一次性求交
    # 这是性能关键路径,必须向量化而不是 for-loop
    results = batch_ray_test(grid_points, sun_positions, obstacles)
    
    # 5. 统计 + 空间特征提取
    statistics = compute_statistics(results, config.threshold_hours)
    patterns = extract_spatial_patterns(results, obstacles)
    
    # 6. 组装结果
    mode = infer_mode(has_scheme=scheme_path is not None,
                      has_context=context_path is not None)
    
    return AnalysisResult(
        version="0.1.0",
        mode=mode,
        config=config,
        sun_positions=sun_positions,
        evaluation_points=results,
        statistics=statistics,
        grid_bounds=bounds_from(grid_points),
        spatial_patterns=patterns,
        disclaimer=DISCLAIMER_TEXT,
    )
```

**性能关键点**:

- 射线与建筑的相交判定用 `trimesh` 的 BVH 加速结构(`mesh.ray.intersects_any`)
- 所有评估点 × 所有时刻的遍历必须**向量化**(一次性生成所有射线,批量相交),不能用嵌套 for-loop
- 典型规模:100m × 100m 地块,2m 网格 ≈ 2500 个评估点;单日 9-15 点 15 分钟步长 ≈ 25 个时刻。总计 62,500 次射线测试,在普通笔记本上应在 30 秒内完成
- 进度条:用 `rich.progress` 按时刻粒度更新

**边界情况**:

- 网格点恰好落在建筑内部 → 跳过
- 红线包含多个不相连区域 → 支持,分别网格化
- 凹形红线 → 使用 `shapely.contains` 判断网格点
- 太阳高度角 ≤ 0(已落山) → 跳过该时刻

### 2.6 输入数据辅助脚本(关键产品决策)

**重要**:MVP 必须交付这两个 helper,否则用户拿不到 CityJSON 数据,工具就没法用。这两个 helper 的重要性**不亚于主分析命令**。

**`sunlit convert obj`**

接受 Rhino/SketchUp/Blender 导出的 OBJ 文件和一个元数据 JSON,输出 CityJSON LOD1。

`meta.json` 示例:

```json
{
  "crs": "EPSG:4326",
  "origin": {
    "lat": 39.9042,
    "lon": 116.4074,
    "elevation": 0,
    "description": "OBJ 的局部原点对应的地理坐标"
  },
  "rotation_degrees": 0,
  "buildings": [
    {
      "obj_group": "Building_A",
      "name": "1号楼",
      "height": 54.0,
      "floors": 18
    },
    {
      "obj_group": "Building_B",
      "name": "2号楼",
      "height": 19.8,
      "floors": 6
    }
  ]
}
```

实现要点:

- 读取 OBJ 中的每个 `g` group 或 `o` object 作为独立建筑
- 按 meta.json 匹配 group 名称,赋予属性
- 从 OBJ 的局部坐标转换到 CityJSON 要求的地理坐标(或本地投影坐标系)
- 如果 OBJ 已经是完整体块 mesh,直接封装;如果是底面 footprint,按 height 属性 extrude
- 输出符合 CityJSON 1.1 规范的 LOD1 文件

**`sunlit convert footprint`**

用户用 QGIS 或手绘 GeoJSON 画了建筑 footprint,每个 feature 带 `height` 属性,脚本自动 extrude。

实现要点:

- 读取 GeoJSON Polygon/MultiPolygon
- 按 `--height-field` 提取高度,无此字段使用 `--default-height`
- extrude 成 LOD1 solid
- 坐标系处理:GeoJSON 默认 WGS84 经纬度,转换到本地投影(UTM 或用户指定)再做几何计算

**文档指引**:

这两个命令的 README 要特别详细,**必须包含从 Rhino/SketchUp/QGIS 导出的 step-by-step 截图指南**(Leo 来拍截图,vibe coding 助手在文档中留位置)。

### 2.7 AI 摘要

**调用方式**:

- 使用 `anthropic` Python SDK
- API key 从环境变量 `ANTHROPIC_API_KEY` 读取
- 默认模型 `claude-sonnet-4-6` (可通过 `SUNLIT_MODEL` 环境变量覆盖)
- 调用失败时降级为仅输出统计数据 + 定位声明,不崩溃
- `--no-ai` 选项可跳过 AI 摘要

**Prompt 模板(`src/sunlit/prompts/summary.md`)**:

```markdown
你是一位资深建筑师,正在帮同事审阅一份地面日照分析结果。

# 分析类型说明

本次分析计算的是**地面网格上每一点在指定日期的有效日照时长**。
不是窗口满窗日照、不是建筑立面日照、不是年累计辐射,仅限于地面。
结果用于设计阶段参考,不用于报建或法律判定。

# 输入数据

**分析模式**:{mode}
**项目位置**:纬度 {lat},经度 {lon}
**评估日期**:{date}({date_name},如"大寒日")
**评估时段**:{start_time} - {end_time}
**达标阈值**:地面点日照 ≥ {threshold} 小时视为达标(用户自定义)

**统计结果**:
- 评估点位总数:{total_points}
- 达标点位:{qualified_points}({qualified_pct}%)
- 达标面积:约 {qualified_area} m²
- 最大日照时长:{max_hours} 小时
- 最小日照时长:{min_hours} 小时
- 平均日照时长:{avg_hours} 小时

**空间分布特征**:
{spatial_patterns_json}

# 你的任务

生成一份简洁的 Markdown 日照分析摘要。要求:

1. 开篇用 1-2 句说清楚总体情况(达标面积占比、主要遮挡方位)
2. 指出主要问题区域(方位 + 受影响程度 + 主要遮挡源建筑)
3. 提出可行的改进方向(降低某建筑高度、调整位置、改变朝向等)
4. 结尾提醒本分析的定位和局限:如用户明显在准备报建材料,提示使用专业软件
5. 避免 AI 腔,语气专业克制
6. 不要使用"合规""符合规范""满足国标"等判定性表述

# 输出格式

```markdown
## 地面日照分析摘要

[2-3 句总体情况]

### 达标情况
[定量描述]

### 主要问题区域
[按严重程度列出 2-3 个问题区域]

### 改进方向
[2-3 条可操作建议]

### 分析局限
[提示:地面日照参考,不含窗口满窗、表面辐射等。如需报建,请用专业软件。]
```
```

### 2.8 输出形态

`sunlit analyze` 在 `--output` 目录生成:

```
sunlit-output/
├── heatmap.png          # 主视觉:日照时长热力图(带红线、建筑轮廓、色标、北针)
├── summary.md           # AI 摘要报告(含统计表)
├── analysis.json        # 完整结构化数据(可供下游消费)
└── metadata.yaml        # 运行参数、版本号、执行时间、输入文件哈希
```

**heatmap.png 的视觉规范**:

- 底图:浅灰色背景
- 建筑轮廓:深灰色填充(方案和周边区分深浅)
- 红线:橙色粗线
- 热力图:viridis 或 inferno 色标,标注达标阈值对应的等高线
- 标注:标题、日期、时段、北针、比例尺、色标
- 分辨率:300 DPI,适合插入报告文档

**summary.md 的标准格式**:

```markdown
# 地面日照分析报告

**生成时间**: 2026-04-24 15:32:18
**工具版本**: sunlit 0.1.0
**分析模式**: 方案自评

## 运行参数

- 位置: 北京 (39.9042°N, 116.4074°E)
- 日期: 2026-01-20 (大寒日)
- 时段: 09:00 - 15:00
- 网格大小: 2.0m
- 达标阈值: 2.0 小时

---

[AI 生成的摘要正文]

---

## 原始统计数据

[自动生成的统计表格]

---

## 工具定位声明

本工具面向设计阶段的参考使用,不用于居住建筑报建或法律用途的满窗日照分析。
如需报建,请使用专业日照软件(众智、天正、斯维尔等)。

Generated by sunlit v0.1.0 · https://github.com/leoyang1984/sunlit
```

### 2.9 测试要求

**单元测试**(必须 100% 覆盖核心算法):

- `test_sun_position_accuracy`:对已知日期/地点的太阳位置,与 NOAA 公开数据对比,误差 < 0.5 度
- `test_ray_intersection_basic`:单个建筑挡单个点,验证遮挡判定正确
- `test_ray_intersection_vectorized`:向量化批量测试和逐点测试结果一致
- `test_grid_inside_convex_boundary`:凸多边形红线内网格生成
- `test_grid_inside_concave_boundary`:凹多边形红线内网格生成
- `test_grid_with_holes`:带洞的红线(如内院)正确生成
- `test_no_context_mode`:仅方案体块时的自遮挡分析
- `test_no_scheme_mode`:仅周边时的空场地评估
- `test_both_missing`:两个 CityJSON 都不提供时明确报错
- `test_points_param_returns_not_implemented`:传入 `--points` 时返回明确错误而非崩溃或静默忽略
- `test_no_compliance_language_in_output`:扫描 AI 摘要输出和所有用户可见文本,不应包含"合规""符合国标""满足规范"等判定性措辞
- `test_disclaimer_always_present`:所有输出(report、summary、CLI 提示)必须含定位声明

**集成测试**:

- 完整跑通三个 examples/ 示例,输出与基准对比
- 跨平台测试:GitHub Actions 在 macOS/Windows/Ubuntu 各跑一次
- 性能测试:2500 点 × 25 时刻,要求 30 秒内完成
- AI 调用 mock:不依赖真实 Anthropic API 也能测试

**Leo 手动验收清单**:

- [ ] `pip install sunlit` 在干净环境下一次成功
- [ ] 按照 README 的 Quick Start,10 分钟内跑通第一次分析
- [ ] 用自己 Rhino 里的某个旧方案,从 OBJ → CityJSON → 跑日照分析,时间 < 15 分钟
- [ ] 输出的热力图在视觉上合理(北侧暗、南侧亮)
- [ ] AI 摘要指出了至少 1 个真实存在的设计问题
- [ ] 切换"大寒日"(1月20日)和"夏至日"(6月21日),结果变化符合直觉(夏天阳光充足、冬天遮挡严重)
- [ ] README 清楚回答"这是什么/不是什么",让普通建筑师看完知道能做/不能做什么
- [ ] 尝试传入 `--points`,得到清晰的"暂未实现"提示而非崩溃
- [ ] 无 `ANTHROPIC_API_KEY` 时加 `--no-ai` 仍可跑完并生成报告(仅无 AI 摘要)
- [ ] 所有面向用户的文本(CLI 帮助、报告、错误信息)不出现"合规""符合规范"等词

---

## 第三部分:开发约束与风格

### 3.1 代码风格

- Python 代码遵循 PEP 8,全面使用 type hints
- 所有面向用户的文本支持 i18n(`zh`/`en` 两种),默认中文
- 几何计算、AI 调用、CLI 交互三层严格分离,便于独立测试
- 错误信息必须是建筑师能看懂的(不要抛裸的 `KeyError`、堆栈给用户)
- 使用 `rich` 做 CLI 输出,不要用 `print()`
- 所有外部命令和 API 调用必须有超时保护

### 3.2 不要做的事

- **不要实现 `--points` 的点位日照计算**——即使看起来只是"地面网格的简化版"。保留接口定义,收到非空输入时返回 "Not implemented in MVP"。详见 1.5 节。
- **不要实现窗口满窗日照(类型 ④)**——这是 GB 50180 的核心报建指标,涉及法律责任,MVP 绝不碰。
- **不要实现建筑表面日照、年累计辐射**——见 1.2 节类型表。
- **不要自己实现太阳位置公式**——用 `pvlib`。
- **不要自己实现射线相交算法**——用 `trimesh` 的 BVH。
- **不要做 3D 可视化**——MVP 只出 2D 热力图。
- **不要内置中国日照规范条款**——只接受数值阈值(如 2 小时),规范判定交给专业软件。
- **不要在任何面向用户的文本中使用"合规""符合规范""满足国标"等判定性表述**。一律表述为"达到用户设定阈值"或"达标"。
- **不要假设用户有政府数据**——所有流程必须在"用户自带数据"前提下可用。
- **不要和现有日照软件(众智、天正)做格式兼容**——保持轻量和独立。
- **不要在 MVP 里引入 GUI、Web 界面、SaaS 后端**——命令行足矣。
- **README 和报告底部必须有定位声明**:"本工具为设计阶段参考工具,不用于居住建筑报建或法律用途的日照分析。如需报建,请使用专业软件。"

### 3.3 开发节奏(建议)

**第一周**:打通核心计算链路

- Day 1-2:项目初始化(pyproject.toml、CI、依赖)+ 太阳位置计算 + 基本单元测试
- Day 3-4:几何加载(CityJSON → trimesh)+ 射线相交 + 网格化
- Day 5:向量化批量计算 + 性能优化 + 集成测试

**第二周**:输入数据辅助与产品化

- Day 6-7:两个 convert 子命令(obj 和 footprint)
- Day 8:AI 摘要集成 + prompt 调优
- Day 9:热力图渲染(matplotlib 美化)+ 报告组装
- Day 10:CLI 完整化(帮助文本、错误处理、进度条)

**第三周**:文档、测试、发布

- Day 11-12:README + getting-started + preparing-data 文档(含截图占位)
- Day 13:examples/ 三个完整示例(含数据、预期输出)
- Day 14:跨平台测试、PyPI 发布流程、GitHub Actions
- Day 15:Leo 审阅 + 迭代

**总计约 3 周(留 buffer 到 4 周)**。

### 3.4 发布后的后续路线(不在本次范围)

| 优先级 | 功能 | 说明 |
|-------|------|------|
| P0 | Lumen 集成 | 作为 Light Skill 调用 `sunlit` 命令 |
| P1 | `--points` 实现 | 点位级日照时长查询 |
| P1 | 多日对比 | 如"大寒日 vs 夏至日"叠加分析 |
| P1 | OSM 直接导入 | `sunlit convert osm --bbox ...` 一步到位 |
| P2 | 交互式 HTML 输出 | 可在浏览器里悬浮查看每点的详细数据 |
| P2 | Rhino 插件 | 不离开 Rhino 调用 sunlit |
| P3 | SVF / 视线分析 | 同数据结构下的其他城市尺度分析 |

---

## 附录 A:关键术语

- **CityJSON**:城市尺度的开放数据格式,基于 JSON,是 CityGML(XML 格式)的轻量化版本。由代尔夫特理工主导。
- **LOD**(Level of Detail):CityJSON 的细节层级。LOD0 = 仅底面轮廓;LOD1 = 体块(extrusion);LOD2 = 带屋顶;LOD3 = 含立面细节。
- **`cjio`**:CityJSON 的官方 Python 命令行工具和库。
- **大寒日**:中国日照规范常用的评估日期,约 1 月 20 日。
- **有效日照时长**:一个地面点或窗口在规定时段内受日照的累计时长。
- **射线相交法**:从评估点向太阳方向投射射线,判断是否被障碍物遮挡的几何算法。
- **BVH**(Bounding Volume Hierarchy):用于加速射线-网格相交测试的空间数据结构。

## 附录 B:参考资料

- CityJSON 官方规范:https://www.cityjson.org/specs/
- `cjio` GitHub:https://github.com/cityjson/cjio
- `pvlib` 文档:https://pvlib-python.readthedocs.io/
- `trimesh` 文档:https://trimesh.org/
- NOAA 太阳位置计算器:https://gml.noaa.gov/grad/solcalc/
- 《城市居住区规划设计标准》GB 50180-2018(日照相关条款 § 4.0.9)——**仅供参考,sunlit 不做此规范的合规判定**

## 附录 C:可用的公开 CityJSON 数据源(供 README 引用)

- 代尔夫特理工 3D Geoinformation 官方示例:https://www.cityjson.org/datasets/
- 鹿特丹市:https://www.3drotterdam.nl/
- 新加坡 OneMap:https://www.onemap.gov.sg/
- 赫尔辛基:https://hri.fi/data/en_GB/dataset/helsingin-3d-kaupunkimalli
- 纽约市(需转换):NYC Open Data Building Footprints + height
- **国内**:目前公开的 CityJSON 数据极少。推荐用户自行从 OSM + 高度数据 + QGIS,通过 `sunlit convert footprint` 生成。

---

*文档结束。架构或范围层面的疑问,联系 Leo 后再启动编码。*
