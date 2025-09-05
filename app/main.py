from fastapi import FastAPI
from .schemas import SolveInput, SolveOutput
from .solver import solve
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="Timetable Solver")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # dev үшін * (кейін нақты домендер)
    allow_credentials=True,
    allow_methods=["*"],           # OPTIONS та кіреді
    allow_headers=["*"],
)
@app.get("/health")
def health():
    return {"ok": True}



@app.post("/solve", response_model=SolveOutput)
def solve_endpoint(body: SolveInput):
    return solve(body)
