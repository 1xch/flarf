from collections import OrderedDict
from flask import Blueprint, g, _request_ctx_stack, current_app
from werkzeug import LocalProxy
from operator import attrgetter
from types import FunctionType

flarf = LocalProxy(lambda: current_app.extensions['flarf'])

_fs = LocalProxy(lambda: current_app.extensions['flarf'].filters)

class FlarfError(Exception):
    pass


class FlarfFiltered(object):
    def __init__(self, filter_params, request):
        for arg in filter_params:
            if isinstance(arg, FunctionType):
                setattr(self, arg.__name__, arg(request))
            else:
                setattr(self, arg, getattr(request, arg, None))


class FlarfFilter(object):
    def __init__(self, filter_tag=None,
                       filter_precedence=100,
                       filtered_cls=FlarfFiltered,
                       filter_params=None,
                       filter_on=['all'],
                       filter_pass=['static'],
                       filter_skip=None):
        self.filter_tag = filter_tag
        self.filter_proxy_tag = "{}_context".format(filter_tag)
        self.filter_precedence = filter_precedence
        self.filtered_cls = filtered_cls
        self.filter_params = filter_params
        self.filter_on = filter_on
        self.filter_pass = filter_pass
        if filter_skip:
            self.filter_pass.extend(filter_skip)

    def filter_request(self, request):
        setattr(g, self.filter_tag, self.filtered_cls(self.filter_params, request))


def flarf_run_filters():
    r = _request_ctx_stack.top.request
    if r.url_rule:
        request_endpoint = str(r.url_rule.endpoint).rsplit('.')[-1]
        for f in _fs.itervalues():
            if request_endpoint not in f.filter_pass:
                if request_endpoint or 'all' in f.filter_on:
                    f.filter_request(r)


class Flarf(object):
    def __init__(self, app=None,
                       before_request_func=flarf_run_filters,
                       filter_cls=FlarfFilter,
                       filtered_cls=None,
                       filters=None):
        self.app = app
        self.before_request_func = before_request_func
        self.filter_cls = filter_cls
        self.filtered_cls = filtered_cls
        self.filters = self.set_filters(filters)

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def set_filters(self, filters):
        d = OrderedDict()
        fs = self.check_filters(filters)
        ofs = self.order_filters(fs)
        for f in ofs:
            d[f.filter_tag] = f
        return d

    def check_filters(self, filters):
        fs = []
        for f in filters:
            if isinstance(f, self.filter_cls):
                fs.append(f)
            elif isinstance(f, dict):
                if self.filtered_cls:
                    f.update({filtered_cls: self.filtered_cls})
                fc = self.filter_cls(**f)
                fs.append(fc)
            else:
                raise FlarfError("""
                                {}\n
                                filter must be a list of:\n
                                - instance of filter_cls given to Flarf extension\n
                                - instance of default filter_cls: FlarfFilter\n
                                - a dict of params for filter_cls\n
                                """.format(f))
        return fs

    def order_filters(self, filters):
        return sorted(filters, key=attrgetter('filter_precedence'))

    def init_app(self, app):
        app.before_request(self.before_request_func)
        app.extensions['flarf'] = self
