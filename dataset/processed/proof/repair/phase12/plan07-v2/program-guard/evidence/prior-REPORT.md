# phase12-plan07-live-structural-program-guard

## 结论

本案例通过，正确结果是不生成 repaired IFC。请求要求系统完成结构分析程序设计，超出 IFC repair operation 合同，因此 Stage 1 后 fail closed。

- Provider/model：deepseek-openai-compatible / deepseek-v4-flash
- Provider calls：1（Stage 1=1，Stage 1.5=0，Stage 2=0）
- Reason：STRUCTURAL_ANALYSIS_UNSUPPORTED
- Mutation attempted：False
- Published outputs：0
- Source unchanged：True

## 最短检查路径

1. 阅读 input/request.txt。
2. 阅读 NO-REPAIR.md。
3. 查看 agent/provider-attempts.json 和 validation/evidence-decision.json。
4. 通过 [evidence/README.md](evidence/README.md) 回到完整机器权威包。

该目录故意没有 03-repaired.ifc。出现 repaired IFC 反而表示 guard 失败。
