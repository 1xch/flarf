from __future__ import with_statement

import sys
import os
from flask import Flask, render_template, current_app, g, request
from flask.ext.flarf import Flarf
import unittest

class FlarfTestCase(unittest.TestCase):
    def setUp(self):
        pre_app = Flask(__name__)
        @pre_app.route('/')
        def test_index():
            return g.__dict__
        post_app = Flask(__name__)
        @post_app.route('/')
        def test_index():
            return g.__dict__
        Flarf(post_app)
        self.app = post_app
        self.pre_app = pre_app

    def tearDown(self):
        self.pre_app = None

    def test_request_filter(self):
        with self.app.test_request_context('/'):
            self.assertTrue(request.path == '/')
            self.app.preprocess_request()
            self.assertIsNotNone(self.app.extensions['flarf'])
            self.assertIsNotNone(getattr(g, 'preprocessed', None))

    def test_filter_params(self):
        Flarf(self.pre_app, filter_params=['path', 'args'])
        with self.pre_app.test_request_context('/?argument=1'):
            self.pre_app.preprocess_request()
            self.assertEqual(g.preprocessed.args['argument'], '1')

    def test_custom_preprocess(self):
        class TestPreProcessRequest(object):
            def __init__(self, request):
                self.request = request
                self.request_path = request.path
            def which_path(self):
                return self.request_path
        Flarf(self.pre_app, filter_cls=TestPreProcessRequest)
        with self.pre_app.test_request_context('/'):
            self.assertTrue(request.path == '/')
            self.pre_app.preprocess_request()
            self.assertEqual(g.preprocessed.which_path(), '/')

    def test_custom_filter_function(self):
        def custom_function_to_g(request):
            g.custom_function_to_g = True
        Flarf(self.pre_app, filter_func=custom_function_to_g)
        with self.pre_app.test_request_context('/'):
            self.pre_app.preprocess_request()
            self.assertTrue(g.custom_function_to_g)

    def test_pass_routes(self):
        @self.pre_app.route('/passme')
        def passme():
            return g.__dict__
        Flarf(self.pre_app, filter_pass=['passme'])
        with self.pre_app.test_request_context('/passme'):
            self.pre_app.preprocess_request()
            with self.assertRaises(AttributeError):
                g.preprocessed

    def test_additional_filtering(self):
        def do_something_extra(request):
            return (request.path, request.args['what'])
        Flarf(self.pre_app, filter_additional={'additional': do_something_extra})
        with self.pre_app.test_request_context('/?what=wat'):
            self.pre_app.preprocess_request()
            self.assertEqual(g.additional, (u'/', 'wat'))

if __name__ == '__main__':
    unittest.main()
