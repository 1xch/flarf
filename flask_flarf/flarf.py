from flask import Blueprint, g, _request_ctx_stack, current_app
from werkzeug import LocalProxy


_flarf = LocalProxy(lambda: current_app.extensions['flarf'])


class PreProcessRequest(object):
    def __init__(self, request):
        if _flarf.preprocess_params:
            for arg in _flarf.preprocess_params:
                setattr(self, arg, getattr(request, arg, None))


def preprocess_to_g(request):
    g.preprocessed = _flarf.preprocess_cls(request)
    _flarf.additional_filter(request)


class Flarf(object):
    def __init__(self, app=None,
                       preprocess_cls=PreProcessRequest,
                       preprocess_params=None,
                       preprocess_func=preprocess_to_g,
                       preprocess_skip=['static'],
                       preprocess_pass=None,
                       preprocess_additional=None):
        self.app = app
        self.preprocess_cls = preprocess_cls
        self.preprocess_params = preprocess_params
        self.preprocess_func = preprocess_func
        self.preprocess_skip = preprocess_skip
        if preprocess_pass:
            self.preprocess_skip.extend(preprocess_pass)
        self.preprocess_additional = preprocess_additional

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def init_app(self, app):
        def preprocess_request(preprocess_func=self.preprocess_func):
            r = _request_ctx_stack.top.request
            request_endpoint = str(r.url_rule.endpoint).rsplit('.')[-1]
            if request_endpoint not in _flarf.preprocess_skip:
                preprocess_func(r)
        app.before_request(preprocess_request)
        app.extensions['flarf'] = self

    def additional_filter(self, request):
        if self.preprocess_additional:
            for k,v in self.preprocess_additional.iteritems():
                setattr(g, k, v(request))
