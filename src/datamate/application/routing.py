"""Check lexical candidates against the supported question shapes."""

from collections.abc import Callable, Mapping

from datamate.application.plans import QuestionPlan, Unresolved
from datamate.ranking.intents import IntentIndex, IntentMatch, normalize_text


def select_plan(question: str, index: IntentIndex,
                parsers: Mapping[str, Callable[[str], QuestionPlan | None]]) -> tuple[QuestionPlan | Unresolved, IntentMatch | None]:
    text = normalize_text(question)
    valid = []
    for match in index.rank(text):
        parse = parsers.get(match.intent)
        if match.score <= 0 or parse is None:
            continue
        plan = parse(text)
        if plan is not None:
            valid.append((plan, match))
    if not valid:
        return Unresolved("unsupported_question"), None
    if len(valid) > 1 and abs(valid[0][1].score - valid[1][1].score) <= 1e-12:
        return Unresolved("ambiguous_intent"), None
    return valid[0]
