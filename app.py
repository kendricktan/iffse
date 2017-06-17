import os
import jinja2

from sanic import Sanic, response
from sanic_cors import CORS, cross_origin

app = Sanic(__name__)
CORS(app)


def render_jinja2(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


@app.route('/')
async def index(request):
    html_ = render_jinja2('./templates/index.html', {'WHAT': 'niggas'})
    return response.html(html_)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
