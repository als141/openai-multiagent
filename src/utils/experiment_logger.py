"""Enhanced experiment logging and debugging system."""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import traceback

import numpy as np


class ExperimentLogger:
    """Enhanced logger for research experiments."""
    
    def __init__(self, experiment_id: str, results_dir: str = "results"):
        self.experiment_id = experiment_id
        self.results_dir = Path(results_dir)
        self.experiment_dir = self.results_dir / f"experiment_{experiment_id}"
        self.logs_dir = self.experiment_dir / "logs"
        
        # Create directories
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup loggers
        self.main_logger = self._setup_logger("main", "experiment.log")
        self.debug_logger = self._setup_logger("debug", "debug.log", level=logging.DEBUG)
        self.error_logger = self._setup_logger("error", "errors.log", level=logging.ERROR)
        
        # Experiment metadata
        self.metadata = {
            "experiment_id": experiment_id,
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "phases": [],
            "errors": [],
            "warnings": [],
            "performance_metrics": {}
        }
        
        self.start_time = datetime.now()
        self.phase_timings = {}
        
    def _setup_logger(self, name: str, filename: str, level: int = logging.INFO) -> logging.Logger:
        """Setup a logger with file handler."""
        logger = logging.getLogger(f"{self.experiment_id}_{name}")
        logger.setLevel(level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(self.logs_dir / filename, encoding='utf-8')
        file_handler.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        return logger
    
    def start_phase(self, phase_name: str, description: str = "") -> None:
        """Start a new experiment phase."""
        phase_start = datetime.now()
        self.phase_timings[phase_name] = {"start": phase_start, "end": None}
        
        phase_info = {
            "name": phase_name,
            "description": description,
            "start_time": phase_start.isoformat(),
            "status": "running"
        }
        
        self.metadata["phases"].append(phase_info)
        self.main_logger.info(f"Starting phase: {phase_name} - {description}")
    
    def end_phase(self, phase_name: str, results: Optional[Dict[str, Any]] = None) -> None:
        """End an experiment phase."""
        phase_end = datetime.now()
        
        if phase_name in self.phase_timings:
            self.phase_timings[phase_name]["end"] = phase_end
            duration = (phase_end - self.phase_timings[phase_name]["start"]).total_seconds()
            
            # Update metadata
            for phase in self.metadata["phases"]:
                if phase["name"] == phase_name and phase["status"] == "running":
                    phase["end_time"] = phase_end.isoformat()
                    phase["duration_seconds"] = duration
                    phase["status"] = "completed"
                    if results:
                        phase["results_summary"] = results
                    break
            
            self.main_logger.info(f"Completed phase: {phase_name} (Duration: {duration:.2f}s)")
        else:
            self.main_logger.warning(f"Attempted to end unknown phase: {phase_name}")
    
    def log_agent_interaction(
        self,
        agent1_name: str,
        agent2_name: str,
        game_type: str,
        round_number: int,
        actions: Dict[str, str],
        payoffs: Dict[str, float],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log detailed agent interaction."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "agent1": agent1_name,
            "agent2": agent2_name,
            "game_type": game_type,
            "round": round_number,
            "actions": actions,
            "payoffs": payoffs,
            **(additional_data or {})
        }
        
        self.debug_logger.info(f"Agent interaction: {json.dumps(interaction, indent=2)}")
    
    def log_decision_process(
        self,
        agent_name: str,
        decision_data: Dict[str, Any]
    ) -> None:
        """Log detailed decision-making process."""
        decision_log = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "decision_data": decision_data
        }
        
        self.debug_logger.debug(f"Decision process: {json.dumps(decision_log, indent=2)}")
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """Log error with full traceback."""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        self.metadata["errors"].append(error_info)
        self.error_logger.error(f"Error in {context}: {json.dumps(error_info, indent=2)}")
    
    def log_warning(self, message: str, context: str = "") -> None:
        """Log warning message."""
        warning_info = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context
        }
        
        self.metadata["warnings"].append(warning_info)
        self.main_logger.warning(f"Warning in {context}: {message}")
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "",
        context: str = ""
    ) -> None:
        """Log performance metric."""
        if metric_name not in self.metadata["performance_metrics"]:
            self.metadata["performance_metrics"][metric_name] = []
        
        metric_entry = {
            "timestamp": datetime.now().isoformat(),
            "value": value,
            "unit": unit,
            "context": context
        }
        
        self.metadata["performance_metrics"][metric_name].append(metric_entry)
        self.main_logger.info(f"Performance metric - {metric_name}: {value} {unit} ({context})")
    
    def save_experiment_state(self, state_data: Dict[str, Any]) -> None:
        """Save current experiment state."""
        state_file = self.experiment_dir / "experiment_state.json"
        
        full_state = {
            "metadata": self.metadata,
            "state_data": state_data,
            "saved_at": datetime.now().isoformat()
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(full_state, f, indent=2, ensure_ascii=False, default=str)
    
    def save_detailed_results(self, results: Dict[str, Any]) -> None:
        """Save detailed experiment results."""
        # Main results file
        results_file = self.experiment_dir / "detailed_results.json"
        
        detailed_results = {
            "experiment_metadata": self.metadata,
            "results": results,
            "analysis": self._generate_analysis(results),
            "saved_at": datetime.now().isoformat()
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Summary file
        summary_file = self.experiment_dir / "experiment_summary.json"
        summary = self._generate_summary(results)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    
    def _generate_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis of experimental results."""
        analysis = {
            "experiment_duration": self._calculate_total_duration(),
            "phase_performance": self._analyze_phase_performance(),
            "error_analysis": self._analyze_errors(),
            "performance_summary": self._summarize_performance_metrics()
        }
        
        # Game-specific analysis
        if "results" in results:
            for game_type, game_results in results["results"].items():
                if game_results:
                    analysis[f"{game_type}_analysis"] = self._analyze_game_results(game_results)
        
        return analysis
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate experiment summary."""
        return {
            "experiment_id": self.experiment_id,
            "status": self.metadata["status"],
            "duration": self._calculate_total_duration(),
            "total_phases": len(self.metadata["phases"]),
            "total_errors": len(self.metadata["errors"]),
            "total_warnings": len(self.metadata["warnings"]),
            "key_metrics": self._extract_key_metrics(results),
            "recommendations": self._generate_recommendations()
        }
    
    def _calculate_total_duration(self) -> float:
        """Calculate total experiment duration."""
        if self.metadata["status"] == "completed":
            end_time = datetime.fromisoformat(self.metadata.get("end_time", datetime.now().isoformat()))
        else:
            end_time = datetime.now()
        
        return (end_time - self.start_time).total_seconds()
    
    def _analyze_phase_performance(self) -> Dict[str, Any]:
        """Analyze performance of each phase."""
        phase_analysis = {}
        
        for phase in self.metadata["phases"]:
            if "duration_seconds" in phase:
                phase_analysis[phase["name"]] = {
                    "duration": phase["duration_seconds"],
                    "status": phase["status"],
                    "efficiency": self._calculate_phase_efficiency(phase)
                }
        
        return phase_analysis
    
    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns."""
        if not self.metadata["errors"]:
            return {"total_errors": 0, "error_types": {}}
        
        error_types = {}
        for error in self.metadata["errors"]:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.metadata["errors"]),
            "error_types": error_types,
            "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
        }
    
    def _summarize_performance_metrics(self) -> Dict[str, Any]:
        """Summarize performance metrics."""
        summary = {}
        
        for metric_name, entries in self.metadata["performance_metrics"].items():
            values = [entry["value"] for entry in entries]
            if values:
                summary[metric_name] = {
                    "count": len(values),
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "unit": entries[0].get("unit", "")
                }
        
        return summary
    
    def _analyze_game_results(self, game_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze results for a specific game type."""
        if not game_results:
            return {}
        
        # Extract payoffs and cooperation rates
        all_payoffs = {}
        all_cooperation_rates = {}
        
        for result in game_results:
            for agent, payoff in result.get("payoffs", {}).items():
                if agent not in all_payoffs:
                    all_payoffs[agent] = []
                all_payoffs[agent].append(payoff)
            
            for agent, coop_rate in result.get("cooperation_rates", {}).items():
                if agent not in all_cooperation_rates:
                    all_cooperation_rates[agent] = []
                all_cooperation_rates[agent].append(coop_rate)
        
        # Calculate statistics
        analysis = {
            "total_games": len(game_results),
            "agent_performance": {}
        }
        
        for agent in all_payoffs:
            payoffs = all_payoffs[agent]
            coop_rates = all_cooperation_rates.get(agent, [])
            
            analysis["agent_performance"][agent] = {
                "average_payoff": np.mean(payoffs),
                "payoff_std": np.std(payoffs),
                "average_cooperation_rate": np.mean(coop_rates) if coop_rates else 0,
                "win_rate": sum(1 for result in game_results if result.get("winner") == agent) / len(game_results)
            }
        
        return analysis
    
    def _calculate_phase_efficiency(self, phase: Dict[str, Any]) -> str:
        """Calculate phase efficiency rating."""
        duration = phase.get("duration_seconds", 0)
        
        if duration < 10:
            return "excellent"
        elif duration < 30:
            return "good"
        elif duration < 60:
            return "fair"
        else:
            return "slow"
    
    def _extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from results."""
        key_metrics = {}
        
        if "results" in results:
            for game_type, game_results in results["results"].items():
                if game_results:
                    # Calculate overall cooperation rate
                    total_cooperation_rate = 0
                    count = 0
                    
                    for result in game_results:
                        for coop_rate in result.get("cooperation_rates", {}).values():
                            total_cooperation_rate += coop_rate
                            count += 1
                    
                    if count > 0:
                        key_metrics[f"{game_type}_avg_cooperation"] = total_cooperation_rate / count
        
        return key_metrics
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on experiment results."""
        recommendations = []
        
        # Performance recommendations
        if len(self.metadata["errors"]) > 0:
            recommendations.append("Consider investigating and fixing errors to improve reliability")
        
        if len(self.metadata["warnings"]) > 5:
            recommendations.append("High number of warnings detected - review experiment configuration")
        
        # Phase duration recommendations
        slow_phases = [
            phase["name"] for phase in self.metadata["phases"]
            if phase.get("duration_seconds", 0) > 60
        ]
        
        if slow_phases:
            recommendations.append(f"Consider optimizing slow phases: {', '.join(slow_phases)}")
        
        if not recommendations:
            recommendations.append("Experiment completed successfully with no major issues detected")
        
        return recommendations
    
    def finalize_experiment(self) -> None:
        """Finalize experiment and save all logs."""
        self.metadata["status"] = "completed"
        self.metadata["end_time"] = datetime.now().isoformat()
        self.metadata["total_duration"] = self._calculate_total_duration()
        
        # Save final metadata
        metadata_file = self.experiment_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False, default=str)
        
        self.main_logger.info(f"Experiment {self.experiment_id} finalized")
    
    def export_logs_csv(self) -> None:
        """Export logs to CSV format for analysis."""
        import csv
        
        # Export performance metrics
        if self.metadata["performance_metrics"]:
            metrics_file = self.experiment_dir / "performance_metrics.csv"
            
            with open(metrics_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'metric_name', 'value', 'unit', 'context']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for metric_name, entries in self.metadata["performance_metrics"].items():
                    for entry in entries:
                        writer.writerow({
                            'timestamp': entry['timestamp'],
                            'metric_name': metric_name,
                            'value': entry['value'],
                            'unit': entry['unit'],
                            'context': entry['context']
                        })
        
        # Export errors
        if self.metadata["errors"]:
            errors_file = self.experiment_dir / "errors.csv"
            
            with open(errors_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'error_type', 'error_message', 'context']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for error in self.metadata["errors"]:
                    writer.writerow({
                        'timestamp': error['timestamp'],
                        'error_type': error['error_type'],
                        'error_message': error['error_message'],
                        'context': error['context']
                    })