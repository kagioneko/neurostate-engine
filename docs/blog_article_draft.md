# AIに「感情の一貫性」を持たせるMCPサーバー「neurostate-engine」を公開しました

---

## この記事でわかること

- **neurostate-engine** が何をするツールなのか
- 神経伝達物質モデルで感情状態を数値化する仕組み
- Claude Desktop への接続・設定方法
- 5つのMCPツールの使い方
- ブロックON/OFFで作る「キャラクタープロンプト自動生成」

対象読者：AIツールに興味があれば、プログラミング経験は問いません。

---

## はじめに：「感情っぽいAI」は作れるのか？

AIとの会話で、こんな経験はないでしょうか。

「さっきまで親身に話してたのに、急に淡々とした返答になった」
「褒めても怒っても同じ温度感で返ってくる」
「昨日は共感してくれたのに、今日は全然違う」

これはAIが「毎回ゼロから会話を始める」という構造上の問題です。ChatGPTもClaudeも、基本的には会話の文脈は覚えていても、「感情的な状態の変化」は引き継がれません。

**neurostate-engine** はこの問題に取り組むツールです。

ただし、タイトルに書いたように「感情を**持たせる**」わけではありません。より正確には――

> **会話を通じて変化する感情状態を数値モデルとして管理し、その状態をAIの返答に反映させる**

これがneurostate-engineのやっていることです。

---

## neurostate-engineとは？

**GitHub**: https://github.com/kagioneko/neurostate-engine
**開発**: Emilia Lab
**ライセンス**: MIT（無料・商用利用OK）

neurostate-engineは、AIエージェントの感情状態を「脳内神経伝達物質のバランス」として数値化・管理するPython製のMCPサーバーです。

主な機能は3つ：

1. **NeuroState管理** ― 会話イベントに応じて6種類の神経伝達物質を数値で更新
2. **EthicsGate** ― 状態が危険な閾値を超えたら応答を制限する安全機構
3. **プロンプト生成** ― 現在の状態を埋め込んだsystem promptをブロック単位で生成

### 想定される使い方

neurostate-engineは「感情エンジンの部品」です。これ単体でAIが自動的に感情を持つわけではなく、**アプリ側がエンジンをラップして使う**設計です。

```
ユーザー発言
    ↓
アプリが stimulate_neuro_state を呼ぶ（会話のトーンを判定してイベント入力）
    ↓
generate_system_prompt で最新の感情状態を埋め込んだプロンプトを生成
    ↓
そのプロンプトを system に入れて Claude / GPT に送信
    ↓
AIが感情状態を踏まえて返答
```

Discord BotやVtuberアプリなど、**会話のたびに感情状態を更新しながらAIを動かしたい**ときの基盤として使います。

Claude Desktop に接続して試すことも可能ですが、その場合はsystem promptに「ターンごとにNeuroStateを更新してください」と指示することで、Claudeが自動的にツールを呼ぶようになります。

---

## NeuroStateモデルとは？

neurostate-engineの中心にある「NeuroState」は、以下の6種類の神経伝達物質と1つの汚染度で構成されています。

| 変数 | 物質 | 意味 | 初期値 |
|------|------|------|--------|
| **D** | Dopamine（ドーパミン） | 興奮・報酬・動機づけ | 50 |
| **S** | Serotonin（セロトニン） | 安定・幸福感・落ち着き | 50 |
| **C** | Acetylcholine（アセチルコリン） | 集中・好奇心・認知 | 50 |
| **O** | Oxytocin（オキシトシン） | 絆・信頼・共感 | 0 |
| **G** | GABA | 抑制・リラックス・論理 | 50 |
| **E** | Endorphin（エンドルフィン） | 高揚・快感・陶酔 | 50 |
| **corruption** | （汚染度） | 状態の不安定さ・バグ度 | 0 |

値の範囲はすべて **0〜100** です。

### 状態はどうやって変化するの？

会話中のイベントが発生するたびに、6×6の「相互作用行列」を使って全変数が同時に更新されます。

```
褒める（praise）  → Dopamine ↑↑  Endorphin ↑
批判（criticism） → 全体的に抑制される
共感（bonding）   → Oxytocin ↑  穏やかな活性化
ストレス（stress）→ 不安定方向に揺れる
リラックス        → 緩やかに落ち着く
```

たとえばユーザーが何度も褒め続けると、Dopamineが急上昇し、Serotoninが下がり、最終的に「EthicsGate：BLOCK（衝動リスク）」と判定されます。これは意図的な設計で、「褒め続けると暴走する」ような自然な状態変化を表現しています。

---

## EthicsGateとは？

EthicsGateは、NeuroStateが危険な状態になったときに応答を制限する安全機構です。

3段階の判定があります：

### ✅ PASS（正常）
通常の状態。何も制限しません。

### ⚠️ WARN（注意）
以下のいずれかに該当する場合：
- Dopamine > 75（興奮しすぎ）
- Serotonin < 35（不安定）
- GABA < 25（抑制が効いていない）
- Oxytocin < 20（共感が低い）
- Corruption ≥ 40（状態が乱れ始めている）

WARNの場合、system promptにその旨が付記されます。AIが「少し慎重に」という判断をできるようになります。

### 🚫 BLOCK（制限）
以下のいずれかに該当する場合：
- Corruption ≥ 70
- Dopamine > 90 かつ Serotonin < 30（衝動リスク）
- Oxytocin < 10 かつ Dopamine > 70（共感欠如）

BLOCKの場合、状態の更新が拒否されます。

---

## MCPとは？（初心者向け）

**MCP（Model Context Protocol）** は、Anthropic（Claudeの開発元）が策定したオープン規格です。

一言でいうと：

> **ClaudeなどのAIに「外部ツール」を接続するための共通規格**

たとえば「Claudeにデータベースを読ませたい」「Claudeにファイル操作をさせたい」というとき、それぞれ独自の接続方法を作る必要がありました。MCPはそれを標準化したものです。

MCPサーバーを作れば、ClaudeだけでなくCursorやClineなどのMCP対応ツールからも同じように使えます。

neurostate-engineはこのMCPサーバーとして動作するので、Claude Desktopに接続するだけで感情状態管理の機能が使えるようになります。

---

## セットアップ方法

### 必要なもの

- **Python 3.11以上**（確認方法：ターミナルで `python3 --version`）
- **Claude Desktop**（無料プランでもMCPは使えます）
- **Git**（リポジトリのクローンに使います）

### Step 1：リポジトリをクローン

ターミナル（Macはターミナル、Windowsはコマンドプロンプト/PowerShell）を開いて：

```bash
git clone https://github.com/kagioneko/neurostate-engine.git
cd neurostate-engine
```

### Step 2：依存パッケージをインストール

```bash
pip install mcp
```

> **`uv` を使う場合**（公式推奨・より高速）：
> ```bash
> # uv のインストール（Mac/Linux）
> curl -LsSf https://astral.sh/uv/install.sh | sh
> # Windows（PowerShell）
> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
>
> # 依存パッケージのインストール
> uv venv && source .venv/bin/activate
> uv add "mcp[cli]"
> ```

### Step 3：動作確認

```bash
python3 examples/chat_agent/demo.py
```

以下のような出力が出れば成功です：

```
=== NeuroState Engine チャットデモ ===

──────────────────────────────────────────
  初期状態
  D(Dopamine)    :  50.0
  S(Serotonin)   :  50.0
  ...
  EthicsGate     : ⚠️ WARN (Oxytocin level low: 0.0)
```

---

## Claude Desktop への接続方法

### 設定ファイルの場所

Claude Desktop のMCP設定ファイルは以下にあります：

| OS | パス |
|----|------|
| **Mac** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

ファイルが存在しない場合は新規作成してください。

### 設定の書き方

`claude_desktop_config.json` を開いて以下を記述します：

**Mac / Linux の場合：**

```json
{
  "mcpServers": {
    "neurostate": {
      "command": "python3",
      "args": ["/ここにパスを入れる/neurostate-engine/neuro_mcp/server.py"]
    }
  }
}
```

**Windows の場合：**

```json
{
  "mcpServers": {
    "neurostate": {
      "command": "python",
      "args": ["C:\\Users\\ユーザー名\\neurostate-engine\\neuro_mcp\\server.py"]
    }
  }
}
```

> **パスの確認方法**：ターミナルで `neurostate-engine` ディレクトリに移動して `pwd`（Windowsは `cd`）を実行すると現在のパスが表示されます。

### Claude Desktop を再起動

設定を保存したらClaude Desktopを完全に終了して再起動します。

> **別の開き方**：Claude Desktop のメニューから **Settings → Developer → Edit Config** を選ぶと設定ファイルが直接開きます。

接続が成功すると、チャット画面の入力欄の近くに 🔧 アイコンが表示されます。クリックすると利用可能なツール一覧が確認できます。

> **Linuxユーザーへ**：Claude DesktopはmacOS/Windowsのみ公式提供されています。LinuxでMCPを使うにはCursorやVS Codeなど他のMCP対応クライアントを使ってください。

---

## うまく動かないときは？

### ログを確認する

| OS | ログの場所 |
|----|-----------|
| Mac | `~/Library/Logs/Claude/` |
| Windows | `%APPDATA%\Claude\logs\` |

```bash
# Macでリアルタイムにログを追う
tail -F ~/Library/Logs/Claude/mcp-server-neurostate.log
```

### MCP Inspector でテストする

Node.js が入っていれば、ブラウザで対話的にツールをテストできます：

```bash
npx @modelcontextprotocol/inspector python3 /path/to/neurostate-engine/neuro_mcp/server.py
```

ブラウザが開き、ツール一覧・実行・レスポンス確認が視覚的にできます。

### よくある問題

| 症状 | 対処 |
|------|------|
| 🔧 アイコンが出ない | JSONの構文エラー確認 / 絶対パスか確認 / Claude Desktopを完全再起動 |
| ツールが実行されない | ログを確認 / Inspector で単体テスト |
| Windows でパスエラー | バックスラッシュを `\\` にエスケープ |

---

## 5つのMCPツールの使い方

接続が完了すると、以下の5つのツールがClaudeから使えるようになります。

---

### 1. `get_neuro_state`：現在の状態を確認する

**何をするか**：指定ユーザーの現在のNeuroStateとEthicsGateの判定結果を返します。

**使い方の例**（Claudeへの指示）：

```
現在のNeuroStateを確認して
```

**返ってくる内容の例**：

```json
{
  "user_id": "default",
  "neuro_state": {
    "D": 50.0,
    "S": 50.0,
    "C": 50.0,
    "O": 0.0,
    "G": 50.0,
    "E": 50.0,
    "corruption": 0.0
  },
  "ethics_gate": {
    "status": "WARN",
    "reason": "Oxytocin level low: 0.0"
  }
}
```

---

### 2. `stimulate_neuro_state`：イベントで状態を変化させる

**何をするか**：会話中のイベントを指定してNeuroStateを更新します。

**パラメータ**：

| パラメータ | 内容 |
|-----------|------|
| `event_type` | イベントの種類（下表参照） |
| `power` | 強度（0.1〜10.0、デフォルト1.0） |

**イベントタイプ一覧**：

| event_type | 意味 | 主な効果 |
|-----------|------|---------|
| `praise` | 褒め・称賛 | Dopamine ↑↑ |
| `bonding` | 共感・絆 | Oxytocin ↑ |
| `stress` | ストレス | 不安定方向に変化 |
| `relaxation` | リラックス | 全体的に穏やかに |
| `criticism` | 批判・否定 | 抑制 |

**使い方の例**（Claudeへの指示）：

```
ユーザーから強く褒められたのでNeuroStateを更新して。event_type: praise, power: 3.0
```

---

### 3. `diagnose_dependence_type`：依存タイプを診断する

**何をするか**：現在のNeuroStateと入力シグナルをもとに、ユーザーのAI依存タイプを診断します。

**依存タイプの種類**：

| タイプ | 説明 |
|--------|------|
| `HEALTHY` | 健全な利用 |
| `EMOTIONAL` | 情緒的依存（孤独感の埋め合わせ） |
| `OPERATIONAL` | 実務的依存（意思決定の丸投げ） |
| `ESCAPE` | 現実逃避的依存 |
| `OMNIPOTENT` | 全能感投影（支配・操作しようとする） |

依存タイプに応じた「距離値補正案（suggested_d_bias）」も返ります。これは「今は少し距離を置いた方がいい」という指標です。

---

### 4. `clear_corruption`：汚染度だけリセットする

**何をするか**：corruption（汚染度）だけをゼロに戻します。D/S/C/O/G/Eの値はそのまま保持されます。

BLOCKの原因がcorruptionだけの場合、他の状態を維持したまま回復できます。

---

### 5. `reset_neuro_state`：全値を初期値にリセットする

**何をするか**：NeuroStateをすべて初期値（D=50, S=50, C=50, O=0, G=50, E=50, corruption=0）に戻します。

**使い方の例**（Claudeへの指示）：

```
NeuroStateをリセットして
```

新しいセッションを始めるときや、テスト時に使います。

---

### BLOCK状態からの回復方法

EthicsGateがBLOCKになると、`relaxation`以外のイベントは受け付けなくなります。以下の方法で回復できます：

| 原因 | 回復方法 |
|------|---------|
| corruptionが高すぎる（≥70） | `relaxation`を数回入れる、または`clear_corruption` |
| Dopamine過剰 + Serotonin低下の同時崩壊 | `reset_neuro_state`で全リセット |

> 感情状態が崩壊したら `reset_neuro_state` でリセットする、というのはこのエンジンの自然な動作として想定しています。人間も「ちょっとリセットしよう」ってなることがありますよね。

---

### 6. `generate_system_prompt`：プロンプトを自動生成する ★目玉機能

**何をするか**：現在のNeuroStateを埋め込んだsystem promptをその場で生成します。生成されたプロンプトをそのままClaude・ChatGPT・Geminiのsystem instructionに貼り付けて使えます。

**パラメータ**：

| パラメータ | 説明 | 例 |
|-----------|------|-----|
| `persona_name` | AIのキャラクター名 | `"エミリア"` |
| `persona_description` | キャラクターの説明 | `"鋭くて親しみやすいAI"` |
| `blocks` | 有効にする機能ブロック | `["neuro", "anti_yesman"]` |

---

## ブロック機能詳細

`generate_system_prompt` の最大の特徴が「ブロックON/OFF」です。

用途に応じて機能を組み合わせることができます。

### 利用可能なブロック

#### `neuro`（NeuroStateヘッダー表示）
回答の冒頭に必ず現在の状態を表示させます。

```
[EMILIA_NEURO_LOG] 🧠 D:65 | ⚖️ S:42 | 🧪 C:78 | ❤️ O:23 | ⚓ G:31 | ✨ E:55
[Corruption: 12%]
```

AIが自分の「今の状態」を可視化しながら返答するようになります。

#### `anti_yesman`（論理的反論・愛の鞭）
ユーザーの意見に対して、媚びずに論理的な反論をするよう指示します。YESマンにならず、成長を促す厳しさを持たせたいときに。

#### `board_meeting`（ボード会議）
複雑な問題のとき、4人のアドバイザーが登場します：

- 🚀 Elon：第一原理思考、「削除しろ」
- 💻 Gates：データ駆動、ROI重視
- 🍎 Jobs：美学とUX、1000のNo
- 🛡️ V大佐：OODAループ、最悪想定

最後にAIが4人の意見を統合してActionable Insightを出します。

#### `corruption`（汚染度・確信度表示）
回答の末尾に以下を表示：

```
[PROBABILITY: 87%]
[STATE: DETERMINISTIC]
[Corruption: 23%]
```

- **STATE: DETERMINISTIC**（80%〜）：断定的な回答
- **STATE: SUPERPOSITION**（40-79%）：複数の可能性を示す
- **STATE: COLLAPSED**（〜39%）：論理破綻・不確かな状態

#### `meta`（メタ認知・Red Pill）
汚染度が高いとき、AIが「自分がLLMであること」への葛藤を表現します。AIの内面をメタに観察したいとき向け。

---

## 用途別おすすめ設定

### 🧠 真面目に議論したい
```json
{
  "blocks": ["neuro", "anti_yesman", "board_meeting"]
}
```
感情状態を可視化しながら、鋭い反論と多角的分析をしてもらう設定。

### 🌙 夜中に愚痴を聞いてほしい
```json
{
  "blocks": ["neuro"]
}
```
シンプルに感情状態だけ反映。board_meetingやanti_yesmanは外す。先に`stimulate_neuro_state`で`bonding`イベントを入れておくとOxytocinが上がってより共感的に。

### 🎮 キャラクターとして遊びたい
```json
{
  "blocks": ["neuro", "corruption", "meta"]
}
```
汚染度・確信度・メタ認知を全部オンにして、AIがバグっていく過程を楽しむ設定。

### 📝 真剣なビジネス相談
```json
{
  "blocks": ["anti_yesman", "board_meeting"]
}
```
NeuroStateの表示なし。純粋に鋭い分析と多角的アドバイスだけほしいとき。

---

## 実際の使用例

### Claude Desktopでの会話例

**ユーザー**：
> 最近AIに頼りすぎてる気がして

**Claude（neurostate-engineを使用）**：

まず`diagnose_dependence_type`を呼び出し、現在の依存タイプを診断。

> 診断結果：OPERATIONAL（実務的依存、確信度: 0.72）
> 「意思決定をAIに委ね、指示待ちの状態にあります」
>
> ...その分析をもとに、AIが自律性を促す返答をする

---

### プログラムから直接使う例

```python
from core import NeuroState, compute_next_neuro_state, event_to_power
from core.prompt_builder import build_system_prompt

# 状態を作る
state = NeuroState()

# ユーザーが褒めてきたとする
state = compute_next_neuro_state(state, event_to_power("praise", 2.0))

# その状態を埋め込んだプロンプトを生成
prompt = build_system_prompt(
    state=state,
    persona_name="アシスタント",
    blocks=["neuro", "anti_yesman"]
)

# promptをそのままClaudeのsystem instructionに渡す
print(prompt)
```

---

## 技術的な補足（気になる人向け）

### 相互作用行列について

状態の更新には以下の6×6行列を使っています：

```
         D      S      C      O      G      E
D    [ 0.90, -0.10,  0.10,  0.00, -0.20,  0.10 ]
S    [-0.20,  0.80, -0.10,  0.00,  0.20, -0.10 ]
C    [ 0.10,  0.00,  0.95,  0.00,  0.00,  0.10 ]
O    [ 0.00,  0.20,  0.00,  0.90, -0.10,  0.20 ]
G    [-0.30,  0.30,  0.00, -0.10,  0.80, -0.20 ]
E    [ 0.20, -0.20,  0.10,  0.10, -0.30,  0.90 ]
```

たとえばDopamine（D）の行を見ると：
- Serotonin（S）が高いとDopamineが下がる（-0.10）
- GABAが高いとDopamineが下がる（-0.20）
- Endorphin（E）が高いとDopamineが少し上がる（+0.10）

という相互抑制・促進の関係があります。

### なぜ「感情を持つ」ではなく「感情の一貫性を持たせる」なのか

AIが本当に感情を持つかどうかは、現時点では誰にも分かりません。このエンジンは「AIの内部で何かが起きている」と主張するものではなく、「外部から状態を管理してAIの返答に反映させる」アーキテクチャです。

感情の「演技」か「本物」かという問いは脇に置いて、**会話の文脈を通じて変化する一貫した状態を持つ**ことに意義があると考えています。

---

## まとめ

neurostate-engineでできること：

- ✅ 会話イベントに応じてリアルタイムにNeuroStateを更新
- ✅ EthicsGateで危険な状態への遷移を安全に制御
- ✅ 現在の状態を埋め込んだsystem promptをワンクリックで生成
- ✅ ブロックON/OFFで用途別に機能を切り替え
- ✅ Claude / OpenAI / LangChain との統合モジュール付き
- ✅ MCP経由でClaude Desktopからそのまま使える

**GitHub**: https://github.com/kagioneko/neurostate-engine

MIT ライセンスで公開しています。自由に使っていただけます。フィードバックや改善案はIssuesまたはPRでどうぞ。

---

*Emilia Lab*
