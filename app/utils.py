from typing import List

def fair_split(total: int, n: int) -> List[int]:
    base = total // n
    extra = total % n
    return [base + (1 if i < extra else 0) for i in range(n)]
