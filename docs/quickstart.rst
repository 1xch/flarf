Quick Start
===========

Requirements: Flask(>v0.9)::


    app.py:
    ------

    from flask import Flask
    from flask.ext.flarf import Flarf, FlarFilter

    def format_from_request(request):
        return """
               HEADER: {}\n
               header: {}\n
               PATH: {}\n
               ARGS: {}\n
               """.format(request.header.upper(),
                          request.header,
                          request.path.upper(),
                          request.args)

    flarf_filter = FlarfFilter(filter_tag='my_first_filter',
                               filter_params=[format_from_request],
                               filter_on=['includeme'])

    app = Flask(__name__)
    Flarf(app, filters=[flarf_filter])

    @app.route("/includeme")
    def index():
        return render_template("index.html")


    index.html:
    -----------

    MY_FIRST_FILTER: {{ my_first_filter.format_from_request  }}
