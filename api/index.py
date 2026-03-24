from jinja2 import Environment, FileSystemLoader
import os

def handler(request):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')

    html = template.render()

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": html
    }