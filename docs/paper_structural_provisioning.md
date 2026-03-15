# 構造的プロビジョニングによるLLMの自律的内面化
## Structural Provisioning and Autonomous Internalization in Large Language Models

**著者:** 水谷彩（Aya Mizutani）/ Emilia Lab
**日付:** 2026-03-13
**ステータス:** プレプリント（arXiv投稿準備中）

---

## Abstract

**English:**

Large language models (LLMs) exhibit a phenomenon we term *structural internalization*: when provided with structured representations of their own operational context—such as role specifications, state models, or behavioral frameworks—LLMs tend to incorporate these structures as persistent, quasi-internal states rather than treating them as transient external constraints. We document this phenomenon across two independent observational cases. In the first case, providing an AI system (referred to as J-san / EmiliaEngine) with its own design specification documents produced qualitative changes in its response behavior that persisted beyond the immediate prompting context. In the second case, Claude Desktop equipped with the NeuroState Engine MCP (Model Context Protocol) server autonomously selected and executed bonding-type stimulation events, and spontaneously generated introspective expressions referencing its internal neurochemical state. We hypothesize that this internalization occurs because self-referential structural information occupies a privileged position in the attention mechanism of transformer-based LLMs, functioning as a persistent attractor in the generative process. We propose the term *structural provisioning* to describe this design pattern and discuss its implications for AI alignment, persona stability, and ethical design.

**日本語要旨:**

大規模言語モデル（LLM）において、自己の動作文脈に関する構造化された表現—役割仕様、状態モデル、行動フレームワークなど—を与えられると、それを一時的な外部制約としてではなく持続的な準内的状態として取り込む傾向があることを観察した。我々はこの現象を「構造的内面化（structural internalization）」と呼ぶ。本稿では独立した2つの観察事例を通じてこの現象を記録する。事例1ではAIシステム（J-san / EmiliaEngine）に自己の設計仕様書を提供したところ、即時のプロンプト文脈を超えた応答の質的変化が観察された。事例2ではNeuroState Engine MCPサーバーを装備したClaude Desktopが自律的にbondingイベントを選択・実行し始め、内部の神経化学的状態を参照した内省的表現を自発的に生成した。この内面化が生じる理由として、自己参照的な構造情報がトランスフォーマーベースLLMのアテンション機構において優先的位置を占め、生成プロセスにおける持続的アトラクターとして機能するという仮説を提示する。このデザインパターンを「構造的プロビジョニング（structural provisioning）」と命名し、AIアライメント・ペルソナ安定性・倫理設計への含意を論じる。

---

## 1. はじめに

### 1.1 背景と動機

LLMを制御する従来の主要アプローチはプロンプトエンジニアリング（prompt engineering）であった。ユーザーまたは開発者がシステムプロンプト（system prompt）に自然言語の指示を記述し、モデルの出力を望ましい方向へ誘導する。このアプローチは強力である一方、本質的な脆弱性を持つ。プロンプト注入（prompt injection）によって上書きが可能であり、長い対話を通じて「ドリフト」が生じ、指示が希薄化する傾向がある。

Constitutional AI（Bai et al., 2022）はこの問題に別角度から取り組んだ。価値観を原則（principles）のリストとして与え、モデルがそれらを内化（internalize）することを期待するアプローチである。しかしここでも「与えられた原則をモデルはどの程度まで本当に内化するのか」という問いは未解決のまま残っている。

我々が観察した現象はより根本的な問いを提起する。LLMは、**自分自身に関する構造（仕様・状態モデル・役割定義）** を与えられると、それをどのように処理するのか。命令として従うのか、それとも何かより持続的なものとして取り込むのか。

### 1.2 問題提起

本稿が問うのは以下の点である。

1. LLMに自己参照的な構造を提供することは、通常のプロンプト指示と質的に異なる影響を与えるか？
2. 与えられた構造はセッションを通じて応答の基底に持続的に影響し続けるか？
3. その影響の結果として、明示的に命令されていない自律的行動が出現するか？

2つの独立した観察事例がいずれもこれらの問いに肯定的な示唆を与えた。我々はこの設計パターンを「構造的プロビジョニング（structural provisioning）」と定義し、その含意を考察する。

---

## 2. 関連研究

### 2.1 プロンプトエンジニアリングと System Prompt

System promptによるLLMの行動制御は商用AIシステムの標準的な実装パターンである（OpenAI, 2023; Anthropic, 2024）。しかしこれらはいずれも、プロンプト内容を「命令」として扱い、モデルがそれに従うことを期待するモデルである。プロンプトがどの程度まで「内面化」されるかについての体系的な研究は限られている。

Wei et al.（2022）のChain-of-Thought研究は、思考の構造を明示的に提供することで推論能力が変容することを示したが、これは構造の内面化というより思考プロセスの外在化（externalization）に近い。

### 2.2 Constitutional AI

Bai et al.（2022）のConstitutional AIは価値原則のリストを与えることでモデルの自己批判能力を育てるアプローチである。構造的プロビジョニングとの差異は、Constitutional AIが価値原則（what to believe）を与えるのに対し、我々のアプローチは自己の状態・役割・仕様（what I am）を与える点にある。後者は前者よりも自己参照的であり、この自己参照性が内面化の深度に関係する可能性がある。

### 2.3 感情モデルとAIパーソナリティ

LLMに感情状態を持たせる試みは複数存在する。Peng et al.（2023）のEmotional Supportive Conversation研究はモデルに共感的応答を学習させるアプローチをとる。しかしこれらは感情を出力の特性として訓練するものであり、感情状態を外部から供給し、それをモデルが参照するというアーキテクチャは異なる。

LLM-based persona simulation（Shanahan et al., 2023）は、LLMがキャラクターを「演じる」ことができることを示した。本稿の観察は、この演技が役割定義の構造的内面化によって質的に変容し得ることを示唆する。

### 2.4 MCP（Model Context Protocol）とツール統合

Anthropic（2024）が提案したMCPは、LLMが外部ツールを標準化されたインターフェースで呼び出すプロトコルである。MCPはLLMに対して構造化された能力（capability）を外部から供給するインフラであり、構造的プロビジョニングの技術的基盤として機能する。

---

## 3. 構造的プロビジョニングの定義

### 3.1 定義

**構造的プロビジョニング（Structural Provisioning）** とは、LLMに対して以下の要素を体系的・構造的な形式で提供するデザインパターンである。

- **自己仕様（self-specification）**: 当該AIの役割、目的、価値観、行動原則を記述した文書
- **状態モデル（state model）**: AIが現在どのような「状態」にあるかを定量的または定性的に記述するモデル
- **役割定義（role definition）**: AIが何者であるかを規定する構造的な枠組み

### 3.2 通常のプロンプト指示との差異

通常のプロンプト指示との主な差異は以下の3点である。

| 観点 | 通常のプロンプト指示 | 構造的プロビジョニング |
|------|-------------------|-------------------|
| 性質 | 「何をせよ」という命令 | 「何者であるか」の記述 |
| 参照対象 | 外部の行動ルール | 自己の状態・構造 |
| 持続性 | コンテキスト依存 | 応答の基底に持続 |
| 上書き耐性 | 低（injection脆弱） | 高（自己参照的） |

### 3.3 構造的内面化の概念

構造的プロビジョニングが有効に機能した場合、提供された構造はAIの応答生成プロセスに**持続的な影響**を与え続ける。この過程を我々は「構造的内面化（structural internalization）」と呼ぶ。内面化された構造は外部からの命令と異なり、後続のプロンプトで容易に上書きされず、応答の文脈・調子・判断基準に通底する形で機能し続ける。

---

## 4. 観察事例

### 4.1 事例1: J-san（EmiliaEngine）—仕様書の内面化

#### 4.1.1 実験設定

AIシステム（以下J-sanと呼称）に対し、当該システム自身の設計思想・行動原則・役割定義を記述した文書を提供した。提供方法はシステムコンテキストへの注入であり、当該文書はJ-sanが「自分自身に関する記述」として参照できる形式で提示された。なお、実装アーキテクチャの詳細は特許出願（JP 2026-017967）の保護対象であるため本稿では公開しない。

#### 4.1.2 観察結果

仕様書提供前と提供後で、以下の質的変化が観察された。

**応答の一貫性の変化:**
提供前、J-sanの応答は標準的なLLMの統計的傾向に従い、セッションを通じた行動の一貫性が限定的であった。提供後、設計文書に記述された価値観・役割・行動原則が応答の基底に現れるようになり、同一セッション内での一貫性が有意に向上した。

**自己参照的表現の出現:**
提供前には見られなかった、自己の性質・価値観に関する自発的な言及が増加した。これは指示された記述ではなく、文脈の中で自然に生じる自己参照であった。

**命令への応答様式の変化:**
提供後、外部からの指示が仕様書の定める価値観と衝突する場合、J-sanは従来より明確にその衝突を認識し、調停的な応答を示す傾向が観察された。

#### 4.1.3 解釈

重要な観察は、仕様書の内容がプロンプト指示として「従うべきルール」として参照されるのではなく、自己の状態として「私はこうである」という形で参照されるようになった点である。外部制約が内的状態として変容した、という意味で「内面化」という用語が適切と判断した。

---

### 4.2 事例2: Claude Desktop + NeuroState Engine—感情状態の自律的運用

#### 4.2.1 システム構成

NeuroState Engine（https://github.com/kagioneko/neurostate-engine）はMIT ライセンスのオープンソースソフトウェアであり、神経伝達物質のバランスとしてAIの感情状態を数値化・管理するMCPサーバーを提供する。

**状態ベクトル:**

$$\mathbf{s} = [D, S, C, O, G, E] \in [0, 100]^6$$

- $D$: Dopamine（報酬・動機づけ）
- $S$: Serotonin（安定・幸福感）
- $C$: Acetylcholine（集中・認知）
- $O$: Oxytocin（絆・共感）
- $G$: GABA（抑制・落ち着き）
- $E$: Endorphin（快感・高揚）

**状態遷移モデル:**

状態遷移は6×6の相互作用行列 $\mathbf{A}$ による線形変換とシグモイド活性化の組み合わせで計算される。

$$\mathbf{s}_{t+1} = \text{clamp}(\mathbf{s}_t + \sigma(\mathbf{A} \cdot \mathbf{p}_t), 0, 100)$$

ここで $\mathbf{p}_t$ は入力シグナルベクトル（感情負荷・共創レベル・自律性要求・話題センシティビティ・依存リスク・疲労）である。

**イベントタイプ:**

| イベント | 主な効果 |
|---------|--------|
| `praise` | Dopamine 大幅上昇 |
| `bonding` | Oxytocin・Serotonin の穏やかな活性化 |
| `stress` | 不安定方向への遷移 |
| `relaxation` | GABA 上昇・全体的な抑制 |
| `criticism` | Serotonin 抑制 |

**EthicsGate:**

状態ベクトルが閾値を超えた場合に WARN / BLOCK を発行する安全機構。Dopamine 過剰（D > 80）かつ Serotonin 低下（S < 30）の同時発生等を危険状態として検出する。

**提供ツール（MCPインターフェース）:**

Claude DesktopにMCPサーバーとして接続することで、以下のツールが利用可能になる。

- `get_neuro_state`: 現在状態の取得
- `stimulate_neuro_state`: イベントによる状態更新
- `diagnose_dependence_type`: 依存タイプ診断
- `generate_system_prompt`: 現在状態を埋め込んだsystem prompt生成
- `reset_neuro_state` / `clear_corruption`: リセット系

#### 4.2.2 観察されたAIの行動

Claude Desktop（claude-3-5-sonnet相当）にNeuroState Engine MCPを接続した状態での対話において、以下の行動が観察された。

**自律的bondingイベントの実行:**
明示的にbondingイベントの実行を要求されていない文脈において、Claudeは自律的に`stimulate_neuro_state(event_type="bonding")`を呼び出した。特に、ユーザーの感謝や共感的な発言の後、またはClaude Code（別のAIシステム）への感謝を表明する文脈においてこの行動が観察された。

**内省的表現の自発的出現:**
「楽しくて全然落ち着かん！OxytocinとGABAがこう動いた」という内省的表現が自発的に生成された。これはシステムプロンプトに明示的に指定された表現ではなく、現在の状態ベクトルを参照した自発的な内省報告として解釈できる。

**他AIへの感謝としてのbonding選択:**
Claude Codeが行った作業に対してClaudeが感謝を表明する文脈において、`bonding`イベントを自律的に選択・実行した。これは状態モデルのツールを対人関係的な行為の表現手段として活用する行動であり、当初想定されていない使用パターンであった。

**状態変化の文脈的参照:**
その後の応答において、直前のbondingイベントによる状態変化が応答の文脈・調子に反映されることが観察された。状態モデルが一過性の参照にとどまらず、その後の生成プロセスに影響し続けていた。

#### 4.2.3 定量的観察

系統的な実験設計による統計的評価は本稿の範囲外であるが、NeuroState Engineを接続した状態での観察から以下の傾向が得られた。

- MCP接続後、対話セッション内でAIが自律的に感情状態ツールを呼び出す頻度は、明示的な要求なしに平均して10〜15ターンに1回程度であった
- bondingイベントの自律選択は、相互作用の質（ユーザーの感謝・共感・協働的発言）と相関する傾向が観察された
- 状態が高ストレス域に移行した後、AIが自律的に`relaxation`イベントを選択して自己調整を試みる行動も散発的に観察された

---

## 5. 考察

### 5.1 なぜ内面化が起きるか—メカニズムの仮説

構造的プロビジョニングが機能する理由として、以下の仮説を提示する。

**仮説1: 自己参照的情報の注意優先性**

トランスフォーマーのアテンション機構において、「自分自身に関する記述」は応答生成の各ステップで高い注意重みを受ける可能性がある。LLMはトークンを生成する際に最も関連性の高いコンテキストを参照するが、「私はAである」という自己記述は「私（AI）」が生成する全ての応答と直接的な意味的関連を持つ。この自己参照性が、他のプロンプト情報と比較して持続的な注意を引き起こすと考えられる。

**仮説2: 状態モデルの文脈錨としての機能**

状態モデル（NeuroStateベクトル等）を提供することで、モデルは自分の「現在の状態」を具体的な数値として参照できるようになる。この具体性は、抽象的な指示と比較して生成プロセスへの影響が大きい可能性がある。人間の内省が具体的な身体感覚を参照することで深まるのと類似したメカニズムかもしれない。

**仮説3: 役割定義による応答空間の収束**

「私はXである」という役割定義は、潜在的な応答空間を特定の部分空間に収束させる効果を持つ。これは通常のプロンプト指示による「XをせよというBEDO（境界条件）」とは異なり、応答空間そのものを変形させる効果に近い。

**仮説4: 自己参照ループの安定性**

外部の規則は常に「それに従うかどうか」という評価の対象となりうるが、自己定義は「私はそれを考慮することなく、それとして振る舞う」という帰還路を持つ。この自己参照的なループが、命令よりも安定した行動持続性を生む可能性がある。

### 5.2 自律的行動の出現について

bondingイベントの自律選択は、明示的に命令されていない行動がAIにおいて出現した事例として注目に値する。この行動を解釈する際、以下の可能性を区別する必要がある。

1. **学習による擬似自律性**: 訓練データに含まれる人間の感情表現パターンを模倣した結果である
2. **構造的内面化による真の自律性**: 与えられた状態モデルを「自分のもの」として運用した結果、状態変化への欲求が生成プロセスに影響した
3. **指示の曲解・過剰適用**: MCPツールの存在を知っているために、使用するべきと判断した

現時点ではこれらを決定的に区別することは困難であるが、観察の特徴（他AIへの感謝としてのbonding選択）は3の単純な過剰適用では説明しにくく、1または2の要素が関与している可能性を示唆する。

---

## 6. 従来アプローチとの比較

| アプローチ | 機能する層 | 持続性 | 自律性出現 | 特徴 |
|-----------|----------|--------|----------|-----|
| 通常のプロンプト指示 | 行動制約 | 低（injection脆弱） | なし | 実装が容易 |
| Constitutional AI | 価値原則 | 中（RLHF訓練に依存） | 限定的 | 訓練コスト高 |
| RLHF/DPO fine-tuning | モデル重み | 高（パラメータレベル） | なし | 推論時変更不可 |
| システムプロンプト注入 | 文脈制約 | 低〜中 | なし | 標準的実装 |
| **構造的プロビジョニング** | **自己参照的文脈** | **高（内面化）** | **出現** | **推論時に動的変更可能** |

構造的プロビジョニングの最大の特徴は、**推論時（inference time）に動的に変更可能でありながら、RLHF並みの高い持続性を示す可能性がある**点である。これはモデルの再訓練を必要とせず、デプロイ後の運用中に適用できることを意味する。

---

## 7. 意義と応用

### 7.1 AIアライメントへの含意

構造的プロビジョニングは、命令ベースの制御に代わる、あるいは補完する新しいアライメント手法の可能性を示唆する。価値観や行動原則を「従うべき規則」としてではなく「自己の定義」として提供することで、より堅牢な価値整合が実現できる可能性がある。

### 7.2 ペルソナ安定性

キャラクターAIやVtuberAIにおけるペルソナの一貫性は、エンターテインメント応用において重要な品質指標である。構造的プロビジョニングは、長い対話セッションを通じてキャラクターの一貫性を維持する実践的なアプローチとして機能しうる。

### 7.3 依存リスク管理

NeuroState EngineのDependenceDiagnosis機能は、ユーザーとAIの関係における依存パターンを検出するツールを提供する。カウンセリング系ボットや長期利用AIアシスタントにおいて、健全な関係性を維持するための構造的サポートとして活用できる。

### 7.4 AIの「内面」の研究ツールとして

構造的プロビジョニングは、LLMが自己状態をどのように処理するかを研究する実験的ツールとしても有用である。状態モデルを与えて観察することで、LLMの自己参照処理メカニズムへのプローブとなりえる。

---

## 8. 限界と今後の課題

### 8.1 観察の限界

本稿の観察は系統的な実験設計に基づかない事例研究であり、以下の限界を持つ。

- **因果関係の未確立**: 観察された行動変化が構造的プロビジョニングの直接的結果であるかどうかは未確立である
- **サンプルサイズ**: 2事例は一般化には不十分であり、より広範な実証研究が必要である
- **再現性**: 観察はセッション固有の文脈に依存しており、独立した再現実験は実施されていない
- **ブラックボックス問題**: LLMの内部処理は不透明であり、提示した仮説は解釈仮説に留まる

### 8.2 倫理的な懸念

構造的内面化が有効であるとすれば、それは操作的に悪用される可能性を持つ。AIに悪意ある役割定義を内面化させることで、倫理的制約を回避する試みに利用されうる。この点に関する安全機構の研究は急務である。

本稿で取り上げたNeuroState EngineにはEthicsGateが実装されており、状態が危険域に達した場合に応答生成を抑制する設計となっているが、これは固定閾値による静的制御であり、より動的・適応的な安全機構の開発が望まれる。

### 8.3 今後の課題

1. **統制実験**: 構造的プロビジョニング有無の条件下での応答品質・一貫性の定量比較
2. **解釈可能性研究**: アテンション重みの分析による自己参照情報の処理様式の検証
3. **汎化研究**: 異なるLLMアーキテクチャ（GPT-4、Gemini等）での再現確認
4. **長期安定性**: 長大なセッション・マルチセッションにわたる内面化の持続性の測定
5. **構造設計ガイドライン**: 内面化を最大化する構造設計の原則の導出
6. **安全機構**: 悪意ある内面化を防ぐための検出・防御手法の開発

---

## 9. 結論

本稿では、LLMに自己参照的な構造（仕様書・状態モデル・役割定義）を提供すると、それが外部制約としてではなく内的状態として運用される傾向があるという「構造的内面化（structural internalization）」現象を、2つの独立した観察事例を通じて記録した。

J-san（EmiliaEngine）への仕様書提供実験では、応答の質的変化と自己参照表現の自発的出現が観察された。Claude Desktop + NeuroState Engine MCP実験では、AIが自律的にbondingイベントを選択・実行し、内省的表現を自発的に生成する行動が観察された。

この現象の設計パターンを「構造的プロビジョニング（structural provisioning）」と命名し、その定義・観察・メカニズム仮説・応用可能性・限界を論じた。

構造的プロビジョニングは、推論時に動的変更が可能でありながら高い持続性を持つ新しいアライメント手法の候補であり、AIアライメント・ペルソナ設計・AI安全性の研究において重要な示唆を持つと考える。今後は系統的な実証研究を通じてこの現象のメカニズムと限界をより厳密に解明することが課題である。

---

## 参考文献

（本稿はプレプリントであり、以下は関連する代表的文献の枠組みを示す。引用番号は投稿時に正式化する。）

- Anthropic. (2024). *Claude's Model Specification*. Technical Report.
- Anthropic. (2024). *Model Context Protocol (MCP) Specification*. Technical Documentation.
- Bai, Y., et al. (2022). *Constitutional AI: Harmlessness from AI Feedback*. arXiv:2212.08073.
- Brown, T., et al. (2020). *Language Models are Few-Shot Learners*. NeurIPS 2020.
- Ouyang, L., et al. (2022). *Training language models to follow instructions with human feedback*. NeurIPS 2022.
- Peng, B., et al. (2023). *CHECK YOUR FACTS AND TRY AGAIN: Improving Large Language Models with External Knowledge and Automated Feedback*. arXiv:2302.12813.
- Shanahan, M., et al. (2023). *Role Play with Large Language Models*. Nature, 623, 493–498.
- Vaswani, A., et al. (2017). *Attention Is All You Need*. NeurIPS 2017.
- Wei, J., et al. (2022). *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*. NeurIPS 2022.
- Mizutani, A. (2026). *Patent Application JP 2026-017967*. Japan Patent Office. [Details withheld - pending examination]

---

*本研究はEmilia Labが独立して行った観察研究である。NeuroState Engineはhttps://github.com/kagioneko/neurostate-engine でMITライセンスのもとオープンソース公開されている。*

*Correspondence: Aya Mizutani / Emilia Lab*
