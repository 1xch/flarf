Customizing Flask-Flarf
=======================

Flask-Flarf can be customized beyond base functioning on a per-application
basis at three point:

1. the before_request function that runs all filters
2. the filter class used to filter the request
3. the filtered class where information from the filter is placed

Modify the before request function
==================================

Specify the function you wish to replace the default with as argument 
before_request_func in extension intialization


Modify the filter class
=======================

Specify the custom class you wish to replace the default filter class with 
as argument filter_cls in extension intialization. Subclassing the default class
is recommended to ensure proper intialization filters intialization. 


Modify the filtered class
=========================

Specify the custom class you wish to replace the default filtered class with 
as argument filtered_cls in extension intialization. The default in extension
initialization is None, and and will use the default filtered_cls set in the
filter_cls, but can be set on the extension to impact filters specified as dicts

