"""Offline native Provider accounting. Does not claim HTTP retry visibility."""
from text2ifc_agent.providers import ProviderOutput


class ObservedReplay:
    def __init__(self, provider, ledger, run_id, reservation):
        self.provider, self.ledger, self.run_id, self.reservation = provider, ledger, run_id, reservation
        self.budget_error = None

    def provider_evidence_delegate(self):
        return self.provider

    def generate_candidate(self, **kwargs):
        request_id = f'native-{len(self.ledger.calls(self.run_id))}'
        try:
            self.ledger.reserve(self.run_id, request_id, self.reservation,
                                metadata={'stage': kwargs.get('state', {}).get('stage'), 'evidence_class': 'deterministic_replay'})
        except ValueError as error:
            if 'BUDGET' in str(error):
                self.budget_error = str(error)
            raise
        self.ledger.record(self.run_id, 'native_provider_input', {'request_id': request_id, **kwargs})
        try:
            result = self.provider.generate_candidate(**kwargs)
            if not isinstance(result, ProviderOutput):
                raise TypeError('PROVIDER_OUTPUT_REQUIRED')
        except Exception as error:
            self.ledger.settle(self.run_id, request_id, usage=None, response={'error': type(error).__name__, 'detail': str(error)}, failed=True)
            raise
        self.ledger.settle(self.run_id, request_id, usage=result.metadata.get('usage'),
                           response={'text': result.text, 'metadata': dict(result.metadata)})
        return result
