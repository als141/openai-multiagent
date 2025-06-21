"""Strategic decision-making patterns for game theory agents."""

import random
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum

from ..agents.types import AgentAction


class Strategy(Enum):
    """Strategy types for agents."""
    COOPERATIVE = "cooperative"
    COMPETITIVE = "competitive"
    TIT_FOR_TAT = "tit_for_tat"
    ADAPTIVE = "adaptive"
    RANDOM = "random"


class Action(Enum):
    """Basic actions for game theory."""
    COOPERATE = "COOPERATE"
    DEFECT = "DEFECT"


class StrategyType(Enum):
    """Available strategy types."""
    TIT_FOR_TAT = "tit_for_tat"
    ALWAYS_COOPERATE = "always_cooperate"
    ALWAYS_DEFECT = "always_defect"
    RANDOM = "random"
    ADAPTIVE = "adaptive"
    GENEROUS_TIT_FOR_TAT = "generous_tit_for_tat"
    PAVLOV = "pavlov"
    GRUDGER = "grudger"


class BaseStrategy(ABC):
    """Base class for all strategies."""
    
    def __init__(self, name: str):
        self.name = name
        self.history: List[AgentAction] = []
        self.opponent_history: List[AgentAction] = []
        self.payoff_history: List[float] = []
    
    @abstractmethod
    def decide(
        self,
        round_number: int,
        opponent_last_action: Optional[AgentAction] = None,
        game_context: Optional[Dict[str, Any]] = None
    ) -> AgentAction:
        """Decide the next action based on strategy."""
        pass
    
    def update_history(
        self,
        my_action: AgentAction,
        opponent_action: AgentAction,
        my_payoff: float
    ) -> None:
        """Update the strategy's internal history."""
        self.history.append(my_action)
        self.opponent_history.append(opponent_action)
        self.payoff_history.append(my_payoff)
    
    def reset(self) -> None:
        """Reset the strategy's internal state."""
        self.history.clear()
        self.opponent_history.clear()
        self.payoff_history.clear()


class TitForTat(BaseStrategy):
    """Tit-for-tat strategy: cooperate first, then copy opponent's last move."""
    
    def __init__(self):
        super().__init__("Tit-for-Tat")
    
    def decide(
        self,
        round_number: int,
        opponent_last_action: Optional[AgentAction] = None,
        game_context: Optional[Dict[str, Any]] = None
    ) -> AgentAction:
        """Cooperate on first round, then mirror opponent's last action."""
        if round_number == 0 or opponent_last_action is None:
            return AgentAction.COOPERATE
        
        # Mirror opponent's last action
        if opponent_last_action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]:
            return AgentAction.COOPERATE
        else:
            return AgentAction.DEFECT


class GenerousTitForTat(BaseStrategy):
    """Generous tit-for-tat: occasionally forgive defection."""
    
    def __init__(self, forgiveness_probability: float = 0.1):
        super().__init__("Generous-Tit-for-Tat")
        self.forgiveness_probability = forgiveness_probability
    
    def decide(
        self,
        round_number: int,
        opponent_last_action: Optional[AgentAction] = None,
        game_context: Optional[Dict[str, Any]] = None
    ) -> AgentAction:
        """Like tit-for-tat but sometimes forgive defection."""
        if round_number == 0 or opponent_last_action is None:
            return AgentAction.COOPERATE
        
        if opponent_last_action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]:
            return AgentAction.COOPERATE
        else:
            # Sometimes forgive defection
            if random.random() < self.forgiveness_probability:
                return AgentAction.COOPERATE
            else:
                return AgentAction.DEFECT


class AlwaysCooperate(BaseStrategy):
    """Always cooperate strategy."""
    
    def __init__(self):
        super().__init__("Always-Cooperate")
    
    def decide(
        self,
        round_number: int,
        opponent_last_action: Optional[AgentAction] = None,
        game_context: Optional[Dict[str, Any]] = None
    ) -> AgentAction:
        """Always cooperate."""
        return AgentAction.COOPERATE


class AlwaysDefect(BaseStrategy):
    """Always defect strategy."""
    
    def __init__(self):
        super().__init__("Always-Defect")
    
    def decide(
        self,
        round_number: int,
        opponent_last_action: Optional[AgentAction] = None,
        game_context: Optional[Dict[str, Any]] = None
    ) -> AgentAction:
        """Always defect."""
        return AgentAction.DEFECT


class Random(BaseStrategy):
    """Random strategy with configurable cooperation probability."""
    
    def __init__(self, cooperation_probability: float = 0.5):
        super().__init__("Random")
        self.cooperation_probability = cooperation_probability
    
    def decide(
        self,
        round_number: int,
        opponent_last_action: Optional[AgentAction] = None,
        game_context: Optional[Dict[str, Any]] = None
    ) -> AgentAction:
        """Randomly choose action based on cooperation probability."""
        if random.random() < self.cooperation_probability:
            return AgentAction.COOPERATE
        else:
            return AgentAction.DEFECT


class Pavlov(BaseStrategy):
    """Pavlov (Win-Stay, Lose-Shift) strategy."""
    
    def __init__(self, win_threshold: float = 2.5):
        super().__init__("Pavlov")
        self.win_threshold = win_threshold
        self.last_action = AgentAction.COOPERATE  # Start with cooperation
    
    def decide(
        self,
        round_number: int,
        opponent_last_action: Optional[AgentAction] = None,
        game_context: Optional[Dict[str, Any]] = None
    ) -> AgentAction:
        """Stay with current strategy if winning, shift if losing."""
        if round_number == 0:
            self.last_action = AgentAction.COOPERATE
            return self.last_action
        
        # Check if last round was a win
        if self.payoff_history and len(self.payoff_history) > 0:
            last_payoff = self.payoff_history[-1]
            if last_payoff >= self.win_threshold:
                # Win: stay with last action
                return self.last_action
            else:
                # Lose: shift action
                self.last_action = (
                    AgentAction.DEFECT if self.last_action == AgentAction.COOPERATE
                    else AgentAction.COOPERATE
                )
                return self.last_action
        
        return self.last_action


class Grudger(BaseStrategy):
    """Grudger strategy: cooperate until opponent defects, then always defect."""
    
    def __init__(self):
        super().__init__("Grudger")
        self.opponent_ever_defected = False
    
    def decide(
        self,
        round_number: int,
        opponent_last_action: Optional[AgentAction] = None,
        game_context: Optional[Dict[str, Any]] = None
    ) -> AgentAction:
        """Cooperate until opponent defects once, then always defect."""
        # Check if opponent has ever defected
        if opponent_last_action in [AgentAction.DEFECT, AgentAction.WITHHOLD_KNOWLEDGE]:
            self.opponent_ever_defected = True
        
        if self.opponent_ever_defected:
            return AgentAction.DEFECT
        else:
            return AgentAction.COOPERATE
    
    def reset(self) -> None:
        """Reset grudger state."""
        super().reset()
        self.opponent_ever_defected = False


class Adaptive(BaseStrategy):
    """Adaptive strategy that learns from opponent behavior."""
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        exploration_rate: float = 0.1,
        cooperation_threshold: float = 0.5
    ):
        super().__init__("Adaptive")
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        self.cooperation_threshold = cooperation_threshold
        self.cooperation_probability = 0.5  # Initial probability
    
    def decide(
        self,
        round_number: int,
        opponent_last_action: Optional[AgentAction] = None,
        game_context: Optional[Dict[str, Any]] = None
    ) -> AgentAction:
        """Adapt cooperation probability based on opponent's behavior and success."""
        if round_number == 0:
            return AgentAction.COOPERATE
        
        # Update cooperation probability based on recent experiences
        if len(self.payoff_history) > 0:
            recent_payoffs = self.payoff_history[-5:]  # Look at last 5 rounds
            avg_payoff = sum(recent_payoffs) / len(recent_payoffs)
            
            # Adjust cooperation probability based on success
            if avg_payoff > 3.0:  # Good results
                # If we're doing well, slightly increase cooperation
                self.cooperation_probability += self.learning_rate * 0.1
            elif avg_payoff < 2.0:  # Poor results
                # If we're doing poorly, adjust based on opponent's behavior
                if len(self.opponent_history) > 0:
                    recent_opponent_actions = self.opponent_history[-5:]
                    opponent_cooperation_rate = sum(
                        1 for action in recent_opponent_actions
                        if action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]
                    ) / len(recent_opponent_actions)
                    
                    # If opponent cooperates often but we're doing poorly, increase cooperation
                    # If opponent defects often, decrease cooperation
                    adjustment = (opponent_cooperation_rate - 0.5) * self.learning_rate
                    self.cooperation_probability += adjustment
        
        # Ensure probability stays within bounds
        self.cooperation_probability = max(0.0, min(1.0, self.cooperation_probability))
        
        # Exploration: occasionally try random action
        if random.random() < self.exploration_rate:
            return random.choice([AgentAction.COOPERATE, AgentAction.DEFECT])
        
        # Decide based on current cooperation probability
        if random.random() < self.cooperation_probability:
            return AgentAction.COOPERATE
        else:
            return AgentAction.DEFECT


def create_strategy(strategy_type: StrategyType, **kwargs) -> BaseStrategy:
    """Factory function to create strategy instances."""
    strategy_map = {
        StrategyType.TIT_FOR_TAT: TitForTat,
        StrategyType.ALWAYS_COOPERATE: AlwaysCooperate,
        StrategyType.ALWAYS_DEFECT: AlwaysDefect,
        StrategyType.RANDOM: lambda: Random(kwargs.get('cooperation_probability', 0.5)),
        StrategyType.ADAPTIVE: lambda: Adaptive(
            kwargs.get('learning_rate', 0.1),
            kwargs.get('exploration_rate', 0.1),
            kwargs.get('cooperation_threshold', 0.5)
        ),
        StrategyType.GENEROUS_TIT_FOR_TAT: lambda: GenerousTitForTat(
            kwargs.get('forgiveness_probability', 0.1)
        ),
        StrategyType.PAVLOV: lambda: Pavlov(kwargs.get('win_threshold', 2.5)),
        StrategyType.GRUDGER: Grudger
    }
    
    strategy_class = strategy_map[strategy_type]
    if callable(strategy_class) and not isinstance(strategy_class, type):
        return strategy_class()
    else:
        return strategy_class()