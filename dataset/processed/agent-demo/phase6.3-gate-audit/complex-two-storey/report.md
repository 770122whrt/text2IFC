# complex-two-storey

- Original input: 创建一个两层小型住宅建筑，单位为毫米。建筑整体为矩形平面，外轮廓尺寸为东西向 10000 mm、南北向 8000 mm，共两层，每层净高 3000 mm，墙厚 200 mm，楼板厚度 150 mm，首层地板厚度 150 mm。坐标约定为：建筑西南角为原点，X 轴向东，Y 轴向北，Z 轴向上。首层包含客厅、厨房、卫生间、楼梯间四个空间：客厅位于西南侧，尺寸 6000 mm × 4500 mm；厨房位于东南侧，尺寸 4000 mm × 3500 mm；卫生间位于东北侧，尺寸 2500 mm × 2500 mm；楼梯间位于西北侧，尺寸 3500 mm × 3500 mm。二层包含主卧、次卧、书房、卫生间、走廊五个空间：主卧位于西南侧，尺寸 5000 mm × 4000 mm；次卧位于东南侧，尺寸 4000 mm × 3500 mm；书房位于东北侧，尺寸 3000 mm × 2500 mm；二层卫生间位于西北侧，尺寸 2500 mm × 2500 mm；走廊连接楼梯口和各房间，宽度 1200 mm。要求生成 IfcBuilding、两个 IfcBuildingStorey、所有 IfcSpace、外墙、内墙、首层地板、二层楼板、屋面板、楼梯、门和窗，并保持空间归属和相邻关系正确。首层客厅南墙居中设置一樘外门，尺寸 1200 mm × 2200 mm；客厅东墙与厨房之间设置一樘室内门，尺寸 900 mm × 2100 mm；厨房北墙与卫生间/过道区域之间设置一樘门，尺寸 800 mm × 2100 mm；卫生间西墙设置一樘门，尺寸 750 mm × 2100 mm；楼梯间东墙设置一樘门，尺寸 900 mm × 2100 mm。二层楼梯上来后进入走廊，走廊分别连接主卧、次卧、书房和卫生间，每个房间门尺寸均为 900 mm × 2100 mm，卫生间门尺寸为 750 mm × 2100 mm。窗户要求如下：客厅南墙设置两扇窗，每扇 1500 mm × 1200 mm，窗台高 900 mm，分布在外门两侧；厨房东墙设置一扇窗，尺寸 1200 mm × 1000 mm，窗台高 1000 mm；首层卫生间北墙设置一扇小窗，尺寸 800 mm × 600 mm，窗台高 1600 mm；主卧南墙设置两扇窗，每扇 1500 mm × 1200 mm，窗台高 900 mm；次卧东墙设置一扇窗，尺寸 1400 mm × 1200 mm，窗台高 900 mm；书房北墙设置一扇窗，尺寸 1200 mm × 1000 mm，窗台高 900 mm；二层卫生间西墙设置一扇小窗，尺寸 800 mm × 600 mm，窗台高 1600 mm。楼梯位于首层楼梯间内，从首层 Z=150 mm 起步到二层楼面 Z=3150 mm，采用直跑或折返楼梯均可，但必须正确连接两层，生成 IfcStair 或等效楼梯构件。所有墙体必须与对应楼层关联，门窗必须嵌入对应墙体并与相邻空间关系一致，楼板和屋面板应覆盖建筑外轮廓，二层空间位于 Z=3150 mm 以上，屋面板位于二层顶部 Z=6150 mm 附近。请生成完整 IFC 模型，保证 IfcSpace、墙、门、窗、楼板、楼梯和楼层结构关系正确。

- Expected counts: `{"IfcBuildingStorey": 2, "IfcDoor": 9, "IfcSpace": 9, "IfcWindow": 9}`
- Gate overall status: `failed`
- Route: `generator_regeneration_required` owned by `generator`
- Final status: `blocked`
- Gate issue codes: `EXPECTED_ENTITY_MISSING, OPENING_FILL_RELATIONSHIP_MISSING, STOREY_CONTAINMENT_MISMATCH, VOID_RELATIONSHIP_MISSING`
- Candidate hash: `ea270d71bc1562346b17b9cc2e5cefcd189e96185297831c468d4a82c3e8cb40`
- Expected facts hash: `1a28c6f3e0d1c4e09e20502816991b99f9b467173e286d2d34ff4430ef8a3f9b`
- Gate summary hash source: `gate-summary.json`
- Route source issue codes: `EXPECTED_ENTITY_MISSING, OPENING_FILL_RELATIONSHIP_MISSING, STOREY_CONTAINMENT_MISMATCH, VOID_RELATIONSHIP_MISSING`
- Non-two-storey route evidence: `False`

## Artifacts

- expected-facts.json
- generator/candidate.json
- gate-summary.json
- route-decision.json
- trace-manifest.json
