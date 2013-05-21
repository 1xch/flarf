from flask import Blueprint, g, _request_ctx_stack, current_app
from werkzeug import LocalProxy


_flarf = LocalProxy(lambda: current_app.extensions['flarf'])


class PreProcessRequest(object):
    def __init__(self, request):
        if _flarf.preprocess_params:
            for arg in _flarf.preprocess_params:
                setattr(self, arg, getattr(request, arg, None))


def preprocess_to_g(request):
    g.preprocessed = _flarf.preprocessor_cls(request)
    _flarf.additional_filter(request)


class Flarf(object):
    def __init__(self, app=None,
                       preprocessor_cls=PreProcessRequest,
                       preprocess_params=None,
                       preprocess_func=preprocess_to_g,
                       skip_routes=['static'],
                       pass_routes=None,
                       additional_filtering=None):
        self.app = app
        self.preprocessor_cls = preprocessor_cls
        self.preprocess_params = preprocess_params
        self.preprocess_func = preprocess_func
        self.skip_routes = skip_routes
        if pass_routes:
            self.skip_routes.extend(pass_routes)
        self.additional_filtering = additional_filtering

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def init_app(self, app):
        def preprocess_request(preprocess_func=self.preprocess_func):
            r = _request_ctx_stack.top.request
            request_endpoint = str(r.url_rule.endpoint).rsplit('.')[-1]
            if request_endpoint not in _flarf.skip_routes:
                preprocess_func(r)
        app.before_request(preprocess_request)
        app.extensions['flarf'] = self

    def additional_filter(self, request):
        if self.additional_filtering:
            for k,v in self.additional_filtering.iteritems():
                setattr(g, k, v(request))
