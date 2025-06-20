# 進化的群知能に基づくLoRAエージェント集団の協調的最適化フレームワーク

## プロジェクト概要

本プロジェクトは、「進化的群知能に基づくLoRAエージェント集団の協調的最適化フレームワーク: ゲーム理論的アプローチによる動的知識進化と創発的問題解決」という修士研究の実装です。

### 研究目的
- ゲーム理論に基づき、エージェント同士が知識を進化させ、動的な適応能力を獲得
- メタ認知・意思決定プロセスの透明性を向上
- ゲーム理論的な相互作用を通じて協調的に知識を進化させ、創発的な問題解決能力を実現

### 背景
- 巨大LLMモデルの限界：計算コスト、新知識への適応の低さ、判断根拠の不透明性
- 社会的問題解決には「コミュニケーション」による協調行動が不可欠
- 生物界の群知能や進化メカニズムに着目し、多数の小規模AIエージェントの協力・競争を通じた問題解決

## 技術スタック選定

調査の結果、以下の理由からOpenAI Agents SDKを採用：

### OpenAI Agents SDK（2025年3月リリース）
- **選定理由**：
  - 軽量で学習曲線が緩やか（数行のコードで開始可能）
  - Handoffsによるエージェント間遷移が本研究のゲーム理論的相互作用に最適
  - 100+ LLMサポート（将来的なローカルLLM移行が容易）
  - 内蔵トレーシング機能で意思決定プロセスの透明性を確保
  - プロダクションレディで安定性が高い

### 比較検討したフレームワーク
- **LangGraph**: グラフベースで高度な制御が可能だが、本研究には複雑すぎる
- **Microsoft AutoGen**: GroupStrategyをゲーム理論アルゴリズムに置換可能だが、重量級
- **CrewAI**: イベント駆動で高速だが、ゲーム理論的相互作用の実装が複雑

## プロジェクト構造

```
openai-multiagent/
├── pyproject.toml          # プロジェクト設定と依存関係
├── README.md              # プロジェクト概要
├── CLAUDE.md              # 本ファイル（プロジェクト指示書）
├── main.py                # エントリーポイント
├── src/
│   ├── __init__.py
│   ├── agents/            # エージェント定義
│   │   ├── __init__.py
│   │   ├── base_agent.py  # 基本エージェントクラス
│   │   ├── game_agents.py # ゲーム理論エージェント
│   │   └── coordinator.py # 調整エージェント
│   ├── game_theory/       # ゲーム理論実装
│   │   ├── __init__.py
│   │   ├── games.py       # ゲーム定義（囚人のジレンマ等）
│   │   ├── strategies.py  # 戦略実装（TFT、Win-Stay等）
│   │   └── payoff.py      # 利得計算
│   ├── evolution/         # 進化アルゴリズム
│   │   ├── __init__.py
│   │   ├── genetic.py     # 遺伝的アルゴリズム
│   │   └── fitness.py     # 適応度関数
│   ├── knowledge/         # 知識管理
│   │   ├── __init__.py
│   │   ├── exchange.py    # 知識交換メカニズム
│   │   └── trust.py       # 信頼・評判システム
│   └── utils/             # ユーティリティ
│       ├── __init__.py
│       ├── logger.py      # ロギング
│       └── visualizer.py  # 結果可視化
├── experiments/           # 実験スクリプト
│   ├── __init__.py
│   ├── prisoner_dilemma.py
│   └── coordination_game.py
├── tests/                 # テストコード
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_game_theory.py
│   └── test_evolution.py
└── results/               # 実験結果保存
    └── .gitkeep
```

## 実装アーキテクチャ

### 1. エージェント設計
```python
from agents import Agent, Runner

class GameTheoryAgent(Agent):
    def __init__(self, name, strategy, trust_threshold=0.5):
        super().__init__(
            name=name,
            instructions=f"You are a {strategy} player in game theory scenarios.",
            handoffs=[]  # 動的に設定
        )
        self.strategy = strategy
        self.trust_scores = {}
        self.knowledge_base = []
```

### 2. ゲーム理論的相互作用
- **囚人のジレンマ**: 協力/裏切りの基本的な意思決定
- **公共財ゲーム**: 集団での協調行動の創発
- **知識共有ゲーム**: 情報交換における信頼と競争

### 3. 進化メカニズム
- 各エージェントの戦略を「遺伝子」として扱う
- 適応度に基づく選択・交叉・突然変異
- 世代交代による集団知能の進化

### 4. 創発的問題解決プロセス
1. **タスク掲示と解釈**: 各エージェントが独自に問題を解釈
2. **個別推論と解候補生成**: 各自の知識ベースから解を生成
3. **ゲーム理論的相互作用**: 協力/競争の意思決定
4. **知識交換とコミュニケーション**: 信頼に基づく情報共有
5. **集合的知識統合**: 部分解の統合と最適化
6. **創発性の評価**: 単独では不可能な解の生成を確認

## 実装計画

### フェーズ1: 基礎実装（現在）
- OpenAI Agents SDKを使用した基本的なマルチエージェントシステム
- 囚人のジレンマの実装
- 簡単な知識交換メカニズム

### フェーズ2: ゲーム理論拡張
- 複数のゲーム理論モデルの実装
- 動的戦略選択メカニズム
- 信頼・評判システムの構築

### フェーズ3: 進化アルゴリズム統合
- 遺伝的アルゴリズムによる戦略進化
- 適応度関数の設計と最適化
- 世代交代メカニズム

### フェーズ4: LoRA統合（将来）
- 各エージェントへのLoRAパラメータ割り当て
- LoRAを「遺伝子」とした進化
- ローカルLLMでの実行

## 開発環境セットアップ

```bash
# Python環境の準備（Python 3.12推奨）
uv venv
source .venv/bin/activate  # Linux/Mac
# または
.venv\Scripts\activate  # Windows

# 依存関係のインストール
uv pip install -e .

# 環境変数の設定
export OPENAI_API_KEY="your-api-key"
```

## 実行方法

```bash
# 基本的な実行
python main.py

# 特定の実験を実行
python experiments/prisoner_dilemma.py

# テストの実行
pytest tests/
```

## 評価指標

1. **協調率**: エージェント間の協力行動の頻度
2. **問題解決精度**: タスクの成功率と品質
3. **創発性スコア**: 個別解と集団解の性能差
4. **適応速度**: 新しい問題への対応速度
5. **知識多様性**: エージェント間の知識の多様性

## 注意事項

- APIコストを考慮し、小規模な実験から開始
- トレーシング機能を活用してデバッグ
- 実験結果は`results/`ディレクトリに自動保存
- ゲーム理論パラメータは`config.yaml`で調整可能

## 今後の拡張

1. **Web UIの追加**: 実験の可視化とインタラクティブな操作
2. **ベンチマーク統合**: 標準的な問題セットでの評価
3. **分散実行**: 大規模エージェント集団の並列処理
4. **リアルタイム学習**: オンライン学習メカニズムの実装

## リンクとコマンド

### 開発時の主要コマンド
```bash
# コードフォーマット
uv run black src/ tests/

# 型チェック
uv run mypy src/

# リント
uv run ruff check src/

# テスト実行
uv run pytest tests/ -v

# カバレッジレポート
uv run pytest --cov=src tests/
```

### 参考リンク
- [OpenAI Agents SDK Documentation](https://openai.github.io/openai-agents-python/)
- [OpenAI Agents SDK GitHub](https://github.com/openai/openai-agents-python)
- [Game Theory and MARL Survey](https://arxiv.org/html/2412.20523v1)

## 研究の意義

本研究は、単一の巨大LLMに依存しない、より柔軟で適応的なAIシステムの実現を目指します。生物の進化と群知能の原理を取り入れることで、計算効率と問題解決能力の両立を図り、持続可能なAI技術の発展に貢献します。