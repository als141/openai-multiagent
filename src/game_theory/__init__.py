"""Game theory module for multi-agent interactions."""

from .games import PrisonersDilemma, PublicGoodsGame, KnowledgeSharingGame
from .strategies import TitForTat, AlwaysCooperate, AlwaysDefect, Random, Adaptive
from .payoff import PayoffCalculator, RewardMatrix

__all__ = [
    "PrisonersDilemma",
    "PublicGoodsGame", 
    "KnowledgeSharingGame",
    "TitForTat",
    "AlwaysCooperate",
    "AlwaysDefect",
    "Random",
    "Adaptive",
    "PayoffCalculator",
    "RewardMatrix",
]