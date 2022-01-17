from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy import INT, String, DATETIME,SMALLINT

base = declarative_base()


class SQLPacket(base):
    """
    status: 1: packet unopened, 0:packet opened
    """
    __tablename__ = 'packet'
    no = Column(INT, autoincrement=True, primary_key=True)
    sender = Column(String(255), ForeignKey('player.email', ondelete='CASCADE'))
    receiver = Column(String(255), ForeignKey('player.email', ondelete='CASCADE'))
    date = Column(DATETIME, nullable=False)

    1q
class SQLPlayer(base):
    """
    unopened_packet： 必定是好友领取成功之后，系统返回的红包数
    """
    __tablename__ = 'player'
    email = Column(String(255), primary_key=True)
    role_id = Column(String(255), nullable=True)
    point = Column(SMALLINT, nullable=False, default=0)
    rank = Column(INT, nullable=False, default=0)
    opened_packet = Column(SMALLINT, nullable=False, default=0)
    unopened_packet = Column(SMALLINT, nullable=False, default=0)
    draw_chance = Column(SMALLINT, nullable=False, default=0)
    draw_count = Column(SMALLINT, nullable=False, default=0)


class SQLPlayerPrize(base):
    __tablename__ = 'player_prize'
    no = Column(INT, primary_key=True, autoincrement=True)
    email = Column(String(255), ForeignKey('player.email', ondelete='CASCADE', onupdate='CASCADE'))
    date = Column(DATETIME, nullable=False)
    prize_name = Column(String(50), nullable=False)
    prize_type = Column(INT, nullable=False)
    prize_event = Column(String(50), nullable=False)
    ForeignKeyConstraint(['prize_name', 'prize_type'], ['prize.name', 'prize.type'], onupdate="CASCADE",
                         ondelete='CASCADE')


class SQLPrize(base):
    """
    1：收到系统回礼红包 2：收到好友红包 3：虎气值达到阈值 4：抽奖 5：排行榜
    """
    __tablename__ = 'prize'
    no = Column(INT,autoincrement=True, nullable=False)
    name = Column(String(50), primary_key=True)
    type = Column(SMALLINT, primary_key=True)
    content = Column(String(100), nullable=False)
    amount = Column(SMALLINT, nullable=False)
