import re
from operator import attrgetter
from types import FunctionType
from functools import partial
from collections import OrderedDict
from werkzeug import LocalProxy
from flask import Blueprint, g, _request_ctx_stack, current_app


fs = LocalProxy(lambda: current_app.extensions['flarf'].filters)


class FlarfFilter(object):
    """
    A class used to instance a filter result on application request

    :param filter_tag:          The name of the filter
    :param filter_precedence:   If you need to order your filters in some way,
                                set this as an integer, defaults to 100.
                                Filters will be ordered from smallest number to
                                largest
    :param filter_params:       A list of paramaters used by the filter on request.
                                May be either string or function:
                                   - a function that takes request as an argument
                                   - a string 'request_x', indicating x is to be
                                     returned from request, e.g. 'request_path'
                                     to have the filter get request.path
                                   - a string 'get_var' referencing a method on
                                     the filter where 'var' is the variable you'd
                                     like the filter to capture e.g. 'get_var'
                                     will do self.get_var(request) to set self.var
                                   - a string for a var found in request.values,
                                     request.form, or request.files
    :param filter_on:           A list of routes to use the filter on, default
                                is ['all'], except static routes
    :param filter_skip:         A list routes/endpoints to pass over and not
                                use filter. By default, all static routes are
                                skipped
    """
    def __init__(self,
                 filter_tag,
                 filter_precedence=100,
                 filter_params=None,
                 filter_on=None,
                 filter_pass=None):
        self.filter_tag = filter_tag
        self.filter_precedence = filter_precedence
        self.filter_params = self.set_params(filter_params)
        self.filter_on = self.set_filter_on(filter_on)
        self.filter_pass = self.set_filter_pass(filter_pass)

    def set_params(self, params):
        return OrderedDict([self.param_is(p) for p in params])

    def set_filter_on(self, filter_on):
        if not filter_on:
            filter_on = ['all']
        return self.re_compile_list(filter_on)

    def set_filter_pass(self, filter_pass):
        if not filter_pass:
            filter_pass = ['static']
        else:
            filter_pass.append('static')
        return self.re_compile_list(filter_pass)

    def re_compile_list(self, l):
        return re.compile(r'(?:{})'.format('|'.join(l)))

    def param_is(self, p):
        if isinstance(p, FunctionType):
            return (p.__name__, p)
        else:
            return self.determine_param(p)

    def determine_param(self, from_p):
        p = from_p.partition('_')
        if p[0] == 'request':
            return p[2], partial(getattr(self, 'param_request'), p[2])
        elif p[0] in ('get', 'self'):
            return p[2], partial(getattr(self, from_p))
        else:
            return from_p, partial(getattr(self, 'param_param'), from_p)

    def get_ctx_prc(self):
        def ctx_prc(tag):
            return getattr(g, tag, None)
        return {self.filter_tag: ctx_prc(self.filter_tag)}

    def param_request(self, param, request):
        return getattr(request, param)

    def param_param(self, param, request):
        p = filter(None, [request.values.get(param, None),
                          request.view_args.get(param, None),
                          request.files.get(param, None)])
        if p:
            return p.pop()
        else:
            return None

    def filter_by_param(self, request):
        for k, v in self.filter_params.items():
            setattr(self, k, v(request))

    def filter_request(self, request):
        self.filter_by_param(request)
        setattr(g, self.filter_tag, self)

    def no_filter(self):
        setattr(g, self.filter_tag, None)


class Flarf(object):
    """
    The Flarf extension object to registered with a Flask application.

    :param app:                 The application to register the function on.
    :param before_request_func: The before request function to run the filters.
                                Defaults to self.flarf_run_filters
    :param filter_cls:          The class used as a filter, defaults to
                                FlarfFilter, used when receiving dicts as filters
    :param filters:             A list of filter instances(or dicts mappable
                                to filter_cls instances) to be run per request.

    """
    def __init__(self,
                 app=None,
                 before_request_func=None,
                 filter_cls=FlarfFilter,
                 filters=None):
        self.app = app
        self.before_request_func = self.set_before_request_func(before_request_func)
        self.filter_cls = filter_cls
        self.filters = self.process_filters(filters)

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def set_before_request_func(self, before_request_func):
        if before_request_func:
            return before_request_func
        else:
            return self.flarf_run_filters

    def process_filters(self, filters):
        fs = self.check_filters(filters)
        ofs = self.order_filters(fs)
        return OrderedDict([(f.filter_tag, f) for f in ofs])

    def check_filters(self, filters):
        return [self.reflect_filter(f) for f in filters]

    def reflect_filter(self, afilter):
        if isinstance(afilter, dict):
            return self.filter_cls(**afilter)
        else:
            return afilter

    def order_filters(self, filters):
        return sorted(filters, key=attrgetter('filter_precedence'))

    def init_context_processors(self, app):
        for f in self.filters.values():
           app.context_processor(f.get_ctx_prc)

    def init_app(self, app):
        app.before_request(self.before_request_func)
        self.init_context_processors(app)
        app.extensions['flarf'] = self

    def flarf_run_filters(self):
        r = _request_ctx_stack.top.request
        request_points = [str(r.endpoint).rsplit('.')[-1], r.path]
        for f in self.filters.values():
            if not any([f.filter_pass.match(ff) for ff in request_points]):
                if f.filter_on.match('all') or any([f.filter_on.match(ff) for ff in request_points]):
                    rv = f.filter_request(r)
                    if rv:
                        return rv
