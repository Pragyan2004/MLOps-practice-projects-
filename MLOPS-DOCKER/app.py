from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/greet', methods=['POST'])
def greet():
    user_input = request.form.get('username', 'Guest')
    return render_template('greet.html', username=user_input)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)