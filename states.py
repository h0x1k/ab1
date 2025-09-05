from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    Time = State()
    Sending = State()
    Frequency = State()
    Dates = State()
    Allbestbets = State()
    Line4bets = State()
    Sports = State()
    Channels = State()
    Contact = State()
    Difference = State()
    Timezone = State()
    BKIntervals = State()