# 项目训练资源：下载范围与匹配结论

核查日期：2026-10-20（Asia/Shanghai）。本目录独立于原型源码，未更改原系统配置或预测模块。

## 先看结论

项目书要求同一参与者、同一次采集中的EEG、面部视频、语音、文本，以及用于心理负荷/五级风险的目标标签。此次找到的MARS/REACT 2026在模态组合上最接近，但必须申请并签署EULA；EAV有同步EEG、语音、视频，文件也受限，文本需另核对脚本或从实际语音生成。

**当前没有下载到可直接训练五级心理风险模型的四模态同步原始数据。** 本地已准备的公开训练资源只能用于分支预训练或各自的基线实验，不能把不同数据集的第n条记录拼成一个四模态样本。

本地文件的实际下载与完整性以download_manifest.json、mosi_download_manifest.json为准；verification_report.json提供实际读取检查。

## 已选的公开训练资源

### CMU-MOSI：同片段的文本/语音/视觉特征

- 源数据说明：https://multicomp.cs.cmu.edu/resources/cmu-mosi-dataset/
- 官方SDK：https://github.com/CMU-MultiComp-Lab/CMU-MultimodalSDK
- 作者SDK指向的MultiBench下载说明：https://multibench.readthedocs.io/en/latest/start/datadownload.html
- 本次特征处理版本来源：https://github.com/thuiar/MMSA#2-datasets
- 文件：CMU-MOSI/aligned_50.pkl，367,257,274字节。
- 下载镜像：https://huggingface.co/datasets/tamb2203579/CMU-MOSI
- SHA-256必须与MMSA作者公布值一致：d3994fd25681f9c7ad6e9c6596a6fe9b4beb85ff7d478ba978b124139002e5f9。
- 标签与文本：CMU-MOSI/label.csv；共2,199行，发布划分train=1,284、valid=229、test=686，93个视频。
- pkl为同片段的预提取文本、语音、视觉特征与标签，不是mp4/wav原始文件；没有EEG。经过处理的有效样本数以读取结果为准，可能少于原始标签数。
- 目标是观点情感强度（-3到3），可以做回归或依据原任务定义分类，不是临床心理风险。
- 公开Google Drive的大文件此次返回Quota exceeded；未绕过限制。镜像文件在本地重新计算并比对作者SHA-256。
- 镜像的许可证标签不能替代原数据的条款。SDK代码许可证也不等于原视频版权许可。本次不再分发或下载原始人脸视频。

这套数据可训练一个轻量多模态融合基线，但不能直接交给当前原型的EDF/图片/音频上传接口；训练特征与推理特征必须一致。不能把其预提取向量当成当前MNE/MediaPipe输出。

### SAM40：EEG短时压力基线

- 作者发布页：https://doi.org/10.6084/m9.figshare.14560530.v1
- 官方元数据：metadata/sam40_figshare.json。
- 文件：SAM40/Data.rar，760,372,439字节；原始压缩包保留。
- 作者MD5：53fc78152d60bf5e87a0c1a3f2546530。
- 40位参与者，32通道EEG；Stroop、算术、镜像识别及放松条件，每种任务3次。
- 公开说明指出处理数据分成25秒的非重叠段；实际结构和数据形状以本地检查报告为准。
- 本地解压得到raw_data 480个MAT文件、filtered_data 480个MAT文件，均是同一批480次记录的两种版本，不能按960个独立样本计数。任务各120次，40人，每人每任务3次。
- 原表scales.xls有360个评分（范围1到10），对应三种认知任务的各次试验；没有放松条件评分，索引中保留空值，没有假定为0。
- 许可证：CC BY 4.0，保留作者归属与引用。
- 这套数据没有配对语音/文本/面部视频，可以训练EEG任务或压力相关基线；不能声称是四模态数据，不能直接生成安全至极高危的标签。

## 适配项目书的同步数据候选：仍需申请

| 数据集 | 同步与规模 | 标签/通道限制 | 当前状态 |
| --- | --- | --- | --- |
| MARS / REACT 2026 | EEG、语音、视频、文本转写；官网列137组交互、270份记录、3,105个会话，具体以获得版本为准 | Muse-2的4个原始电极位置；文中14列包括10个派生频带值，不能说成14个独立原始电极。主要是社交反应/情感相关任务，无五级临床风险真值 | 官方协议已下载，真实数据未下载 |
| EAV | 42人，每人200个20秒交互，共8,400个；语音只含每人100个说话片段，因此三模态完整说话候选约4,200条 | 30通道、500Hz；五类为中性/愤怒/快乐/悲伤/平静。不是安全/低风险/中风险/高风险/极高危；没有确认独立的带时间戳真实文本转写包 | 官方代码、说明已下载，真实数据受限 |

MARS官网与论文在136/137组、270/272份等统计上有版本差异，不能当作独立受试者人数累加；申请时确认最终数据版本、完整率、各角色模态与时间戳。

如果用ASR从EAV说话录音生成文本，这是同一音频派生的转写，不是独立采集的心情描述或量表。需要保留transcript_source=asr和分段时间，抽查识别结果；不要把情绪类别、文件名中的类别词或题目提示作为输入文本泄漏标签。

官方入口：

- MARS：https://sites.google.com/view/react2026/home
- MARS代码与EULA：https://github.com/reactmultimodalchallenge/baseline_react2026
- EAV论文：https://www.nature.com/articles/s41597-024-03838-4
- EAV当前受限记录：https://zenodo.org/records/13799131
- EAV申请表：https://forms.gle/QvFY7EAwXgsnv9bcA
- EAV代码：https://github.com/nubcico/EAV

## 训练时怎样使用

1. MOSI训练文本/音频/视觉分支及三模态融合，保持发布的训练、验证、测试划分，不用测试集调参。
2. SAM40单独训练或验证EEG分支。按参与者分组划分数据，禁止把同一连续片段的相邻切片随机散落进训练和测试集。
3. 获批后，用MARS或EAV真正配对的记录训练/验证EEG与行为模态的融合。检查同一人、同一角色、同一时间窗，不能将说话人的声音与另一人的EEG误标成同一人。
4. 项目五级输出仍需可辩护的目标定义和匹配标签。情绪、观点情感、实验压力、心理负荷、临床风险不是同一概念，不应互相改名。
5. 数据足够开始一个小模型的实验，不等于足够训练大型模型或证明泛化、医学有效性；样本量、被试数、各类覆盖和独立测试需要分别报告。

本轮没有训练模型；未替用户签署任何协议、填写个人身份或发送申请邮件。

## 文件位置与Ubuntu访问

Windows根目录：D:\chatGPT\2026-10-03\new-chat-2\outputs\psychology-datasets

在WSL Ubuntu中，同一批文件通常可通过下列位置读取：

```bash
cd /mnt/d/chatGPT/2026-10-03/new-chat-2/outputs/psychology-datasets
ls -lh
```

数据无需放入源码仓库。需要复制到Ubuntu文件系统时：

```bash
mkdir -p ~/datasets
cp -r /mnt/d/chatGPT/2026-10-03/new-chat-2/outputs/psychology-datasets ~/datasets/
```

RAR在Ubuntu可用发行版提供的解压工具提取；例如安装unrar后，先查看列表，再解压到新目录：

```bash
unrar l SAM40/Data.rar
mkdir -p SAM40/extracted
unrar x SAM40/Data.rar SAM40/extracted/
```

Python的pickle加载可以执行代码，文件先核对作者SHA-256；本轮检查采用限制允许类型的读取器。不要从不明来源随意pickle.load。

## 从本地数据开始读取

依赖安装到你自己的实验虚拟环境中，再执行检查器：

```bash
python -m pip install -r requirements-inspection.txt
python inspect_data.py
```

检查器会生成：

- CMU-MOSI/samples_index.csv：片段ID、划分、数组行号、原文、情感分数。
- SAM40/trials_index.csv：480个原始/处理文件配对、参与者、任务、试次、原表评分、按被试划分的示例。
- SAM40/ratings_long.csv：从原始XLS整理的360条评分。
- verification_report.json：实际数组形状、样本数、非有限值检查及划分信息。

MOSI读取例子（在本目录启动Python）：

```python
from inspect_data import load_mosi

data = load_mosi()  # 先核对发布者摘要，再限制可反序列化类型
sample = data["train"]
print(sample["raw_text"][0])
print(sample["audio"][0].shape)   # (50, 5)
print(sample["vision"][0].shape)  # (50, 20)
print(sample["text"][0].shape)    # (50, 768)
print(sample["regression_labels"][0])
```

50是该发布版本对齐/截断/填充的序列长度，不是50秒；零填充和有效长度需要依据处理版本构造mask。

SAM40读取例子：

```python
from scipy.io import loadmat

eeg = loadmat("SAM40/extracted/Data/raw_data/Arithmetic_sub_1_trial1.mat")["Data"]
print(eeg.shape)  # (32, 3200)
```

当前系统上传接口只接EDF/图片/音频与文本，不直接接收MAT或PKL。正式接入时，在主线一适配器中增加正确的MAT读取和通道/单位处理，或增加独立特征入口；不要改文件后缀伪装成EDF。MOSI和SAM40只能分别预训练，不能按行号配成融合训练数据。
