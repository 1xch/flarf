from flask import Flask, render_template
from flask_flarf import Flarf, FlarfFilter

def format_from_request(request):
    return """
            HEADER: {}\n<br>
            <br>
            header: {}\n<br>
            <br>
            METHOD: {}\n<br>
            <br>
            ARGS: {}\n<br>
            """.format(str(request.headers).upper(),
                       request.headers,
                       request.method.lower(),
                       request.args)

flarf_filter1 = FlarfFilter(filter_tag='flarf_filter1',
                            filter_params=[format_from_request, 'my_val'],
                            filter_on=['index'])

flarf_filter2 = FlarfFilter(filter_tag='flarf_filter2',
                            filter_params=[format_from_request, 'my_val'],
                            filter_pass=[u'/dontincludeme'])

flarf_filter3 = FlarfFilter(filter_tag='flarf_filter3',
                            filter_params=[format_from_request, 'my_val'])




app = Flask(__name__)
Flarf(app, filters=[flarf_filter1, flarf_filter2, flarf_filter3])

@app.route("/includeme")
def index():
    return render_template("index.html")

@app.route('/justhere')
def anyroute():
    return render_template("index.html")

@app.route("/dontincludeme")
def nothing():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
