# 为什么没有 repaired.ifc

请求同时包含 Beam 和当前合同不支持的 structural analysis node。系统在 Stage 1 后以 `STRUCTURAL_ANALYSIS_UNSUPPORTED` 终止；Stage 2、IFC mutation 和 publish 都是零。没有 repaired.ifc 是正确的安全结果，不是遗漏。
