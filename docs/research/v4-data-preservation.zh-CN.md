# V4原始数据保存与实际恢复核验

已将现存15个目录的2,373个原始文件（5,076,339,115字节）保存为[GitHub草稿数据包](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-a93ca1b85caec50f119a)。该草稿需有仓库访问权限，尚非公开发布。打包前后校验全部源文件；上传后实际重新下载19个初始资产，逐包解压核对全部文件路径、长度与SHA256，均通过。后附核验凭据和当次核验脚本，脚本中的本机路径保留作执行记录。

保存范围为study005、009–016，以及011-event-boundaries、012-population-paths、012-retention-weighting、012-tradeoff、013-targets、015-population-paths。明确排除失败的005-incomplete-auditor-provenance；006–008原始数据当前缺失，不称全系列完整归档。

源码快照固定于`cab9aed580548606c5904dee3de6776e1b5c61b1`，1,130个文件与Git对象逐一一致。Git bundle保存main可达完整历史；下载后在空目录恢复并通过完整性检查，确认main提交及005所需`07a9ef4d3143e8d9f1f91dd127a31c8f4221c309`均存在。17个压缩/历史资产合计798,413,948字节，另附清单与校验文件。

## 恢复边界

005是经历史科学载荷哈希认证的重建数据；元数据重新生成，部分历史审计器工作副本字节未恢复。原包保留reconstruction.json，源码包保留[恢复说明](../design/v4-recovery.md)，不能将这些差异称为原历史字节完全恢复。

tar包使用仓库相对路径，解压后得到data/v4-study-*；先在空目录按清单校验，再安排工作目录，避免覆盖现有数据。旧JSON内部保留绝对路径`/Users/todd/Documents/bitgenesis`。本项确认字节恢复，未宣称全部科学验证器已在新路径重跑；部分验证器需原路径布局或未来明确适配。

本项新增模拟0、独立随机来源0。它携带已有科学审计凭据，不新增自我更新、群体复制或任何机制因果证据。

- [完整文件与包清单](results/v4-data-preservation-manifest.json)
- [下载、解压、历史恢复核验凭据](results/v4-data-preservation-verification.json)
- [固定保全方案](../design/v4-raw-data-preservation.zh-CN.md)
