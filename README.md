Flask request filter

Flarf allows you to filter flask request to your specification within your application.

Example for example purposes only (see example app in examples directory): 

    example.py:
    ------

    from flask import Flask
    from flask.ext.flarf import Flarf, FlarFilter

    def format_from_request(request):
        return """
               HEADER: {}\n
               header: {}\n
               METHOD: {}\n
               ARGS: {}\n
               """.format(request.headers.upper(),
                          request.headers,
                          request.method.lower(),
                          request.args)

    flarf_filter = FlarfFilter(filter_tag='flarf_filter',
                               filter_params=[format_from_request, 'my_val'],
                               filter_on=['includeme'])

    app = Flask(__name__)
    Flarf(app, filters=[flarf_filter])

    @app.route("/includeme")
    def index():
       return render_template("index.html")


    index.html:
    ----------

    MY_VAL: {{flarf_filter.my_val|safe}}
    MY_REQUEST: {{ flarf_filter.format_from_request|safe}}

    Run the app and visit: http://127.0.0.1:5000/includeme?my_val="helloworld" 

Suggestions, input, & improvements welcomed.
