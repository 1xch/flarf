from __future__ import with_statement
import sys
import os
from flask import Flask, render_template, current_app, g, request, redirect
from flask.ext.flarf import Flarf, FlarfFilter, flarf
import unittest


class FlarfTest(unittest.TestCase):
    def setUp(self):
        def custom_before_func():
            setattr(g, 'custom_before_func', True)
        class CustomFilter(FlarfFilter):
            def __init__(self, something_custom="NOTHING", **kwargs):
                self.something_custom = something_custom
                super(CustomFilter, self).__init__(**kwargs)
            def get_something(self, request):
                return "something"
            def filter_request(self, request):
                setattr(g, 'custom_filter_run', True)
                self.filter_by_param(request)
                setattr(g, self.filter_tag, self)
                #setattr(g, self.filter_tag, self.something_custom)
                return redirect('/')
        def path_to_upper(request):
            return request.path.upper()
        self.custom_before_func = custom_before_func
        self.custom_filter = CustomFilter
        test_filter1 = FlarfFilter(filter_tag='test_filter1',
                                   filter_precedence=100,
                                   filter_params=['request_path', path_to_upper])
        test_filter2 = FlarfFilter(filter_tag='test_filter2',
                                   filter_precedence=200,
                                   filter_params=['request_values', 'yod', 'zed'])
        test_filter3 = {'filter_tag': 'test_filter3',
                        'filter_precedence': 300,
                        'filter_params': ['request_path', 'args']}
        test_filter4 = CustomFilter(filter_tag='test_filter4',
                                    filter_precedence=100,
                                    filter_params=['request_path', path_to_upper, 'get_something'],
                                    filter_on=['/', 'app_route'],
                                    something_custom="I am test filter 4")
        test_filter5 = {'filter_tag': 'test_filter5',
                        'filter_precedence': 300,
                        'filter_params': ['request_path', 'request_args'],
                        'filter_pass':['passme'],
                        'something_custom': 'I am test filter 5'}
        test_filter6 = {'filter_tag': 'test_filter6',
                        'filter_precedence': 400,
                        'filter_params': ['request_path', 'request_args'],
                        'filter_pass': ['test_app_route', '/app_route', '/passme'],
                        'filter_on':['/includeme', 'test_index']}
        self.test_filters1 = [test_filter1]
        self.test_filters2 = [test_filter1, test_filter2, test_filter3]
        self.test_filters3 = [test_filter4]
        self.test_filters4 = [test_filter6]
        pre_app = Flask(__name__)
        @pre_app.route('/')
        def test_index():
            return g.__dict__
        @pre_app.route('/app_route')
        def test_app_route():
            return g.__dict__
        @pre_app.route('/context_processor')
        def test_c_route():
            return render_template('test_template.html')
        @pre_app.route('/includeme')
        def includeme():
            return g.__dict__
        @pre_app.route('/passme')
        def passme():
            return g.__dict__
        post_app = Flask(__name__)
        @post_app.route('/')
        def test_index():
            return g.__dict__
        Flarf(post_app, filters=self.test_filters1)
        self.base_app = post_app
        self.pre_app = pre_app

    def tearDown(self):
        self.pre_app = None
        self.base_app = None
