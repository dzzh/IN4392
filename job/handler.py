import matrix
import web
from web import form

render = web.template.render('templates/')
urls = (
    '/', 'index'
    )

app = web.application(urls, globals())

matrix_mult_form = form.Form(
    form.Textbox('dim',
        form.notnull,
        form.regexp('\d+', 'Must be a number'),
        form.Validator('Must be between 10 and 1000', lambda x: int(x) >= 10 and int(x) <= 1000),
        description='Matrices dimension',
        value="100",
    ),
    form.Button('Multiply',
        class_='btn')
)

class index:
    def GET(self):
        form = matrix_mult_form()
        return render.form(form)

    def POST(self):
        form = matrix_mult_form()
        if not form.validates():
            return render.form(form)
        else:
            return render.result(matrix.compute(int(form['dim'].value)))

if __name__ == "__main__":
    web.internalerror = web.debugerror
    app.run()

