from tests import *


class FlarfBase(FlarfTest):
    def test_base(self):
        with self.base_app.test_request_context('/'):
            self.base_app.preprocess_request()
            self.assertIsNotNone(self.base_app.extensions['flarf'])
            self.assertIsNotNone(getattr(g, 'test_filter1', None))


class FlarfFilters(FlarfTest):
    def test_filters(self):
        Flarf(self.pre_app, filters=self.test_filters2)
        with self.pre_app.test_request_context('/app_route?zed=z'):
            self.pre_app.preprocess_request()
            self.assertIsNotNone(getattr(g, 'test_filter3', None))
            self.assertEqual(getattr(g, 'test_filter3', None),
                             getattr(g, 'test_filter3', None))
            self.assertEqual(g.test_filter1.path_to_upper, u'/APP_ROUTE')
            self.assertEqual(u'/app_route', g.test_filter3.path)
            self.assertEqual(g.test_filter1.path,
                             g.test_filter3.path)


class FlarfContext(FlarfTest):
    def test_context_processor(self):
        Flarf(self.pre_app, filters=self.test_filters2)
        with self.pre_app.test_client() as ct:
            rv = ct.get('/context_processor?zed=z')
            self.assertIsNotNone(rv.data)
            self.assertEqual(rv.data.decode(), g.test_filter2.zed)


class FlarfCustomize(FlarfTest):
    def test_custom_before_request_func(self):
        Flarf(self.pre_app,
              filters=self.test_filters2,
              before_request_func=self.custom_before_func)
        with self.pre_app.test_request_context('/'):
            self.pre_app.preprocess_request()
            self.assertTrue(g.custom_before_func)

    def test_custom_filter_cls(self):
        Flarf(self.pre_app,
              filter_cls=self.custom_filter,
              filters=self.test_filters3)
        with self.pre_app.test_request_context('/'):
            self.pre_app.preprocess_request()
            self.assertTrue(g.custom_filter_run)
            self.assertEqual('something', g.test_filter4.something)
        with self.pre_app.test_client() as ct:
            rv = ct.get('/app_route')
            self.assertEqual(rv.status_code, 302)


class FlarfRoutes(FlarfTest):
    def test_include_route(self):
        Flarf(self.pre_app,
              filters=self.test_filters4)
        with self.pre_app.test_request_context('/includeme'):
            self.pre_app.preprocess_request()
            self.assertTrue(g.test_filter6.path)
            self.assertEqual(g.test_filter6.path, u'/includeme')

    def test_exclude_route(self):
        Flarf(self.pre_app,
              filters=self.test_filters4)
        with self.pre_app.test_request_context('/passme'):
            self.pre_app.preprocess_request()
            with self.assertRaises(AttributeError):
                g.test_filter4


if __name__ == '__main__':
    unittest.main()
