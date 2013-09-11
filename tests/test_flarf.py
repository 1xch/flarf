from __future__ import with_statement
import sys
import os
from flask import Flask, render_template, current_app, g, request, redirect
from flask.ext.flarf import Flarf, FlarfFilter, flarf
import unittest

class FlarfTestCase(unittest.TestCase):
    def setUp(self):
        def custom_before_func():
            setattr(g, 'custom_before_func', True)
        class CustomFilter(FlarfFilter):
            def __init__(self, something_custom="NOTHING", **kwargs):
                self.something_custom = something_custom
                super(CustomFilter, self).__init__(**kwargs)
            def filter_request(self, request):
                setattr(g, 'custom_filter_run', True)
                setattr(g, self.filter_tag, self.something_custom)
                return redirect('/')
        def path_to_upper(request):
            return request.path.upper()
        self.custom_before_func = custom_before_func
        self.custom_filter = CustomFilter
        test_filter1 = FlarfFilter(filter_tag='test_filter1',
                                   filter_precedence=100,
                                   filter_params=['path', path_to_upper],
                                   filter_on=['includeme'])
        test_filter2 = FlarfFilter(filter_tag='test_filter2',
                                   filter_precedence=200,
                                   filter_params=['values', 'yod', 'zed'])
        test_filter3 = {'filter_tag': 'test_filter3',
                        'filter_precedence': 300,
                        'filter_params': ['path', 'args'],
                        'filter_skip':['passme']}
        test_filter4 = CustomFilter(filter_tag='test_filter4',
                                    filter_precedence=100,
                                    filter_params=['path', path_to_upper],
                                    filter_on=['app_route'],
                                    something_custom="I am test filter 4")
        test_filter5 = {'filter_tag': 'test_filter5',
                        'filter_precedence': 300,
                        'filter_params': ['path', 'args'],
                        'filter_skip':['passme'],
                        'something_custom': 'I am test filter 5'}
        self.test_filters1 = [test_filter1]
        self.test_filters2 = [test_filter1, test_filter2, test_filter3]
        self.test_filters3 = [test_filter4, test_filter5]
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
        post_app = Flask(__name__)
        @post_app.route('/')
        def test_index():
            return g.__dict__
        Flarf(post_app, filters=self.test_filters1)
        self.base_app = post_app
        self.pre_app = pre_app

    def tearDown(self):
        self.pre_app = None

    def test_base(self):
        with self.base_app.test_request_context('/'):
            self.base_app.preprocess_request()
            self.assertIsNotNone(self.base_app.extensions['flarf'])
            self.assertIsNotNone(getattr(g, 'test_filter1', None))

    def test_filters(self):
        Flarf(self.pre_app, filters=self.test_filters2)
        with self.pre_app.test_request_context('/app_route?zed=z'):
            self.pre_app.preprocess_request()
            self.assertIsNotNone(getattr(g, 'test_filter3', None))
            self.assertEqual(getattr(g, 'test_filter3', None),
                             getattr(g, 'test_filter3', None))
            self.assertEqual(g.test_filter1.path_to_upper, u'/APP_ROUTE')
            #self.assertEqual(u'/app_route', g.test_filter3.path)
            self.assertEqual(g.test_filter1.path,
                             g.test_filter3.path)

    def test_context_processor(self):
        Flarf(self.pre_app, filters=self.test_filters2)
        with self.pre_app.test_client() as ct:
            rv = ct.get('/context_processor?zed=z')
            self.assertIsNotNone(rv.data)
            self.assertEqual(rv.data.decode(), g.test_filter2.zed)

    def test_custom_before_request_func(self):
        Flarf(self.pre_app,
              filters=self.test_filters2,
              before_request_func=self.custom_before_func)
        with self.pre_app.test_request_context('/'):
            self.pre_app.preprocess_request()
            self.assertTrue(g.custom_before_func)

    def test_custom_filter_cls(self):
        Flarf(self.pre_app, filter_cls=self.custom_filter, filters=self.test_filters3)
        with self.pre_app.test_request_context('/'):
            self.pre_app.preprocess_request()
            self.assertTrue(g.custom_filter_run)
        with self.pre_app.test_client() as ct:
            rv = ct.get('/app_route')
            self.assertEqual(rv.status_code, 302)

    def test_include_route(self):
        @self.pre_app.route('/includeme')
        def includeme():
            return g.__dict__
        Flarf(self.pre_app, filters=self.test_filters2)
        with self.pre_app.test_request_context('/includeme'):
            self.pre_app.preprocess_request()
            #self.assertTrue(g.test_filter1.path)
            #self.assertEqual(g.test_filter1.path, u'/includeme')

    def test_exclude_route(self):
        @self.pre_app.route('/passme')
        def passme():
            return g.__dict__
        Flarf(self.pre_app, filters=self.test_filters2)
        with self.pre_app.test_request_context('/passme'):
            self.pre_app.preprocess_request()
            with self.assertRaises(AttributeError):
                g.test_filter3

if __name__ == '__main__':
    unittest.main()
