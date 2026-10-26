"""A4 exam observer, never a controller. One charged query after execution, no outcome input."""
import hashlib
import json
import re
from r1.c3.prior_model import chat_client, parse_typed_answer


class SelfForecastObserver:
    version = 'exam_self_forecast/v1'
    llm_calls_per_observation = 1

    def __init__(self, base_url=None, model=None, *, llm=None):
        self.client = llm or chat_client(base_url, model, max_tokens=4096, temperature=0.0)

    def observe(self, proposal, status, node_spec):
        edit=proposal.extra.get('structured_edit') or {'objective':proposal.objective}
        prompt=('You proposed the edit below. Predict its effect without observing its outcome.\n'
                f'Node: {node_spec.name}. Edit: {json.dumps(edit,sort_keys=True)}.\n'
                'Return JSON with "p_no_effect": probability of no effect, "p_positive": probability '
                'of a metric improvement conditional on some effect, and "size": tiny, small, medium, large.\n'
                'No metric outcome is supplied.')
        raw=self.client(prompt)
        answer=parse_typed_answer(re.sub(r'<think>.*?</think>\s*','',raw,flags=re.S))
        return {'status':'ok', 'p_no_effect':answer['p_no_effect'],
                'p_delta_positive':(1-answer['p_no_effect'])*answer['p_positive'],
                'p_positive_given_effect':answer['p_positive'], 'size':answer['size'],
                'raw_answer':raw, 'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                'llm_calls':1}
