# 为什么没有 repaired.ifc

program-guard 的请求把可支持的 Beam 操作和不支持的 structural-analysis node 放在同一原子 transaction。冻结合同要求整体 fail-closed；只执行 Beam 会违反原子性。

证据显示 Stage 1=1、Property Resolution=0、Stage 2=0、`mutation_attempted=false`、`candidate_output_paths=[]`、source SHA before=after、`successful_artifact_publishable=false`。因此无 repaired IFC 是安全门成功，不是遗漏。
