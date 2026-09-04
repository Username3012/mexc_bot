import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate

class TestAnalyzer:
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)
    
    def generate_report(self, stats):
        lines = []
        lines.append("=" * 60)
        lines.append("MEXC TRADING BOT - TEST RESULTS REPORT")
        lines.append("=" * 60)
        lines.append(f"Test Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append("")
        
        if not stats or stats.get('total_trades', 0) == 0:
            lines.append("⚠️ No trades executed during test period.")
            return "\n".join(lines)
        
        lines.append("📊 PERFORMANCE METRICS")
        lines.append("-" * 40)
        lines.append(f"Initial Balance: ${stats.get('initial_balance', 0):.2f}")
        lines.append(f"Current Balance: ${stats.get('current_balance', 0):.2f}")
        lines.append(f"Total PnL: ${stats.get('total_pnl', 0):.2f}")
        lines.append(f"Total PnL %: {stats.get('total_pnl_percent', 0):.2f}%")
        lines.append("")
        
        lines.append("📈 TRADE STATISTICS")
        lines.append("-" * 40)
        lines.append(f"Total Trades: {stats.get('total_trades', 0)}")
        lines.append(f"Winning Trades: {stats.get('winning_trades', 0)}")
        lines.append(f"Losing Trades: {stats.get('losing_trades', 0)}")
        lines.append(f"Win Rate: {stats.get('win_rate', 0):.1f}%")
        lines.append("")
        
        if stats.get('total_pnl', 0) > 0 and stats.get('win_rate', 0) > 55:
            lines.append("✅ STRATEGY PERFORMING WELL")
            lines.append("   Consider moving to live trading with small capital")
        else:
            lines.append("⚠️ STRATEGY NEEDS IMPROVEMENT")
            lines.append("   Continue testing and adjust parameters")
        
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def create_visualization(self, trades):
        # Простая версия без сложных графиков
        pass