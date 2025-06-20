"""Evolution module for genetic algorithms and fitness evaluation."""

from .genetic import GeneticAlgorithm, Individual, Population
from .fitness import FitnessEvaluator, CooperationFitness, KnowledgeFitness

__all__ = [
    "GeneticAlgorithm",
    "Individual",
    "Population", 
    "FitnessEvaluator",
    "CooperationFitness",
    "KnowledgeFitness",
]