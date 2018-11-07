from vcr_unittest import VCRTestCase


class BiglearnVCRTestCase(VCRTestCase):

    def _get_vcr_kwargs(self, **kwargs):
        kw = {'filter_headers': ['Biglearn-Api-Token', 'Biglearn-Scheduler-Token']}
        kw.update(kwargs)
        return kw
