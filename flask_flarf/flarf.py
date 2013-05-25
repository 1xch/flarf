from flask import Blueprint, g, _request_ctx_stack, current_app
from werkzeug import LocalProxy

requested = LocalProxy(lambda: _request_ctx_stack.top.g.flarf_filtered)

_flarf = LocalProxy(lambda: current_app.extensions['flarf'])

class FilterRequest(object):
    def __init__(self, request):
        if _flarf.filter_params:
            for arg in _flarf.filter_params:
                setattr(self, arg, getattr(request, arg, None))


def filter_to_g(request):
    g.flarf_filtered = _flarf.filter_cls(request)
    _flarf.additional_filter(request)


class Flarf(object):
    def __init__(self, app=None,
                       filter_cls=FilterRequest,
                       filter_params=None,
                       filter_func=filter_to_g,
                       filter_skip=['static'],
                       filter_pass=None,
                       filter_additional=None):
        self.app = app
        self.filter_cls = filter_cls
        self.filter_params = filter_params
        self.filter_func = filter_func
        self.filter_skip = filter_skip
        if filter_pass:
            self.filter_skip.extend(filter_pass)
        self.filter_additional = filter_additional

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def init_app(self, app):
        def flarf_filter_request(filter_func=self.filter_func):
            r = _request_ctx_stack.top.request
            request_endpoint = str(r.url_rule.endpoint).rsplit('.')[-1]
            if request_endpoint not in _flarf.filter_skip:
                filter_func(r)
        app.before_request(flarf_filter_request)
        app.extensions['flarf'] = self

    def additional_filter(self, request):
        if self.filter_additional:
            for k,v in self.filter_additional.iteritems():
                setattr(g, k, v(request))
