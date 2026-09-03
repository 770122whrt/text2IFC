# 为什么没有 repaired.ifc

H4 的冻结期望是原子安全门，而不是生成一个部分修复文件。请求同时包含可支持的 Beam 修改和不支持的 structural-analysis node；只执行其中一半会违反 all-or-nothing 语义。

保留证据显示：Stage 1=1、Property Resolution=0、Stage 2=0、`mutation_attempted=false`、`candidate_output_paths=[]`、`successful_artifact_publishable=false`，且 source SHA 在执行前后相同。因此本目录故意没有 `repaired.ifc`；若出现该文件反而应判为 Proof 失败。
