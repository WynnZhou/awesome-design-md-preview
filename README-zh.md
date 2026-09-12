# awesome-design-md → 预览页

<p dir="auto"><a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License: MIT"></a> <a href="./index.html"><img src="https://img.shields.io/badge/Styles-76%20previews-4B32C3" alt="76 个预览"></a> <a href="https://github.com/VoltAgent/awesome-design-md"><img src="https://img.shields.io/badge/Source-awesome--design--md-181717" alt="来源：awesome-design-md"></a> <a href="https://getdesign.md/"><img src="https://img.shields.io/badge/Previews-getdesign.md-0052CC" alt="预览：getdesign.md"></a> <a href="https://developer.mozilla.org/docs/Web/HTML"><img src="https://img.shields.io/badge/Language-HTML%20%2F%20CSS-E34F26" alt="HTML / CSS"></a></p>

[English](README.md) · **中文**

**在线：** <https://wynnzhou.github.io/awesome-design-md-preview/> —— 同一个浏览器，从仓库直接托管。

76 个设计系统，离线可看。`index.html` 是浏览器；每个风格目录里那一页同时带着它的浅色和深色主题。

## 目录结构
    awesome-design-md-preview/
    ├── index.html                  浏览器 —— 左边风格列表，右边实时预览。手工维护，没有脚本写它
    ├── README.md · README-zh.md · LICENSE
    ├── design-md/                  每个风格一个目录，共 76 个，和上游的排布一致
    │   ├── <style>/
    │   │   ├── DESIGN.md           上游设计文档，逐字节拷贝
    │   │   ├── README.md           上游 readme 加一段本目录说明
    │   │   ├── preview.html        合并版 —— getdesign.md 那两份合进一个文件（默认）
    │   │   ├── preview.css         它的样式表，深浅两套在一起
    │   │   ├── preview_auto.html   从 DESIGN.md 生成 —— 浏览器的"自动版"模式
    │   │   ├── preview_auto.css    它的样式表。76 个里 74 个有 auto 页 —— Discord 和 Mobbin
    │   │   │                       没有 DESIGN.md，生不出来
    │   │   ├── preview_light.html  getdesign.md 自己保存的浅色页 —— 作为源保留
    │   │   └── preview_dark.html   同一份的深色版。76 个里 74 个有 —— BMW M 和 Lamborghini
    │   │                           上游没有深色变体
    │   └── fonts/                  21 个 woff2（latin 子集），对应我们自托管的 5 个家族。
    │                               放在这里是因为旁边的样式表引用的是 ../fonts/
    ├── icons/                      72 个风格图标，index.html 用。另外 4 行回退到品牌色块
    └── _generator/
        ├── build_previews.py       DESIGN.md → preview_auto.html、preview_auto.css、fonts/，以及
        │                           每个目录的 DESIGN.md + README.md
        ├── merge_themes.py         preview_light.html + preview_dark.html → preview.html 和
        │                           preview.css，两套主题合进一个文件
        └── fetch_getdesign.py      <slug> → preview_light.html + preview_dark.html，从
                                    getdesign.md 渲染。只在这个目录新增风格时才需要跑

## 浏览器

列表头部三个开关：

    EN / 中        只切浏览器自己的界面文字，默认中文。风格列表跟着翻译；预览内容本身永远不翻。
    合并版/分离版/自动版   三个循环切换：preview.html、preview_light.html / preview_dark.html、
                          或 preview_auto.html
    ☀ / ☾          浅色 / 深色 —— 浏览器外壳和被预览的页面一起翻

快捷键：`/` 筛选 · `Esc` 清空 · `↑` `↓` 上一个/下一个 · `t` 切主题。三个开关都会记住。

合并版和自动版都通过 postMessage 把主题传给页面，原地切换、不重新加载；分离版只是加载另一个文件。某个模式缺页时会回退到合并版 —— BMW M 和 Lamborghini 没有深色页，Discord 和 Mobbin 没有 auto 页。

## 合并版

`preview_light.html` 和 `preview_dark.html` 近乎副本 —— 同样的 head、同样的字体 CSS、样式表只差 `:root` —— 所以能折成一页一表，两套主题分别罩在 `html[data-theme]` 下。76 个风格里 43 个的两份正文完全相同；另外 33 个的文案和色板不同，两份都保留，由 CSS 隐藏不生效的那份。

主题在首屏绘制前就定好（`<head>` 里一小段脚本读 `?theme=` 和 localStorage），所以切深色不会先白一下。

## 全部样式

76 个，分组和侧栏一致。每个链接指向该风格的合并版页面 —— `preview_light.html` 和 `preview_dark.html` 就在它旁边。

### AI 与 LLM 平台

- [Claude](design-md/claude/preview.html) — Anthropic 的 AI 助手。暖陶土色点缀、清爽的编辑式排版。
- [Cohere](design-md/cohere/preview.html) — 企业 AI 平台。鲜艳渐变、数据密集的仪表盘美学。
- [ElevenLabs](design-md/elevenlabs/preview.html) — AI 语音平台。深色电影感界面、声波美学。
- [MiniMax](design-md/minimax/preview.html) — AI 模型提供方。大胆的深色界面配霓虹点缀。
- [Mistral AI](design-md/mistral-ai/preview.html) — 开放权重的大模型提供方。法式工程极简，偏紫调。
- [Ollama](design-md/ollama/preview.html) — 本地跑大模型。终端优先、单色极简。
- [OpenCode](design-md/opencode-ai/preview.html) — AI 编程平台。以开发者为中心的深色主题。
- [Replicate](design-md/replicate/preview.html) — 通过 API 跑机器学习模型。干净的白色画布、以代码为中心。
- [Runway](design-md/runwayml/preview.html) — AI 视频生成。电影感深色界面、以媒体为主的版式。
- [Together AI](design-md/together-ai/preview.html) — 开源 AI 基础设施。技术感、蓝图式设计。
- [VoltAgent](design-md/voltagent/preview.html) — AI agent 框架。虚空黑画布、祖母绿点缀、终端原生。
- [xAI](design-md/x-ai/preview.html) — Elon Musk 的 AI 实验室。凛冽单色、未来极简。

### 开发者工具与 IDE

- [Cursor](design-md/cursor/preview.html) — AI 优先的代码编辑器。利落的深色界面、渐变点缀。
- [Expo](design-md/expo/preview.html) — React Native 平台。深色主题、紧字距、以代码为中心。
- [Lovable](design-md/lovable/preview.html) — AI 全栈构建器。活泼渐变、友好的开发者气质。
- [Raycast](design-md/raycast/preview.html) — 效率启动器。利落的深色外壳、鲜艳的渐变点缀。
- [Superhuman](design-md/superhuman/preview.html) — 快速邮件客户端。高级深色界面、键盘优先、紫色辉光。
- [Vercel](design-md/vercel/preview.html) — 前端部署。黑与白的精确、Geist 字体。
- [Warp](design-md/warp/preview.html) — 现代终端。类 IDE 的深色界面、块状命令 UI。

### 后端、数据库与 DevOps

- [ClickHouse](design-md/clickhouse/preview.html) — 快速分析数据库。黄色点缀、技术文档风格。
- [Composio](design-md/composio/preview.html) — 工具集成平台。现代深色配彩色集成图标。
- [HashiCorp](design-md/hashicorp/preview.html) — 基础设施自动化。企业级干净，黑与白。
- [MongoDB](design-md/mongodb/preview.html) — 文档数据库。绿叶品牌，聚焦开发者文档。
- [PostHog](design-md/posthog/preview.html) — 产品分析。俏皮的刺猬品牌、对开发者友好的深色界面。
- [Sanity](design-md/sanity/preview.html) — 无头 CMS。红色点缀、内容优先的编辑式版式。
- [Sentry](design-md/sentry/preview.html) — 错误监控。深色仪表盘、数据密集、粉紫点缀。
- [Supabase](design-md/supabase/preview.html) — 开源的 Firebase 替代品。深祖母绿主题、代码优先。

### 效率工具与 SaaS

- [Cal.com](design-md/cal/preview.html) — 开源日程调度。干净中性的界面，开发者式的简洁。
- [Intercom](design-md/intercom/preview.html) — 客户消息。友好的蓝色调、对话式界面范式。
- [Linear](design-md/linear-app/preview.html) — 项目管理。极简、精确、紫色点缀。
- [Mintlify](design-md/mintlify/preview.html) — 文档平台。干净、绿色点缀、为阅读优化。
- [Notion](design-md/notion/preview.html) — 一体化工作空间。温暖极简、衬线标题、柔和表面。
- [Resend](design-md/resend/preview.html) — 邮件 API。极简深色主题、等宽字点缀。
- [Zapier](design-md/zapier/preview.html) — 自动化平台。暖橙色、友好的插画驱动。
- [Discord](design-md/discord/preview.html) — 团队与社群聊天平台。深靛蓝画布配 Blurple 渐变、厚重的全大写标题字。
- [Slack](design-md/slack/preview.html) — 职场通讯品牌。深茄紫主色，配奶油薰衣草色的 hero 渐变和胶囊 CTA。

### 设计与创意工具

- [Airtable](design-md/airtable/preview.html) — 电子表格与数据库的混合体。多彩、亲和、结构化数据美学。
- [Clay](design-md/clay/preview.html) — 创意机构。有机形状、柔和渐变、艺术指导式版式。
- [Figma](design-md/figma/preview.html) — 协作设计工具。鲜艳多色，活泼而专业。
- [Framer](design-md/framer/preview.html) — 网站构建器。大胆的黑与蓝，动效优先，设计导向。
- [Miro](design-md/miro/preview.html) — 可视化协作。明黄点缀、无限画布美学。
- [Webflow](design-md/webflow/preview.html) — 可视化建站。蓝色点缀、精致的营销站美学。
- [Mobbin](design-md/mobbin/preview.html) — UI 参考库。画廊白单色、胶囊形按钮、电光蓝点缀。

### 金融科技与加密货币

- [Binance](design-md/binance/preview.html) — 加密货币交易所。单色底上的一抹明黄，交易大厅般的紧迫感。
- [Coinbase](design-md/coinbase/preview.html) — 加密货币交易所。干净的蓝色识别，强调信任、机构感。
- [Kraken](design-md/kraken/preview.html) — 加密货币交易。紫色点缀的深色界面、数据密集的仪表盘。
- [Mastercard](design-md/mastercard/preview.html) — 全球支付网络。暖奶油画布、轨道般的胶囊形、编辑式的暖意。
- [Revolut](design-md/revolut/preview.html) — 数字银行。利落的深色界面、渐变卡片、金融科技式的精确。
- [Stripe](design-md/stripe/preview.html) — 支付基础设施。标志性的紫色渐变、字重 300 的优雅。
- [Wise](design-md/wise/preview.html) — 跨境汇款。亮绿点缀、友好清晰。

### 电商与零售

- [Airbnb](design-md/airbnb/preview.html) — 旅行民宿平台。暖珊瑚色点缀、图片驱动、圆润界面。
- [Meta](design-md/meta/preview.html) — 科技零售店。影像优先、明暗两极的表面、Meta 蓝 CTA。
- [Nike](design-md/nike/preview.html) — 运动零售。单色界面、巨大的全大写字、满幅摄影。
- [Shopify](design-md/shopify/preview.html) — 电商平台。深色优先的电影感、霓虹绿点缀、极细字重。
- [Starbucks](design-md/starbucks/preview.html) — 全球咖啡零售品牌。四层绿色体系、暖奶油画布、全胶囊按钮。

### 媒体与消费科技

- [Apple](design-md/apple/preview.html) — 消费电子。大量留白、SF Pro、电影感影像。
- [HP](design-md/hp/preview.html) — 消费电子目录。白画布配电光蓝点缀、棱角分明的箭头母题。
- [IBM](design-md/ibm/preview.html) — 企业技术。Carbon 设计系统、结构化的蓝色调。
- [NVIDIA](design-md/nvidia/preview.html) — GPU 计算。绿黑能量、技术力量感。
- [Pinterest](design-md/pinterest/preview.html) — 视觉发现。红色点缀、瀑布流网格、图片优先。
- [PlayStation](design-md/playstation/preview.html) — 游戏主机零售。三层表面频道布局、沉稳权威的标题字、青色悬停放大。
- [SpaceX](design-md/spacex/preview.html) — 航天技术。凛冽的黑与白、满幅影像、未来感。
- [Spotify](design-md/spotify/preview.html) — 音乐流媒体。深色上的鲜艳绿、粗体字、专辑封面驱动。
- [The Verge](design-md/theverge/preview.html) — 科技编辑媒体。酸薄荷与紫外光点缀、Manuka 标题字、锐舞传单式的内容块。
- [Uber](design-md/uber/preview.html) — 出行平台。大胆的黑与白、紧凑的字、都市能量。
- [Vodafone](design-md/vodafone/preview.html) — 全球电信品牌。纪念碑式的全大写标题、Vodafone 红的章节色带。
- [WIRED](design-md/wired/preview.html) — 科技杂志。报纸白的高密度版面、定制衬线标题、等宽字引题、墨蓝链接。

### 汽车

- [BMW](design-md/bmw/preview.html) — 豪华汽车。深色高级表面，精确的德式工程美学。
- [BMW M](design-md/bmw-m/preview.html) — 赛车运动。纯黑画布、M 三色条纹、满幅摄影。
- [Bugatti](design-md/bugatti/preview.html) — 超跑品牌。影院级黑画布、单色克制、纪念碑式标题字。
- [Ferrari](design-md/ferrari/preview.html) — 豪华汽车。明暗对照的编辑式排版、法拉利红点缀、影院级黑。
- [Lamborghini](design-md/lamborghini/preview.html) — 超跑品牌。纯黑表面、金色点缀、戏剧性的全大写字体。
- [Renault](design-md/renault/preview.html) — 法国汽车。鲜艳的极光渐变、NouvelR 字体、大胆的能量。
- [Tesla](design-md/tesla/preview.html) — 电动汽车。极致的减法、满视口摄影、近乎为零的界面。

### 复古网页 · DESIGN.md 怀旧

- [Dell (1996)](design-md/dell-1996/preview.html) — 目录时代的 PC 零售网页。黑色页框、扁平色块缎带卡，Helvetica Black 压在 Times Roman 上。
- [Nintendo (2001)](design-md/nintendo-2001/preview.html) — 千禧年“主机金属”网页。拉丝长春花蓝金属面板、点阵碳纤条上的琥珀色导航、描边 Arial Black 盒绘字。

## 重新生成

    git clone --depth 1 https://github.com/VoltAgent/awesome-design-md /tmp/awesome-design-md
    python3 _generator/build_previews.py      # DESIGN.md -> preview_auto.html, preview_auto.css, fonts/
    python3 _generator/merge_themes.py        # preview_light/dark.html -> preview.html, preview.css

这个目录新增风格时，得先有它的源页面 —— 那是 `fetch_getdesign.py` 唯一的用途：

    python3 _generator/fetch_getdesign.py <slug>   # getdesign.md -> preview_light.html, preview_dark.html

`fetch_getdesign.py <slug>` 是这里唯一会联网的脚本，而且是三处：用 headless Chrome 打开线上站点（那站是 JS 应用，curl 只拿得到 8K 空壳）；那次加载本身也会触发那个页面自己的请求 —— Google Fonts、站点的 Cloudflare beacon、页脚的 GitHub 头像 —— 这些随后会从保存的副本里清掉；本地没有的 woff2 再去 jsDelivr 取。所以跑一次 = 在别人的站点上产生一次真实访问。`merge_themes.py` 完全不联网。

两个脚本各写各的文件名，互不相干，所以顺序随意：`build_previews.py` 写 `preview_auto.*`， `merge_themes.py` 写 `preview.*`。

`index.html` 不由任何脚本重新生成 —— 侧栏那些行、中英切换表、以及两个"缺 dark / 缺 auto 页"的回退名单，都直接在文件里维护。

## 许可证

[MIT](LICENSE)，与上游设计文档的许可一致。

## 致谢

- [**VoltAgent/awesome-design-md**](https://github.com/VoltAgent/awesome-design-md) —— 每一页所依据的 `DESIGN.md`，以及本目录沿用的许可证。
- [**getdesign.md**](https://getdesign.md/) —— 那些手工撰写的浅色和深色页，以及侧栏那份列表。
- [**fontsource**](https://fontsource.org/)（jsDelivr 上）—— `fonts/` 里的 woff2，一次取齐，让页面自带字体。
- [**Simple Icons**](https://simpleicons.org/)（CC0 1.0）—— `icons/` 里 19 个 SVG 标识的来源；其余是各组织的 GitHub 头像。
- 品牌名称、商标和设计系统归各自所有者。`DESIGN.md` 来自 VoltAgent（MIT）；浅色和深色页来自 getdesign.md，镜像在这里是为了整套能离线查看。
