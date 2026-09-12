# 真实 Audit 载荷预览

这份预览由生产 Audit 渲染器在已通过检查的同一真实候选续跑上生成；测试 Audit 响应未写入输入。实际运行的路径与生成时间等元数据可能不同，设计请求、Brief、候选实体及追加关系范围保持不变。

目的地 api.deepseek.com，模型 deepseek-v4-flash；新增一次 Audit，不重跑 Brief/Generator。继承8次调用、626258 token、1415.344秒，累计上限32次/200万token/3600秒。只发送本例请求、原有对话、Brief、候选JSON、生产自动检查反馈和运行元数据；不发送IFC文件字节、独立检查器/结论、private Gold、其他案例或凭据值。

原失败仍保留。这不是已经完成的真实 Audit。
