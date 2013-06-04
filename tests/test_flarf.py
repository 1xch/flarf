from __future__ import with_statement
import sys
import os
from flask import Flask, render_template, current_app, g, request
from flask.ext.flarf import Flarf, FlarfFilter, flarf
import unittest

class FlarfTestCase(unittest.TestCase):
    def setUp(self):
        test_filter1 = FlarfFilter(filter_tag='test_filter1',
                                   filter_precedence=100,
                                   filter_params=['path',],
                                   filter_on=['includeme'])
        test_filter2 = FlarfFilter(filter_tag='test_filter2',
                                   filter_precedence=200,
                                   filter_params=['args',])
        test_filter3 = {'filter_tag': 'test_filter3',
                        'filter_precedence': 300,
                        'filter_params': ['path', 'args'],
                        'filter_skip':['passme']}
        self.test_filters1 = [test_filter1]
        self.test_filters2 = [test_filter1, test_filter2, test_filter3]
        pre_app = Flask(__name__)
        @pre_app.route('/')
        def test_index():
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

    def test_base(self):
        with self.base_app.test_request_context('/'):
            self.base_app.preprocess_request()
            self.assertIsNotNone(self.base_app.extensions['flarf'])
            self.assertIsNotNone(getattr(g, 'test_filter1', None))
            self.assertIsNotNone(flarf.test_filter1_context)

    def test_filters(self):
        Flarf(self.pre_app, filters=self.test_filters2)
        with self.pre_app.test_request_context('/'):
            self.pre_app.preprocess_request()
            self.assertIsNotNone(getattr(g, 'test_filter3', None))
            self.assertEqual(getattr(g, 'test_filter3', None),
                             getattr(g, 'test_filter3', None))
            self.assertEqual(g.test_filter1.path, u'/')
            self.assertEqual(u'/', g.test_filter3.path)
            self.assertEqual(g.test_filter1.path,
                             g.test_filter3.path)

    def test_custom_before_request_func(self):
        pass

    def test_custom_filter_cls(self):
        pass

    def test_custom_filtered_cls(self):
        pass

    def test_include_route(self):
        @self.pre_app.route('/includeme')
        def includeme():
            return g.__dict__
        Flarf(self.pre_app, filters=self.test_filters2)
        with self.pre_app.test_request_context('/includeme'):
            self.pre_app.preprocess_request()
            self.assertTrue(g.test_filter1.path)
            self.assertEqual(g.test_filter1.path, u'/includeme')

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
