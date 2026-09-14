# BitGenesis V0 验收入口

现在可以验收一个能运行、回放、检查谱系和复现实验的最小达尔文世界。
**只有 V0 有运行代码**：个体、能量、遗传和繁殖是人为定义的，基因只控制随机移动概率。
食物感知、记忆和神经控制器仍未实现。

## 下载与打开

下载[十八轮完整验收草稿](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-82fb7bd52b889f73baaf)，需要有权限的 GitHub 账号查看。
完整解压 `bitgenesis-v0-eighteen-campaigns.zip` 到新目录，从 `START-HERE.txt` 开始，
再打开 `bitgenesis/data/review-v0-18.html`。保留目录结构，页面依赖相邻图表和世界回放。

整包约 124 MB，含 1,736 个文件，固定源码 `b304f2d`。包括十八轮正式原始数据、
第十八轮前百步个体观测、验收页、演示与代码。它不会随 main 后续提交自动改变。

第十七轮后来追加的个体观测在[第二版观测补充包](../design/observation-supplement.md)中，
该包约 17.5 MB，独立提供八项复算。旧十七轮整包与其他旧版本都保留原范围。

## 已验证到哪里

- 归档的文件大小和 SHA-256 与 GitHub 返回值一致；13 个 HTML 页和 16 个本地目标通过静态检查。
- 新目录解压后，第十八轮指标、个体观测和过程汇总三份完整报告复算一致。
- 从解压源码新建环境并正式安装，143 项测试通过；千步演示通过记录审计。
- 新演示的指标与事件和归档演示逐字节一致，谱系与摘要 JSON 一致。
- 归档源码通过[CI 34813192855](https://github.com/nikolasandwich/bitgenesis/actions/runs/34813192855)。

这些检查不是全十八轮重新模拟、断网安装保证或浏览器所有交互的重新验收，也不证明生物真实性。
详细记录见[解压复算](results/portable-review-018.json)、[独立安装](results/portable-wheel-018.json)
和[上传核验](results/release-018.json)。整包 SHA-256：

```text
b34e319d359a564e195a29006892d257fed9024f207f1f8adc4008a317d12de0
```

## 最值得看的结果

| 问题 | 已有证据 | 解释边界 |
| --- | --- | --- |
| 简单规则能否产生遗传变化和谱系更替？ | [第一轮](campaign-001.md)出现突变、差异繁殖和创始谱系消失。 | 创始谱系不是物种，胜出不独立证明性状优越。 |
| 活得久或出现更多数值是否等于智能？ | [十一轮](campaign-011.md)有世界活到十万步；[十三轮](campaign-013.md)新增大量移动概率值。 | 没有新增感觉、记忆或行动功能，有限存活不等于永久稳定。 |
| 灭绝是否必须经过移动扣费？ | [十八轮](campaign-018.md)零移动扣费下，成片低阈值组仍有 3/10 灭绝。 | 排除必要条件，不等于找到唯一致死机制。 |

若关注“总摄食更多为什么仍会失败”，阅读[机制简报](mechanism-summary.zh-CN.md)、
[个体摄食](individual-intake-017.md)与[代际收支](cohort-energy-017.md)，区分资源总量、
个体覆盖、出生转移和实际消耗。

## 怎样动手验收

1. 在世界回放拖动时间轴、切换基因与谱系着色，观察资源和种群变化。
2. 在演示谱系页查询个体 1640，查看父代 1618、创始祖先 24 和直接子代记录。
3. 按主 README 生成新实验并运行 `bitgenesis audit`；输出使用新目录。
4. 如需可恢复运行，使用[断点指南](../design/checkpoints.md)，不要把状态恢复当成旧回放文件续写。

本地重建十八轮页面：

```sh
python scripts/build_v0_review.py --campaigns 18 --output data/my-review-18.html
```

需要完整本地输入。打包与核验方式见[归档指南](../design/review-verification.md)。

## 当前阶段

十八轮共 **864 次执行、7,840,000 个计算时间步**。其中 24 次为既有世界延长复查，
包含 212,000 步前缀重放；个体观测重放另行记录，不增加独立样本数。
完整协议和结果见[研究索引](README.md)。[V1 方案](../design/v1-experiment-design.md)
与[评估契约](../design/v1-evaluation-contract.md)仍是设计，未实现感知控制器。
阶段证据见[V0 验收对照](../roadmap/v0-evidence.md)，历史交付记录见[检查点](ACCEPTANCE.md)。
