# Repair 首批五题

五个不同 IFC；三份 CC BY 4.0、两份 GPL。五题只审题和离线检查，未向模型发送，保留作正式候选。输入测试已做，人审仍待接受，指标尚未冻结。

- [formal-001：补一扇门](formal-001/REVIEW.md)
- [formal-002：补两扇窗](formal-002/REVIEW.md)
- [formal-003：补一扇窗和一扇门](formal-003/REVIEW.md)
- [formal-004：补一扇窗](formal-004/REVIEW.md)
- [formal-005：补一扇门](formal-005/REVIEW.md)

每题 `REVIEW.md` 直接展示局部水平剖切对照图；红色为 G 中的被删构件，D 的红十字仅标注删除位置，蓝色为保留参照。图来自已有 IFC 世界坐标网格，两侧同尺度；不显示原材质，也不代替格式校验或人审。每个目标均单独显示，含两个目标的题有两行。

`VIEW.html` 是可旋转的 G/D 查看器；本环境浏览器桥暂不可用，交互界面的视觉验收未完成。局部图已生成并查看，不因此将题目标为 accepted。

[局部图生成脚本](render_review_sections.py)读取各题现有 `VIEW.html` 中的网格，不修改 IFC。使用已有 Pillow、NumPy 和 Windows 微软雅黑字体运行即可，无需为本轮安装软件。
