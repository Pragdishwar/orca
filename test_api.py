import asyncio, json
from backend.app.api.endpoints.query import run_query, answer_for_intent
from backend.app.core.nlu import parse_utterance
from backend.app.schemas.query import QueryResponse

async def main():
    query = 'Where is the nearest fishing zone?'
    context = {}
    parsed = parse_utterance(query, context)
    print('parsed intent:', parsed['intent'])
    state = await run_query(query, '123', context, 'fisherman', {'sources': [], 'log': {}}, {}, False)
    intent = state.get('llm_output', {}).get('intent', 'crossing_safety')
    print('state intent:', intent)
    computed = state['computed']
    intent_result = await answer_for_intent(intent, state['slots'], computed['cruise_knots'])
    print('intent_result:', bool(intent_result))
    resp = QueryResponse(answer='hello', verdict='SAFE', index_value=0.1, hull_class='FRP', hull_label='FRP', date='2026', guard={}, sources=[], discovery_log={}, layers=[], language='en', context={}, provenance='test', intent_result=intent_result)
    print('has intent_result:', bool(resp.intent_result))

asyncio.run(main())
