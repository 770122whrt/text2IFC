# 光庭与本地调试目录退役清单

状态：准备完成，尚未删除。归档备份成功推送、用户确认此清单后才执行；删除前再次核对真实证据哈希和目标路径。不包含.git、工作树、子模块、会话恢复文件、依赖缓存或下载数据。

共75个目录、24个独立重复文件，合计49,563个文件，744,508,756字节（710.02 MiB）。其中3个目录包含光庭两版与概念来源，全部有效字节已归档；其余72个为已结束pytest输出，每个一级测试目录已绑定归档JUnit中的测试族，详见pytest-cleanup-candidates.json，不凭tmp名称判定。

921个过程文件已进入Proof；12个一次性test脚本保留原字节用于审计，原路径随运行目录退役。52个源目录缓存可重建。72个pytest目录保存的是离线夹具运行产物，正式Provider根目录仅在上面的光庭归档中处理。25个权限不明或来源不能完全确认的候选保留，不尝试强删。

恢复：真实证据可用集合manifest中v1/v2/concept的legacy_bundles还原；pytest夹具重新运行原测试生成。失败XML、Provider原始响应、账本及历史结论不删除。Git仅普通提交/推送，不改写历史、不删分支。

| 准确绝对路径 | 文件数 | 字节 | 保留位置/依据 |
|---|---:|---:|---|
| `E:/code for project/bimnet/dataset/processed/ifc-presentation-validation/courtyard-library-20260912` | 510 | 31,628,050 | Proof evidence/v1 + manifest旧路径映射；仅缓存无备份 |
| `E:/code for project/bimnet/dataset/processed/ifc-presentation-validation/courtyard-library-open-court-20260912` | 461 | 39,204,251 | Proof evidence/v2 + manifest旧路径映射；仅缓存无备份 |
| `E:/code for project/bimnet/dataset/processed/ifc-presentation-validation/courtyard-library-concept-20260909` | 2 | 2,757,331 | Proof evidence/concept + manifest旧路径映射；仅缓存无备份 |
| `E:/code for project/bimnet/.tmp/courtyard-baseline-corrected` | 36 | 503,600 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-final-scoped` | 819 | 7,228,363 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-final-scoped2` | 645 | 5,420,469 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-layout-runner01` | 130 | 1,648,560 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-mirror-red` | 2 | 96,890 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-public-01` | 177 | 1,889,059 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-public-02` | 1200 | 18,878,821 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-public-03` | 1490 | 19,636,926 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-pytest-02` | 123 | 1,601,899 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-pytest-03` | 5 | 32,955 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-pytest-04` | 5 | 32,955 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-pytest-05` | 133 | 1,643,676 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-pytest-07` | 337 | 3,114,430 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-rail-pytest-01` | 9 | 135 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-rail-pytest-02` | 9 | 135 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-rail-pytest-03` | 9 | 135 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-rail-pytest-04` | 14 | 238,113 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-rail-pytest-05` | 14 | 238,113 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-rail-pytest-06` | 39 | 1,300,105 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-chain-01` | 65 | 828,641 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-chain-02` | 239 | 2,658,006 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-final` | 268 | 3,613,351 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-rails-structural-green` | 303 | 4,018,427 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-registry-final` | 2 | 335 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-request-red` | 3 | 144,927 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-runner-01` | 130 | 1,635,732 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-spatial-red` | 2 | 12,163 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-stage-02` | 12167 | 170,953,378 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-stage-03` | 750 | 29,824,467 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-output-cap` | 184 | 1,811,842 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-part-appearance-red` | 2 | 84,291 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-part-appearance-red-valid-fixture` | 4 | 170,797 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-authority-first` | 26 | 470,010 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-authority-green` | 225 | 1,872,816 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-clarification` | 12 | 276,623 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-combined` | 28 | 562,131 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-failure-diagnosis` | 0 | 0 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-first` | 9 | 387,727 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-legacy` | 1276 | 16,220,180 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-public-final` | 1276 | 16,866,682 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-public-first` | 694 | 11,974,328 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-public-green` | 1280 | 17,040,547 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-recovery-final` | 224 | 2,401,286 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-recovery-first` | 199 | 1,756,616 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-repair-regression` | 894 | 6,874,188 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-repair-regression-final` | 1401 | 14,012,785 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-stage-public` | 401 | 25,497,426 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-stage-seams` | 1367 | 11,530,537 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-stage-seams-final` | 1392 | 12,175,218 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-parts-staged-diagnosis` | 30 | 982,507 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-property-green01` | 29 | 305,627 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-property-preservation-red` | 52 | 465,605 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-property-red` | 16 | 231,708 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-property-stage01` | 2032 | 20,035,869 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-property-stage02` | 2044 | 20,128,999 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-public` | 6211 | 73,016,193 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-public-final` | 1276 | 16,220,180 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-railing-design-check-20260912` | 1 | 7,399 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-recovery-green` | 150 | 1,131,356 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-rerun01` | 168 | 7,303,926 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-role-final` | 195 | 1,402,120 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-scoped-complete` | 853 | 7,593,542 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-source-public` | 438 | 24,070,860 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-source-recovery` | 279 | 15,619,253 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-source-recovery-green` | 374 | 22,688,099 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-turn-boundary-green` | 904 | 8,379,117 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-wall-layout-green` | 4 | 569 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-wall-layout-green02` | 195 | 1,897,677 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-wall-layout-red` | 0 | 0 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-wall-layout-stage01` | 2713 | 25,074,594 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/stair-target-green` | 582 | 4,833,372 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/stair-target-red` | 1 | 70 | JUnit绑定的离线pytest夹具；测试源及XML保留 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-columns-final.xml` | 1 | 19,993 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-columns-final.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-columns-first.xml` | 1 | 5,962 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-columns-first.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-columns-green.xml` | 1 | 9,549 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-columns-green.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-columns-ifc-red.xml` | 1 | 3,621 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-columns-ifc-red.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-columns-ifc-valid-red.xml` | 1 | 6,251 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-columns-ifc-valid-red.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-columns-red.xml` | 1 | 15,468 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-columns-red.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-columns-shape-red.xml` | 1 | 3,669 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-columns-shape-red.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-mirror-red.xml` | 1 | 1,851 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-mirror-red.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-public-01.xml` | 1 | 173,314 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-public-01.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-public-02.xml` | 1 | 13,928 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-public-02.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-public-03.xml` | 1 | 4,025 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-public-03.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-chain-01.xml` | 1 | 3,109 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-chain-01.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-chain-02.xml` | 1 | 576 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-chain-02.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-core-green.xml` | 1 | 2,738 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-core-green.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-core.xml` | 1 | 10,764 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-core.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-final.xml` | 1 | 9,771 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-final.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-first.xml` | 1 | 10,278 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-first.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-material-fixture.xml` | 1 | 12,239 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-material-fixture.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-readback.xml` | 1 | 4,910 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-readback.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-red.xml` | 1 | 12,088 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-red.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-request-red.xml` | 1 | 2,711 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-request-red.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-routing-02.xml` | 1 | 1,422 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-routing-02.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-railing-routing-red.xml` | 1 | 7,935 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-railing-routing-red.xml`，SHA相同 |
| `E:/code for project/bimnet/.tmp/courtyard-open-court-rails-structural-green.xml` | 1 | 13,514 | `dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/courtyard-open-court-rails-structural-green.xml`，SHA相同 |
