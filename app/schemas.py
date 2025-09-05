from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

Day = Literal["mon","tue","wed","thu","fri","sat"]

class Config(BaseModel):
    days: List[Day]
    periods_per_day: int
    week_mode: int = 5
    horizon_weeks: int = 1  # MVP: 1 апта (кейін 2 аптаға кеңейтеміз)

class RoomType(BaseModel):
    type: str
    count: int

class Subject(BaseModel):
    id: str
    require_room: str = "classroom"
    double_ok: bool = False  # біріктірілген/қатар 2 пара подряд оқытуға бола ма

class Teacher(BaseModel):
    id: str
    skills: List[str]

class ClassRequirement(BaseModel):
    subject: str
    periods_per_week: Optional[int] = None
    periods_per_fortnight: Optional[int] = None  # 0.5 сағат үшін

class ClassItem(BaseModel):
    id: str
    direction: Optional[str] = None
    requirements: List[ClassRequirement]

class Policies(BaseModel):
    no_student_gaps: bool = True
    teacher_gaps_penalty: int = 1
    fair_load_by_subject: bool = True
    parallel_allowed: bool = True

class SolveInput(BaseModel):
    config: Config
    room_types: List[RoomType]
    subjects: List[Subject]
    teachers: List[Teacher]
    classes: List[ClassItem]
    policies: Policies

class Timeslot(BaseModel):
    class_id: str
    day: Day
    period: int
    subject: str
    teacher: str
    room: str

class StatsTeacherLoad(BaseModel):
    teacher: str
    hours: int

class SolveOutput(BaseModel):
    timeslots: List[Timeslot]
    teacher_load: List[StatsTeacherLoad]
    violations: List[str] = Field(default_factory=list)
