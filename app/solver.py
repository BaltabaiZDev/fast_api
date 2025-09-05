from typing import Dict, List, Tuple, Optional
from .schemas import SolveInput, SolveOutput, Timeslot, StatsTeacherLoad

def solve(input: SolveInput) -> SolveOutput:
    data = input

    days = data.config.days
    D = list(range(len(days)))
    P = list(range(data.config.periods_per_day))

    class_idx = {c.id: i for i, c in enumerate(data.classes)}
    subject_idx = {s.id: i for i, s in enumerate(data.subjects)}
    teacher_idx = {t.id: i for i, t in enumerate(data.teachers)}

    room_types: Dict[str, int] = {rt.type: rt.count for rt in data.room_types}
    has_classroom_bucket = "classroom" in room_types

    C = list(range(len(data.classes)))
    S = list(range(len(data.subjects)))
    T = list(range(len(data.teachers)))

    # subject -> teachers
    subj_teachers: Dict[int, List[int]] = {si: [] for si in S}
    for t in data.teachers:
        ti = teacher_idx[t.id]
        for sid in t.skills:
            if sid in subject_idx:
                subj_teachers[subject_idx[sid]].append(ti)

    # subject props
    subj_room_type: Dict[int, Optional[str]] = {}
    subj_room_strict: Dict[int, bool] = {}
    subj_allow_double: Dict[int, bool] = {}
    for s in data.subjects:
        si = subject_idx[s.id]
        subj_room_type[si] = getattr(s, "require_room", None)
        subj_room_strict[si] = bool(getattr(s, "strict_room", False))
        subj_allow_double[si] = bool(getattr(s, "allow_double", False))

    # class -> weekly needs
    class_need: Dict[int, Dict[int, int]] = {}
    for c in data.classes:
        ci = class_idx[c.id]
        m: Dict[int, int] = {}
        for r in c.requirements:
            if r.subject not in subject_idx:
                continue
            si = subject_idx[r.subject]
            need = 0
            if r.periods_per_week is not None:
                need += int(r.periods_per_week)
            if r.periods_per_fortnight is not None:
                need += 1
            if need > 0:
                m[si] = need
        class_need[ci] = m

    # allowed room types
    allowed_rts: Dict[int, List[str]] = {}
    for si in S:
        rt = subj_room_type.get(si, None)
        strict = subj_room_strict.get(si, False)
        opts: List[str] = []
        if rt is None:
            if has_classroom_bucket:
                opts = ["classroom"]
        else:
            if strict:
                opts = [rt]
            else:
                opts = [rt]
                if has_classroom_bucket and rt != "classroom":
                    opts.append("classroom")
        allowed_rts[si] = [r for r in opts if r in room_types]

    # ===== SUBJECT DISTRIBUTION (тең тарату) =====
    placed_subj: Dict[Tuple[int,int,int], Optional[int]] = {(ci,d,p): None for ci in C for d in D for p in P}
    perday_subj_cnt: Dict[Tuple[int,int,int], int] = {}
    room_used: Dict[Tuple[str,int,int], int] = {(rt,d,p):0 for rt in room_types for d in D for p in P}

    def can_place(ci:int, di:int, pi:int, si:int) -> bool:
        if placed_subj[(ci,di,pi)] is not None:
            return False
        cap = 2 if subj_allow_double.get(si, False) else 1
        if perday_subj_cnt.get((ci,di,si),0) >= cap:
            return False
        rts = allowed_rts.get(si, ["classroom"] if has_classroom_bucket else [])
        for rt in rts:
            if room_used[(rt,di,pi)] < room_types[rt]:
                return True
        return False

    def place(ci:int, di:int, pi:int, si:int) -> bool:
        if not can_place(ci,di,pi,si): return False
        rts = allowed_rts.get(si, ["classroom"] if has_classroom_bucket else [])
        for rt in rts:
            if room_used[(rt,di,pi)] < room_types[rt]:
                placed_subj[(ci,di,pi)] = si
                perday_subj_cnt[(ci,di,si)] = perday_subj_cnt.get((ci,di,si),0)+1
                room_used[(rt,di,pi)] += 1
                return True
        return False

    for ci in C:
        for si, need in sorted(class_need[ci].items(), key=lambda x: -x[1]):
            left = need
            while left > 0:
                # ең аз жүктелген күн
                loads = {di: sum(1 for p in P if placed_subj[(ci,di,p)] is not None) for di in D}
                di = min(loads, key=loads.get)
                # бірінші бос период
                placed = False
                for pi in P:
                    if place(ci,di,pi,si):
                        left -= 1
                        placed = True
                        break
                if not placed:
                    # басқа күндерді қарау
                    found = False
                    for dj in D:
                        if dj == di: continue
                        for pj in P:
                            if place(ci,dj,pj,si):
                                left -= 1
                                found = True
                                break
                        if found: break
                    if not found:
                        break  # swap/recolor кезеңінде көріп шығамыз

    # ===== TEACHER ASSIGNMENT =====
    teacher_load = {ti: 0 for ti in T}
    busy_teacher = {(ti,d,p): False for ti in T for d in D for p in P}
    assigned_teacher: Dict[Tuple[int,int,int], Optional[int]] = {(ci,d,p): None for ci in C for d in D for p in P}

    TARGET, MIN_LOAD = 16, 10

    def pick_teacher(di:int, pi:int, si:int) -> Optional[int]:
        cands = [ti for ti in subj_teachers.get(si, []) if not busy_teacher[(ti,di,pi)]]
        if not cands: return None
        def score(ti:int):
            load = teacher_load[ti]
            band = 0 if load < MIN_LOAD else (1 if load < TARGET else 2)
            return (band, abs(load - TARGET))
        cands.sort(key=score)
        return cands[0]

    pending: List[Tuple[int,int,int,int]] = []
    for di in D:
        for pi in P:
            for ci in C:
                si = placed_subj[(ci,di,pi)]
                if si is None: continue
                ti = pick_teacher(di,pi,si)
                if ti is None:
                    pending.append((ci,di,pi,si))
                else:
                    assigned_teacher[(ci,di,pi)] = ti
                    busy_teacher[(ti,di,pi)] = True
                    teacher_load[ti] += 1

    # ===== REPAIR: көп өтумен swap / recolor =====
    def day_cap_ok(ci:int, di:int, si:int, delta:int) -> bool:
        cap = 2 if subj_allow_double.get(si, False) else 1
        return perday_subj_cnt.get((ci,di,si),0) + delta <= cap

    def try_swap(ci, di, pi, si) -> bool:
        for dj in D:
            for pj in P:
                if (dj,pj) == (di,pi): continue
                sj = placed_subj.get((ci,dj,pj))
                if sj is None: continue
                # күндік лимит
                if not (day_cap_ok(ci,di,sj,+1) and day_cap_ok(ci,di,si,-1) and
                        day_cap_ok(ci,dj,si,+1) and day_cap_ok(ci,dj,sj,-1)):
                    continue
                ti1 = pick_teacher(di,pi,sj)
                ti2 = pick_teacher(dj,pj,si)
                if ti1 is None or ti2 is None:
                    continue
                # swap
                placed_subj[(ci,di,pi)], placed_subj[(ci,dj,pj)] = sj, si
                perday_subj_cnt[(ci,di,si)] = perday_subj_cnt.get((ci,di,si),0)-1
                perday_subj_cnt[(ci,dj,si)] = perday_subj_cnt.get((ci,dj,si),0)+1
                perday_subj_cnt[(ci,dj,sj)] = perday_subj_cnt.get((ci,dj,sj),0)-1
                perday_subj_cnt[(ci,di,sj)] = perday_subj_cnt.get((ci,di,sj),0)+1
                assigned_teacher[(ci,di,pi)] = ti1
                busy_teacher[(ti1,di,pi)] = True
                teacher_load[ti1] += 1
                assigned_teacher[(ci,dj,pj)] = ti2
                busy_teacher[(ti2,dj,pj)] = True
                teacher_load[ti2] += 1
                return True
        return False

    def try_recolor(ci, di, pi, si) -> bool:
        for dj in D:
            for pj in P:
                if (dj,pj) == (di,pi): continue
                sj = placed_subj.get((ci,dj,pj))
                if sj is None or sj == si: continue
                if not (day_cap_ok(ci,di,sj,+1) and day_cap_ok(ci,dj,si,+1)):
                    continue
                ti_here = pick_teacher(di,pi,sj)
                ti_there = pick_teacher(dj,pj,si)
                if ti_here is None or ti_there is None:
                    continue
                placed_subj[(ci,di,pi)], placed_subj[(ci,dj,pj)] = sj, si
                perday_subj_cnt[(ci,di,si)] = max(0, perday_subj_cnt.get((ci,di,si),0)-1)
                perday_subj_cnt[(ci,di,sj)] = perday_subj_cnt.get((ci,di,sj),0)+1
                perday_subj_cnt[(ci,dj,sj)] = max(0, perday_subj_cnt.get((ci,dj,sj),0)-1)
                perday_subj_cnt[(ci,dj,si)] = perday_subj_cnt.get((ci,dj,si),0)+1
                assigned_teacher[(ci,di,pi)] = ti_here
                busy_teacher[(ti_here,di,pi)] = True
                teacher_load[ti_here] += 1
                assigned_teacher[(ci,dj,pj)] = ti_there
                busy_teacher[(ti_there,dj,pj)] = True
                teacher_load[ti_there] += 1
                return True
        return False

    # бірнеше итерация: неғұрлым көп жөндеуге тырысамыз
    MAX_ITERS = 3
    for _ in range(MAX_ITERS):
        changed = False
        for item in list(pending):
            ci, di, pi, si = item
            if assigned_teacher[(ci,di,pi)] is not None:
                pending.remove(item)
                continue
            if try_swap(ci,di,pi,si) or try_recolor(ci,di,pi,si):
                pending.remove(item)
                changed = True
        if not changed:
            break

    # ===== OUTPUT (unknown fallback) =====
    rt_used = {(rt,d,p):0 for rt in room_types for d in D for p in P}
    out: List[Timeslot] = []
    for di in D:
        for pi in P:
            for ci in C:
                si = placed_subj[(ci,di,pi)]
                if si is None:
                    continue
                # room
                rts = allowed_rts.get(si, ["classroom"] if has_classroom_bucket else [])
                chosen_rt = None
                for rt in rts:
                    if rt_used[(rt,di,pi)] < room_types[rt]:
                        rt_used[(rt,di,pi)] += 1
                        chosen_rt = rt
                        break
                room_name = f"{chosen_rt}_{rt_used[(chosen_rt,di,pi)]}" if chosen_rt else ("classroom_1" if has_classroom_bucket else "")
                # teacher (егер табылмаса — unknown)
                ti = assigned_teacher[(ci,di,pi)]
                teacher_id = data.teachers[ti].id if ti is not None else "unknown"
                out.append(
                    Timeslot(
                        class_id=data.classes[ci].id,
                        day=days[di],
                        period=pi+1,
                        subject=data.subjects[si].id,
                        teacher=teacher_id,
                        room=room_name
                    )
                )

    # teacher load summary
    tl_counter = {t.id:0 for t in data.teachers}
    for s in out:
        if s.teacher != "unknown":
            tl_counter[s.teacher] += 1
    load_list = [StatsTeacherLoad(teacher=t.id, hours=tl_counter[t.id]) for t in data.teachers]

    return SolveOutput(timeslots=out, teacher_load=load_list, violations=[])
