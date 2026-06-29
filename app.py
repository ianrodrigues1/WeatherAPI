import os

from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS

from routes.weather import weather_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(weather_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/widget.js")
    def widget_script():
        return send_from_directory("widget", "widget.js")

    @app.get("/health")
    def health_check():
        return jsonify({"status": "ok", "service": "Weather API"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
