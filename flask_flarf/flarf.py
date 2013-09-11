from collections import OrderedDict
from flask import Blueprint, g, _request_ctx_stack, current_app, request
from werkzeug import LocalProxy
from operator import attrgetter
from types import FunctionType
from functools import partial

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
                                May be strings or functions. Strings must be
                                attributes of request, found within (request.values,
                                request.form, or request.files) or reference a
                                method on the filter class that take request as
                                an argument. Passed in functions must take request
                                as a single argument.
                                On filter run params are run in order supplied
                                where param indicates:
                                   - a function
                                   - an attribute of flask request
                                   - a "get_var" method on the filter where
                                     'var' is the variable you'd like the filter
                                     to capture or generate
                                   - in request.values, request.form,
                                     and request.files
    :param filter_on:           A list of routes to use the filter on, default
                                is ['all'], except static routes
    :param filter_skip:         A list routes to pass and not use filter.
                                By default, all static routes are skipped

    use:

    my_filter = FlarfFilter('my_filter', filter_params=['values', 'my_id'])

    my_filter is then available after request as g.my_filter or in templates as
    {{my_filter}} with the attributes my_filter.values & my_filter.my_id where
    values is request.values, and my_id is from request.values, request.view_args,
    or request.files and is None if not available

    To customize a specific instance,

    class MyFilter(FlarfFilter):
        def __init__(self, **kwargs):
            super(MyFilter, self).__init__(**kwargs)
        def get_post(self, request):
            return make_db_request(request.args.post_id)

    m = MyFilter("my_custom_filter")

    When m is passed to the extension and used on request, you will have
    my_custom_filter.post available with your exact post where post_id is
    supplied as an arg
    """
    def __init__(self,
                 filter_tag,
                 filter_precedence=100,
                 filter_params=None,
                 filter_on=['all'],
                 filter_skip=None):
        self.filter_tag = filter_tag
        self.filter_precedence = filter_precedence
        self.filter_params = self.set_params(filter_params)
        self.filter_on = filter_on
        self.filter_pass = ['static']
        if filter_skip:
            self.filter_pass.extend(filter_skip)

    def set_params(self, params):
        d = OrderedDict()
        for p in params:
            if isinstance(p, FunctionType):
                d[p.__name__] = p
            elif p[:4] == 'get_':
                d[p[4:]] = partial(getattr(self, p))
            elif hasattr(request, p):
                d[p] = partial(getattr(self, 'param_request'), p)
            else:
                d[p] = partial(getattr(self, 'param_param'), p)
        return d

    def get_ctx_prc(self):
        def ctx_prc(tag):
            return getattr(g, tag, None)
        return {self.filter_tag: ctx_prc(self.filter_tag)}

    def param_request(self, param, request):
        return getattr(request, param, None)

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

    use as part of your application construction:

    from flask import Flask
    app = Flask(__name__)

    Flarf(app, filters=[m])  # where m is an instance of MyFilter above

    @app.route("/")
    def hello():
        return "Hello World!"

    if __name__ == "__main__":
        app.run()
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

    def init_context_processors(self, app):
        for f in self.filters.values():
           app.context_processor(f.get_ctx_prc)

    def init_app(self, app):
        app.before_request(self.before_request_func)
        self.init_context_processors(app)
        app.extensions['flarf'] = self

    def flarf_run_filters(self):
        """
        A before_request function registered on the extension that runs each filter.
        """
        r = _request_ctx_stack.top.request
        if r.url_rule:
            request_endpoint = str(r.endpoint).rsplit('.')[-1]
            for f in self.filters.values():
                if request_endpoint not in f.filter_pass:
                    if request_endpoint or 'all' in f.filter_on:
                        rv = f.filter_request(r)
                        if rv:
                            return rv
