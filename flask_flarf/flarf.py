from collections import OrderedDict
from flask import Blueprint, g, _request_ctx_stack, current_app
from werkzeug import LocalProxy
from operator import attrgetter
from types import FunctionType


_fs = LocalProxy(lambda: current_app.extensions['flarf'].filters)


class FlarfFiltered(dict):
    def __getattr__(self, attr):
        return self.get(attr, None)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__
    def __iter__(self):
        return dict.__iter__(self)
    def __len__(self):
        return dict.__len__(self)
    def __contains__(self, x):
        return dict.__contains__(self, x)


class FlarfFilter(object):
    """
    A single instance of a filter

    :param filter_tag:          The name of the filter
    :param filter_precedence:   If you need to order your filters in some way,
                                set this as an integer, defaults to 100.
                                Filters will be ordered from smallest number to
                                largest
    :param filtered_cls:        The class used for recording the info from the
                                filter. Default is FlarfFiltered
    :param filter_params:       A list of params used by the filter on request.
                                Strings must be attributes of request, functions
                                must take request as a single argument.
    :param filter_on:           Which routes to use the filter on.
    :param filter_skip:         Which routes to skip and to NOT use the filter.
    """
    def __init__(self,
                 filter_tag=None,
                 filter_precedence=100,
                 filtered_cls=FlarfFiltered,
                 filter_params=None,
                 filter_on=['all'],
                 filter_skip=None):
        self.filter_tag = filter_tag
        self.filter_precedence = filter_precedence
        self.filtered_cls = filtered_cls
        self.filter_params = filter_params
        self.filter_on = filter_on
        self.filter_pass = ['static']
        if filter_skip:
            self.filter_pass.extend(filter_skip)

    def filter_param(self, param, request):
        if isinstance(param, FunctionType):
            setattr(self.filtered, param.__name__, param(request))
        else:
            setattr(self.filtered, param, getattr(request, param, None))

    def filter_by_param(self, request):
        for param in self.filter_params:
            self.filter_param(param, request)

    def filter_request(self, request):
        self.filtered = self.filtered_cls()
        self.filter_by_param(request)
        setattr(g, self.filter_tag, self.filtered)


def flarf_run_filters():
    """
    A before_request function registered on the application that runs each filter.
    """
    r = _request_ctx_stack.top.request
    if r.url_rule:
        request_endpoint = str(r.endpoint).rsplit('.')[-1]
        for f in _fs.values():
            if request_endpoint not in f.filter_pass:
                if request_endpoint or 'all' in f.filter_on:
                    rv = f.filter_request(r)
                    if rv:
                        return rv

def flarf_ctx_processor():
    """
    Context processor which makes the filtered info available inside a template.
    """
    def flarf_ctx(which_filter):
        return getattr(g, which_filter, None)
    return dict(flarf_ctx=flarf_ctx)


class Flarf(object):
    """
    The Flarf extension object.

    :param app:                 The application to register the function on.
    :param before_request_func: The before request function to run the filters.
                                Defaults to flarf_run_filters
    :param filters:             A list of filter instances(or dicts mappable
                                to filter instances) to be run per request.
    """

    def __init__(self,
                 app=None,
                 before_request_func=flarf_run_filters,
                 filter_cls=FlarfFilter,
                 filters=None):
        self.app = app
        self.before_request_func = before_request_func
        self.filter_cls = filter_cls
        self.filters = self.process_filters(filters)

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def process_filters(self, filters):
        d = OrderedDict()
        fs = self.check_filters(filters)
        ofs = self.order_filters(fs)
        for f in ofs:
            d[f.filter_tag] = f
        return d

    def check_filters(self, filters):
        return [self.reflect_filter(f) for f in filters]

    def reflect_filter(self, afilter):
        if isinstance(afilter, dict):
            return self.filter_cls(**afilter)
        else:
            return afilter

    def order_filters(self, filters):
        return sorted(filters, key=attrgetter('filter_precedence'))

    def init_app(self, app):
        app.before_request(self.before_request_func)
        app.context_processor(flarf_ctx_processor)
        app.extensions['flarf'] = self
