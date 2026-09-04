"""Стратегия с анализом исторических данных."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class ScalpingStrategy:
    def __init__(
        self, 
        ema_period=50, 
        rsi_period=14, 
        volume_spike=1.8, 
        lookback_levels=50, 
        min_trend_strength=0.3,
        historical_bars=200
    ):
        self.ema_period = ema_period
        self.rsi_period = rsi_period
        self.volume_spike = volume_spike
        self.lookback_levels = lookback_levels
        self.min_trend_strength = min_trend_strength
        self.historical_bars = historical_bars
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Расчет индикаторов с учетом истории."""
        data = df.copy()
        
        # 1. EMA (тренд)
        data[f'ema_{self.ema_period}'] = data['close'].ewm(
            span=self.ema_period, adjust=False
        ).mean()
        
        # 2. RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # 3. Объем
        data['volume_ma'] = data['volume'].rolling(window=20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_ma']
        
        # 4. ATR (волатильность)
        high = data['high']
        low = data['low']
        close = data['close'].shift(1)
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        data['atr'] = tr.rolling(window=14).mean()
        
        return data
    
    def find_levels(
        self, 
        df: pd.DataFrame, 
        current_price: float
    ) -> Dict[str, float]:
        """Поиск уровней поддержки/сопротивления на истории."""
        data = df.iloc[-self.lookback_levels:].copy()
        
        window = 5
        data['rolling_high'] = data['high'].rolling(window=window, center=True).max()
        data['rolling_low'] = data['low'].rolling(window=window, center=True).min()
        
        pivot_highs = data[data['high'] == data['rolling_high']]['high'].values
        pivot_lows = data[data['low'] == data['rolling_low']]['low'].values
        
        unique_highs = list(set(pivot_highs))
        unique_lows = list(set(pivot_lows))
        
        nearest_resistance = min(
            [h for h in unique_highs if h > current_price], 
            default=current_price * 1.02
        )
        nearest_support = max(
            [l for l in unique_lows if l < current_price], 
            default=current_price * 0.98
        )
        
        if abs(nearest_resistance - current_price) / current_price > 0.05:
            nearest_resistance = current_price * 1.02
        if abs(current_price - nearest_support) / current_price > 0.05:
            nearest_support = current_price * 0.98
        
        return {
            'resistance': nearest_resistance,
            'support': nearest_support
        }
    
    def check_volume_confirmation(
        self, 
        data: pd.DataFrame, 
        price_movement: float
    ) -> bool:
        """Проверка объема для подтверждения движения."""
        last_volume = data['volume_ratio'].iloc[-1]
        
        if last_volume < self.volume_spike:
            return False
        
        volume_trend = data['volume'].iloc[-5:].mean() > data['volume'].iloc[-10:-5].mean()
        
        return volume_trend
    
    def generate_signal(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Генерация сигнала с анализом истории.
        
        Условия для BUY:
        1. Цена выше EMA (восходящий тренд)
        2. RSI > 50 (бычий импульс)
        3. Объем выше среднего
        4. Цена пробила уровень сопротивления ИЛИ отскочила от поддержки
        """
        if len(df) < self.historical_bars:
            return {
                'signal': 'HOLD', 
                'strength': 0.0, 
                'reason': f'need_{self.historical_bars}_bars'
            }
        
        data = self.calculate_indicators(df)
        last = data.iloc[-1]
        prev = data.iloc[-2]
        
        current_price = last['close']
        ema = last[f'ema_{self.ema_period}']
        rsi = last['rsi']
        atr = last['atr']
        
        # --- ТРЕНД ---
        is_uptrend = current_price > ema
        trend_strength = abs(current_price - ema) / ema
        
        # --- УРОВНИ ---
        levels = self.find_levels(data, current_price)
        resistance = levels['resistance']
        support = levels['support']
        
        # --- ПРОБОЙ ---
        breakout_up = (
            prev['close'] < resistance and 
            current_price > resistance * 1.001
        )
        breakout_down = (
            prev['close'] > support and 
            current_price < support * 0.999
        )
        
        # --- ПОДТВЕРЖДЕНИЕ ОБЪЕМОМ ---
        volume_confirmed = self.check_volume_confirmation(data, current_price - prev['close'])
        
        # --- RSI ПОДТВЕРЖДЕНИЕ ---
        rsi_bullish = rsi > 50
        
        # --- СИЛА СИГНАЛА ---
        strength = 0.0
        reason = "no_confirmation"
        
        # --- BUY ---
        if is_uptrend and breakout_up and volume_confirmed and rsi_bullish:
            strength = 0.3
            reason = "breakout_uptrend"
            
            if trend_strength > 0.005:
                strength += 0.2
                reason = "breakout_uptrend_strong"
            
            if rsi > 60:
                strength += 0.2
                reason = "breakout_uptrend_rsi_strong"
            
            if last['volume_ratio'] > 2.0:
                strength += 0.2
                reason = "breakout_uptrend_volume_strong"
            
            if trend_strength < 0.03:
                strength += 0.1
            
            if strength >= 0.6:
                return {
                    'signal': 'BUY',
                    'strength': min(strength, 1.0),
                    'reason': reason,
                    'metadata': {
                        'resistance': resistance,
                        'support': support,
                        'ema': ema,
                        'rsi': rsi,
                        'volume_ratio': last['volume_ratio'],
                        'atr': atr,
                        'trend_strength': trend_strength
                    }
                }
        
        return {
            'signal': 'HOLD',
            'strength': strength,
            'reason': reason,
            'metadata': {
                'trend_strength': trend_strength,
                'rsi': rsi,
                'volume_ratio': last['volume_ratio'] if 'volume_ratio' in last else 1.0
            }
        }
    
    def get_atr(self, df: pd.DataFrame) -> float:
        """Получить текущий ATR."""
        if len(df) < 20:
            return df['high'].iloc[-1] * 0.01
        data = self.calculate_indicators(df)
        return data['atr'].iloc[-1]