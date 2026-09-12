# Phase 6.2 Interactive CLI Run Report

Generated from SQLite session records and linked trace artifacts.

## Original Input

```text
请建一座两层的开敞光庭阅读馆，参考我们确认的概念图右上角：后翼和两侧翼围着庭院，前侧向南真正敞开；从正面能看到庭院、二层回廊、细杆栏杆以及沿庭外露的上楼楼梯。不要做成封闭盒子或藏在墙里的楼梯间。暖米白主体、浅砂色梁柱、深青灰框与金属栏杆、少量木色门扇，窗洞上下对齐，构件有明确的节奏。只建建筑本体，不建家具、植物、招牌、设备或景观摆件。

以下是我委托设计采用的具体方案，尺寸和布置不是从概念图测量得到的。按这些参数建模，不需要再问没有要求的Type、家具或性能等级；发现真正矛盾或能力不支持时请指出，不要自行移位、缩小、封闭或删减。

坐标以建筑外轮廓西南角为原点，向东为X、向北为Y、向上为Z。以下距离均为米，IFC采用毫米。总外轮廓24×18米，只有首层和二层，完成面标高0和3.6。两层墙体各高3.4。首层地板是一整块24×18米混凝土板，底面-0.2、顶面0，庭院地面保留。二层地板底面3.4、顶面3.6，采用前侧敞开的U形：外边界依次为(0,0)、(7.4,0)、(7.4,10.6)、(16.6,10.6)、(16.6,0)、(24,0)、(24,18)、(0,18)，最后闭合。平屋盖与这块U形板相同，底面7、顶面7.2，按一块屋面用途的IfcSlab表达，不增加重复IfcRoof或第三层。不能以矩形整板代替U形板，也不能通过隐藏构件伪装开敞。主露天天井X=7.4到16.6、Y=0到10.6，与南侧外部连通；除了下述外露楼梯和局部上端平台，不在这里加楼板、屋盖、玻璃顶或通高围墙。

每层有西侧阅读室、东侧阅读室和北侧阅览室。西室净范围X=0.2到4.8、Y=0.2到12.9；东室X=19.2到23.8、Y=0.2到12.9；北室X=0.2到23.8、Y=13.1到17.8。房间各高3.4。临庭是半室外有顶回廊：西侧X=5到7.4、Y=0到10.6；东侧X=16.6到19、Y=0到10.6；北侧X=5到19、Y=10.6到12.9。每层分别建立这三个回廊空间，按EXTERNAL表达；三段在边界相接，不要重复堆叠空间。光庭不建跨层室内空间。回廊及平台只以实际板和柱梁围成，不加实墙封闭临庭面。

墙厚200毫米。每层严格采用下列8条墙的实体平面范围，墙角、墙端只相接不重叠，Z从本层完成面开始。南侧中段敞开，不能自动补墙：
- 西外墙X=0到0.2、Y=0到18；东外墙X=23.8到24、Y=0到18。
- 北外墙X=0.2到23.8、Y=17.8到18。
- 西前墙X=0.2到4.8、Y=0到0.2；东前墙X=19.2到23.8、Y=0到0.2。
- 西侧面向庭院的墙X=4.8到5、Y=0到12.9；东侧X=19到19.2、Y=0到12.9。
- 北侧房间南墙是一整条X=0.2到23.8、Y=12.9到13.1，不分成重叠段。
两层共16条墙。

回廊边缘布置方柱和连续梁，呈现清楚的两层柱廊，不进行结构计算。每层10根300×300毫米混凝土柱。西列X=7.1到7.4，东列X=16.6到16.9；两列柱的Y范围各为0到0.3、3.4到3.7、6.8到7.1、10.3到10.6，每列4根。北廊再加2根，Y=10.6到10.9，X分别10.35到10.65及13.35到13.65。首层柱从Z=0到3.1，二层柱从3.6到6.7，共20根。每层3条混凝土梁：西梁X=7.1到7.4、Y=0到10.9；东梁X=16.6到16.9、Y=0到10.9；北梁X=7.4到16.6、Y=10.6到10.9。首层梁Z=3.1到3.4，二层梁Z=6.7到7。柱梁按真实IfcColumn和IfcBeam表达，梁端相接，柱顶抵梁底。不要用墙冒充柱梁，或自动补其他梁柱。

庭院右侧设一座外露直跑混凝土楼梯，从南向北上升，X=14.8到16.6、Y=2.2到8.2，宽1.8米，从首层0米上到二层3.6米，共20级，每级180毫米高、水平进深300毫米。真实梯段从属于楼梯父项。楼梯下端的Y=0到2.2是地面到达区，不设门或墙阻挡。二层上端平台单独加一块板，X=14.8到16.6、Y=8.2到10.6，底面3.4、顶面3.6；平台北边与北回廊相接，东边与东回廊相接。平台和U形板不能有正面积重叠。楼梯在主U形楼板外露空区内，不需要额外挖一个封闭洞口，更不能给它加楼梯间墙。

护栏采用单一钢材的深灰细杆形式，有立柱、竖向细杆、顶部连续扶手和下横杆，使用系统metal-picket基本护栏模板。不要换成玻璃板或不透明整板。水平护栏底面标高3.6，栏高1.1米、深40毫米；下表为其中心基线端点，表中未写Z的端点均为3.6，模板端头不能超出端点。柱间栏杆以柱面为止，不穿过混凝土柱：
- 西廊3段，X=7.38，Y分别0.3到3.4、3.7到6.8、7.1到10.3。
- 东廊3段，X=16.62，Y分别0.3到3.4、3.7到6.8、7.1到8.2；Y=8.2以北与平台连通，不补一段横挡。
- 北廊3段，Y=10.62，X分别7.4到10.35、10.65到13.35、13.65到14.8。
- 两翼前端各1段，Y=0.02，X分别5到7.1和16.9到19。
- 楼梯上端平台西侧1段，X=14.82、Y=8.2到10.6。平台南侧是楼梯到达口，不横加栏杆。
- 梯段左右各1段斜护栏，基线从(X,2.2,0)到(X,8.2,3.6)，X分别14.82和16.58，栏高按基线上方的竖直高度1.1米，深40毫米；立柱和细杆保持竖直，扶手随楼梯上升。不能把一段水平栏杆旋转到导致立柱也倾斜。
共14段护栏。模板默认杆件尺寸和间距沿用其已校验版本，不另行猜参数；不需要复杂五金、曲线栏杆或多材料附件。平台与楼梯的连接及防护情况应在审查报告中说明，不能将建模成功说成已证明建筑安全。

每层有3扇面向回廊的基本木门：西阅读室门在西侧临庭墙，中心Y=8，宽1.2、高2.4，左单开；东室门在东侧临庭墙，中心Y=8，同尺寸右单开；北室门在北室南墙，中心X=12，宽1.4、高2.4，左单开。门底均在本层完成面，不额外创建封闭南侧主入口。共6扇门，表达门框和门扇；仅要求上述左/右单开，不推断房间相对开启方向，不要求推拉或双扇门。

每层窗表如下，两个楼层同轴对齐；均为双竖面板窗、窗台高0.6、窗高2.4。窗头在完成面以上3米。每窗有独立洞口、宿主墙、窗框和两块玻璃：
- 西外墙和东外墙，中心Y=3、7、11、16，各4窗，宽2米。
- 北外墙，中心X=4、9、15、20，共4窗，宽2米。
- 西、东侧临庭墙，中心Y=2、5、11，各3窗，宽2米；与Y=8的门分开。
- 北室南墙，中心X=7和17，共2窗，宽2米，与中门分开。
- 西前墙、东前墙，中心X=2.5和21.5，各1窗，宽2.6米。
每层22窗，共44窗。墙体中的窗洞和门洞必须真实切除，不能将窗门放在未开洞的实墙上。

全部墙、板、楼梯、梁柱明确使用单一混凝土材料；门整体材料为木材，护栏整体为钢材。窗是组合构件，不声明整窗为纯玻璃或纯金属，不要求当前不支持的逐部件物理材料。没有要求共享Type或Style，请不创建额外用户类型；编译器必须的最小合法附件除外。

顶层使用neutral-architectural协调风格，明确墙、全部板、混凝土楼梯的整件颜色#E6E0D3；梁柱颜色#D2C7B3；护栏整件颜色#304B4D且不透明。所有窗框和门框为#304B4D，门扇为#A66F43，窗玻璃透明度0.65，保留玻璃默认色。框、扇、玻璃分别用部件样式表达，不能把整窗都涂成框色或都变透明。外观不授权补写材料性能。

请输出完整IFC2X3。不要创建未指定的强度、耐火、热工等性能属性，不填零、null或未知。报告分别列出输入符合性、确定性检查、真实Provider阶段以及仍需人工或工程核验的问题。不要声称可直接施工，也不要把AI概念图当作最终IFC的截图。

```

## Transcript

```json
[
  {
    "created_at": "2026-09-12T12:06:30+00:00",
    "role": "user",
    "text": "请建一座两层的开敞光庭阅读馆，参考我们确认的概念图右上角：后翼和两侧翼围着庭院，前侧向南真正敞开；从正面能看到庭院、二层回廊、细杆栏杆以及沿庭外露的上楼楼梯。不要做成封闭盒子或藏在墙里的楼梯间。暖米白主体、浅砂色梁柱、深青灰框与金属栏杆、少量木色门扇，窗洞上下对齐，构件有明确的节奏。只建建筑本体，不建家具、植物、招牌、设备或景观摆件。\n\n以下是我委托设计采用的具体方案，尺寸和布置不是从概念图测量得到的。按这些参数建模，不需要再问没有要求的Type、家具或性能等级；发现真正矛盾或能力不支持时请指出，不要自行移位、缩小、封闭或删减。\n\n坐标以建筑外轮廓西南角为原点，向东为X、向北为Y、向上为Z。以下距离均为米，IFC采用毫米。总外轮廓24×18米，只有首层和二层，完成面标高0和3.6。两层墙体各高3.4。首层地板是一整块24×18米混凝土板，底面-0.2、顶面0，庭院地面保留。二层地板底面3.4、顶面3.6，采用前侧敞开的U形：外边界依次为(0,0)、(7.4,0)、(7.4,10.6)、(16.6,10.6)、(16.6,0)、(24,0)、(24,18)、(0,18)，最后闭合。平屋盖与这块U形板相同，底面7、顶面7.2，按一块屋面用途的IfcSlab表达，不增加重复IfcRoof或第三层。不能以矩形整板代替U形板，也不能通过隐藏构件伪装开敞。主露天天井X=7.4到16.6、Y=0到10.6，与南侧外部连通；除了下述外露楼梯和局部上端平台，不在这里加楼板、屋盖、玻璃顶或通高围墙。\n\n每层有西侧阅读室、东侧阅读室和北侧阅览室。西室净范围X=0.2到4.8、Y=0.2到12.9；东室X=19.2到23.8、Y=0.2到12.9；北室X=0.2到23.8、Y=13.1到17.8。房间各高3.4。临庭是半室外有顶回廊：西侧X=5到7.4、Y=0到10.6；东侧X=16.6到19、Y=0到10.6；北侧X=5到19、Y=10.6到12.9。每层分别建立这三个回廊空间，按EXTERNAL表达；三段在边界相接，不要重复堆叠空间。光庭不建跨层室内空间。回廊及平台只以实际板和柱梁围成，不加实墙封闭临庭面。\n\n墙厚200毫米。每层严格采用下列8条墙的实体平面范围，墙角、墙端只相接不重叠，Z从本层完成面开始。南侧中段敞开，不能自动补墙：\n- 西外墙X=0到0.2、Y=0到18；东外墙X=23.8到24、Y=0到18。\n- 北外墙X=0.2到23.8、Y=17.8到18。\n- 西前墙X=0.2到4.8、Y=0到0.2；东前墙X=19.2到23.8、Y=0到0.2。\n- 西侧面向庭院的墙X=4.8到5、Y=0到12.9；东侧X=19到19.2、Y=0到12.9。\n- 北侧房间南墙是一整条X=0.2到23.8、Y=12.9到13.1，不分成重叠段。\n两层共16条墙。\n\n回廊边缘布置方柱和连续梁，呈现清楚的两层柱廊，不进行结构计算。每层10根300×300毫米混凝土柱。西列X=7.1到7.4，东列X=16.6到16.9；两列柱的Y范围各为0到0.3、3.4到3.7、6.8到7.1、10.3到10.6，每列4根。北廊再加2根，Y=10.6到10.9，X分别10.35到10.65及13.35到13.65。首层柱从Z=0到3.1，二层柱从3.6到6.7，共20根。每层3条混凝土梁：西梁X=7.1到7.4、Y=0到10.9；东梁X=16.6到16.9、Y=0到10.9；北梁X=7.4到16.6、Y=10.6到10.9。首层梁Z=3.1到3.4，二层梁Z=6.7到7。柱梁按真实IfcColumn和IfcBeam表达，梁端相接，柱顶抵梁底。不要用墙冒充柱梁，或自动补其他梁柱。\n\n庭院右侧设一座外露直跑混凝土楼梯，从南向北上升，X=14.8到16.6、Y=2.2到8.2，宽1.8米，从首层0米上到二层3.6米，共20级，每级180毫米高、水平进深300毫米。真实梯段从属于楼梯父项。楼梯下端的Y=0到2.2是地面到达区，不设门或墙阻挡。二层上端平台单独加一块板，X=14.8到16.6、Y=8.2到10.6，底面3.4、顶面3.6；平台北边与北回廊相接，东边与东回廊相接。平台和U形板不能有正面积重叠。楼梯在主U形楼板外露空区内，不需要额外挖一个封闭洞口，更不能给它加楼梯间墙。\n\n护栏采用单一钢材的深灰细杆形式，有立柱、竖向细杆、顶部连续扶手和下横杆，使用系统metal-picket基本护栏模板。不要换成玻璃板或不透明整板。水平护栏底面标高3.6，栏高1.1米、深40毫米；下表为其中心基线端点，表中未写Z的端点均为3.6，模板端头不能超出端点。柱间栏杆以柱面为止，不穿过混凝土柱：\n- 西廊3段，X=7.38，Y分别0.3到3.4、3.7到6.8、7.1到10.3。\n- 东廊3段，X=16.62，Y分别0.3到3.4、3.7到6.8、7.1到8.2；Y=8.2以北与平台连通，不补一段横挡。\n- 北廊3段，Y=10.62，X分别7.4到10.35、10.65到13.35、13.65到14.8。\n- 两翼前端各1段，Y=0.02，X分别5到7.1和16.9到19。\n- 楼梯上端平台西侧1段，X=14.82、Y=8.2到10.6。平台南侧是楼梯到达口，不横加栏杆。\n- 梯段左右各1段斜护栏，基线从(X,2.2,0)到(X,8.2,3.6)，X分别14.82和16.58，栏高按基线上方的竖直高度1.1米，深40毫米；立柱和细杆保持竖直，扶手随楼梯上升。不能把一段水平栏杆旋转到导致立柱也倾斜。\n共14段护栏。模板默认杆件尺寸和间距沿用其已校验版本，不另行猜参数；不需要复杂五金、曲线栏杆或多材料附件。平台与楼梯的连接及防护情况应在审查报告中说明，不能将建模成功说成已证明建筑安全。\n\n每层有3扇面向回廊的基本木门：西阅读室门在西侧临庭墙，中心Y=8，宽1.2、高2.4，左单开；东室门在东侧临庭墙，中心Y=8，同尺寸右单开；北室门在北室南墙，中心X=12，宽1.4、高2.4，左单开。门底均在本层完成面，不额外创建封闭南侧主入口。共6扇门，表达门框和门扇；仅要求上述左/右单开，不推断房间相对开启方向，不要求推拉或双扇门。\n\n每层窗表如下，两个楼层同轴对齐；均为双竖面板窗、窗台高0.6、窗高2.4。窗头在完成面以上3米。每窗有独立洞口、宿主墙、窗框和两块玻璃：\n- 西外墙和东外墙，中心Y=3、7、11、16，各4窗，宽2米。\n- 北外墙，中心X=4、9、15、20，共4窗，宽2米。\n- 西、东侧临庭墙，中心Y=2、5、11，各3窗，宽2米；与Y=8的门分开。\n- 北室南墙，中心X=7和17，共2窗，宽2米，与中门分开。\n- 西前墙、东前墙，中心X=2.5和21.5，各1窗，宽2.6米。\n每层22窗，共44窗。墙体中的窗洞和门洞必须真实切除，不能将窗门放在未开洞的实墙上。\n\n全部墙、板、楼梯、梁柱明确使用单一混凝土材料；门整体材料为木材，护栏整体为钢材。窗是组合构件，不声明整窗为纯玻璃或纯金属，不要求当前不支持的逐部件物理材料。没有要求共享Type或Style，请不创建额外用户类型；编译器必须的最小合法附件除外。\n\n顶层使用neutral-architectural协调风格，明确墙、全部板、混凝土楼梯的整件颜色#E6E0D3；梁柱颜色#D2C7B3；护栏整件颜色#304B4D且不透明。所有窗框和门框为#304B4D，门扇为#A66F43，窗玻璃透明度0.65，保留玻璃默认色。框、扇、玻璃分别用部件样式表达，不能把整窗都涂成框色或都变透明。外观不授权补写材料性能。\n\n请输出完整IFC2X3。不要创建未指定的强度、耐火、热工等性能属性，不填零、null或未知。报告分别列出输入符合性、确定性检查、真实Provider阶段以及仍需人工或工程核验的问题。不要声称可直接施工，也不要把AI概念图当作最终IFC的截图。\n",
    "turn_index": 0
  },
  {
    "created_at": "2026-09-12T12:06:30+00:00",
    "role": "user",
    "text": "1.等一下如果不是从头到尾的话 我建议你进行一个修复 然后重新从头到尾跑一遍\n2.我们似乎不支持柱子？如有必要可以添加在generation的部分\n3.基本做成右上角的形式即可 不需要家具和植物",
    "turn_index": 1
  }
]
```

## Design Brief Agent

- [design-brief/input.txt](design-brief/input.txt)
- [design-brief/conversation.json](design-brief/conversation.json)
- [design-brief/prompt-rendered.md](design-brief/prompt-rendered.md)
- [design-brief/request.redacted.json](design-brief/request.redacted.json)
- [design-brief/response.raw.json](design-brief/response.raw.json)
- [design-brief/model-text.txt](design-brief/model-text.txt)
- [design-brief/design-brief.json](design-brief/design-brief.json)
- [design-brief/validation.json](design-brief/validation.json)
- [design-brief/metrics.json](design-brief/metrics.json)

## BIM JSON Generator

- [generator/prompt-rendered.md](generator/prompt-rendered.md)
- [generator/request.redacted.json](generator/request.redacted.json)
- [generator/response.raw.json](generator/response.raw.json)
- [generator/model-text.txt](generator/model-text.txt)
- [generator/candidate.json](generator/candidate.json)
- [generator/validation.json](generator/validation.json)
- [generator/metrics.json](generator/metrics.json)

## Repair Route

- [repair/route.json](repair/route.json)
- [repair/repair-attempts.json](repair/repair-attempts.json)
- [repair/source-validation.json](repair/source-validation.json)
- [repair/metrics.json](repair/metrics.json)

## Audit Agent

- [audit/prompt-rendered.md](audit/prompt-rendered.md)
- [audit/request.redacted.json](audit/request.redacted.json)
- [audit/response.raw.json](audit/response.raw.json)
- [audit/model-text.txt](audit/model-text.txt)
- [audit/audit-report.json](audit/audit-report.json)
- [audit/validation.json](audit/validation.json)
- [audit/metrics.json](audit/metrics.json)

## Semantic Coverage

- [semantic-capabilities.json](semantic-capabilities.json)
- [semantic-coverage.json](semantic-coverage.json)
- [semantic-geometry-expectation.json](semantic-geometry-expectation.json)

## Deterministic Gates

- [acceptance-metrics.json](acceptance-metrics.json)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)
- [secret-scan.json](secret-scan.json)

```json
{
  "case_id": "ce8116ce095acdcf",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-open-court-20260912\\rerun-03\\live-run\\runs\\ce8116ce095acdcf\\output.ifc",
  "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-open-court-20260912\\rerun-03\\live-run\\runs\\ce8116ce095acdcf",
  "report_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-open-court-20260912\\rerun-03\\live-run\\runs\\ce8116ce095acdcf\\report.md",
  "secret_finding_count": 0,
  "stage": "final-acceptance",
  "valid": true
}
```

## Revision and ChangeSet History

```json
{
  "issues": [],
  "reason": "No candidate revision sidecar exists for this legacy run.",
  "status": "not_applicable"
}
```


## Final Artifacts

- [output.ifc](output.ifc)
- [candidate.json](candidate.json)
- [report.md](report.md)

## Session Export

- [runs/ce8116ce095acdcf/session-export.json](runs/ce8116ce095acdcf/session-export.json)

## Session DB Evidence

### Events

```json
[
  {
    "created_at": "2026-09-12T12:12:30+00:00",
    "event_index": 0,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "ce8116ce095acdcf",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "live",
      "output_dir": "dataset/processed/ifc-presentation-validation/courtyard-library-open-court-20260912/rerun-03/live-run/runs/ce8116ce095acdcf/generator",
      "response_id": "fd3e18d0-7072-41e4-93ee-b8799734e7a4",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-09-12T12:12:31+00:00",
    "event_index": 1,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:cdf910348007cc2135b22e0c42a46bae6ba8ca958df4f287a2f9ec1bb708cf30",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.3/1.0",
      "case_id": "ce8116ce095acdcf",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 179,
        "capability_profile_hash": "sha256:cdf910348007cc2135b22e0c42a46bae6ba8ca958df4f287a2f9ec1bb708cf30",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.3/1.0",
        "case_id": "ce8116ce095acdcf",
        "custom_property_policy": {
          "counts_as_semantic_support": false,
          "state": "preserved_text_only"
        },
        "facts": [
          {
            "coverage_state": "represented",
            "path": "/known_facts/appearance/profile",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "neutral-architectural"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/appearance/style_notes",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "暖米白主体、浅砂色梁柱、深青灰框与金属栏杆、少量木色门扇；后翼与两侧翼围合庭院，南侧敞开，两层柱廊与上下对齐窗洞形成明确节奏"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/beams",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "bounds_mm": {
                  "x": [
                    7100,
                    7400
                  ],
                  "y": [
                    0,
                    10900
                  ],
                  "z": [
                    3100,
                    3400
                  ]
                },
                "id": "storey-1-beam-west",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    16600,
                    16900
                  ],
                  "y": [
                    0,
                    10900
                  ],
                  "z": [
                    3100,
                    3400
                  ]
                },
                "id": "storey-1-beam-east",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    7400,
                    16600
                  ],
                  "y": [
                    10600,
                    10900
                  ],
                  "z": [
                    3100,
                    3400
                  ]
                },
                "id": "storey-1-beam-north",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    7100,
                    7400
                  ],
                  "y": [
                    0,
                    10900
                  ],
                  "z": [
                    6700,
                    7000
                  ]
                },
                "id": "storey-2-beam-west",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    16600,
                    16900
                  ],
                  "y": [
                    0,
                    10900
                  ],
                  "z": [
                    6700,
                    7000
                  ]
                },
                "id": "storey-2-beam-east",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    7400,
                    16600
                  ],
                  "y": [
                    10600,
                    10900
                  ],
                  "z": [
                    6700,
                    7000
                  ]
                },
                "id": "storey-2-beam-north",
                "storey": "storey-2"
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/concept_reference",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "已确认概念图右上角；尺寸与布置不按概念图测量"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/coordinate_frame/origin",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "建筑外轮廓西南角"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/coordinate_frame/unit",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "MILLIMETRE"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/coordinate_frame/x",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "东"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/coordinate_frame/y",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "北"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/coordinate_frame/z",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "上"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/courtyard/bounds/x",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              7400,
              16600
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/courtyard/bounds/y",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              0,
              10600
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/courtyard/note",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "主露天天井；除指定外露楼梯与局部上端平台外不加楼板、屋盖、玻璃顶或通高围墙"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/courtyard/open_to",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "south"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/name",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "开敞光庭阅读馆"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/polygon",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              [
                0,
                0
              ],
              [
                24000,
                0
              ],
              [
                24000,
                18000
              ],
              [
                0,
                18000
              ],
              [
                0,
                0
              ]
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/x_max",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 24000
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/x_min",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 0
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/y_max",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 18000
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/y_min",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 0
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/scope_exclusions",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              "家具",
              "植物",
              "招牌",
              "设备",
              "景观摆件"
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/storey_count",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 2
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/storey_height_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 3400
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/wall_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 200
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/columns",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "bounds_mm": {
                  "x": [
                    7100,
                    7400
                  ],
                  "y": [
                    0,
                    300
                  ],
                  "z": [
                    0,
                    3100
                  ]
                },
                "id": "storey-1-col-west-1",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    7100,
                    7400
                  ],
                  "y": [
                    3400,
                    3700
                  ],
                  "z": [
                    0,
                    3100
                  ]
                },
                "id": "storey-1-col-west-2",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    7100,
                    7400
                  ],
                  "y": [
                    6800,
                    7100
                  ],
                  "z": [
                    0,
                    3100
                  ]
                },
                "id": "storey-1-col-west-3",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    7100,
                    7400
                  ],
                  "y": [
                    10300,
                    10600
                  ],
                  "z": [
                    0,
                    3100
                  ]
                },
                "id": "storey-1-col-west-4",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    16600,
                    16900
                  ],
                  "y": [
                    0,
                    300
                  ],
                  "z": [
                    0,
                    3100
                  ]
                },
                "id": "storey-1-col-east-1",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    16600,
                    16900
                  ],
                  "y": [
                    3400,
                    3700
                  ],
                  "z": [
                    0,
                    3100
                  ]
                },
                "id": "storey-1-col-east-2",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    16600,
                    16900
                  ],
                  "y": [
                    6800,
                    7100
                  ],
                  "z": [
                    0,
                    3100
                  ]
                },
                "id": "storey-1-col-east-3",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    16600,
                    16900
                  ],
                  "y": [
                    10300,
                    10600
                  ],
                  "z": [
                    0,
                    3100
                  ]
                },
                "id": "storey-1-col-east-4",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    10350,
                    10650
                  ],
                  "y": [
                    10600,
                    10900
                  ],
                  "z": [
                    0,
                    3100
                  ]
                },
                "id": "storey-1-col-north-1",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    13350,
                    13650
                  ],
                  "y": [
                    10600,
                    10900
                  ],
                  "z": [
                    0,
                    3100
                  ]
                },
                "id": "storey-1-col-north-2",
                "storey": "storey-1"
              },
              {
                "bounds_mm": {
                  "x": [
                    7100,
                    7400
                  ],
                  "y": [
                    0,
                    300
                  ],
                  "z": [
                    3600,
                    6700
                  ]
                },
                "id": "storey-2-col-west-1",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    7100,
                    7400
                  ],
                  "y": [
                    3400,
                    3700
                  ],
                  "z": [
                    3600,
                    6700
                  ]
                },
                "id": "storey-2-col-west-2",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    7100,
                    7400
                  ],
                  "y": [
                    6800,
                    7100
                  ],
                  "z": [
                    3600,
                    6700
                  ]
                },
                "id": "storey-2-col-west-3",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    7100,
                    7400
                  ],
                  "y": [
                    10300,
                    10600
                  ],
                  "z": [
                    3600,
                    6700
                  ]
                },
                "id": "storey-2-col-west-4",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    16600,
                    16900
                  ],
                  "y": [
                    0,
                    300
                  ],
                  "z": [
                    3600,
                    6700
                  ]
                },
                "id": "storey-2-col-east-1",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    16600,
                    16900
                  ],
                  "y": [
                    3400,
                    3700
                  ],
                  "z": [
                    3600,
                    6700
                  ]
                },
                "id": "storey-2-col-east-2",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    16600,
                    16900
                  ],
                  "y": [
                    6800,
                    7100
                  ],
                  "z": [
                    3600,
                    6700
                  ]
                },
                "id": "storey-2-col-east-3",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    16600,
                    16900
                  ],
                  "y": [
                    10300,
                    10600
                  ],
                  "z": [
                    3600,
                    6700
                  ]
                },
                "id": "storey-2-col-east-4",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    10350,
                    10650
                  ],
                  "y": [
                    10600,
                    10900
                  ],
                  "z": [
                    3600,
                    6700
                  ]
                },
                "id": "storey-2-col-north-1",
                "storey": "storey-2"
              },
              {
                "bounds_mm": {
                  "x": [
                    13350,
                    13650
                  ],
                  "y": [
                    10600,
                    10900
                  ],
                  "z": [
                    3600,
                    6700
                  ]
                },
                "id": "storey-2-col-north-2",
                "storey": "storey-2"
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/floor_slabs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "bounds": {
                  "x": [
                    0,
                    24000
                  ],
                  "y": [
                    0,
                    18000
                  ]
                },
                "id": "slab-ground-1",
                "note": "一整块24×18米混凝土板，底面-0.2、顶面0；庭院地面保留",
                "storey": "storey-1",
                "thickness_mm": 200,
                "top_elevation_mm": 0
              },
              {
                "id": "slab-u-floor-2",
                "note": "前侧敞开的U形板，不得以矩形整板代替",
                "polygon": [
                  [
                    0,
                    0
                  ],
                  [
                    7400,
                    0
                  ],
                  [
                    7400,
                    10600
                  ],
                  [
                    16600,
                    10600
                  ],
                  [
                    16600,
                    0
                  ],
                  [
                    24000,
                    0
                  ],
                  [
                    24000,
                    18000
                  ],
                  [
                    0,
                    18000
                  ],
                  [
                    0,
                    0
                  ]
                ],
                "storey": "storey-2",
                "thickness_mm": 200,
                "top_elevation_mm": 3600
              },
              {
                "bounds": {
                  "x": [
                    14800,
                    16600
                  ],
                  "y": [
                    8200,
                    10600
                  ]
                },
                "id": "slab-landing-2",
                "note": "楼梯上端平台，与U形板仅边界相接，无正面积重叠；北接北回廊，东接东回廊",
                "storey": "storey-2",
                "thickness_mm": 200,
                "top_elevation_mm": 3600
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/plan_constraints",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "checks": [
                  "non_overlapping"
                ],
                "derived_wall_ids": [
                  "storey-1-wall-west-exterior",
                  "storey-1-wall-east-exterior",
                  "storey-1-wall-north-exterior",
                  "storey-1-wall-west-front",
                  "storey-1-wall-east-front",
                  "storey-1-wall-west-court",
                  "storey-1-wall-east-court",
                  "storey-1-wall-north-room-south"
                ],
                "id": "pc-storey-1-wall-layout",
                "kind": "wall_layout",
                "outline_ref": "/known_facts/building/outline/polygon",
                "source_turns": [
                  "turn-user-001"
                ],
                "storey_ref": "/known_facts/storeys/0"
              },
              {
                "checks": [
                  "non_overlapping"
                ],
                "derived_wall_ids": [
                  "storey-2-wall-west-exterior",
                  "storey-2-wall-east-exterior",
                  "storey-2-wall-north-exterior",
                  "storey-2-wall-west-front",
                  "storey-2-wall-east-front",
                  "storey-2-wall-west-court",
                  "storey-2-wall-east-court",
                  "storey-2-wall-north-room-south"
                ],
                "id": "pc-storey-2-wall-layout",
                "kind": "wall_layout",
                "outline_ref": "/known_facts/building/outline/polygon",
                "source_turns": [
                  "turn-user-001"
                ],
                "storey_ref": "/known_facts/storeys/1"
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/railings",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "alignment_target": "西列柱间，止于柱面",
                "end_mm": [
                  7380,
                  3400,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-west-1",
                "start_mm": [
                  7380,
                  300,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "西列柱间，止于柱面",
                "end_mm": [
                  7380,
                  6800,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-west-2",
                "start_mm": [
                  7380,
                  3700,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "西列柱间，止于柱面",
                "end_mm": [
                  7380,
                  10300,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-west-3",
                "start_mm": [
                  7380,
                  7100,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "东列柱间，止于柱面",
                "end_mm": [
                  16620,
                  3400,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-east-1",
                "start_mm": [
                  16620,
                  300,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "东列柱间，止于柱面",
                "end_mm": [
                  16620,
                  6800,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-east-2",
                "start_mm": [
                  16620,
                  3700,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "东列柱间，止于柱面；Y=8.2以北与平台连通，不补横挡",
                "end_mm": [
                  16620,
                  8200,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-east-3",
                "start_mm": [
                  16620,
                  7100,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "北廊柱间，止于柱面",
                "end_mm": [
                  10350,
                  10620,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-north-1",
                "start_mm": [
                  7400,
                  10620,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "北廊柱间，止于柱面",
                "end_mm": [
                  13350,
                  10620,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-north-2",
                "start_mm": [
                  10650,
                  10620,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "北廊柱间，止于平台西边",
                "end_mm": [
                  14800,
                  10620,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-north-3",
                "start_mm": [
                  13650,
                  10620,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "西翼前端，止于柱面",
                "end_mm": [
                  7100,
                  20,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-front-west",
                "start_mm": [
                  5000,
                  20,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "东翼前端，止于柱面",
                "end_mm": [
                  19000,
                  20,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-front-east",
                "start_mm": [
                  16900,
                  20,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "楼梯上端平台西侧；平台南侧为楼梯到达口，不横加栏杆",
                "end_mm": [
                  14820,
                  10600,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-2-rail-landing-west",
                "start_mm": [
                  14820,
                  8200,
                  3600
                ],
                "storey": "storey-2",
                "thickness_mm": 40
              },
              {
                "alignment_target": "梯段左侧斜护栏；栏高按基线上方竖直高度，立柱与细杆保持竖直，扶手随梯段上升",
                "end_mm": [
                  14820,
                  8200,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-1-rail-stair-left",
                "start_mm": [
                  14820,
                  2200,
                  0
                ],
                "storey": "storey-1",
                "thickness_mm": 40
              },
              {
                "alignment_target": "梯段右侧斜护栏；栏高按基线上方竖直高度，立柱与细杆保持竖直，扶手随梯段上升",
                "end_mm": [
                  16580,
                  8200,
                  3600
                ],
                "height_mm": 1100,
                "id": "storey-1-rail-stair-right",
                "start_mm": [
                  16580,
                  2200,
                  0
                ],
                "storey": "storey-1",
                "thickness_mm": 40
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/bottom_elevation_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 7000
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/id",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "slab-roof"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/ifc_class",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "IfcSlab"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/note",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "与二层U形板相同平面；按一块屋面用途IfcSlab表达，不增加IfcRoof或第三层"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/polygon",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              [
                0,
                0
              ],
              [
                7400,
                0
              ],
              [
                7400,
                10600
              ],
              [
                16600,
                10600
              ],
              [
                16600,
                0
              ],
              [
                24000,
                0
              ],
              [
                24000,
                18000
              ],
              [
                0,
                18000
              ],
              [
                0,
                0
              ]
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/predefined_type",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "ROOF"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/storey",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "storey-2"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 200
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_requirements",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-1-wall-west-exterior",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-1-wall-east-exterior",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-1-wall-north-exterior",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-1-wall-west-front",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-1-wall-east-front",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-1-wall-west-court",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-1-wall-east-court",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-1-wall-north-room-south",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-2-wall-west-exterior",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-2-wall-east-exterior",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-2-wall-north-exterior",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-2-wall-west-front",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-2-wall-east-front",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-2-wall-west-court",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-2-wall-east-court",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "storey-2-wall-north-room-south",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "slab-ground-1",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "slab-u-floor-2",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "slab-landing-2",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "slab-roof",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "stair-1",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                },
                "entity_id": "stair-flight-1",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-beam-west",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-beam-east",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-beam-north",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-beam-west",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-beam-east",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-beam-north",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-col-west-1",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-col-west-2",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-col-west-3",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-col-west-4",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-col-east-1",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-col-east-2",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-col-east-3",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-col-east-4",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-col-north-1",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-1-col-north-2",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-col-west-1",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-col-west-2",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-col-west-3",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-col-west-4",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-col-east-1",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-col-east-2",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-col-east-3",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-col-east-4",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-col-north-1",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                },
                "entity_id": "storey-2-col-north-2",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-west-1",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-west-2",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-west-3",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-east-1",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-east-2",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-east-3",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-north-1",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-north-2",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-north-3",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-front-west",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-front-east",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-2-rail-landing-west",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-1-rail-stair-left",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "appearance": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                },
                "entity_id": "storey-1-rail-stair-right",
                "material": {
                  "kind": "single_material",
                  "name": "钢材"
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-1-door-west-reading",
                "material": {
                  "kind": "single_material",
                  "name": "木材"
                },
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-door-east-reading",
                "material": {
                  "kind": "single_material",
                  "name": "木材"
                },
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-door-north-reading",
                "material": {
                  "kind": "single_material",
                  "name": "木材"
                },
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-door-west-reading",
                "material": {
                  "kind": "single_material",
                  "name": "木材"
                },
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-door-east-reading",
                "material": {
                  "kind": "single_material",
                  "name": "木材"
                },
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-door-north-reading",
                "material": {
                  "kind": "single_material",
                  "name": "木材"
                },
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-west-ext-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-west-ext-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-west-ext-3",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-west-ext-4",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-east-ext-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-east-ext-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-east-ext-3",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-east-ext-4",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-north-ext-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-north-ext-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-north-ext-3",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-north-ext-4",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-west-court-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-west-court-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-west-court-3",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-east-court-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-east-court-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-east-court-3",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-north-room-south-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-north-room-south-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-west-front",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-1-win-east-front",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-west-ext-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-west-ext-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-west-ext-3",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-west-ext-4",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-east-ext-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-east-ext-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-east-ext-3",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-east-ext-4",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-north-ext-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-north-ext-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-north-ext-3",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-north-ext-4",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-west-court-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-west-court-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-west-court-3",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-east-court-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-east-court-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-east-court-3",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-north-room-south-1",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-north-room-south-2",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-west-front",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "storey-2-win-east-front",
                "part_appearance": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                },
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_review/appearance/source_turns",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              "turn-user-001"
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_review/appearance/status",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "specified"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_review/material/source_turns",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              "turn-user-001"
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_review/material/status",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "specified"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_review/property/source_turns",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              "turn-user-001"
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_review/property/status",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "not_specified"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_review/template/source_turns",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              "turn-user-001"
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_review/template/status",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "specified"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_review/type/source_turns",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              "turn-user-001",
              "turn-user-concept-revision"
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/semantic_review/type/status",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "not_specified"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/stairs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "bounds": {
                  "x": [
                    14800,
                    16600
                  ],
                  "y": [
                    2200,
                    8200
                  ]
                },
                "end_elevation_mm": 3600,
                "flight_ids": [
                  "stair-flight-1"
                ],
                "from_storey": "storey-1",
                "id": "stair-1",
                "note": "外露直跑混凝土楼梯，位于主U形楼板外露空区内；Y=0到2.2为地面到达区，不设门或墙阻挡，无楼梯间墙、无额外封闭洞口",
                "number_of_risers": 20,
                "number_of_treads": 20,
                "riser_height_mm": 180,
                "run_direction": "north",
                "start_elevation_mm": 0,
                "to_storey": "storey-2",
                "tread_depth_mm": 300,
                "width_mm": 1800
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/storeys",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "doors": [
                  {
                    "center_global_mm": [
                      4900,
                      8000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-west-court",
                    "id": "storey-1-door-west-reading",
                    "operation": "left",
                    "sill_height_mm": 0,
                    "width_mm": 1200
                  },
                  {
                    "center_global_mm": [
                      19100,
                      8000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-east-court",
                    "id": "storey-1-door-east-reading",
                    "operation": "right",
                    "sill_height_mm": 0,
                    "width_mm": 1200
                  },
                  {
                    "center_global_mm": [
                      12000,
                      13000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-north-room-south",
                    "id": "storey-1-door-north-reading",
                    "operation": "left",
                    "sill_height_mm": 0,
                    "width_mm": 1400
                  }
                ],
                "elevation_mm": 0,
                "id": "storey-1",
                "name": "首层",
                "net_height_mm": 3400,
                "spaces": [
                  {
                    "bounds": {
                      "x": [
                        200,
                        4800
                      ],
                      "y": [
                        200,
                        12900
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-1-space-west-reading",
                    "name": "西侧阅读室"
                  },
                  {
                    "bounds": {
                      "x": [
                        19200,
                        23800
                      ],
                      "y": [
                        200,
                        12900
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-1-space-east-reading",
                    "name": "东侧阅读室"
                  },
                  {
                    "bounds": {
                      "x": [
                        200,
                        23800
                      ],
                      "y": [
                        13100,
                        17800
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-1-space-north-reading",
                    "name": "北侧阅览室"
                  },
                  {
                    "bounds": {
                      "x": [
                        5000,
                        7400
                      ],
                      "y": [
                        0,
                        10600
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-1-space-west-colonnade",
                    "interior_or_exterior": "EXTERNAL",
                    "name": "西侧回廊"
                  },
                  {
                    "bounds": {
                      "x": [
                        16600,
                        19000
                      ],
                      "y": [
                        0,
                        10600
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-1-space-east-colonnade",
                    "interior_or_exterior": "EXTERNAL",
                    "name": "东侧回廊"
                  },
                  {
                    "bounds": {
                      "x": [
                        5000,
                        19000
                      ],
                      "y": [
                        10600,
                        12900
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-1-space-north-colonnade",
                    "interior_or_exterior": "EXTERNAL",
                    "name": "北侧回廊"
                  }
                ],
                "walls": {
                  "exterior": [
                    {
                      "bounds": {
                        "x": [
                          0,
                          200
                        ],
                        "y": [
                          0,
                          18000
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-1-wall-west-exterior",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          23800,
                          24000
                        ],
                        "y": [
                          0,
                          18000
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-1-wall-east-exterior",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          200,
                          23800
                        ],
                        "y": [
                          17800,
                          18000
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-1-wall-north-exterior",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          200,
                          4800
                        ],
                        "y": [
                          0,
                          200
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-1-wall-west-front",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          19200,
                          23800
                        ],
                        "y": [
                          0,
                          200
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-1-wall-east-front",
                      "thickness_mm": 200
                    }
                  ],
                  "interior": [
                    {
                      "bounds": {
                        "x": [
                          4800,
                          5000
                        ],
                        "y": [
                          0,
                          12900
                        ]
                      },
                      "connects": [
                        "storey-1-space-west-reading",
                        "storey-1-space-west-colonnade"
                      ],
                      "height_mm": 3400,
                      "id": "storey-1-wall-west-court",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          19000,
                          19200
                        ],
                        "y": [
                          0,
                          12900
                        ]
                      },
                      "connects": [
                        "storey-1-space-east-reading",
                        "storey-1-space-east-colonnade"
                      ],
                      "height_mm": 3400,
                      "id": "storey-1-wall-east-court",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          200,
                          23800
                        ],
                        "y": [
                          12900,
                          13100
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-1-wall-north-room-south",
                      "thickness_mm": 200
                    }
                  ]
                },
                "windows": [
                  {
                    "center_global_mm": [
                      100,
                      3000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-west-exterior",
                    "id": "storey-1-win-west-ext-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      100,
                      7000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-west-exterior",
                    "id": "storey-1-win-west-ext-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      100,
                      11000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-west-exterior",
                    "id": "storey-1-win-west-ext-3",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      100,
                      16000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-west-exterior",
                    "id": "storey-1-win-west-ext-4",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      23900,
                      3000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-east-exterior",
                    "id": "storey-1-win-east-ext-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      23900,
                      7000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-east-exterior",
                    "id": "storey-1-win-east-ext-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      23900,
                      11000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-east-exterior",
                    "id": "storey-1-win-east-ext-3",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      23900,
                      16000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-east-exterior",
                    "id": "storey-1-win-east-ext-4",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      4000,
                      17900
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-north-exterior",
                    "id": "storey-1-win-north-ext-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      9000,
                      17900
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-north-exterior",
                    "id": "storey-1-win-north-ext-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      15000,
                      17900
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-north-exterior",
                    "id": "storey-1-win-north-ext-3",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      20000,
                      17900
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-north-exterior",
                    "id": "storey-1-win-north-ext-4",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      4900,
                      2000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-west-court",
                    "id": "storey-1-win-west-court-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      4900,
                      5000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-west-court",
                    "id": "storey-1-win-west-court-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      4900,
                      11000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-west-court",
                    "id": "storey-1-win-west-court-3",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      19100,
                      2000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-east-court",
                    "id": "storey-1-win-east-court-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      19100,
                      5000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-east-court",
                    "id": "storey-1-win-east-court-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      19100,
                      11000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-east-court",
                    "id": "storey-1-win-east-court-3",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      7000,
                      13000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-north-room-south",
                    "id": "storey-1-win-north-room-south-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      17000,
                      13000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-north-room-south",
                    "id": "storey-1-win-north-room-south-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      2500,
                      100
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-west-front",
                    "id": "storey-1-win-west-front",
                    "sill_height_mm": 600,
                    "width_mm": 2600
                  },
                  {
                    "center_global_mm": [
                      21500,
                      100
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-east-front",
                    "id": "storey-1-win-east-front",
                    "sill_height_mm": 600,
                    "width_mm": 2600
                  }
                ]
              },
              {
                "doors": [
                  {
                    "center_global_mm": [
                      4900,
                      8000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-west-court",
                    "id": "storey-2-door-west-reading",
                    "operation": "left",
                    "sill_height_mm": 0,
                    "width_mm": 1200
                  },
                  {
                    "center_global_mm": [
                      19100,
                      8000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-east-court",
                    "id": "storey-2-door-east-reading",
                    "operation": "right",
                    "sill_height_mm": 0,
                    "width_mm": 1200
                  },
                  {
                    "center_global_mm": [
                      12000,
                      13000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-north-room-south",
                    "id": "storey-2-door-north-reading",
                    "operation": "left",
                    "sill_height_mm": 0,
                    "width_mm": 1400
                  }
                ],
                "elevation_mm": 3600,
                "id": "storey-2",
                "name": "二层",
                "net_height_mm": 3400,
                "spaces": [
                  {
                    "bounds": {
                      "x": [
                        200,
                        4800
                      ],
                      "y": [
                        200,
                        12900
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-2-space-west-reading",
                    "name": "西侧阅读室"
                  },
                  {
                    "bounds": {
                      "x": [
                        19200,
                        23800
                      ],
                      "y": [
                        200,
                        12900
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-2-space-east-reading",
                    "name": "东侧阅读室"
                  },
                  {
                    "bounds": {
                      "x": [
                        200,
                        23800
                      ],
                      "y": [
                        13100,
                        17800
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-2-space-north-reading",
                    "name": "北侧阅览室"
                  },
                  {
                    "bounds": {
                      "x": [
                        5000,
                        7400
                      ],
                      "y": [
                        0,
                        10600
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-2-space-west-colonnade",
                    "interior_or_exterior": "EXTERNAL",
                    "name": "西侧回廊"
                  },
                  {
                    "bounds": {
                      "x": [
                        16600,
                        19000
                      ],
                      "y": [
                        0,
                        10600
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-2-space-east-colonnade",
                    "interior_or_exterior": "EXTERNAL",
                    "name": "东侧回廊"
                  },
                  {
                    "bounds": {
                      "x": [
                        5000,
                        19000
                      ],
                      "y": [
                        10600,
                        12900
                      ]
                    },
                    "height_mm": 3400,
                    "id": "storey-2-space-north-colonnade",
                    "interior_or_exterior": "EXTERNAL",
                    "name": "北侧回廊"
                  }
                ],
                "walls": {
                  "exterior": [
                    {
                      "bounds": {
                        "x": [
                          0,
                          200
                        ],
                        "y": [
                          0,
                          18000
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-2-wall-west-exterior",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          23800,
                          24000
                        ],
                        "y": [
                          0,
                          18000
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-2-wall-east-exterior",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          200,
                          23800
                        ],
                        "y": [
                          17800,
                          18000
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-2-wall-north-exterior",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          200,
                          4800
                        ],
                        "y": [
                          0,
                          200
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-2-wall-west-front",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          19200,
                          23800
                        ],
                        "y": [
                          0,
                          200
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-2-wall-east-front",
                      "thickness_mm": 200
                    }
                  ],
                  "interior": [
                    {
                      "bounds": {
                        "x": [
                          4800,
                          5000
                        ],
                        "y": [
                          0,
                          12900
                        ]
                      },
                      "connects": [
                        "storey-2-space-west-reading",
                        "storey-2-space-west-colonnade"
                      ],
                      "height_mm": 3400,
                      "id": "storey-2-wall-west-court",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          19000,
                          19200
                        ],
                        "y": [
                          0,
                          12900
                        ]
                      },
                      "connects": [
                        "storey-2-space-east-reading",
                        "storey-2-space-east-colonnade"
                      ],
                      "height_mm": 3400,
                      "id": "storey-2-wall-east-court",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          200,
                          23800
                        ],
                        "y": [
                          12900,
                          13100
                        ]
                      },
                      "height_mm": 3400,
                      "id": "storey-2-wall-north-room-south",
                      "thickness_mm": 200
                    }
                  ]
                },
                "windows": [
                  {
                    "center_global_mm": [
                      100,
                      3000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-west-exterior",
                    "id": "storey-2-win-west-ext-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      100,
                      7000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-west-exterior",
                    "id": "storey-2-win-west-ext-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      100,
                      11000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-west-exterior",
                    "id": "storey-2-win-west-ext-3",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      100,
                      16000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-west-exterior",
                    "id": "storey-2-win-west-ext-4",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      23900,
                      3000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-east-exterior",
                    "id": "storey-2-win-east-ext-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      23900,
                      7000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-east-exterior",
                    "id": "storey-2-win-east-ext-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      23900,
                      11000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-east-exterior",
                    "id": "storey-2-win-east-ext-3",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      23900,
                      16000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-east-exterior",
                    "id": "storey-2-win-east-ext-4",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      4000,
                      17900
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-north-exterior",
                    "id": "storey-2-win-north-ext-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      9000,
                      17900
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-north-exterior",
                    "id": "storey-2-win-north-ext-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      15000,
                      17900
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-north-exterior",
                    "id": "storey-2-win-north-ext-3",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      20000,
                      17900
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-north-exterior",
                    "id": "storey-2-win-north-ext-4",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      4900,
                      2000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-west-court",
                    "id": "storey-2-win-west-court-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      4900,
                      5000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-west-court",
                    "id": "storey-2-win-west-court-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      4900,
                      11000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-west-court",
                    "id": "storey-2-win-west-court-3",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      19100,
                      2000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-east-court",
                    "id": "storey-2-win-east-court-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      19100,
                      5000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-east-court",
                    "id": "storey-2-win-east-court-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      19100,
                      11000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-east-court",
                    "id": "storey-2-win-east-court-3",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      7000,
                      13000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-north-room-south",
                    "id": "storey-2-win-north-room-south-1",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      17000,
                      13000
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-north-room-south",
                    "id": "storey-2-win-north-room-south-2",
                    "sill_height_mm": 600,
                    "width_mm": 2000
                  },
                  {
                    "center_global_mm": [
                      2500,
                      100
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-west-front",
                    "id": "storey-2-win-west-front",
                    "sill_height_mm": 600,
                    "width_mm": 2600
                  },
                  {
                    "center_global_mm": [
                      21500,
                      100
                    ],
                    "height_mm": 2400,
                    "host_wall": "storey-2-wall-east-front",
                    "id": "storey-2-win-east-front",
                    "sill_height_mm": 600,
                    "width_mm": 2600
                  }
                ]
              }
            ]
          }
        ],
        "schema_version": "text2ifc/semantic-coverage/1.0",
        "valid": true
      },
      "fact_count": 48,
      "stage": "semantic-coverage",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-12T12:12:32+00:00",
    "event_index": 2,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "ce8116ce095acdcf",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/ifc-presentation-validation/courtyard-library-open-court-20260912/rerun-03/live-run/runs/ce8116ce095acdcf/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "fd3e18d0-7072-41e4-93ee-b8799734e7a4",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-12T12:14:31+00:00",
    "event_index": 3,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "ce8116ce095acdcf",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "0e6bec77b6ce51d1093f45d2388b5700baa9f1e4ec0cfdbcb70f66558654f25d",
          "expected-facts.json": "1ef2e9c2f98a51efc41fe74f4e738738ab60d7b640bf81539be4922028adab14",
          "generator/candidate.json": "fc7135b29a722f33174e6ebf17a87f2274679eb25cc7ee925004269b578124bf",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "f8bf2e2d12d0366dde2a122c56e21c44fef16debe1f28c6a03ff30ea4d1b509a",
          "ifc-verification.json": "381267222dcd8254c892d624d4b3a8fe776e1de067b8994b8f0fb46f2b30f300",
          "repair/route.json": "9ab3e13b76e4f7c71e2f46bc9b21491f249536cbaeb95ca6359eb8108db42b31",
          "request-semantics.json": "1605b4a7648916fcb122b650348f316d293175ffa2ca77b5263c4e030976b591",
          "semantic-coverage.json": "0dbdb1cb0181c1796507c74861414172257f958ddcee4cb5104e47c59951847c",
          "semantic-verification.json": "6d6a4130005dd7f0ab1a388783a5fb4d4c24aaf551bbbce4d419f64959f091a7"
        },
        "candidate_hash": "fc7135b29a722f33174e6ebf17a87f2274679eb25cc7ee925004269b578124bf",
        "candidate_path": "generator/candidate.json",
        "case_id": "ce8116ce095acdcf",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-open-court-20260912\\rerun-03\\live-run\\runs\\ce8116ce095acdcf\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "design_brief_expected_facts",
            "issues": [],
            "metrics": {
              "case_id": "ce8116ce095acdcf",
              "floor_openings": {},
              "products": {
                "storey-1-beam-east": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.9
                    ],
                    "y": [
                      0.0,
                      10.9
                    ],
                    "z": [
                      3.1,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcBeam",
                  "storey_id": "storey-1"
                },
                "storey-1-beam-north": {
                  "bbox": {
                    "x": [
                      7.3999999999999995,
                      16.6
                    ],
                    "y": [
                      10.6,
                      10.9
                    ],
                    "z": [
                      3.1,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcBeam",
                  "storey_id": "storey-1"
                },
                "storey-1-beam-west": {
                  "bbox": {
                    "x": [
                      7.1,
                      7.4
                    ],
                    "y": [
                      0.0,
                      10.9
                    ],
                    "z": [
                      3.1,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcBeam",
                  "storey_id": "storey-1"
                },
                "storey-1-col-east-1": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.9
                    ],
                    "y": [
                      0.0,
                      0.3
                    ],
                    "z": [
                      0.0,
                      3.1
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-1"
                },
                "storey-1-col-east-2": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.9
                    ],
                    "y": [
                      3.4000000000000004,
                      3.7
                    ],
                    "z": [
                      0.0,
                      3.1
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-1"
                },
                "storey-1-col-east-3": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.9
                    ],
                    "y": [
                      6.8,
                      7.1000000000000005
                    ],
                    "z": [
                      0.0,
                      3.1
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-1"
                },
                "storey-1-col-east-4": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.9
                    ],
                    "y": [
                      10.3,
                      10.600000000000001
                    ],
                    "z": [
                      0.0,
                      3.1
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-1"
                },
                "storey-1-col-north-1": {
                  "bbox": {
                    "x": [
                      10.35,
                      10.65
                    ],
                    "y": [
                      10.6,
                      10.9
                    ],
                    "z": [
                      0.0,
                      3.1
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-1"
                },
                "storey-1-col-north-2": {
                  "bbox": {
                    "x": [
                      13.35,
                      13.65
                    ],
                    "y": [
                      10.6,
                      10.9
                    ],
                    "z": [
                      0.0,
                      3.1
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-1"
                },
                "storey-1-col-west-1": {
                  "bbox": {
                    "x": [
                      7.1,
                      7.4
                    ],
                    "y": [
                      0.0,
                      0.3
                    ],
                    "z": [
                      0.0,
                      3.1
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-1"
                },
                "storey-1-col-west-2": {
                  "bbox": {
                    "x": [
                      7.1,
                      7.4
                    ],
                    "y": [
                      3.4000000000000004,
                      3.7
                    ],
                    "z": [
                      0.0,
                      3.1
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-1"
                },
                "storey-1-col-west-3": {
                  "bbox": {
                    "x": [
                      7.1,
                      7.4
                    ],
                    "y": [
                      6.8,
                      7.1000000000000005
                    ],
                    "z": [
                      0.0,
                      3.1
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-1"
                },
                "storey-1-col-west-4": {
                  "bbox": {
                    "x": [
                      7.1,
                      7.4
                    ],
                    "y": [
                      10.3,
                      10.600000000000001
                    ],
                    "z": [
                      0.0,
                      3.1
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-1"
                },
                "storey-1-rail-stair-left": {
                  "bbox": {
                    "x": [
                      14.8,
                      14.84
                    ],
                    "y": [
                      2.2,
                      8.2
                    ],
                    "z": [
                      0.0,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-1"
                },
                "storey-1-rail-stair-right": {
                  "bbox": {
                    "x": [
                      16.560000000000002,
                      16.6
                    ],
                    "y": [
                      2.2,
                      8.2
                    ],
                    "z": [
                      0.0,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-1"
                },
                "storey-2-beam-east": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.9
                    ],
                    "y": [
                      0.0,
                      10.9
                    ],
                    "z": [
                      6.7,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcBeam",
                  "storey_id": "storey-2"
                },
                "storey-2-beam-north": {
                  "bbox": {
                    "x": [
                      7.3999999999999995,
                      16.6
                    ],
                    "y": [
                      10.6,
                      10.9
                    ],
                    "z": [
                      6.7,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcBeam",
                  "storey_id": "storey-2"
                },
                "storey-2-beam-west": {
                  "bbox": {
                    "x": [
                      7.1,
                      7.4
                    ],
                    "y": [
                      0.0,
                      10.9
                    ],
                    "z": [
                      6.7,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcBeam",
                  "storey_id": "storey-2"
                },
                "storey-2-col-east-1": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.9
                    ],
                    "y": [
                      0.0,
                      0.3
                    ],
                    "z": [
                      3.6,
                      6.7
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-2"
                },
                "storey-2-col-east-2": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.9
                    ],
                    "y": [
                      3.4000000000000004,
                      3.7
                    ],
                    "z": [
                      3.6,
                      6.7
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-2"
                },
                "storey-2-col-east-3": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.9
                    ],
                    "y": [
                      6.8,
                      7.1000000000000005
                    ],
                    "z": [
                      3.6,
                      6.7
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-2"
                },
                "storey-2-col-east-4": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.9
                    ],
                    "y": [
                      10.3,
                      10.600000000000001
                    ],
                    "z": [
                      3.6,
                      6.7
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-2"
                },
                "storey-2-col-north-1": {
                  "bbox": {
                    "x": [
                      10.35,
                      10.65
                    ],
                    "y": [
                      10.6,
                      10.9
                    ],
                    "z": [
                      3.6,
                      6.7
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-2"
                },
                "storey-2-col-north-2": {
                  "bbox": {
                    "x": [
                      13.35,
                      13.65
                    ],
                    "y": [
                      10.6,
                      10.9
                    ],
                    "z": [
                      3.6,
                      6.7
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-2"
                },
                "storey-2-col-west-1": {
                  "bbox": {
                    "x": [
                      7.1,
                      7.4
                    ],
                    "y": [
                      0.0,
                      0.3
                    ],
                    "z": [
                      3.6,
                      6.7
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-2"
                },
                "storey-2-col-west-2": {
                  "bbox": {
                    "x": [
                      7.1,
                      7.4
                    ],
                    "y": [
                      3.4000000000000004,
                      3.7
                    ],
                    "z": [
                      3.6,
                      6.7
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-2"
                },
                "storey-2-col-west-3": {
                  "bbox": {
                    "x": [
                      7.1,
                      7.4
                    ],
                    "y": [
                      6.8,
                      7.1000000000000005
                    ],
                    "z": [
                      3.6,
                      6.7
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-2"
                },
                "storey-2-col-west-4": {
                  "bbox": {
                    "x": [
                      7.1,
                      7.4
                    ],
                    "y": [
                      10.3,
                      10.600000000000001
                    ],
                    "z": [
                      3.6,
                      6.7
                    ]
                  },
                  "ifc_class": "IfcColumn",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-east-1": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.64
                    ],
                    "y": [
                      0.3,
                      3.4
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-east-2": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.64
                    ],
                    "y": [
                      3.7,
                      6.800000000000001
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-east-3": {
                  "bbox": {
                    "x": [
                      16.6,
                      16.64
                    ],
                    "y": [
                      7.1000000000000005,
                      8.200000000000001
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-front-east": {
                  "bbox": {
                    "x": [
                      16.9,
                      19.0
                    ],
                    "y": [
                      0.0,
                      0.04
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-front-west": {
                  "bbox": {
                    "x": [
                      5.0,
                      7.1
                    ],
                    "y": [
                      0.0,
                      0.04
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-landing-west": {
                  "bbox": {
                    "x": [
                      14.8,
                      14.84
                    ],
                    "y": [
                      8.2,
                      10.6
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-north-1": {
                  "bbox": {
                    "x": [
                      7.4,
                      10.350000000000001
                    ],
                    "y": [
                      10.600000000000001,
                      10.64
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-north-2": {
                  "bbox": {
                    "x": [
                      10.65,
                      13.350000000000001
                    ],
                    "y": [
                      10.600000000000001,
                      10.64
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-north-3": {
                  "bbox": {
                    "x": [
                      13.65,
                      14.8
                    ],
                    "y": [
                      10.600000000000001,
                      10.64
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-west-1": {
                  "bbox": {
                    "x": [
                      7.36,
                      7.4
                    ],
                    "y": [
                      0.3,
                      3.4
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-west-2": {
                  "bbox": {
                    "x": [
                      7.36,
                      7.4
                    ],
                    "y": [
                      3.7,
                      6.800000000000001
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                },
                "storey-2-rail-west-3": {
                  "bbox": {
                    "x": [
                      7.36,
                      7.4
                    ],
                    "y": [
                      7.1000000000000005,
                      10.3
                    ],
                    "z": [
                      3.6,
                      4.7
                    ]
                  },
                  "ifc_class": "IfcRailing",
                  "storey_id": "storey-2"
                }
              },
              "roof": {
                "slab-roof": {
                  "bbox": {
                    "x": [
                      0.0,
                      24.0
                    ],
                    "y": [
                      0.0,
                      18.0
                    ],
                    "z": [
                      7.0,
                      7.2
                    ]
                  },
                  "ifc_class": "IfcSlab"
                }
              },
              "slabs": {
                "slab-ground-1": {
                  "bbox": {
                    "x": [
                      0.0,
                      24.0
                    ],
                    "y": [
                      0.0,
                      18.0
                    ],
                    "z": [
                      -0.2,
                      0.0
                    ]
                  },
                  "ifc_class": "IfcSlab"
                },
                "slab-landing-2": {
                  "bbox": {
                    "x": [
                      14.8,
                      16.6
                    ],
                    "y": [
                      8.200000000000001,
                      10.6
                    ],
                    "z": [
                      3.4,
                      3.6
                    ]
                  },
                  "ifc_class": "IfcSlab"
                },
                "slab-u-floor-2": {
                  "bbox": {
                    "x": [
                      0.0,
                      24.0
                    ],
                    "y": [
                      0.0,
                      18.0
                    ],
                    "z": [
                      3.4,
                      3.6
                    ]
                  },
                  "ifc_class": "IfcSlab"
                }
              },
              "spaces": {
                "space-storey-1-storey-1-space-east-colonnade": {
                  "bbox": {
                    "x": [
                      16.6,
                      19.0
                    ],
                    "y": [
                      0.0,
                      10.6
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-1"
                },
                "space-storey-1-storey-1-space-east-reading": {
                  "bbox": {
                    "x": [
                      19.2,
                      23.8
                    ],
                    "y": [
                      0.1999999999999993,
                      12.9
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-1"
                },
                "space-storey-1-storey-1-space-north-colonnade": {
                  "bbox": {
                    "x": [
                      5.0,
                      19.0
                    ],
                    "y": [
                      10.6,
                      12.9
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-1"
                },
                "space-storey-1-storey-1-space-north-reading": {
                  "bbox": {
                    "x": [
                      0.1999999999999993,
                      23.8
                    ],
                    "y": [
                      13.100000000000001,
                      17.8
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-1"
                },
                "space-storey-1-storey-1-space-west-colonnade": {
                  "bbox": {
                    "x": [
                      5.0,
                      7.4
                    ],
                    "y": [
                      0.0,
                      10.6
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-1"
                },
                "space-storey-1-storey-1-space-west-reading": {
                  "bbox": {
                    "x": [
                      0.19999999999999973,
                      4.800000000000001
                    ],
                    "y": [
                      0.1999999999999993,
                      12.9
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-1"
                },
                "space-storey-2-storey-2-space-east-colonnade": {
                  "bbox": {
                    "x": [
                      16.6,
                      19.0
                    ],
                    "y": [
                      0.0,
                      10.6
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-2"
                },
                "space-storey-2-storey-2-space-east-reading": {
                  "bbox": {
                    "x": [
                      19.2,
                      23.8
                    ],
                    "y": [
                      0.1999999999999993,
                      12.9
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-2"
                },
                "space-storey-2-storey-2-space-north-colonnade": {
                  "bbox": {
                    "x": [
                      5.0,
                      19.0
                    ],
                    "y": [
                      10.6,
                      12.9
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-2"
                },
                "space-storey-2-storey-2-space-north-reading": {
                  "bbox": {
                    "x": [
                      0.1999999999999993,
                      23.8
                    ],
                    "y": [
                      13.100000000000001,
                      17.8
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-2"
                },
                "space-storey-2-storey-2-space-west-colonnade": {
                  "bbox": {
                    "x": [
                      5.0,
                      7.4
                    ],
                    "y": [
                      0.0,
                      10.6
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-2"
                },
                "space-storey-2-storey-2-space-west-reading": {
                  "bbox": {
                    "x": [
                      0.19999999999999973,
                      4.800000000000001
                    ],
                    "y": [
                      0.1999999999999993,
                      12.9
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcSpace",
                  "storey_id": "storey-2"
                }
              },
              "stairs": {
                "stair-1": {
                  "bbox": {
                    "x": [
                      14.8,
                      16.6
                    ],
                    "y": [
                      2.2,
                      8.2
                    ],
                    "z": [
                      0.0,
                      3.6
                    ]
                  },
                  "flight_ids": [
                    "stair-flight-1"
                  ],
                  "has_stepped_profile": true,
                  "wall_intersections": []
                }
              },
              "wall_set_convention": "primary",
              "walls": {
                "wall-storey-1-storey-1-wall-east-court": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      19.0,
                      19.200000000000003
                    ],
                    "y": [
                      0.0,
                      12.9
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-east-exterior": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      23.8,
                      24.000000000000004
                    ],
                    "y": [
                      0.0,
                      18.0
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-east-front": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      19.2,
                      23.8
                    ],
                    "y": [
                      0.0,
                      0.2
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-north-exterior": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.1999999999999993,
                      23.8
                    ],
                    "y": [
                      17.8,
                      18.000000000000004
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-north-room-south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.1999999999999993,
                      23.8
                    ],
                    "y": [
                      12.9,
                      13.1
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-west-court": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      5.0
                    ],
                    "y": [
                      0.0,
                      12.9
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-west-exterior": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      0.0,
                      0.2
                    ],
                    "y": [
                      0.0,
                      18.0
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-west-front": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.19999999999999973,
                      4.800000000000001
                    ],
                    "y": [
                      0.0,
                      0.2
                    ],
                    "z": [
                      0.0,
                      3.4
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-east-court": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      19.0,
                      19.200000000000003
                    ],
                    "y": [
                      0.0,
                      12.9
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-east-exterior": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      23.8,
                      24.000000000000004
                    ],
                    "y": [
                      0.0,
                      18.0
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-east-front": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      19.2,
                      23.8
                    ],
                    "y": [
                      0.0,
                      0.2
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-north-exterior": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.1999999999999993,
                      23.8
                    ],
                    "y": [
                      17.8,
                      18.000000000000004
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-north-room-south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.1999999999999993,
                      23.8
                    ],
                    "y": [
                      12.9,
                      13.1
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-west-court": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      5.0
                    ],
                    "y": [
                      0.0,
                      12.9
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-west-exterior": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      0.0,
                      0.2
                    ],
                    "y": [
                      0.0,
                      18.0
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-west-front": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.19999999999999973,
                      4.800000000000001
                    ],
                    "y": [
                      0.0,
                      0.2
                    ],
                    "z": [
                      3.6,
                      7.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                }
              }
            },
            "success": true
          },
          "repair_history": {
            "assessment_scope": {
              "geometry_feedback_supplied": false,
              "geometry_issue_count_basis": "supplied_feedback_only",
              "geometry_pass_certified": false,
              "interpretation": "This route assesses generator validation and only the geometry issues supplied to this invocation. Zero issues/no_repair_needed is not a geometry pass. Current compile/reopen/geometry gates remain authoritative."
            },
            "case_id": "ce8116ce095acdcf",
            "fact_delta": null,
            "geometry_issue_count": 0,
            "provider_call_count": 0,
            "repair_attempts": [],
            "repair_diagnostics": [],
            "repair_source_artifact": "candidate.json",
            "route": "no_repair_needed",
            "schema_version": "text2ifc/repair-route/1.1",
            "source_document_kind": "candidate",
            "source_document_path": "candidate.json",
            "source_generator_dir": "dataset/processed/ifc-presentation-validation/courtyard-library-open-court-20260912/rerun-03/live-run/runs/ce8116ce095acdcf/generator",
            "source_generator_response_id": "fd3e18d0-7072-41e4-93ee-b8799734e7a4",
            "valid": true,
            "validation_issue_count": 0
          },
          "request_semantics": {
            "basis": "request expectations independently compared with reopened IFC before atomic publication",
            "expectations": [
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/0",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/0",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/1",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/1",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-north-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/2",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-north-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/2",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-front",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/3",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-front",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/3",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-front",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/4",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-front",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/4",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-court",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/5",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-court",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/5",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-court",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/6",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-court",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/6",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-north-room-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/7",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-north-room-south",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/7",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/8",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/8",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/9",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/9",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-north-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/10",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-north-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/10",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-front",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/11",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-front",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/11",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-front",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/12",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-front",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/12",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-court",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/13",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-court",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/13",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-court",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/14",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-court",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/14",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-north-room-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/15",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-north-room-south",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/15",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "slab-ground-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-ground-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "slab-u-floor-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/17",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-u-floor-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/17",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "slab-landing-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/18",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-landing-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/18",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "slab-roof",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/19",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-roof",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/19",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "stair-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/20",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "stair-flight-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/21",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "stair-flight-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/21",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "storey-1-beam-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/22",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-beam-west",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/22",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-beam-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/23",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-beam-east",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/23",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-beam-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/24",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-beam-north",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/24",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-beam-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/25",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-beam-west",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/25",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-beam-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/26",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-beam-east",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/26",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-beam-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/27",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-beam-north",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/27",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-west-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/28",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-west-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/28",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-west-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/29",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-west-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/29",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-west-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/30",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-west-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/30",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-west-4",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/31",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-west-4",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/31",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-east-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/32",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-east-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/32",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-east-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/33",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-east-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/33",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-east-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/34",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-east-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/34",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-east-4",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/35",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-east-4",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/35",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-north-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/36",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-north-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/36",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-north-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/37",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-north-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/37",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-west-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/38",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-west-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/38",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-west-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/39",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-west-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/39",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-west-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/40",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-west-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/40",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-west-4",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/41",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-west-4",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/41",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-east-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/42",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-east-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/42",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-east-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/43",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-east-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/43",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-east-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/44",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-east-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/44",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-east-4",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/45",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-east-4",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/45",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-north-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/46",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-north-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/46",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-north-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/47",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-north-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/47",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-rail-west-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/48",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-west-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/48",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-west-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/48",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-west-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/49",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-west-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/49",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-west-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/49",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-west-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/50",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-west-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/50",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-west-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/50",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-east-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/51",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-east-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/51",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-east-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/51",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-east-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/52",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-east-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/52",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-east-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/52",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-east-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/53",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-east-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/53",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-east-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/53",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-north-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/54",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-north-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/54",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-north-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/54",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-north-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/55",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-north-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/55",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-north-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/55",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-north-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/56",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-north-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/56",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-north-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/56",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-front-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/57",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-front-west",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/57",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-front-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/57",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-front-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/58",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-front-east",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/58",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-front-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/58",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-landing-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/59",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-landing-west",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/59",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-landing-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/59",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-1-rail-stair-left",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/60",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-1-rail-stair-left",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/60",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-1-rail-stair-left",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/60",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-1-rail-stair-right",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/61",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-1-rail-stair-right",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/61",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-1-rail-stair-right",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/61",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-west-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/62",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-west-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/62",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-west-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/62",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-east-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/63",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-east-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/63",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-east-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/63",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-north-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/64",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-north-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/64",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-north-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/64",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-west-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/65",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-west-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/65",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-west-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/65",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-east-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/66",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-east-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/66",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-east-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/66",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-north-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/67",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-north-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/67",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-north-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/67",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/68",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/68",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/69",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/69",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/70",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/70",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/71",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/71",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/72",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/72",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/73",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/73",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/74",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/74",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/75",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/75",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/76",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/76",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/77",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/77",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/78",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/78",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/79",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/79",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/80",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/80",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/81",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/81",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/82",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/82",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/83",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/83",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/84",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/84",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/85",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/85",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-room-south-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/86",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-room-south-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/86",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-room-south-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/87",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-room-south-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/87",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-front",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/88",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-front",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/88",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-front",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/89",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-front",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/89",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/90",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/90",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/91",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/91",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/92",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/92",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/93",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/93",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/94",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/94",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/95",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/95",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/96",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/96",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/97",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/97",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/98",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/98",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/99",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/99",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/100",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/100",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/101",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/101",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/102",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/102",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/103",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/103",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/104",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/104",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/105",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/105",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/106",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/106",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/107",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/107",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-room-south-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/108",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-room-south-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/108",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-room-south-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/109",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-room-south-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/109",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-front",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/110",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-front",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/110",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-front",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/111",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-front",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/111",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/0",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/0",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/1",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/1",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-north-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/2",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-north-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/2",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-front",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/3",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-front",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/3",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-front",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/4",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-front",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/4",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-court",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/5",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west-court",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/5",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-court",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/6",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east-court",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/6",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-north-room-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/7",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-north-room-south",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/7",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/8",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/8",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/9",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/9",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-north-exterior",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/10",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-north-exterior",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/10",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-front",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/11",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-front",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/11",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-front",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/12",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-front",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/12",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-court",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/13",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west-court",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/13",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-court",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/14",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east-court",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/14",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-north-room-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/15",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-north-room-south",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/15",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "slab-ground-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-ground-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "slab-u-floor-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/17",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-u-floor-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/17",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "slab-landing-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/18",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-landing-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/18",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "slab-roof",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/19",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-roof",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/19",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "stair-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/20",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "stair-flight-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/21",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "stair-flight-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/21",
                "value": {
                  "color": [
                    0.902,
                    0.878,
                    0.827
                  ]
                }
              },
              {
                "entity_id": "storey-1-beam-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/22",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-beam-west",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/22",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-beam-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/23",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-beam-east",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/23",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-beam-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/24",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-beam-north",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/24",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-beam-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/25",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-beam-west",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/25",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-beam-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/26",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-beam-east",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/26",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-beam-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/27",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-beam-north",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/27",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-west-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/28",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-west-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/28",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-west-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/29",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-west-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/29",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-west-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/30",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-west-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/30",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-west-4",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/31",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-west-4",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/31",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-east-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/32",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-east-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/32",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-east-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/33",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-east-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/33",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-east-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/34",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-east-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/34",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-east-4",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/35",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-east-4",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/35",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-north-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/36",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-north-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/36",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-1-col-north-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/37",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-1-col-north-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/37",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-west-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/38",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-west-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/38",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-west-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/39",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-west-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/39",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-west-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/40",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-west-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/40",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-west-4",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/41",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-west-4",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/41",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-east-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/42",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-east-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/42",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-east-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/43",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-east-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/43",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-east-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/44",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-east-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/44",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-east-4",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/45",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-east-4",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/45",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-north-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/46",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-north-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/46",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-col-north-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/47",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "storey-2-col-north-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/47",
                "value": {
                  "color": [
                    0.824,
                    0.78,
                    0.702
                  ]
                }
              },
              {
                "entity_id": "storey-2-rail-west-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/48",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-west-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/48",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-west-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/48",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-west-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/49",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-west-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/49",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-west-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/49",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-west-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/50",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-west-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/50",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-west-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/50",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-east-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/51",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-east-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/51",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-east-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/51",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-east-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/52",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-east-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/52",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-east-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/52",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-east-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/53",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-east-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/53",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-east-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/53",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-north-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/54",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-north-1",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/54",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-north-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/54",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-north-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/55",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-north-2",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/55",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-north-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/55",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-north-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/56",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-north-3",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/56",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-north-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/56",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-front-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/57",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-front-west",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/57",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-front-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/57",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-front-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/58",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-front-east",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/58",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-front-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/58",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-2-rail-landing-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/59",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-2-rail-landing-west",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/59",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-2-rail-landing-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/59",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-1-rail-stair-left",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/60",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-1-rail-stair-left",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/60",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-1-rail-stair-left",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/60",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "storey-1-rail-stair-right",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/61",
                "value": {
                  "kind": "single_material",
                  "name": "钢材"
                }
              },
              {
                "entity_id": "storey-1-rail-stair-right",
                "kind": "appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/61",
                "value": {
                  "color": [
                    0.188,
                    0.294,
                    0.302
                  ],
                  "transparency": 0
                }
              },
              {
                "entity_id": "storey-1-rail-stair-right",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/61",
                "value": {
                  "template_id": "metal-picket",
                  "template_version": "text2ifc/basic-railing/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-west-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/62",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-west-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/62",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-west-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/62",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-east-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/63",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-east-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/63",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-east-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/63",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-north-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/64",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-north-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/64",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-north-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/64",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-west-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/65",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-west-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/65",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-west-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/65",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-east-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/66",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-east-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/66",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-east-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/66",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-north-reading",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/67",
                "value": {
                  "kind": "single_material",
                  "name": "木材"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-north-reading",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/67",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "panel": {
                    "color": [
                      0.651,
                      0.435,
                      0.263
                    ]
                  }
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-north-reading",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/67",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/68",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/68",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/69",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/69",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/70",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/70",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/71",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/71",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/72",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/72",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/73",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/73",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/74",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/74",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/75",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/75",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/76",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/76",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/77",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/77",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/78",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/78",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/79",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/79",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/80",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/80",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/81",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/81",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/82",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-court-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/82",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/83",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/83",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/84",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/84",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/85",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-court-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/85",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-room-south-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/86",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-room-south-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/86",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-room-south-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/87",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-north-room-south-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/87",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-front",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/88",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-west-front",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/88",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-front",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/89",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-win-east-front",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/89",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/90",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/90",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/91",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/91",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/92",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/92",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/93",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/93",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/94",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/94",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/95",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/95",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/96",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/96",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/97",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/97",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/98",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/98",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/99",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/99",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/100",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/100",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-4",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/101",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-ext-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/101",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/102",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/102",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/103",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/103",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/104",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-court-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/104",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/105",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/105",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/106",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/106",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-3",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/107",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-court-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/107",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-room-south-1",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/108",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-room-south-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/108",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-room-south-2",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/109",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-north-room-south-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/109",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-front",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/110",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-west-front",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/110",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-front",
                "kind": "part_appearance",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/111",
                "value": {
                  "frame": {
                    "color": [
                      0.188,
                      0.294,
                      0.302
                    ]
                  },
                  "glazing": {
                    "transparency": 0.65
                  }
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-win-east-front",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/111",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              }
            ],
            "issues": [],
            "schema_version": "text2ifc/request-semantic-verification/1.0",
            "valid": true
          },
          "schema_validation": {
            "issue_count": 0,
            "issues": [],
            "valid": true
          },
          "semantic_coverage": {
            "blocking_facts": [],
            "candidate_entity_count": 179,
            "capability_profile_hash": "sha256:cdf910348007cc2135b22e0c42a46bae6ba8ca958df4f287a2f9ec1bb708cf30",
            "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.3/1.0",
            "case_id": "ce8116ce095acdcf",
            "custom_property_policy": {
              "counts_as_semantic_support": false,
              "state": "preserved_text_only"
            },
            "facts": [
              {
                "coverage_state": "represented",
                "path": "/known_facts/appearance/profile",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "neutral-architectural"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/appearance/style_notes",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "暖米白主体、浅砂色梁柱、深青灰框与金属栏杆、少量木色门扇；后翼与两侧翼围合庭院，南侧敞开，两层柱廊与上下对齐窗洞形成明确节奏"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/beams",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "bounds_mm": {
                      "x": [
                        7100,
                        7400
                      ],
                      "y": [
                        0,
                        10900
                      ],
                      "z": [
                        3100,
                        3400
                      ]
                    },
                    "id": "storey-1-beam-west",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        16600,
                        16900
                      ],
                      "y": [
                        0,
                        10900
                      ],
                      "z": [
                        3100,
                        3400
                      ]
                    },
                    "id": "storey-1-beam-east",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        7400,
                        16600
                      ],
                      "y": [
                        10600,
                        10900
                      ],
                      "z": [
                        3100,
                        3400
                      ]
                    },
                    "id": "storey-1-beam-north",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        7100,
                        7400
                      ],
                      "y": [
                        0,
                        10900
                      ],
                      "z": [
                        6700,
                        7000
                      ]
                    },
                    "id": "storey-2-beam-west",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        16600,
                        16900
                      ],
                      "y": [
                        0,
                        10900
                      ],
                      "z": [
                        6700,
                        7000
                      ]
                    },
                    "id": "storey-2-beam-east",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        7400,
                        16600
                      ],
                      "y": [
                        10600,
                        10900
                      ],
                      "z": [
                        6700,
                        7000
                      ]
                    },
                    "id": "storey-2-beam-north",
                    "storey": "storey-2"
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/concept_reference",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "已确认概念图右上角；尺寸与布置不按概念图测量"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/coordinate_frame/origin",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "建筑外轮廓西南角"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/coordinate_frame/unit",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "MILLIMETRE"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/coordinate_frame/x",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "东"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/coordinate_frame/y",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "北"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/coordinate_frame/z",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "上"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/courtyard/bounds/x",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  7400,
                  16600
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/courtyard/bounds/y",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  0,
                  10600
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/courtyard/note",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "主露天天井；除指定外露楼梯与局部上端平台外不加楼板、屋盖、玻璃顶或通高围墙"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/courtyard/open_to",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "south"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/name",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "开敞光庭阅读馆"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/polygon",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  [
                    0,
                    0
                  ],
                  [
                    24000,
                    0
                  ],
                  [
                    24000,
                    18000
                  ],
                  [
                    0,
                    18000
                  ],
                  [
                    0,
                    0
                  ]
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/x_max",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 24000
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/x_min",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 0
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/y_max",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 18000
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/y_min",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 0
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/scope_exclusions",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  "家具",
                  "植物",
                  "招牌",
                  "设备",
                  "景观摆件"
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/storey_count",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 2
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/storey_height_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 3400
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/wall_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 200
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/columns",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "bounds_mm": {
                      "x": [
                        7100,
                        7400
                      ],
                      "y": [
                        0,
                        300
                      ],
                      "z": [
                        0,
                        3100
                      ]
                    },
                    "id": "storey-1-col-west-1",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        7100,
                        7400
                      ],
                      "y": [
                        3400,
                        3700
                      ],
                      "z": [
                        0,
                        3100
                      ]
                    },
                    "id": "storey-1-col-west-2",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        7100,
                        7400
                      ],
                      "y": [
                        6800,
                        7100
                      ],
                      "z": [
                        0,
                        3100
                      ]
                    },
                    "id": "storey-1-col-west-3",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        7100,
                        7400
                      ],
                      "y": [
                        10300,
                        10600
                      ],
                      "z": [
                        0,
                        3100
                      ]
                    },
                    "id": "storey-1-col-west-4",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        16600,
                        16900
                      ],
                      "y": [
                        0,
                        300
                      ],
                      "z": [
                        0,
                        3100
                      ]
                    },
                    "id": "storey-1-col-east-1",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        16600,
                        16900
                      ],
                      "y": [
                        3400,
                        3700
                      ],
                      "z": [
                        0,
                        3100
                      ]
                    },
                    "id": "storey-1-col-east-2",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        16600,
                        16900
                      ],
                      "y": [
                        6800,
                        7100
                      ],
                      "z": [
                        0,
                        3100
                      ]
                    },
                    "id": "storey-1-col-east-3",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        16600,
                        16900
                      ],
                      "y": [
                        10300,
                        10600
                      ],
                      "z": [
                        0,
                        3100
                      ]
                    },
                    "id": "storey-1-col-east-4",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        10350,
                        10650
                      ],
                      "y": [
                        10600,
                        10900
                      ],
                      "z": [
                        0,
                        3100
                      ]
                    },
                    "id": "storey-1-col-north-1",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        13350,
                        13650
                      ],
                      "y": [
                        10600,
                        10900
                      ],
                      "z": [
                        0,
                        3100
                      ]
                    },
                    "id": "storey-1-col-north-2",
                    "storey": "storey-1"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        7100,
                        7400
                      ],
                      "y": [
                        0,
                        300
                      ],
                      "z": [
                        3600,
                        6700
                      ]
                    },
                    "id": "storey-2-col-west-1",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        7100,
                        7400
                      ],
                      "y": [
                        3400,
                        3700
                      ],
                      "z": [
                        3600,
                        6700
                      ]
                    },
                    "id": "storey-2-col-west-2",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        7100,
                        7400
                      ],
                      "y": [
                        6800,
                        7100
                      ],
                      "z": [
                        3600,
                        6700
                      ]
                    },
                    "id": "storey-2-col-west-3",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        7100,
                        7400
                      ],
                      "y": [
                        10300,
                        10600
                      ],
                      "z": [
                        3600,
                        6700
                      ]
                    },
                    "id": "storey-2-col-west-4",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        16600,
                        16900
                      ],
                      "y": [
                        0,
                        300
                      ],
                      "z": [
                        3600,
                        6700
                      ]
                    },
                    "id": "storey-2-col-east-1",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        16600,
                        16900
                      ],
                      "y": [
                        3400,
                        3700
                      ],
                      "z": [
                        3600,
                        6700
                      ]
                    },
                    "id": "storey-2-col-east-2",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        16600,
                        16900
                      ],
                      "y": [
                        6800,
                        7100
                      ],
                      "z": [
                        3600,
                        6700
                      ]
                    },
                    "id": "storey-2-col-east-3",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        16600,
                        16900
                      ],
                      "y": [
                        10300,
                        10600
                      ],
                      "z": [
                        3600,
                        6700
                      ]
                    },
                    "id": "storey-2-col-east-4",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        10350,
                        10650
                      ],
                      "y": [
                        10600,
                        10900
                      ],
                      "z": [
                        3600,
                        6700
                      ]
                    },
                    "id": "storey-2-col-north-1",
                    "storey": "storey-2"
                  },
                  {
                    "bounds_mm": {
                      "x": [
                        13350,
                        13650
                      ],
                      "y": [
                        10600,
                        10900
                      ],
                      "z": [
                        3600,
                        6700
                      ]
                    },
                    "id": "storey-2-col-north-2",
                    "storey": "storey-2"
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/floor_slabs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "bounds": {
                      "x": [
                        0,
                        24000
                      ],
                      "y": [
                        0,
                        18000
                      ]
                    },
                    "id": "slab-ground-1",
                    "note": "一整块24×18米混凝土板，底面-0.2、顶面0；庭院地面保留",
                    "storey": "storey-1",
                    "thickness_mm": 200,
                    "top_elevation_mm": 0
                  },
                  {
                    "id": "slab-u-floor-2",
                    "note": "前侧敞开的U形板，不得以矩形整板代替",
                    "polygon": [
                      [
                        0,
                        0
                      ],
                      [
                        7400,
                        0
                      ],
                      [
                        7400,
                        10600
                      ],
                      [
                        16600,
                        10600
                      ],
                      [
                        16600,
                        0
                      ],
                      [
                        24000,
                        0
                      ],
                      [
                        24000,
                        18000
                      ],
                      [
                        0,
                        18000
                      ],
                      [
                        0,
                        0
                      ]
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 200,
                    "top_elevation_mm": 3600
                  },
                  {
                    "bounds": {
                      "x": [
                        14800,
                        16600
                      ],
                      "y": [
                        8200,
                        10600
                      ]
                    },
                    "id": "slab-landing-2",
                    "note": "楼梯上端平台，与U形板仅边界相接，无正面积重叠；北接北回廊，东接东回廊",
                    "storey": "storey-2",
                    "thickness_mm": 200,
                    "top_elevation_mm": 3600
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/plan_constraints",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "checks": [
                      "non_overlapping"
                    ],
                    "derived_wall_ids": [
                      "storey-1-wall-west-exterior",
                      "storey-1-wall-east-exterior",
                      "storey-1-wall-north-exterior",
                      "storey-1-wall-west-front",
                      "storey-1-wall-east-front",
                      "storey-1-wall-west-court",
                      "storey-1-wall-east-court",
                      "storey-1-wall-north-room-south"
                    ],
                    "id": "pc-storey-1-wall-layout",
                    "kind": "wall_layout",
                    "outline_ref": "/known_facts/building/outline/polygon",
                    "source_turns": [
                      "turn-user-001"
                    ],
                    "storey_ref": "/known_facts/storeys/0"
                  },
                  {
                    "checks": [
                      "non_overlapping"
                    ],
                    "derived_wall_ids": [
                      "storey-2-wall-west-exterior",
                      "storey-2-wall-east-exterior",
                      "storey-2-wall-north-exterior",
                      "storey-2-wall-west-front",
                      "storey-2-wall-east-front",
                      "storey-2-wall-west-court",
                      "storey-2-wall-east-court",
                      "storey-2-wall-north-room-south"
                    ],
                    "id": "pc-storey-2-wall-layout",
                    "kind": "wall_layout",
                    "outline_ref": "/known_facts/building/outline/polygon",
                    "source_turns": [
                      "turn-user-001"
                    ],
                    "storey_ref": "/known_facts/storeys/1"
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/railings",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "alignment_target": "西列柱间，止于柱面",
                    "end_mm": [
                      7380,
                      3400,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-west-1",
                    "start_mm": [
                      7380,
                      300,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "西列柱间，止于柱面",
                    "end_mm": [
                      7380,
                      6800,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-west-2",
                    "start_mm": [
                      7380,
                      3700,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "西列柱间，止于柱面",
                    "end_mm": [
                      7380,
                      10300,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-west-3",
                    "start_mm": [
                      7380,
                      7100,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "东列柱间，止于柱面",
                    "end_mm": [
                      16620,
                      3400,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-east-1",
                    "start_mm": [
                      16620,
                      300,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "东列柱间，止于柱面",
                    "end_mm": [
                      16620,
                      6800,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-east-2",
                    "start_mm": [
                      16620,
                      3700,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "东列柱间，止于柱面；Y=8.2以北与平台连通，不补横挡",
                    "end_mm": [
                      16620,
                      8200,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-east-3",
                    "start_mm": [
                      16620,
                      7100,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "北廊柱间，止于柱面",
                    "end_mm": [
                      10350,
                      10620,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-north-1",
                    "start_mm": [
                      7400,
                      10620,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "北廊柱间，止于柱面",
                    "end_mm": [
                      13350,
                      10620,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-north-2",
                    "start_mm": [
                      10650,
                      10620,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "北廊柱间，止于平台西边",
                    "end_mm": [
                      14800,
                      10620,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-north-3",
                    "start_mm": [
                      13650,
                      10620,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "西翼前端，止于柱面",
                    "end_mm": [
                      7100,
                      20,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-front-west",
                    "start_mm": [
                      5000,
                      20,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "东翼前端，止于柱面",
                    "end_mm": [
                      19000,
                      20,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-front-east",
                    "start_mm": [
                      16900,
                      20,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "楼梯上端平台西侧；平台南侧为楼梯到达口，不横加栏杆",
                    "end_mm": [
                      14820,
                      10600,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-2-rail-landing-west",
                    "start_mm": [
                      14820,
                      8200,
                      3600
                    ],
                    "storey": "storey-2",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "梯段左侧斜护栏；栏高按基线上方竖直高度，立柱与细杆保持竖直，扶手随梯段上升",
                    "end_mm": [
                      14820,
                      8200,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-1-rail-stair-left",
                    "start_mm": [
                      14820,
                      2200,
                      0
                    ],
                    "storey": "storey-1",
                    "thickness_mm": 40
                  },
                  {
                    "alignment_target": "梯段右侧斜护栏；栏高按基线上方竖直高度，立柱与细杆保持竖直，扶手随梯段上升",
                    "end_mm": [
                      16580,
                      8200,
                      3600
                    ],
                    "height_mm": 1100,
                    "id": "storey-1-rail-stair-right",
                    "start_mm": [
                      16580,
                      2200,
                      0
                    ],
                    "storey": "storey-1",
                    "thickness_mm": 40
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/bottom_elevation_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 7000
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/id",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "slab-roof"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/ifc_class",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "IfcSlab"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/note",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "与二层U形板相同平面；按一块屋面用途IfcSlab表达，不增加IfcRoof或第三层"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/polygon",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  [
                    0,
                    0
                  ],
                  [
                    7400,
                    0
                  ],
                  [
                    7400,
                    10600
                  ],
                  [
                    16600,
                    10600
                  ],
                  [
                    16600,
                    0
                  ],
                  [
                    24000,
                    0
                  ],
                  [
                    24000,
                    18000
                  ],
                  [
                    0,
                    18000
                  ],
                  [
                    0,
                    0
                  ]
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/predefined_type",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "ROOF"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/storey",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "storey-2"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 200
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_requirements",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-1-wall-west-exterior",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-1-wall-east-exterior",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-1-wall-north-exterior",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-1-wall-west-front",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-1-wall-east-front",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-1-wall-west-court",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-1-wall-east-court",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-1-wall-north-room-south",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-2-wall-west-exterior",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-2-wall-east-exterior",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-2-wall-north-exterior",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-2-wall-west-front",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-2-wall-east-front",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-2-wall-west-court",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-2-wall-east-court",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "storey-2-wall-north-room-south",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "slab-ground-1",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "slab-u-floor-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "slab-landing-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "slab-roof",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "stair-1",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.902,
                        0.878,
                        0.827
                      ]
                    },
                    "entity_id": "stair-flight-1",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-beam-west",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-beam-east",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-beam-north",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-beam-west",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-beam-east",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-beam-north",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-col-west-1",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-col-west-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-col-west-3",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-col-west-4",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-col-east-1",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-col-east-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-col-east-3",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-col-east-4",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-col-north-1",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-1-col-north-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-col-west-1",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-col-west-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-col-west-3",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-col-west-4",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-col-east-1",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-col-east-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-col-east-3",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-col-east-4",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-col-north-1",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.824,
                        0.78,
                        0.702
                      ]
                    },
                    "entity_id": "storey-2-col-north-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-west-1",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-west-2",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-west-3",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-east-1",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-east-2",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-east-3",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-north-1",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-north-2",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-north-3",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-front-west",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-front-east",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-2-rail-landing-west",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-1-rail-stair-left",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "appearance": {
                      "color": [
                        0.188,
                        0.294,
                        0.302
                      ],
                      "transparency": 0
                    },
                    "entity_id": "storey-1-rail-stair-right",
                    "material": {
                      "kind": "single_material",
                      "name": "钢材"
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "metal-picket",
                      "template_version": "text2ifc/basic-railing/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-door-west-reading",
                    "material": {
                      "kind": "single_material",
                      "name": "木材"
                    },
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "panel": {
                        "color": [
                          0.651,
                          0.435,
                          0.263
                        ]
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-left",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-door-east-reading",
                    "material": {
                      "kind": "single_material",
                      "name": "木材"
                    },
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "panel": {
                        "color": [
                          0.651,
                          0.435,
                          0.263
                        ]
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-door-north-reading",
                    "material": {
                      "kind": "single_material",
                      "name": "木材"
                    },
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "panel": {
                        "color": [
                          0.651,
                          0.435,
                          0.263
                        ]
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-left",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-door-west-reading",
                    "material": {
                      "kind": "single_material",
                      "name": "木材"
                    },
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "panel": {
                        "color": [
                          0.651,
                          0.435,
                          0.263
                        ]
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-left",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-door-east-reading",
                    "material": {
                      "kind": "single_material",
                      "name": "木材"
                    },
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "panel": {
                        "color": [
                          0.651,
                          0.435,
                          0.263
                        ]
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-door-north-reading",
                    "material": {
                      "kind": "single_material",
                      "name": "木材"
                    },
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "panel": {
                        "color": [
                          0.651,
                          0.435,
                          0.263
                        ]
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-left",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-west-ext-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-west-ext-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-west-ext-3",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-west-ext-4",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-east-ext-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-east-ext-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-east-ext-3",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-east-ext-4",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-north-ext-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-north-ext-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-north-ext-3",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-north-ext-4",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-west-court-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-west-court-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-west-court-3",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-east-court-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-east-court-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-east-court-3",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-north-room-south-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-north-room-south-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-west-front",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-win-east-front",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-west-ext-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-west-ext-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-west-ext-3",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-west-ext-4",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-east-ext-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-east-ext-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-east-ext-3",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-east-ext-4",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-north-ext-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-north-ext-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-north-ext-3",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-north-ext-4",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-west-court-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-west-court-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-west-court-3",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-east-court-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-east-court-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-east-court-3",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-north-room-south-1",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-north-room-south-2",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-west-front",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-win-east-front",
                    "part_appearance": {
                      "frame": {
                        "color": [
                          0.188,
                          0.294,
                          0.302
                        ]
                      },
                      "glazing": {
                        "transparency": 0.65
                      }
                    },
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_review/appearance/source_turns",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  "turn-user-001"
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_review/appearance/status",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "specified"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_review/material/source_turns",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  "turn-user-001"
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_review/material/status",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "specified"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_review/property/source_turns",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  "turn-user-001"
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_review/property/status",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "not_specified"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_review/template/source_turns",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  "turn-user-001"
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_review/template/status",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "specified"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_review/type/source_turns",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  "turn-user-001",
                  "turn-user-concept-revision"
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/semantic_review/type/status",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "not_specified"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/stairs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "bounds": {
                      "x": [
                        14800,
                        16600
                      ],
                      "y": [
                        2200,
                        8200
                      ]
                    },
                    "end_elevation_mm": 3600,
                    "flight_ids": [
                      "stair-flight-1"
                    ],
                    "from_storey": "storey-1",
                    "id": "stair-1",
                    "note": "外露直跑混凝土楼梯，位于主U形楼板外露空区内；Y=0到2.2为地面到达区，不设门或墙阻挡，无楼梯间墙、无额外封闭洞口",
                    "number_of_risers": 20,
                    "number_of_treads": 20,
                    "riser_height_mm": 180,
                    "run_direction": "north",
                    "start_elevation_mm": 0,
                    "to_storey": "storey-2",
                    "tread_depth_mm": 300,
                    "width_mm": 1800
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/storeys",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "doors": [
                      {
                        "center_global_mm": [
                          4900,
                          8000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-west-court",
                        "id": "storey-1-door-west-reading",
                        "operation": "left",
                        "sill_height_mm": 0,
                        "width_mm": 1200
                      },
                      {
                        "center_global_mm": [
                          19100,
                          8000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-east-court",
                        "id": "storey-1-door-east-reading",
                        "operation": "right",
                        "sill_height_mm": 0,
                        "width_mm": 1200
                      },
                      {
                        "center_global_mm": [
                          12000,
                          13000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-north-room-south",
                        "id": "storey-1-door-north-reading",
                        "operation": "left",
                        "sill_height_mm": 0,
                        "width_mm": 1400
                      }
                    ],
                    "elevation_mm": 0,
                    "id": "storey-1",
                    "name": "首层",
                    "net_height_mm": 3400,
                    "spaces": [
                      {
                        "bounds": {
                          "x": [
                            200,
                            4800
                          ],
                          "y": [
                            200,
                            12900
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-1-space-west-reading",
                        "name": "西侧阅读室"
                      },
                      {
                        "bounds": {
                          "x": [
                            19200,
                            23800
                          ],
                          "y": [
                            200,
                            12900
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-1-space-east-reading",
                        "name": "东侧阅读室"
                      },
                      {
                        "bounds": {
                          "x": [
                            200,
                            23800
                          ],
                          "y": [
                            13100,
                            17800
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-1-space-north-reading",
                        "name": "北侧阅览室"
                      },
                      {
                        "bounds": {
                          "x": [
                            5000,
                            7400
                          ],
                          "y": [
                            0,
                            10600
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-1-space-west-colonnade",
                        "interior_or_exterior": "EXTERNAL",
                        "name": "西侧回廊"
                      },
                      {
                        "bounds": {
                          "x": [
                            16600,
                            19000
                          ],
                          "y": [
                            0,
                            10600
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-1-space-east-colonnade",
                        "interior_or_exterior": "EXTERNAL",
                        "name": "东侧回廊"
                      },
                      {
                        "bounds": {
                          "x": [
                            5000,
                            19000
                          ],
                          "y": [
                            10600,
                            12900
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-1-space-north-colonnade",
                        "interior_or_exterior": "EXTERNAL",
                        "name": "北侧回廊"
                      }
                    ],
                    "walls": {
                      "exterior": [
                        {
                          "bounds": {
                            "x": [
                              0,
                              200
                            ],
                            "y": [
                              0,
                              18000
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-1-wall-west-exterior",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              23800,
                              24000
                            ],
                            "y": [
                              0,
                              18000
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-1-wall-east-exterior",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              200,
                              23800
                            ],
                            "y": [
                              17800,
                              18000
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-1-wall-north-exterior",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              200,
                              4800
                            ],
                            "y": [
                              0,
                              200
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-1-wall-west-front",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              19200,
                              23800
                            ],
                            "y": [
                              0,
                              200
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-1-wall-east-front",
                          "thickness_mm": 200
                        }
                      ],
                      "interior": [
                        {
                          "bounds": {
                            "x": [
                              4800,
                              5000
                            ],
                            "y": [
                              0,
                              12900
                            ]
                          },
                          "connects": [
                            "storey-1-space-west-reading",
                            "storey-1-space-west-colonnade"
                          ],
                          "height_mm": 3400,
                          "id": "storey-1-wall-west-court",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              19000,
                              19200
                            ],
                            "y": [
                              0,
                              12900
                            ]
                          },
                          "connects": [
                            "storey-1-space-east-reading",
                            "storey-1-space-east-colonnade"
                          ],
                          "height_mm": 3400,
                          "id": "storey-1-wall-east-court",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              200,
                              23800
                            ],
                            "y": [
                              12900,
                              13100
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-1-wall-north-room-south",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_global_mm": [
                          100,
                          3000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-west-exterior",
                        "id": "storey-1-win-west-ext-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          100,
                          7000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-west-exterior",
                        "id": "storey-1-win-west-ext-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          100,
                          11000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-west-exterior",
                        "id": "storey-1-win-west-ext-3",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          100,
                          16000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-west-exterior",
                        "id": "storey-1-win-west-ext-4",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          23900,
                          3000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-east-exterior",
                        "id": "storey-1-win-east-ext-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          23900,
                          7000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-east-exterior",
                        "id": "storey-1-win-east-ext-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          23900,
                          11000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-east-exterior",
                        "id": "storey-1-win-east-ext-3",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          23900,
                          16000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-east-exterior",
                        "id": "storey-1-win-east-ext-4",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          4000,
                          17900
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-north-exterior",
                        "id": "storey-1-win-north-ext-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          9000,
                          17900
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-north-exterior",
                        "id": "storey-1-win-north-ext-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          15000,
                          17900
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-north-exterior",
                        "id": "storey-1-win-north-ext-3",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          20000,
                          17900
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-north-exterior",
                        "id": "storey-1-win-north-ext-4",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          4900,
                          2000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-west-court",
                        "id": "storey-1-win-west-court-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          4900,
                          5000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-west-court",
                        "id": "storey-1-win-west-court-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          4900,
                          11000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-west-court",
                        "id": "storey-1-win-west-court-3",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          19100,
                          2000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-east-court",
                        "id": "storey-1-win-east-court-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          19100,
                          5000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-east-court",
                        "id": "storey-1-win-east-court-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          19100,
                          11000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-east-court",
                        "id": "storey-1-win-east-court-3",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          7000,
                          13000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-north-room-south",
                        "id": "storey-1-win-north-room-south-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          17000,
                          13000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-north-room-south",
                        "id": "storey-1-win-north-room-south-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          2500,
                          100
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-west-front",
                        "id": "storey-1-win-west-front",
                        "sill_height_mm": 600,
                        "width_mm": 2600
                      },
                      {
                        "center_global_mm": [
                          21500,
                          100
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-east-front",
                        "id": "storey-1-win-east-front",
                        "sill_height_mm": 600,
                        "width_mm": 2600
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "center_global_mm": [
                          4900,
                          8000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-west-court",
                        "id": "storey-2-door-west-reading",
                        "operation": "left",
                        "sill_height_mm": 0,
                        "width_mm": 1200
                      },
                      {
                        "center_global_mm": [
                          19100,
                          8000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-east-court",
                        "id": "storey-2-door-east-reading",
                        "operation": "right",
                        "sill_height_mm": 0,
                        "width_mm": 1200
                      },
                      {
                        "center_global_mm": [
                          12000,
                          13000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-north-room-south",
                        "id": "storey-2-door-north-reading",
                        "operation": "left",
                        "sill_height_mm": 0,
                        "width_mm": 1400
                      }
                    ],
                    "elevation_mm": 3600,
                    "id": "storey-2",
                    "name": "二层",
                    "net_height_mm": 3400,
                    "spaces": [
                      {
                        "bounds": {
                          "x": [
                            200,
                            4800
                          ],
                          "y": [
                            200,
                            12900
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-2-space-west-reading",
                        "name": "西侧阅读室"
                      },
                      {
                        "bounds": {
                          "x": [
                            19200,
                            23800
                          ],
                          "y": [
                            200,
                            12900
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-2-space-east-reading",
                        "name": "东侧阅读室"
                      },
                      {
                        "bounds": {
                          "x": [
                            200,
                            23800
                          ],
                          "y": [
                            13100,
                            17800
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-2-space-north-reading",
                        "name": "北侧阅览室"
                      },
                      {
                        "bounds": {
                          "x": [
                            5000,
                            7400
                          ],
                          "y": [
                            0,
                            10600
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-2-space-west-colonnade",
                        "interior_or_exterior": "EXTERNAL",
                        "name": "西侧回廊"
                      },
                      {
                        "bounds": {
                          "x": [
                            16600,
                            19000
                          ],
                          "y": [
                            0,
                            10600
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-2-space-east-colonnade",
                        "interior_or_exterior": "EXTERNAL",
                        "name": "东侧回廊"
                      },
                      {
                        "bounds": {
                          "x": [
                            5000,
                            19000
                          ],
                          "y": [
                            10600,
                            12900
                          ]
                        },
                        "height_mm": 3400,
                        "id": "storey-2-space-north-colonnade",
                        "interior_or_exterior": "EXTERNAL",
                        "name": "北侧回廊"
                      }
                    ],
                    "walls": {
                      "exterior": [
                        {
                          "bounds": {
                            "x": [
                              0,
                              200
                            ],
                            "y": [
                              0,
                              18000
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-2-wall-west-exterior",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              23800,
                              24000
                            ],
                            "y": [
                              0,
                              18000
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-2-wall-east-exterior",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              200,
                              23800
                            ],
                            "y": [
                              17800,
                              18000
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-2-wall-north-exterior",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              200,
                              4800
                            ],
                            "y": [
                              0,
                              200
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-2-wall-west-front",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              19200,
                              23800
                            ],
                            "y": [
                              0,
                              200
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-2-wall-east-front",
                          "thickness_mm": 200
                        }
                      ],
                      "interior": [
                        {
                          "bounds": {
                            "x": [
                              4800,
                              5000
                            ],
                            "y": [
                              0,
                              12900
                            ]
                          },
                          "connects": [
                            "storey-2-space-west-reading",
                            "storey-2-space-west-colonnade"
                          ],
                          "height_mm": 3400,
                          "id": "storey-2-wall-west-court",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              19000,
                              19200
                            ],
                            "y": [
                              0,
                              12900
                            ]
                          },
                          "connects": [
                            "storey-2-space-east-reading",
                            "storey-2-space-east-colonnade"
                          ],
                          "height_mm": 3400,
                          "id": "storey-2-wall-east-court",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              200,
                              23800
                            ],
                            "y": [
                              12900,
                              13100
                            ]
                          },
                          "height_mm": 3400,
                          "id": "storey-2-wall-north-room-south",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_global_mm": [
                          100,
                          3000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-west-exterior",
                        "id": "storey-2-win-west-ext-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          100,
                          7000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-west-exterior",
                        "id": "storey-2-win-west-ext-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          100,
                          11000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-west-exterior",
                        "id": "storey-2-win-west-ext-3",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          100,
                          16000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-west-exterior",
                        "id": "storey-2-win-west-ext-4",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          23900,
                          3000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-east-exterior",
                        "id": "storey-2-win-east-ext-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          23900,
                          7000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-east-exterior",
                        "id": "storey-2-win-east-ext-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          23900,
                          11000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-east-exterior",
                        "id": "storey-2-win-east-ext-3",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          23900,
                          16000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-east-exterior",
                        "id": "storey-2-win-east-ext-4",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          4000,
                          17900
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-north-exterior",
                        "id": "storey-2-win-north-ext-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          9000,
                          17900
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-north-exterior",
                        "id": "storey-2-win-north-ext-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          15000,
                          17900
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-north-exterior",
                        "id": "storey-2-win-north-ext-3",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          20000,
                          17900
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-north-exterior",
                        "id": "storey-2-win-north-ext-4",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          4900,
                          2000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-west-court",
                        "id": "storey-2-win-west-court-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          4900,
                          5000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-west-court",
                        "id": "storey-2-win-west-court-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          4900,
                          11000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-west-court",
                        "id": "storey-2-win-west-court-3",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          19100,
                          2000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-east-court",
                        "id": "storey-2-win-east-court-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          19100,
                          5000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-east-court",
                        "id": "storey-2-win-east-court-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          19100,
                          11000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-east-court",
                        "id": "storey-2-win-east-court-3",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          7000,
                          13000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-north-room-south",
                        "id": "storey-2-win-north-room-south-1",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          17000,
                          13000
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-north-room-south",
                        "id": "storey-2-win-north-room-south-2",
                        "sill_height_mm": 600,
                        "width_mm": 2000
                      },
                      {
                        "center_global_mm": [
                          2500,
                          100
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-west-front",
                        "id": "storey-2-win-west-front",
                        "sill_height_mm": 600,
                        "width_mm": 2600
                      },
                      {
                        "center_global_mm": [
                          21500,
                          100
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-2-wall-east-front",
                        "id": "storey-2-win-east-front",
                        "sill_height_mm": 600,
                        "width_mm": 2600
                      }
                    ]
                  }
                ]
              }
            ],
            "schema_version": "text2ifc/semantic-coverage/1.0",
            "valid": true
          }
        },
        "expected_facts_hash": "1ef2e9c2f98a51efc41fe74f4e738738ab60d7b640bf81539be4922028adab14",
        "expected_facts_path": "expected-facts.json",
        "gates": [
          {
            "applicability": "applicable",
            "basis": "generator validation sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "bim_json_validation",
            "source_paths": [
              "generator/validation.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "expected-facts total_counts compared with candidate entities",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_entity_completeness",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "expected storey and host-wall facts compared with candidate placement/void-fill graph",
            "entity_matches": [
              {
                "candidate_id": "door-storey-1-storey-1-door-west-reading",
                "collection": "doors",
                "expected_id": "storey-1-door-west-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-1-storey-1-door-east-reading",
                "collection": "doors",
                "expected_id": "storey-1-door-east-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-1-storey-1-door-north-reading",
                "collection": "doors",
                "expected_id": "storey-1-door-north-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-2-storey-2-door-west-reading",
                "collection": "doors",
                "expected_id": "storey-2-door-west-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-2-storey-2-door-east-reading",
                "collection": "doors",
                "expected_id": "storey-2-door-east-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-2-storey-2-door-north-reading",
                "collection": "doors",
                "expected_id": "storey-2-door-north-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "storey-1-col-west-1",
                "collection": "products",
                "expected_id": "storey-1-col-west-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-col-west-2",
                "collection": "products",
                "expected_id": "storey-1-col-west-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-col-west-3",
                "collection": "products",
                "expected_id": "storey-1-col-west-3",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-col-west-4",
                "collection": "products",
                "expected_id": "storey-1-col-west-4",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-col-east-1",
                "collection": "products",
                "expected_id": "storey-1-col-east-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-col-east-2",
                "collection": "products",
                "expected_id": "storey-1-col-east-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-col-east-3",
                "collection": "products",
                "expected_id": "storey-1-col-east-3",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-col-east-4",
                "collection": "products",
                "expected_id": "storey-1-col-east-4",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-col-north-1",
                "collection": "products",
                "expected_id": "storey-1-col-north-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-col-north-2",
                "collection": "products",
                "expected_id": "storey-1-col-north-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-col-west-1",
                "collection": "products",
                "expected_id": "storey-2-col-west-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-col-west-2",
                "collection": "products",
                "expected_id": "storey-2-col-west-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-col-west-3",
                "collection": "products",
                "expected_id": "storey-2-col-west-3",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-col-west-4",
                "collection": "products",
                "expected_id": "storey-2-col-west-4",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-col-east-1",
                "collection": "products",
                "expected_id": "storey-2-col-east-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-col-east-2",
                "collection": "products",
                "expected_id": "storey-2-col-east-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-col-east-3",
                "collection": "products",
                "expected_id": "storey-2-col-east-3",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-col-east-4",
                "collection": "products",
                "expected_id": "storey-2-col-east-4",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-col-north-1",
                "collection": "products",
                "expected_id": "storey-2-col-north-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-col-north-2",
                "collection": "products",
                "expected_id": "storey-2-col-north-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-beam-west",
                "collection": "products",
                "expected_id": "storey-1-beam-west",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-beam-east",
                "collection": "products",
                "expected_id": "storey-1-beam-east",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-beam-north",
                "collection": "products",
                "expected_id": "storey-1-beam-north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-beam-west",
                "collection": "products",
                "expected_id": "storey-2-beam-west",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-beam-east",
                "collection": "products",
                "expected_id": "storey-2-beam-east",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-beam-north",
                "collection": "products",
                "expected_id": "storey-2-beam-north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-west-1",
                "collection": "products",
                "expected_id": "storey-2-rail-west-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-west-2",
                "collection": "products",
                "expected_id": "storey-2-rail-west-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-west-3",
                "collection": "products",
                "expected_id": "storey-2-rail-west-3",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-east-1",
                "collection": "products",
                "expected_id": "storey-2-rail-east-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-east-2",
                "collection": "products",
                "expected_id": "storey-2-rail-east-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-east-3",
                "collection": "products",
                "expected_id": "storey-2-rail-east-3",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-north-1",
                "collection": "products",
                "expected_id": "storey-2-rail-north-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-north-2",
                "collection": "products",
                "expected_id": "storey-2-rail-north-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-north-3",
                "collection": "products",
                "expected_id": "storey-2-rail-north-3",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-front-west",
                "collection": "products",
                "expected_id": "storey-2-rail-front-west",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-front-east",
                "collection": "products",
                "expected_id": "storey-2-rail-front-east",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-2-rail-landing-west",
                "collection": "products",
                "expected_id": "storey-2-rail-landing-west",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-rail-stair-left",
                "collection": "products",
                "expected_id": "storey-1-rail-stair-left",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "storey-1-rail-stair-right",
                "collection": "products",
                "expected_id": "storey-1-rail-stair-right",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-storey-1-storey-1-space-west-reading",
                "collection": "spaces",
                "expected_id": "storey-1-space-west-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-1-storey-1-space-east-reading",
                "collection": "spaces",
                "expected_id": "storey-1-space-east-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-1-storey-1-space-north-reading",
                "collection": "spaces",
                "expected_id": "storey-1-space-north-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-1-storey-1-space-west-colonnade",
                "collection": "spaces",
                "expected_id": "storey-1-space-west-colonnade",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-1-storey-1-space-east-colonnade",
                "collection": "spaces",
                "expected_id": "storey-1-space-east-colonnade",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-1-storey-1-space-north-colonnade",
                "collection": "spaces",
                "expected_id": "storey-1-space-north-colonnade",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-2-storey-2-space-west-reading",
                "collection": "spaces",
                "expected_id": "storey-2-space-west-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-2-storey-2-space-east-reading",
                "collection": "spaces",
                "expected_id": "storey-2-space-east-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-2-storey-2-space-north-reading",
                "collection": "spaces",
                "expected_id": "storey-2-space-north-reading",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-2-storey-2-space-west-colonnade",
                "collection": "spaces",
                "expected_id": "storey-2-space-west-colonnade",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-2-storey-2-space-east-colonnade",
                "collection": "spaces",
                "expected_id": "storey-2-space-east-colonnade",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-2-storey-2-space-north-colonnade",
                "collection": "spaces",
                "expected_id": "storey-2-space-north-colonnade",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-west-exterior",
                "collection": "walls",
                "expected_id": "storey-1-wall-west-exterior",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-east-exterior",
                "collection": "walls",
                "expected_id": "storey-1-wall-east-exterior",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-north-exterior",
                "collection": "walls",
                "expected_id": "storey-1-wall-north-exterior",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-west-front",
                "collection": "walls",
                "expected_id": "storey-1-wall-west-front",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-east-front",
                "collection": "walls",
                "expected_id": "storey-1-wall-east-front",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-west-court",
                "collection": "walls",
                "expected_id": "storey-1-wall-west-court",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-east-court",
                "collection": "walls",
                "expected_id": "storey-1-wall-east-court",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-north-room-south",
                "collection": "walls",
                "expected_id": "storey-1-wall-north-room-south",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-west-exterior",
                "collection": "walls",
                "expected_id": "storey-2-wall-west-exterior",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-east-exterior",
                "collection": "walls",
                "expected_id": "storey-2-wall-east-exterior",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-north-exterior",
                "collection": "walls",
                "expected_id": "storey-2-wall-north-exterior",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-west-front",
                "collection": "walls",
                "expected_id": "storey-2-wall-west-front",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-east-front",
                "collection": "walls",
                "expected_id": "storey-2-wall-east-front",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-west-court",
                "collection": "walls",
                "expected_id": "storey-2-wall-west-court",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-east-court",
                "collection": "walls",
                "expected_id": "storey-2-wall-east-court",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-north-room-south",
                "collection": "walls",
                "expected_id": "storey-2-wall-north-room-south",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-west-ext-1",
                "collection": "windows",
                "expected_id": "storey-1-win-west-ext-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-west-ext-2",
                "collection": "windows",
                "expected_id": "storey-1-win-west-ext-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-west-ext-3",
                "collection": "windows",
                "expected_id": "storey-1-win-west-ext-3",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-west-ext-4",
                "collection": "windows",
                "expected_id": "storey-1-win-west-ext-4",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-east-ext-1",
                "collection": "windows",
                "expected_id": "storey-1-win-east-ext-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-east-ext-2",
                "collection": "windows",
                "expected_id": "storey-1-win-east-ext-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-east-ext-3",
                "collection": "windows",
                "expected_id": "storey-1-win-east-ext-3",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-east-ext-4",
                "collection": "windows",
                "expected_id": "storey-1-win-east-ext-4",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-north-ext-1",
                "collection": "windows",
                "expected_id": "storey-1-win-north-ext-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-north-ext-2",
                "collection": "windows",
                "expected_id": "storey-1-win-north-ext-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-north-ext-3",
                "collection": "windows",
                "expected_id": "storey-1-win-north-ext-3",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-north-ext-4",
                "collection": "windows",
                "expected_id": "storey-1-win-north-ext-4",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-west-court-1",
                "collection": "windows",
                "expected_id": "storey-1-win-west-court-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-west-court-2",
                "collection": "windows",
                "expected_id": "storey-1-win-west-court-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-west-court-3",
                "collection": "windows",
                "expected_id": "storey-1-win-west-court-3",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-east-court-1",
                "collection": "windows",
                "expected_id": "storey-1-win-east-court-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-east-court-2",
                "collection": "windows",
                "expected_id": "storey-1-win-east-court-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-east-court-3",
                "collection": "windows",
                "expected_id": "storey-1-win-east-court-3",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-north-room-south-1",
                "collection": "windows",
                "expected_id": "storey-1-win-north-room-south-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-north-room-south-2",
                "collection": "windows",
                "expected_id": "storey-1-win-north-room-south-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-west-front",
                "collection": "windows",
                "expected_id": "storey-1-win-west-front",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-win-east-front",
                "collection": "windows",
                "expected_id": "storey-1-win-east-front",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-west-ext-1",
                "collection": "windows",
                "expected_id": "storey-2-win-west-ext-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-west-ext-2",
                "collection": "windows",
                "expected_id": "storey-2-win-west-ext-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-west-ext-3",
                "collection": "windows",
                "expected_id": "storey-2-win-west-ext-3",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-west-ext-4",
                "collection": "windows",
                "expected_id": "storey-2-win-west-ext-4",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-east-ext-1",
                "collection": "windows",
                "expected_id": "storey-2-win-east-ext-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-east-ext-2",
                "collection": "windows",
                "expected_id": "storey-2-win-east-ext-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-east-ext-3",
                "collection": "windows",
                "expected_id": "storey-2-win-east-ext-3",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-east-ext-4",
                "collection": "windows",
                "expected_id": "storey-2-win-east-ext-4",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-north-ext-1",
                "collection": "windows",
                "expected_id": "storey-2-win-north-ext-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-north-ext-2",
                "collection": "windows",
                "expected_id": "storey-2-win-north-ext-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-north-ext-3",
                "collection": "windows",
                "expected_id": "storey-2-win-north-ext-3",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-north-ext-4",
                "collection": "windows",
                "expected_id": "storey-2-win-north-ext-4",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-west-court-1",
                "collection": "windows",
                "expected_id": "storey-2-win-west-court-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-west-court-2",
                "collection": "windows",
                "expected_id": "storey-2-win-west-court-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-west-court-3",
                "collection": "windows",
                "expected_id": "storey-2-win-west-court-3",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-east-court-1",
                "collection": "windows",
                "expected_id": "storey-2-win-east-court-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-east-court-2",
                "collection": "windows",
                "expected_id": "storey-2-win-east-court-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-east-court-3",
                "collection": "windows",
                "expected_id": "storey-2-win-east-court-3",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-north-room-south-1",
                "collection": "windows",
                "expected_id": "storey-2-win-north-room-south-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-north-room-south-2",
                "collection": "windows",
                "expected_id": "storey-2-win-north-room-south-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-west-front",
                "collection": "windows",
                "expected_id": "storey-2-win-west-front",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-win-east-front",
                "collection": "windows",
                "expected_id": "storey-2-win-east-front",
                "match_basis": "canonical_entity_id"
              }
            ],
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_storey_containment",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "explicit component storey labels compared with placement ownership and uniquely frozen cross-storey service context; names do not certify ownership",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_storey_name_consistency",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "expected opening/fill obligations compared with IfcRelVoidsElement and IfcRelFillsElement",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_opening_fill",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "semantic coverage sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "semantic_coverage",
            "source_paths": [
              "semantic-coverage.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "independent reopened IFC/request comparison",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "request_semantics",
            "source_paths": [
              "semantic-verification.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "IFC compile/reopen sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "ifc_compile_reopen",
            "source_paths": [
              "ifc-verification.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "geometry feedback sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "geometry",
            "source_paths": [
              "geometry-feedback.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "repair route is no_repair_needed; this gate checks route eligibility only, not a geometry pass. Counts in route/metrics refer only to feedback supplied to that routing invocation; current geometry gate is independent.",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "repair_route",
            "source_paths": [
              "repair/route.json"
            ],
            "status": "passed"
          }
        ],
        "overall_status": "passed",
        "schema_version": "text2ifc/gate-summary/1.0"
      },
      "geometry_feedback": {
        "expectation_source": "design_brief_expected_facts",
        "issues": [],
        "metrics": {
          "case_id": "ce8116ce095acdcf",
          "floor_openings": {},
          "products": {
            "storey-1-beam-east": {
              "bbox": {
                "x": [
                  16.6,
                  16.9
                ],
                "y": [
                  0.0,
                  10.9
                ],
                "z": [
                  3.1,
                  3.4
                ]
              },
              "ifc_class": "IfcBeam",
              "storey_id": "storey-1"
            },
            "storey-1-beam-north": {
              "bbox": {
                "x": [
                  7.3999999999999995,
                  16.6
                ],
                "y": [
                  10.6,
                  10.9
                ],
                "z": [
                  3.1,
                  3.4
                ]
              },
              "ifc_class": "IfcBeam",
              "storey_id": "storey-1"
            },
            "storey-1-beam-west": {
              "bbox": {
                "x": [
                  7.1,
                  7.4
                ],
                "y": [
                  0.0,
                  10.9
                ],
                "z": [
                  3.1,
                  3.4
                ]
              },
              "ifc_class": "IfcBeam",
              "storey_id": "storey-1"
            },
            "storey-1-col-east-1": {
              "bbox": {
                "x": [
                  16.6,
                  16.9
                ],
                "y": [
                  0.0,
                  0.3
                ],
                "z": [
                  0.0,
                  3.1
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-1"
            },
            "storey-1-col-east-2": {
              "bbox": {
                "x": [
                  16.6,
                  16.9
                ],
                "y": [
                  3.4000000000000004,
                  3.7
                ],
                "z": [
                  0.0,
                  3.1
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-1"
            },
            "storey-1-col-east-3": {
              "bbox": {
                "x": [
                  16.6,
                  16.9
                ],
                "y": [
                  6.8,
                  7.1000000000000005
                ],
                "z": [
                  0.0,
                  3.1
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-1"
            },
            "storey-1-col-east-4": {
              "bbox": {
                "x": [
                  16.6,
                  16.9
                ],
                "y": [
                  10.3,
                  10.600000000000001
                ],
                "z": [
                  0.0,
                  3.1
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-1"
            },
            "storey-1-col-north-1": {
              "bbox": {
                "x": [
                  10.35,
                  10.65
                ],
                "y": [
                  10.6,
                  10.9
                ],
                "z": [
                  0.0,
                  3.1
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-1"
            },
            "storey-1-col-north-2": {
              "bbox": {
                "x": [
                  13.35,
                  13.65
                ],
                "y": [
                  10.6,
                  10.9
                ],
                "z": [
                  0.0,
                  3.1
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-1"
            },
            "storey-1-col-west-1": {
              "bbox": {
                "x": [
                  7.1,
                  7.4
                ],
                "y": [
                  0.0,
                  0.3
                ],
                "z": [
                  0.0,
                  3.1
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-1"
            },
            "storey-1-col-west-2": {
              "bbox": {
                "x": [
                  7.1,
                  7.4
                ],
                "y": [
                  3.4000000000000004,
                  3.7
                ],
                "z": [
                  0.0,
                  3.1
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-1"
            },
            "storey-1-col-west-3": {
              "bbox": {
                "x": [
                  7.1,
                  7.4
                ],
                "y": [
                  6.8,
                  7.1000000000000005
                ],
                "z": [
                  0.0,
                  3.1
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-1"
            },
            "storey-1-col-west-4": {
              "bbox": {
                "x": [
                  7.1,
                  7.4
                ],
                "y": [
                  10.3,
                  10.600000000000001
                ],
                "z": [
                  0.0,
                  3.1
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-1"
            },
            "storey-1-rail-stair-left": {
              "bbox": {
                "x": [
                  14.8,
                  14.84
                ],
                "y": [
                  2.2,
                  8.2
                ],
                "z": [
                  0.0,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-1"
            },
            "storey-1-rail-stair-right": {
              "bbox": {
                "x": [
                  16.560000000000002,
                  16.6
                ],
                "y": [
                  2.2,
                  8.2
                ],
                "z": [
                  0.0,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-1"
            },
            "storey-2-beam-east": {
              "bbox": {
                "x": [
                  16.6,
                  16.9
                ],
                "y": [
                  0.0,
                  10.9
                ],
                "z": [
                  6.7,
                  7.0
                ]
              },
              "ifc_class": "IfcBeam",
              "storey_id": "storey-2"
            },
            "storey-2-beam-north": {
              "bbox": {
                "x": [
                  7.3999999999999995,
                  16.6
                ],
                "y": [
                  10.6,
                  10.9
                ],
                "z": [
                  6.7,
                  7.0
                ]
              },
              "ifc_class": "IfcBeam",
              "storey_id": "storey-2"
            },
            "storey-2-beam-west": {
              "bbox": {
                "x": [
                  7.1,
                  7.4
                ],
                "y": [
                  0.0,
                  10.9
                ],
                "z": [
                  6.7,
                  7.0
                ]
              },
              "ifc_class": "IfcBeam",
              "storey_id": "storey-2"
            },
            "storey-2-col-east-1": {
              "bbox": {
                "x": [
                  16.6,
                  16.9
                ],
                "y": [
                  0.0,
                  0.3
                ],
                "z": [
                  3.6,
                  6.7
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-2"
            },
            "storey-2-col-east-2": {
              "bbox": {
                "x": [
                  16.6,
                  16.9
                ],
                "y": [
                  3.4000000000000004,
                  3.7
                ],
                "z": [
                  3.6,
                  6.7
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-2"
            },
            "storey-2-col-east-3": {
              "bbox": {
                "x": [
                  16.6,
                  16.9
                ],
                "y": [
                  6.8,
                  7.1000000000000005
                ],
                "z": [
                  3.6,
                  6.7
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-2"
            },
            "storey-2-col-east-4": {
              "bbox": {
                "x": [
                  16.6,
                  16.9
                ],
                "y": [
                  10.3,
                  10.600000000000001
                ],
                "z": [
                  3.6,
                  6.7
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-2"
            },
            "storey-2-col-north-1": {
              "bbox": {
                "x": [
                  10.35,
                  10.65
                ],
                "y": [
                  10.6,
                  10.9
                ],
                "z": [
                  3.6,
                  6.7
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-2"
            },
            "storey-2-col-north-2": {
              "bbox": {
                "x": [
                  13.35,
                  13.65
                ],
                "y": [
                  10.6,
                  10.9
                ],
                "z": [
                  3.6,
                  6.7
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-2"
            },
            "storey-2-col-west-1": {
              "bbox": {
                "x": [
                  7.1,
                  7.4
                ],
                "y": [
                  0.0,
                  0.3
                ],
                "z": [
                  3.6,
                  6.7
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-2"
            },
            "storey-2-col-west-2": {
              "bbox": {
                "x": [
                  7.1,
                  7.4
                ],
                "y": [
                  3.4000000000000004,
                  3.7
                ],
                "z": [
                  3.6,
                  6.7
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-2"
            },
            "storey-2-col-west-3": {
              "bbox": {
                "x": [
                  7.1,
                  7.4
                ],
                "y": [
                  6.8,
                  7.1000000000000005
                ],
                "z": [
                  3.6,
                  6.7
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-2"
            },
            "storey-2-col-west-4": {
              "bbox": {
                "x": [
                  7.1,
                  7.4
                ],
                "y": [
                  10.3,
                  10.600000000000001
                ],
                "z": [
                  3.6,
                  6.7
                ]
              },
              "ifc_class": "IfcColumn",
              "storey_id": "storey-2"
            },
            "storey-2-rail-east-1": {
              "bbox": {
                "x": [
                  16.6,
                  16.64
                ],
                "y": [
                  0.3,
                  3.4
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-east-2": {
              "bbox": {
                "x": [
                  16.6,
                  16.64
                ],
                "y": [
                  3.7,
                  6.800000000000001
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-east-3": {
              "bbox": {
                "x": [
                  16.6,
                  16.64
                ],
                "y": [
                  7.1000000000000005,
                  8.200000000000001
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-front-east": {
              "bbox": {
                "x": [
                  16.9,
                  19.0
                ],
                "y": [
                  0.0,
                  0.04
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-front-west": {
              "bbox": {
                "x": [
                  5.0,
                  7.1
                ],
                "y": [
                  0.0,
                  0.04
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-landing-west": {
              "bbox": {
                "x": [
                  14.8,
                  14.84
                ],
                "y": [
                  8.2,
                  10.6
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-north-1": {
              "bbox": {
                "x": [
                  7.4,
                  10.350000000000001
                ],
                "y": [
                  10.600000000000001,
                  10.64
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-north-2": {
              "bbox": {
                "x": [
                  10.65,
                  13.350000000000001
                ],
                "y": [
                  10.600000000000001,
                  10.64
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-north-3": {
              "bbox": {
                "x": [
                  13.65,
                  14.8
                ],
                "y": [
                  10.600000000000001,
                  10.64
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-west-1": {
              "bbox": {
                "x": [
                  7.36,
                  7.4
                ],
                "y": [
                  0.3,
                  3.4
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-west-2": {
              "bbox": {
                "x": [
                  7.36,
                  7.4
                ],
                "y": [
                  3.7,
                  6.800000000000001
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            },
            "storey-2-rail-west-3": {
              "bbox": {
                "x": [
                  7.36,
                  7.4
                ],
                "y": [
                  7.1000000000000005,
                  10.3
                ],
                "z": [
                  3.6,
                  4.7
                ]
              },
              "ifc_class": "IfcRailing",
              "storey_id": "storey-2"
            }
          },
          "roof": {
            "slab-roof": {
              "bbox": {
                "x": [
                  0.0,
                  24.0
                ],
                "y": [
                  0.0,
                  18.0
                ],
                "z": [
                  7.0,
                  7.2
                ]
              },
              "ifc_class": "IfcSlab"
            }
          },
          "slabs": {
            "slab-ground-1": {
              "bbox": {
                "x": [
                  0.0,
                  24.0
                ],
                "y": [
                  0.0,
                  18.0
                ],
                "z": [
                  -0.2,
                  0.0
                ]
              },
              "ifc_class": "IfcSlab"
            },
            "slab-landing-2": {
              "bbox": {
                "x": [
                  14.8,
                  16.6
                ],
                "y": [
                  8.200000000000001,
                  10.6
                ],
                "z": [
                  3.4,
                  3.6
                ]
              },
              "ifc_class": "IfcSlab"
            },
            "slab-u-floor-2": {
              "bbox": {
                "x": [
                  0.0,
                  24.0
                ],
                "y": [
                  0.0,
                  18.0
                ],
                "z": [
                  3.4,
                  3.6
                ]
              },
              "ifc_class": "IfcSlab"
            }
          },
          "spaces": {
            "space-storey-1-storey-1-space-east-colonnade": {
              "bbox": {
                "x": [
                  16.6,
                  19.0
                ],
                "y": [
                  0.0,
                  10.6
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-1"
            },
            "space-storey-1-storey-1-space-east-reading": {
              "bbox": {
                "x": [
                  19.2,
                  23.8
                ],
                "y": [
                  0.1999999999999993,
                  12.9
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-1"
            },
            "space-storey-1-storey-1-space-north-colonnade": {
              "bbox": {
                "x": [
                  5.0,
                  19.0
                ],
                "y": [
                  10.6,
                  12.9
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-1"
            },
            "space-storey-1-storey-1-space-north-reading": {
              "bbox": {
                "x": [
                  0.1999999999999993,
                  23.8
                ],
                "y": [
                  13.100000000000001,
                  17.8
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-1"
            },
            "space-storey-1-storey-1-space-west-colonnade": {
              "bbox": {
                "x": [
                  5.0,
                  7.4
                ],
                "y": [
                  0.0,
                  10.6
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-1"
            },
            "space-storey-1-storey-1-space-west-reading": {
              "bbox": {
                "x": [
                  0.19999999999999973,
                  4.800000000000001
                ],
                "y": [
                  0.1999999999999993,
                  12.9
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-1"
            },
            "space-storey-2-storey-2-space-east-colonnade": {
              "bbox": {
                "x": [
                  16.6,
                  19.0
                ],
                "y": [
                  0.0,
                  10.6
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-2"
            },
            "space-storey-2-storey-2-space-east-reading": {
              "bbox": {
                "x": [
                  19.2,
                  23.8
                ],
                "y": [
                  0.1999999999999993,
                  12.9
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-2"
            },
            "space-storey-2-storey-2-space-north-colonnade": {
              "bbox": {
                "x": [
                  5.0,
                  19.0
                ],
                "y": [
                  10.6,
                  12.9
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-2"
            },
            "space-storey-2-storey-2-space-north-reading": {
              "bbox": {
                "x": [
                  0.1999999999999993,
                  23.8
                ],
                "y": [
                  13.100000000000001,
                  17.8
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-2"
            },
            "space-storey-2-storey-2-space-west-colonnade": {
              "bbox": {
                "x": [
                  5.0,
                  7.4
                ],
                "y": [
                  0.0,
                  10.6
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-2"
            },
            "space-storey-2-storey-2-space-west-reading": {
              "bbox": {
                "x": [
                  0.19999999999999973,
                  4.800000000000001
                ],
                "y": [
                  0.1999999999999993,
                  12.9
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcSpace",
              "storey_id": "storey-2"
            }
          },
          "stairs": {
            "stair-1": {
              "bbox": {
                "x": [
                  14.8,
                  16.6
                ],
                "y": [
                  2.2,
                  8.2
                ],
                "z": [
                  0.0,
                  3.6
                ]
              },
              "flight_ids": [
                "stair-flight-1"
              ],
              "has_stepped_profile": true,
              "wall_intersections": []
            }
          },
          "wall_set_convention": "primary",
          "walls": {
            "wall-storey-1-storey-1-wall-east-court": {
              "axis": "y",
              "bbox": {
                "x": [
                  19.0,
                  19.200000000000003
                ],
                "y": [
                  0.0,
                  12.9
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-east-exterior": {
              "axis": "y",
              "bbox": {
                "x": [
                  23.8,
                  24.000000000000004
                ],
                "y": [
                  0.0,
                  18.0
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-east-front": {
              "axis": "x",
              "bbox": {
                "x": [
                  19.2,
                  23.8
                ],
                "y": [
                  0.0,
                  0.2
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-north-exterior": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.1999999999999993,
                  23.8
                ],
                "y": [
                  17.8,
                  18.000000000000004
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-north-room-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.1999999999999993,
                  23.8
                ],
                "y": [
                  12.9,
                  13.1
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-west-court": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.800000000000001,
                  5.0
                ],
                "y": [
                  0.0,
                  12.9
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-west-exterior": {
              "axis": "y",
              "bbox": {
                "x": [
                  0.0,
                  0.2
                ],
                "y": [
                  0.0,
                  18.0
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-west-front": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.19999999999999973,
                  4.800000000000001
                ],
                "y": [
                  0.0,
                  0.2
                ],
                "z": [
                  0.0,
                  3.4
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-east-court": {
              "axis": "y",
              "bbox": {
                "x": [
                  19.0,
                  19.200000000000003
                ],
                "y": [
                  0.0,
                  12.9
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-east-exterior": {
              "axis": "y",
              "bbox": {
                "x": [
                  23.8,
                  24.000000000000004
                ],
                "y": [
                  0.0,
                  18.0
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-east-front": {
              "axis": "x",
              "bbox": {
                "x": [
                  19.2,
                  23.8
                ],
                "y": [
                  0.0,
                  0.2
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-north-exterior": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.1999999999999993,
                  23.8
                ],
                "y": [
                  17.8,
                  18.000000000000004
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-north-room-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.1999999999999993,
                  23.8
                ],
                "y": [
                  12.9,
                  13.1
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-west-court": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.800000000000001,
                  5.0
                ],
                "y": [
                  0.0,
                  12.9
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-west-exterior": {
              "axis": "y",
              "bbox": {
                "x": [
                  0.0,
                  0.2
                ],
                "y": [
                  0.0,
                  18.0
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-west-front": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.19999999999999973,
                  4.800000000000001
                ],
                "y": [
                  0.0,
                  0.2
                ],
                "z": [
                  3.6,
                  7.0
                ]
              },
              "ifc_class": "IfcWall"
            }
          }
        },
        "success": true
      },
      "geometry_success": true,
      "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-open-court-20260912\\rerun-03\\live-run\\runs\\ce8116ce095acdcf\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-open-court-20260912\\rerun-03\\live-run\\runs\\ce8116ce095acdcf\\output.ifc",
        "success": true
      },
      "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-open-court-20260912\\rerun-03\\live-run\\runs\\ce8116ce095acdcf",
      "semantic_geometry_expectation": {
        "case_id": "ce8116ce095acdcf",
        "complete": true,
        "doors": {},
        "floor_openings": {},
        "products": {
          "storey-1-beam-east": {
            "bbox": {
              "x": [
                16.6,
                16.9
              ],
              "y": [
                0.0,
                10.9
              ],
              "z": [
                3.1,
                3.4
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcBeam",
            "source_fact_refs": [
              "/products/21/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-beam-north": {
            "bbox": {
              "x": [
                7.4,
                16.6
              ],
              "y": [
                10.6,
                10.9
              ],
              "z": [
                3.1,
                3.4
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcBeam",
            "source_fact_refs": [
              "/products/22/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-beam-west": {
            "bbox": {
              "x": [
                7.1,
                7.4
              ],
              "y": [
                0.0,
                10.9
              ],
              "z": [
                3.1,
                3.4
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcBeam",
            "source_fact_refs": [
              "/products/20/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-col-east-1": {
            "bbox": {
              "x": [
                16.6,
                16.9
              ],
              "y": [
                0.0,
                0.3
              ],
              "z": [
                0.0,
                3.1
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/4/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-col-east-2": {
            "bbox": {
              "x": [
                16.6,
                16.9
              ],
              "y": [
                3.4,
                3.7
              ],
              "z": [
                0.0,
                3.1
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/5/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-col-east-3": {
            "bbox": {
              "x": [
                16.6,
                16.9
              ],
              "y": [
                6.8,
                7.1
              ],
              "z": [
                0.0,
                3.1
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/6/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-col-east-4": {
            "bbox": {
              "x": [
                16.6,
                16.9
              ],
              "y": [
                10.3,
                10.6
              ],
              "z": [
                0.0,
                3.1
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/7/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-col-north-1": {
            "bbox": {
              "x": [
                10.35,
                10.65
              ],
              "y": [
                10.6,
                10.9
              ],
              "z": [
                0.0,
                3.1
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/8/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-col-north-2": {
            "bbox": {
              "x": [
                13.35,
                13.65
              ],
              "y": [
                10.6,
                10.9
              ],
              "z": [
                0.0,
                3.1
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/9/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-col-west-1": {
            "bbox": {
              "x": [
                7.1,
                7.4
              ],
              "y": [
                0.0,
                0.3
              ],
              "z": [
                0.0,
                3.1
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/0/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-col-west-2": {
            "bbox": {
              "x": [
                7.1,
                7.4
              ],
              "y": [
                3.4,
                3.7
              ],
              "z": [
                0.0,
                3.1
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/1/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-col-west-3": {
            "bbox": {
              "x": [
                7.1,
                7.4
              ],
              "y": [
                6.8,
                7.1
              ],
              "z": [
                0.0,
                3.1
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/2/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-col-west-4": {
            "bbox": {
              "x": [
                7.1,
                7.4
              ],
              "y": [
                10.3,
                10.6
              ],
              "z": [
                0.0,
                3.1
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/3/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-rail-stair-left": {
            "alignment_target": "梯段左侧斜护栏；栏高按基线上方竖直高度，立柱与细杆保持竖直，扶手随梯段上升",
            "bbox": {
              "x": [
                14.8,
                14.84
              ],
              "y": [
                2.2,
                8.2
              ],
              "z": [
                0.0,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                14820,
                8200,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                14820,
                2200,
                0
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/38/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-1-rail-stair-right": {
            "alignment_target": "梯段右侧斜护栏；栏高按基线上方竖直高度，立柱与细杆保持竖直，扶手随梯段上升",
            "bbox": {
              "x": [
                16.56,
                16.6
              ],
              "y": [
                2.2,
                8.2
              ],
              "z": [
                0.0,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                16580,
                8200,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                16580,
                2200,
                0
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/39/geometry"
            ],
            "storey_id": "storey-1"
          },
          "storey-2-beam-east": {
            "bbox": {
              "x": [
                16.6,
                16.9
              ],
              "y": [
                0.0,
                10.9
              ],
              "z": [
                6.7,
                7.0
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcBeam",
            "source_fact_refs": [
              "/products/24/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-beam-north": {
            "bbox": {
              "x": [
                7.4,
                16.6
              ],
              "y": [
                10.6,
                10.9
              ],
              "z": [
                6.7,
                7.0
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcBeam",
            "source_fact_refs": [
              "/products/25/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-beam-west": {
            "bbox": {
              "x": [
                7.1,
                7.4
              ],
              "y": [
                0.0,
                10.9
              ],
              "z": [
                6.7,
                7.0
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcBeam",
            "source_fact_refs": [
              "/products/23/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-col-east-1": {
            "bbox": {
              "x": [
                16.6,
                16.9
              ],
              "y": [
                0.0,
                0.3
              ],
              "z": [
                3.6,
                6.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/14/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-col-east-2": {
            "bbox": {
              "x": [
                16.6,
                16.9
              ],
              "y": [
                3.4,
                3.7
              ],
              "z": [
                3.6,
                6.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/15/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-col-east-3": {
            "bbox": {
              "x": [
                16.6,
                16.9
              ],
              "y": [
                6.8,
                7.1
              ],
              "z": [
                3.6,
                6.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/16/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-col-east-4": {
            "bbox": {
              "x": [
                16.6,
                16.9
              ],
              "y": [
                10.3,
                10.6
              ],
              "z": [
                3.6,
                6.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/17/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-col-north-1": {
            "bbox": {
              "x": [
                10.35,
                10.65
              ],
              "y": [
                10.6,
                10.9
              ],
              "z": [
                3.6,
                6.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/18/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-col-north-2": {
            "bbox": {
              "x": [
                13.35,
                13.65
              ],
              "y": [
                10.6,
                10.9
              ],
              "z": [
                3.6,
                6.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/19/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-col-west-1": {
            "bbox": {
              "x": [
                7.1,
                7.4
              ],
              "y": [
                0.0,
                0.3
              ],
              "z": [
                3.6,
                6.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/10/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-col-west-2": {
            "bbox": {
              "x": [
                7.1,
                7.4
              ],
              "y": [
                3.4,
                3.7
              ],
              "z": [
                3.6,
                6.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/11/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-col-west-3": {
            "bbox": {
              "x": [
                7.1,
                7.4
              ],
              "y": [
                6.8,
                7.1
              ],
              "z": [
                3.6,
                6.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/12/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-col-west-4": {
            "bbox": {
              "x": [
                7.1,
                7.4
              ],
              "y": [
                10.3,
                10.6
              ],
              "z": [
                3.6,
                6.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "world_axis_aligned_box",
            "ifc_class": "IfcColumn",
            "source_fact_refs": [
              "/products/13/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-east-1": {
            "alignment_target": "东列柱间，止于柱面",
            "bbox": {
              "x": [
                16.6,
                16.64
              ],
              "y": [
                0.3,
                3.4
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                16620,
                3400,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                16620,
                300,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/29/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-east-2": {
            "alignment_target": "东列柱间，止于柱面",
            "bbox": {
              "x": [
                16.6,
                16.64
              ],
              "y": [
                3.7,
                6.8
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                16620,
                6800,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                16620,
                3700,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/30/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-east-3": {
            "alignment_target": "东列柱间，止于柱面；Y=8.2以北与平台连通，不补横挡",
            "bbox": {
              "x": [
                16.6,
                16.64
              ],
              "y": [
                7.1,
                8.2
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                16620,
                8200,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                16620,
                7100,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/31/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-front-east": {
            "alignment_target": "东翼前端，止于柱面",
            "bbox": {
              "x": [
                16.9,
                19.0
              ],
              "y": [
                0.0,
                0.04
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                19000,
                20,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                16900,
                20,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/36/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-front-west": {
            "alignment_target": "西翼前端，止于柱面",
            "bbox": {
              "x": [
                5.0,
                7.1
              ],
              "y": [
                0.0,
                0.04
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                7100,
                20,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                5000,
                20,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/35/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-landing-west": {
            "alignment_target": "楼梯上端平台西侧；平台南侧为楼梯到达口，不横加栏杆",
            "bbox": {
              "x": [
                14.8,
                14.84
              ],
              "y": [
                8.2,
                10.6
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                14820,
                10600,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                14820,
                8200,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/37/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-north-1": {
            "alignment_target": "北廊柱间，止于柱面",
            "bbox": {
              "x": [
                7.4,
                10.35
              ],
              "y": [
                10.6,
                10.64
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                10350,
                10620,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                7400,
                10620,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/32/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-north-2": {
            "alignment_target": "北廊柱间，止于柱面",
            "bbox": {
              "x": [
                10.65,
                13.35
              ],
              "y": [
                10.6,
                10.64
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                13350,
                10620,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                10650,
                10620,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/33/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-north-3": {
            "alignment_target": "北廊柱间，止于平台西边",
            "bbox": {
              "x": [
                13.65,
                14.8
              ],
              "y": [
                10.6,
                10.64
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                14800,
                10620,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                13650,
                10620,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/34/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-west-1": {
            "alignment_target": "西列柱间，止于柱面",
            "bbox": {
              "x": [
                7.36,
                7.4
              ],
              "y": [
                0.3,
                3.4
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                7380,
                3400,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                7380,
                300,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/26/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-west-2": {
            "alignment_target": "西列柱间，止于柱面",
            "bbox": {
              "x": [
                7.36,
                7.4
              ],
              "y": [
                3.7,
                6.8
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                7380,
                6800,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                7380,
                3700,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/27/geometry"
            ],
            "storey_id": "storey-2"
          },
          "storey-2-rail-west-3": {
            "alignment_target": "西列柱间，止于柱面",
            "bbox": {
              "x": [
                7.36,
                7.4
              ],
              "y": [
                7.1,
                10.3
              ],
              "z": [
                3.6,
                4.7
              ]
            },
            "bbox_issue_code": "PRODUCT_BBOX_MISMATCH",
            "geometry_kind": "basic_railing_segment",
            "ifc_class": "IfcRailing",
            "railing_geometry": {
              "end_mm": [
                7380,
                10300,
                3600
              ],
              "height_mm": 1100,
              "kind": "basic_railing_segment",
              "start_mm": [
                7380,
                7100,
                3600
              ],
              "template": {
                "template_id": "metal-picket",
                "template_version": "text2ifc/basic-railing/1.0"
              },
              "thickness_mm": 40
            },
            "source_fact_refs": [
              "/products/28/geometry"
            ],
            "storey_id": "storey-2"
          }
        },
        "roof": {
          "slab-roof": {
            "bbox": {
              "x": [
                0.0,
                24.0
              ],
              "y": [
                0.0,
                18.0
              ],
              "z": [
                7.0,
                7.2
              ]
            },
            "datum": "roof_bottom",
            "source_fact_refs": [
              "/known_facts/roof_slab"
            ]
          }
        },
        "schema_version": "text2ifc/design-geometry-expectation/1.1",
        "slabs": {
          "slab-ground-1": {
            "bbox": {
              "x": [
                0.0,
                24.0
              ],
              "y": [
                0.0,
                18.0
              ],
              "z": [
                -0.2,
                0.0
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [],
            "source_fact_refs": [
              "/known_facts/floor_slabs/0"
            ]
          },
          "slab-landing-2": {
            "bbox": {
              "x": [
                14.8,
                16.6
              ],
              "y": [
                8.2,
                10.6
              ],
              "z": [
                3.4,
                3.6
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [
              "wall-storey-1-storey-1-wall-east-court",
              "wall-storey-1-storey-1-wall-east-exterior",
              "wall-storey-1-storey-1-wall-east-front",
              "wall-storey-1-storey-1-wall-north-exterior",
              "wall-storey-1-storey-1-wall-north-room-south",
              "wall-storey-1-storey-1-wall-west-court",
              "wall-storey-1-storey-1-wall-west-exterior",
              "wall-storey-1-storey-1-wall-west-front"
            ],
            "source_fact_refs": [
              "/known_facts/floor_slabs/2"
            ]
          },
          "slab-u-floor-2": {
            "bbox": {
              "x": [
                0.0,
                24.0
              ],
              "y": [
                0.0,
                18.0
              ],
              "z": [
                3.4,
                3.6
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [
              "wall-storey-1-storey-1-wall-east-court",
              "wall-storey-1-storey-1-wall-east-exterior",
              "wall-storey-1-storey-1-wall-east-front",
              "wall-storey-1-storey-1-wall-north-exterior",
              "wall-storey-1-storey-1-wall-north-room-south",
              "wall-storey-1-storey-1-wall-west-court",
              "wall-storey-1-storey-1-wall-west-exterior",
              "wall-storey-1-storey-1-wall-west-front"
            ],
            "source_fact_refs": [
              "/known_facts/floor_slabs/1"
            ]
          }
        },
        "source": "design_brief_expected_facts",
        "spaces": {
          "space-storey-1-storey-1-space-east-colonnade": {
            "bbox": {
              "x": [
                16.6,
                19.0
              ],
              "y": [
                0.0,
                10.6
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/4"
            ],
            "storey_id": "storey-1"
          },
          "space-storey-1-storey-1-space-east-reading": {
            "bbox": {
              "x": [
                19.2,
                23.8
              ],
              "y": [
                0.2,
                12.9
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/1"
            ],
            "storey_id": "storey-1"
          },
          "space-storey-1-storey-1-space-north-colonnade": {
            "bbox": {
              "x": [
                5.0,
                19.0
              ],
              "y": [
                10.6,
                12.9
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/5"
            ],
            "storey_id": "storey-1"
          },
          "space-storey-1-storey-1-space-north-reading": {
            "bbox": {
              "x": [
                0.2,
                23.8
              ],
              "y": [
                13.1,
                17.8
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/2"
            ],
            "storey_id": "storey-1"
          },
          "space-storey-1-storey-1-space-west-colonnade": {
            "bbox": {
              "x": [
                5.0,
                7.4
              ],
              "y": [
                0.0,
                10.6
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/3"
            ],
            "storey_id": "storey-1"
          },
          "space-storey-1-storey-1-space-west-reading": {
            "bbox": {
              "x": [
                0.2,
                4.8
              ],
              "y": [
                0.2,
                12.9
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/0"
            ],
            "storey_id": "storey-1"
          },
          "space-storey-2-storey-2-space-east-colonnade": {
            "bbox": {
              "x": [
                16.6,
                19.0
              ],
              "y": [
                0.0,
                10.6
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/1/spaces/4"
            ],
            "storey_id": "storey-2"
          },
          "space-storey-2-storey-2-space-east-reading": {
            "bbox": {
              "x": [
                19.2,
                23.8
              ],
              "y": [
                0.2,
                12.9
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/1/spaces/1"
            ],
            "storey_id": "storey-2"
          },
          "space-storey-2-storey-2-space-north-colonnade": {
            "bbox": {
              "x": [
                5.0,
                19.0
              ],
              "y": [
                10.6,
                12.9
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/1/spaces/5"
            ],
            "storey_id": "storey-2"
          },
          "space-storey-2-storey-2-space-north-reading": {
            "bbox": {
              "x": [
                0.2,
                23.8
              ],
              "y": [
                13.1,
                17.8
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/1/spaces/2"
            ],
            "storey_id": "storey-2"
          },
          "space-storey-2-storey-2-space-west-colonnade": {
            "bbox": {
              "x": [
                5.0,
                7.4
              ],
              "y": [
                0.0,
                10.6
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/1/spaces/3"
            ],
            "storey_id": "storey-2"
          },
          "space-storey-2-storey-2-space-west-reading": {
            "bbox": {
              "x": [
                0.2,
                4.8
              ],
              "y": [
                0.2,
                12.9
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/1/spaces/0"
            ],
            "storey_id": "storey-2"
          }
        },
        "stairs": {
          "stair-1": {
            "bbox": {
              "x": [
                14.8,
                16.6
              ],
              "y": [
                2.2,
                8.2
              ],
              "z": [
                0.0,
                3.6
              ]
            },
            "bbox_issue_code": "STAIR_BBOX_MISMATCH",
            "flight_ids": [
              "stair-flight-1"
            ],
            "require_steps": true,
            "source_fact_refs": [
              "/known_facts/stairs/0"
            ]
          }
        },
        "tolerance": 0.05,
        "units": "METRE",
        "unresolved": [],
        "walls": {
          "wall-storey-1-storey-1-wall-east-court": {
            "axis": "y",
            "bbox": {
              "x": [
                19.0,
                19.2
              ],
              "y": [
                0.0,
                12.9
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-east-court",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/1"
            ]
          },
          "wall-storey-1-storey-1-wall-east-exterior": {
            "axis": "y",
            "bbox": {
              "x": [
                23.8,
                24.0
              ],
              "y": [
                0.0,
                18.0
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-east-exterior",
            "source_fact_refs": [
              "/known_facts/walls/1"
            ]
          },
          "wall-storey-1-storey-1-wall-east-front": {
            "axis": "x",
            "bbox": {
              "x": [
                19.2,
                23.8
              ],
              "y": [
                0.0,
                0.2
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-east-front",
            "source_fact_refs": [
              "/known_facts/walls/4"
            ]
          },
          "wall-storey-1-storey-1-wall-north-exterior": {
            "axis": "x",
            "bbox": {
              "x": [
                0.2,
                23.8
              ],
              "y": [
                17.8,
                18.0
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-north-exterior",
            "source_fact_refs": [
              "/known_facts/walls/2"
            ]
          },
          "wall-storey-1-storey-1-wall-north-room-south": {
            "axis": "x",
            "bbox": {
              "x": [
                0.2,
                23.8
              ],
              "y": [
                12.9,
                13.1
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-north-room-south",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/2"
            ]
          },
          "wall-storey-1-storey-1-wall-west-court": {
            "axis": "y",
            "bbox": {
              "x": [
                4.8,
                5.0
              ],
              "y": [
                0.0,
                12.9
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-west-court",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/0"
            ]
          },
          "wall-storey-1-storey-1-wall-west-exterior": {
            "axis": "y",
            "bbox": {
              "x": [
                0.0,
                0.2
              ],
              "y": [
                0.0,
                18.0
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-west-exterior",
            "source_fact_refs": [
              "/known_facts/walls/0"
            ]
          },
          "wall-storey-1-storey-1-wall-west-front": {
            "axis": "x",
            "bbox": {
              "x": [
                0.2,
                4.8
              ],
              "y": [
                0.0,
                0.2
              ],
              "z": [
                0.0,
                3.4
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-west-front",
            "source_fact_refs": [
              "/known_facts/walls/3"
            ]
          },
          "wall-storey-2-storey-2-wall-east-court": {
            "axis": "y",
            "bbox": {
              "x": [
                19.0,
                19.2
              ],
              "y": [
                0.0,
                12.9
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-east-court",
            "source_fact_refs": [
              "/known_facts/storeys/1/walls/interior/1"
            ]
          },
          "wall-storey-2-storey-2-wall-east-exterior": {
            "axis": "y",
            "bbox": {
              "x": [
                23.8,
                24.0
              ],
              "y": [
                0.0,
                18.0
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-east-exterior",
            "source_fact_refs": [
              "/known_facts/walls/9"
            ]
          },
          "wall-storey-2-storey-2-wall-east-front": {
            "axis": "x",
            "bbox": {
              "x": [
                19.2,
                23.8
              ],
              "y": [
                0.0,
                0.2
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-east-front",
            "source_fact_refs": [
              "/known_facts/walls/12"
            ]
          },
          "wall-storey-2-storey-2-wall-north-exterior": {
            "axis": "x",
            "bbox": {
              "x": [
                0.2,
                23.8
              ],
              "y": [
                17.8,
                18.0
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-north-exterior",
            "source_fact_refs": [
              "/known_facts/walls/10"
            ]
          },
          "wall-storey-2-storey-2-wall-north-room-south": {
            "axis": "x",
            "bbox": {
              "x": [
                0.2,
                23.8
              ],
              "y": [
                12.9,
                13.1
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-north-room-south",
            "source_fact_refs": [
              "/known_facts/storeys/1/walls/interior/2"
            ]
          },
          "wall-storey-2-storey-2-wall-west-court": {
            "axis": "y",
            "bbox": {
              "x": [
                4.8,
                5.0
              ],
              "y": [
                0.0,
                12.9
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-west-court",
            "source_fact_refs": [
              "/known_facts/storeys/1/walls/interior/0"
            ]
          },
          "wall-storey-2-storey-2-wall-west-exterior": {
            "axis": "y",
            "bbox": {
              "x": [
                0.0,
                0.2
              ],
              "y": [
                0.0,
                18.0
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-west-exterior",
            "source_fact_refs": [
              "/known_facts/walls/8"
            ]
          },
          "wall-storey-2-storey-2-wall-west-front": {
            "axis": "x",
            "bbox": {
              "x": [
                0.2,
                4.8
              ],
              "y": [
                0.0,
                0.2
              ],
              "z": [
                3.6,
                7.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-west-front",
            "source_fact_refs": [
              "/known_facts/walls/11"
            ]
          }
        },
        "windows": {}
      },
      "semantic_verification": {
        "basis": "request expectations independently compared with reopened IFC before atomic publication",
        "expectations": [
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/0",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/0",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/1",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/1",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-north-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/2",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-north-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/2",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-front",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/3",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-front",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/3",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-front",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/4",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-front",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/4",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-court",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/5",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-court",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/5",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-court",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/6",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-court",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/6",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-north-room-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/7",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-north-room-south",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/7",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/8",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/8",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/9",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/9",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-north-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/10",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-north-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/10",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-front",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/11",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-front",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/11",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-front",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/12",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-front",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/12",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-court",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/13",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-court",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/13",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-court",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/14",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-court",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/14",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-north-room-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/15",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-north-room-south",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/15",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "slab-ground-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-ground-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "slab-u-floor-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/17",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-u-floor-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/17",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "slab-landing-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/18",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-landing-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/18",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "slab-roof",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/19",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-roof",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/19",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "stair-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/20",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "stair-flight-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/21",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "stair-flight-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/21",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "storey-1-beam-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/22",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-beam-west",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/22",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-beam-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/23",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-beam-east",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/23",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-beam-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/24",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-beam-north",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/24",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-beam-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/25",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-beam-west",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/25",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-beam-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/26",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-beam-east",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/26",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-beam-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/27",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-beam-north",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/27",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-west-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/28",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-west-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/28",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-west-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/29",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-west-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/29",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-west-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/30",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-west-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/30",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-west-4",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/31",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-west-4",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/31",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-east-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/32",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-east-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/32",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-east-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/33",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-east-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/33",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-east-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/34",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-east-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/34",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-east-4",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/35",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-east-4",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/35",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-north-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/36",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-north-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/36",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-north-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/37",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-north-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/37",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-west-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/38",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-west-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/38",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-west-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/39",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-west-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/39",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-west-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/40",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-west-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/40",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-west-4",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/41",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-west-4",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/41",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-east-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/42",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-east-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/42",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-east-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/43",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-east-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/43",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-east-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/44",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-east-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/44",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-east-4",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/45",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-east-4",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/45",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-north-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/46",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-north-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/46",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-north-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/47",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-north-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/47",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-rail-west-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/48",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-west-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/48",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-west-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/48",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-west-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/49",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-west-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/49",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-west-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/49",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-west-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/50",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-west-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/50",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-west-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/50",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-east-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/51",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-east-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/51",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-east-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/51",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-east-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/52",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-east-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/52",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-east-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/52",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-east-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/53",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-east-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/53",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-east-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/53",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-north-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/54",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-north-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/54",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-north-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/54",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-north-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/55",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-north-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/55",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-north-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/55",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-north-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/56",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-north-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/56",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-north-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/56",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-front-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/57",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-front-west",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/57",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-front-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/57",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-front-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/58",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-front-east",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/58",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-front-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/58",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-landing-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/59",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-landing-west",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/59",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-landing-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/59",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-1-rail-stair-left",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/60",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-1-rail-stair-left",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/60",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-1-rail-stair-left",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/60",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-1-rail-stair-right",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/61",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-1-rail-stair-right",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/61",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-1-rail-stair-right",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/61",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-west-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/62",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-west-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/62",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-west-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/62",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-east-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/63",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-east-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/63",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-east-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/63",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-north-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/64",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-north-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/64",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-north-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/64",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-west-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/65",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-west-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/65",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-west-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/65",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-east-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/66",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-east-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/66",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-east-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/66",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-north-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/67",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-north-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/67",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-north-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/67",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/68",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/68",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/69",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/69",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/70",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/70",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/71",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/71",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/72",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/72",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/73",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/73",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/74",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/74",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/75",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/75",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/76",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/76",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/77",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/77",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/78",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/78",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/79",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/79",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/80",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/80",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/81",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/81",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/82",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/82",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/83",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/83",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/84",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/84",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/85",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/85",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-room-south-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/86",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-room-south-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/86",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-room-south-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/87",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-room-south-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/87",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-front",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/88",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-front",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/88",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-front",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/89",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-front",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/89",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/90",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/90",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/91",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/91",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/92",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/92",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/93",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/93",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/94",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/94",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/95",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/95",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/96",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/96",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/97",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/97",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/98",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/98",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/99",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/99",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/100",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/100",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/101",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/101",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/102",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/102",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/103",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/103",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/104",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/104",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/105",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/105",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/106",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/106",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/107",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/107",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-room-south-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/108",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-room-south-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/108",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-room-south-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/109",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-room-south-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/109",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-front",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/110",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-front",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/110",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-front",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/111",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-front",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/111",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/0",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/0",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/1",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/1",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-north-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/2",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-north-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/2",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-front",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/3",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-front",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/3",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-front",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/4",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-front",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/4",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-court",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/5",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west-court",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/5",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-court",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/6",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east-court",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/6",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-north-room-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/7",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-north-room-south",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/7",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/8",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/8",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/9",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/9",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-north-exterior",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/10",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-north-exterior",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/10",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-front",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/11",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-front",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/11",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-front",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/12",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-front",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/12",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-court",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/13",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west-court",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/13",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-court",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/14",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east-court",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/14",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-north-room-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/15",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-north-room-south",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/15",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "slab-ground-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-ground-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "slab-u-floor-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/17",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-u-floor-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/17",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "slab-landing-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/18",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-landing-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/18",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "slab-roof",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/19",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-roof",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/19",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "stair-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/20",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "stair-flight-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/21",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "stair-flight-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/21",
            "value": {
              "color": [
                0.902,
                0.878,
                0.827
              ]
            }
          },
          {
            "entity_id": "storey-1-beam-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/22",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-beam-west",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/22",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-beam-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/23",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-beam-east",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/23",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-beam-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/24",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-beam-north",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/24",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-beam-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/25",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-beam-west",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/25",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-beam-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/26",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-beam-east",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/26",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-beam-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/27",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-beam-north",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/27",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-west-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/28",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-west-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/28",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-west-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/29",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-west-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/29",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-west-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/30",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-west-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/30",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-west-4",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/31",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-west-4",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/31",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-east-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/32",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-east-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/32",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-east-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/33",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-east-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/33",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-east-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/34",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-east-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/34",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-east-4",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/35",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-east-4",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/35",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-north-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/36",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-north-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/36",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-1-col-north-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/37",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-1-col-north-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/37",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-west-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/38",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-west-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/38",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-west-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/39",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-west-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/39",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-west-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/40",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-west-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/40",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-west-4",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/41",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-west-4",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/41",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-east-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/42",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-east-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/42",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-east-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/43",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-east-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/43",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-east-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/44",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-east-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/44",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-east-4",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/45",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-east-4",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/45",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-north-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/46",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-north-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/46",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-col-north-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/47",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "storey-2-col-north-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/47",
            "value": {
              "color": [
                0.824,
                0.78,
                0.702
              ]
            }
          },
          {
            "entity_id": "storey-2-rail-west-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/48",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-west-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/48",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-west-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/48",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-west-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/49",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-west-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/49",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-west-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/49",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-west-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/50",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-west-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/50",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-west-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/50",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-east-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/51",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-east-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/51",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-east-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/51",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-east-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/52",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-east-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/52",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-east-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/52",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-east-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/53",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-east-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/53",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-east-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/53",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-north-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/54",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-north-1",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/54",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-north-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/54",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-north-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/55",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-north-2",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/55",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-north-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/55",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-north-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/56",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-north-3",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/56",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-north-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/56",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-front-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/57",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-front-west",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/57",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-front-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/57",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-front-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/58",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-front-east",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/58",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-front-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/58",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-2-rail-landing-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/59",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-2-rail-landing-west",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/59",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-2-rail-landing-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/59",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-1-rail-stair-left",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/60",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-1-rail-stair-left",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/60",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-1-rail-stair-left",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/60",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "storey-1-rail-stair-right",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/61",
            "value": {
              "kind": "single_material",
              "name": "钢材"
            }
          },
          {
            "entity_id": "storey-1-rail-stair-right",
            "kind": "appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/61",
            "value": {
              "color": [
                0.188,
                0.294,
                0.302
              ],
              "transparency": 0
            }
          },
          {
            "entity_id": "storey-1-rail-stair-right",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/61",
            "value": {
              "template_id": "metal-picket",
              "template_version": "text2ifc/basic-railing/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-west-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/62",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-west-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/62",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-west-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/62",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-east-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/63",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-east-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/63",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-east-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/63",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-north-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/64",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-north-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/64",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-north-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/64",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-west-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/65",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-west-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/65",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-west-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/65",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-east-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/66",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-east-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/66",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-east-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/66",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-north-reading",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/67",
            "value": {
              "kind": "single_material",
              "name": "木材"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-north-reading",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/67",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "panel": {
                "color": [
                  0.651,
                  0.435,
                  0.263
                ]
              }
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-north-reading",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/67",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/68",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/68",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/69",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/69",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/70",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/70",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/71",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/71",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/72",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/72",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/73",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/73",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/74",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/74",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/75",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/75",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/76",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/76",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/77",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/77",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/78",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/78",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/79",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/79",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/80",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/80",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/81",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/81",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/82",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-court-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/82",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/83",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/83",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/84",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/84",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/85",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-court-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/85",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-room-south-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/86",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-room-south-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/86",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-room-south-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/87",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-north-room-south-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/87",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-front",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/88",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-west-front",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/88",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-front",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/89",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-win-east-front",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/89",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/90",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/90",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/91",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/91",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/92",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/92",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/93",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/93",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/94",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/94",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/95",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/95",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/96",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/96",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/97",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/97",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/98",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/98",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/99",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/99",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/100",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/100",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-4",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/101",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-ext-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/101",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/102",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/102",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/103",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/103",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/104",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-court-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/104",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/105",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/105",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/106",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/106",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-3",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/107",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-court-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/107",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-room-south-1",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/108",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-room-south-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/108",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-room-south-2",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/109",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-north-room-south-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/109",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-front",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/110",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-west-front",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/110",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-front",
            "kind": "part_appearance",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/111",
            "value": {
              "frame": {
                "color": [
                  0.188,
                  0.294,
                  0.302
                ]
              },
              "glazing": {
                "transparency": 0.65
              }
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-win-east-front",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/111",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          }
        ],
        "issues": [],
        "schema_version": "text2ifc/request-semantic-verification/1.0",
        "valid": true
      },
      "stage": "candidate-gates",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-12T12:15:29+00:00",
    "event_index": 4,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "ce8116ce095acdcf",
      "evidence_class": "live",
      "output_dir": "dataset/processed/ifc-presentation-validation/courtyard-library-open-court-20260912/rerun-03/live-run/runs/ce8116ce095acdcf",
      "report_path": "dataset/processed/ifc-presentation-validation/courtyard-library-open-court-20260912/rerun-03/live-run/runs/ce8116ce095acdcf/report.md",
      "response_id": "59015aad-3bb9-426c-8a05-86e625968c1d",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-12T12:17:33+00:00",
    "event_index": 5,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "ce8116ce095acdcf",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-open-court-20260912\\rerun-03\\live-run\\runs\\ce8116ce095acdcf\\output.ifc",
      "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-open-court-20260912\\rerun-03\\live-run\\runs\\ce8116ce095acdcf",
      "report_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-open-court-20260912\\rerun-03\\live-run\\runs\\ce8116ce095acdcf\\report.md",
      "secret_finding_count": 0,
      "stage": "final-acceptance",
      "valid": true
    }
  }
]
```

### Artifact Index

```json
[
  {
    "created_at": "2026-09-12T12:09:26+00:00",
    "kind": "expected_facts",
    "path": "runs/ce8116ce095acdcf/expected-facts.json"
  },
  {
    "created_at": "2026-09-12T12:12:30+00:00",
    "kind": "candidate",
    "path": "runs/ce8116ce095acdcf/candidate.json"
  },
  {
    "created_at": "2026-09-12T12:12:30+00:00",
    "kind": "semantic_capabilities",
    "path": "runs/ce8116ce095acdcf/semantic-capabilities.json"
  },
  {
    "created_at": "2026-09-12T12:12:31+00:00",
    "kind": "semantic_coverage",
    "path": "runs/ce8116ce095acdcf/semantic-coverage.json"
  },
  {
    "created_at": "2026-09-12T12:17:33+00:00",
    "kind": "issues",
    "path": "runs/ce8116ce095acdcf/issues.json"
  },
  {
    "created_at": "2026-09-12T12:17:33+00:00",
    "kind": "route_decision",
    "path": "runs/ce8116ce095acdcf/route-decision.json"
  },
  {
    "created_at": "2026-09-12T12:17:33+00:00",
    "kind": "feedback_rounds",
    "path": "runs/ce8116ce095acdcf/feedback-rounds.json"
  },
  {
    "created_at": "2026-09-12T12:17:33+00:00",
    "kind": "ifc",
    "path": "runs/ce8116ce095acdcf/output.ifc"
  },
  {
    "created_at": "2026-09-12T12:17:33+00:00",
    "kind": "report",
    "path": "runs/ce8116ce095acdcf/report.md"
  },
  {
    "created_at": "2026-09-12T12:17:33+00:00",
    "kind": "session_export",
    "path": "runs/ce8116ce095acdcf/session-export.json"
  }
]
```


## 合理性问题与用户决定

以下为 Audit 的有限审查记录，技术／请求符合性通过不代表合理性或规范通过。
用户保留的已知问题仍然存在；要求修改也不等于已经独立验证修改成功。
[用户决定与参考证据](design-review-context.json) · [Audit 校验](audit/validation.json)

```json
{
  "concerns": [
    {
      "description": "对照已确认修订核验：当前候选的 slab-u-floor-2 与 slab-roof 均采用前侧敞开 U 形多边形（缺口 X=7400~16600、Y=0~10600 向南连通），南侧中段仅有 X=200~4800 与 X=19200~23800 的两段前墙，天井范围内无楼板、屋盖、玻璃顶或通高围墙，未见以矩形整板替代或隐藏构件伪装开敞。该结论仅为对 IFC 构件清单与几何门限的模型检查，未做渲染/视觉或独立工程核验，故标记为未验证而非已解决；若下游需要视觉确认，应另行核查。",
      "evidence_paths": [
        "design-review-context.json",
        "reference-design-review.json",
        "generator/candidate.json",
        "geometry-feedback.json"
      ],
      "id": "open-front-courtyard",
      "status": "not_verified"
    },
    {
      "description": "对照已确认修订核验：corridor 一侧设有外露 stair-1，含从属 stair-flight-1（20 级×180mm、进深 20×300mm、宽 1800mm，Y=2200~8200），位于 U 形楼板外露空区内，geometry 指标 wall_intersections 为空且未见楼梯间墙或额外封闭洞口；上端 slab-landing-2（Y=8200~10600）与 U 形板无正面积重叠，北接北回廊、东接东回廊，Y=0~2200 为无门无墙的到达区。模型层面未发现该修订被违反；但平台与梯段的实际连接构造与防护未做工程核验，故状态为未验证。",
      "evidence_paths": [
        "design-review-context.json",
        "reference-design-review.json",
        "generator/candidate.json",
        "semantic-geometry-expectation.json"
      ],
      "id": "exposed-stair-access",
      "status": "not_verified"
    },
    {
      "description": "对照已确认修订核验：14 段 IfcRailing 均使用 metal-picket 模板、单一钢材材料、整件颜色 #304B4D 且 transparency=0，栏高 1100mm、深 40mm，水平段底面位于 3.6m，两段梯段斜护栏以 rise=3600 表达坡度而栏高按基线上方竖直高度取 1100mm；未使用玻璃板或不透明整板替代，柱间段止于柱面。模型层面未发现该修订被违反；但模板默认杆件尺寸与间距沿用其已校验版本，其可施工性、锚固与整体防护合规性未做独立工程核验，故状态为未验证。",
      "evidence_paths": [
        "design-review-context.json",
        "reference-design-review.json",
        "generator/candidate.json",
        "semantic-capabilities.json"
      ],
      "id": "visible-picket-railing",
      "status": "not_verified"
    }
  ],
  "limitations": [
    "未进行完整建筑规范审查。",
    "未做结构计算、承载力或抗震核验；梁柱截面与材料强度等级均由用户给定且未经复核。",
    "未验证楼梯上端平台与梯段的连接构造、平台南侧到达口防护、防水排水与栏杆锚固节点。",
    "未验证窗玻璃透明度 0.65 与各外观颜色以外的热工、防火、声学等性能；外观不构成性能声明。",
    "评审仅基于 IFC/BIM JSON 构件清单、确定性 gate 与几何门限，未做现场踏勘或独立工程复核，也未对渲染外观做像素级比对。"
  ],
  "scope": "limited_review_not_code_compliance"
}
```
