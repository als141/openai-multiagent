# Game Theory Multi-Agent System

A research framework for cooperative knowledge evolution and emergent problem-solving through game theory-based multi-agent interactions.

## Features

- **Game Theory Interactions**: Prisoner's Dilemma, Public Goods Game, Knowledge Sharing Game
- **Diverse Agent Strategies**: Cooperative, Competitive, Tit-for-Tat, Adaptive, Random
- **Knowledge Sharing**: Dynamic trust evaluation and knowledge exchange mechanisms
- **Comprehensive Analysis**: Real-time statistics and interactive result visualization
- **Experiment Framework**: Tournament-style strategy comparison and evolution analysis

## Quick Start

### 1. Setup Environment

```bash
# Create Python environment (3.12+ recommended)
uv venv
source .venv/bin/activate  # Linux/Mac

# Install dependencies
uv sync
```

### 2. Configure Environment

Set your OpenAI API key in `.env` file:

```bash
OPENAI_API_KEY=your-api-key-here
```

### 3. Run Demo

```bash
# Run quick demo
python main.py demo

# Run specific game
python main.py game prisoners_dilemma Alice_cooperative Bob_competitive --rounds 15

# Run custom experiment
python main.py experiment --games prisoners_dilemma knowledge_sharing --agents Alice_cooperative Bob_competitive Charlie_tit_for_tat --rounds 20 --repetitions 3
```

## Available Games

1. **Prisoner's Dilemma**: Classic cooperation/defection strategy game
2. **Public Goods Game**: Collective contribution and benefit distribution
3. **Knowledge Sharing Game**: Knowledge sharing with cost-benefit tradeoffs

## Agent Strategies

- **Cooperative**: Always chooses to cooperate
- **Competitive**: Generally non-cooperative, cooperates only with high trust
- **Tit-for-Tat**: Mirrors opponent's last action, starts with cooperation
- **Adaptive**: Adapts strategy based on success rate and opponent behavior
- **Random**: Random choice for baseline comparison

## Project Structure

```
src/
├── agents/           # Agent implementations
├── game_theory/      # Game theory implementations
├── utils/            # Utilities (logging, visualization)
experiments/          # Experiment scripts
tests/                # Test code
results/              # Experiment results
logs/                 # Log files
```

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific tests
uv run pytest tests/test_agents.py -v

# Coverage report
uv run pytest --cov=src tests/
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit pull requests.