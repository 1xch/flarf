from collections import OrderedDict
from flask import Blueprint, g, _request_ctx_stack, current_app
from werkzeug import LocalProxy
from operator import attrgetter
from types import FunctionType
#from functools import wraps
import pprint

#flarf = LocalProxy(lambda: current_app.extensions['flarf'])

_fs = LocalProxy(lambda: current_app.extensions['flarf'].filters)

class FlarfError(Exception):
    pass


class FlarfFiltered(object):
    """
    The class used to place information filtered from request.
    """
    def __init__(self, filter_params, request):
        for arg in filter_params:
            if isinstance(arg, FunctionType):
                setattr(self, arg.__name__, arg(request))
            else:
                setattr(self, arg, getattr(request, arg, None))


class FlarfFilter(object):
    """
    A single instance of a filter

    :param filter_tag:          The name of the filter
    :param filter_precedence:   If you need to order your filters in some way
                                defaults to 100. Filters will be ordered from
                                smallest number to largest
    :param filtered_cls:        The class used for recording the info from the
                                filter. Default is FlarfFiltered
    :param filter_params:       What to use to filter, strings must be attributes
                                of request, functions must take request as a
                                single argument.
    :param filter_on:           Which routes to use the filter on.
    :param filter_skip:         Which routes to NOT use the filter.
    """
    def __init__(self, filter_tag=None,
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

    def filter_request(self, request):
        setattr(g,
                self.filter_tag,
                self.filtered_cls(self.filter_params,
                                  request))


def flarf_run_filters():
    """
    A before_request function registered on the application that runs each filter.
    """
    r = _request_ctx_stack.top.request
    if r.url_rule:
        request_endpoint = str(r.endpoint).rsplit('.')[-1]
        for f in _fs.itervalues():
            if request_endpoint not in f.filter_pass:
                if request_endpoint or 'all' in f.filter_on:
                    f.filter_request(r)

def flarf_ctx_processor():
    """
    Context processor which makes the filtered info  available inside a template.
    """
    def flarf_ctx(which_filter):
        return getattr(g, which_filter)
    return dict(flarf_ctx=flarf_ctx)


class Flarf(object):
    """
    The Flarf extension object.

    :param app:                 The application to register the function on.
    :param before_request_func: The before request function to run the filters.
                                Defaults to flarf_run_filters
    :param filter_cls:          The default filter class to use in registering
                                filters. Defaults to FlarfFilter.
    :param filtered_cls:        The default class for filtered info, if none
                                FlarfFiltered will be used.
    :param filters:             The filters to be run per request
    """

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
        app.context_processor(flarf_ctx_processor)
        app.extensions['flarf'] = self
