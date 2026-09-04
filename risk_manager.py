from dataclasses import dataclass

@dataclass
class PositionSizing:
    amount: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    reward_amount: float
    total_value: float
    risk_reward_ratio: float

class ScalpingRiskManager:
    def __init__(self, config, logger, max_concurrent_positions=2, 
                 sl_percent=0.008, tp_percent=0.015):
        self.config = config
        self.logger = logger
        self.max_concurrent_positions = max_concurrent_positions
        self.sl_percent = sl_percent
        self.tp_percent = tp_percent
        self.daily_loss_triggered = False
        self.open_positions = {}
        self.daily_pnl = 0.0
    
    def calculate_position_size(self, balance, current_price, volatility=None):
        if balance <= 0 or current_price <= 0:
            return None
        
        if self.daily_loss_triggered:
            return None
        
        total_positions = sum(len(pos) for pos in self.open_positions.values())
        if total_positions >= self.max_concurrent_positions:
            return None
        
        risk_percent = min(self.config.max_risk_per_trade, 0.02)
        
        stop_loss = current_price * (1 - self.sl_percent)
        take_profit = current_price * (1 + self.tp_percent)
        
        risk_amount = balance * risk_percent
        price_distance = current_price - stop_loss
        if price_distance <= 0:
            return None
        
        position_size = risk_amount / price_distance
        max_size = balance * 0.3 / current_price
        position_size = min(position_size, max_size)
        
        total_value = position_size * current_price
        if total_value < self.config.min_notional:
            return None
        
        actual_risk = position_size * (current_price - stop_loss)
        actual_reward = position_size * (take_profit - current_price)
        risk_reward_ratio = actual_reward / actual_risk if actual_risk > 0 else 0
        
        return PositionSizing(
            amount=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=actual_risk,
            reward_amount=actual_reward,
            total_value=total_value,
            risk_reward_ratio=risk_reward_ratio
        )
    
    def can_open_position(self, symbol):
        if self.daily_loss_triggered:
            return False
        total = sum(len(pos) for pos in self.open_positions.values())
        return total < self.max_concurrent_positions
    
    def update_open_positions(self, symbol, positions):
        if positions:
            self.open_positions[symbol] = positions
        else:
            self.open_positions.pop(symbol, None)