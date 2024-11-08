from aiogram.fsm.state import State, StatesGroup

class UserData(StatesGroup):
    Faculty = State()
    Form = State()
    Step = State()
    Course = State()
    Group = State()
    SubGroup = State()

class Broadcast(StatesGroup):
    Message = State()
    MessageType = State()

class Mailing(StatesGroup):
    Subscribe = State()
    Unsubscribe = State()
    
class BroadcastAbort(StatesGroup):
    Abort = State()

class StarsRefund(StatesGroup):
    Refund = State()
    Confirm = State()