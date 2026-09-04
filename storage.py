from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base, Trade, Position, DailyStats

class Storage:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.engine = create_engine(config.url)
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        return Session(self.engine)
    
    async def save_trade(self, trade):
        with self.get_session() as session:
            session.add(trade)
            session.commit()
            session.refresh(trade)
            return trade
    
    async def save_position(self, position):
        with self.get_session() as session:
            session.add(position)
            session.commit()
            session.refresh(position)
            return position
    
    async def get_open_positions(self):
        with self.get_session() as session:
            return session.query(Position).all()