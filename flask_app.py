import os
import pandas as pd
import datetime
from dotenv import load_dotenv, find_dotenv
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
from flask import Flask, render_template, jsonify, request

from api.device_info.db import create_tables as create_device_table
from api.customer_emails.db import create_tables as create_email_table
from api.tasks import energy_alert, register_energy_alert_task
from api.validation_schema import EnergyAlertTaskSchema, GenReportSchema
from api.utils import message_resp, send_mail, gen_report
from api.device_info.routes import device_bp
from api.device_info.controllers import get_device_info
from api.customer_emails.routes import customer_bp


app = Flask(__name__)
app.register_blueprint(device_bp, url_prefix="/science/device")
app.register_blueprint(customer_bp, url_prefix="/science/emails")

# mail_list = [
#     'phuong.huynhtuan@thecoffeehouse.vn',
#     'an.nguyen@seedcom.vn',
#     'thinh.huynhhuy@thecoffeehouse.vn',
#     'hai.hoang@thecoffeehouse.vn',
#     'luan.nguyen@seedcom.vn'
# ]

# mail_list = ["nhat.thai@lab2lives.com"]
mail_list = ["nhat.thai@lab2lives.com", "thomas.luu@lab2lives.com"]


@app.route("/science/")
def hello():
    return render_template("home.html")


@app.route("/science/v1/daily-report", methods=["GET"])
def dailyReport():
    records = get_device_info()
    df_info = pd.DataFrame(
        records,
        columns=[
            "no",
            "user_id",
            "user_name",
            "device_id",
            "device_name",
            "status",
            "outdoor_unit",
        ],
    )
    df_info = df_info.drop(columns="no")

    # request_data = request.args
    # schema = GenReportSchema()
    # try:
    #     data = schema.load(request_data)
    #     user_id = data["user_id"]
    #     track_day = data["track_day"]g
    # except ValidationError as err:
    #     return message_resp(err.messages, 400)

    date = datetime.datetime.now() - datetime.timedelta(days=1)
    print(date)
    track_day = "{}-{:02d}-{:02d}".format(date.year, date.month, date.day)

    ids = ["10019", "11294", "11296"]

    for user_id in ids:
        gen_report(df_info, user_id, track_day)
        send_mail(df_info, user_id, track_day, mail_list)

    return message_resp()


@app.route("/science/health/")
def health():
    return message_resp()


@app.route(
    "/science/v1/energy-alert-handler", methods=["POST"],
)
def alert():
    request_data = request.json
    schema = EnergyAlertTaskSchema()
    try:
        valid_data = schema.load(request_data)
        status_code = energy_alert(valid_data)
        return message_resp("succeed", status_code)
    except ValidationError as err:
        return message_resp(err.messages, 400)


@app.route("/science/v1/energy-alert-task", methods=["POST"])
def energy_alert_task():
    request_data = request.json
    schema = EnergyAlertTaskSchema()
    try:
        valid_data = schema.load(request_data)
        tast_name = register_energy_alert_task(valid_data)
        return message_resp("Created task {}".format(tast_name), 201)
    except ValidationError as err:
        return message_resp(err.messages, 400)


@app.errorhandler(Exception)
def global_error_handler(e):
    code = 400
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error="Something went wrong"), code


if __name__ == "__main__":
    os.environ['TZ'] = 'Asia/Ho_Chi_Minh'
    load_dotenv(find_dotenv())
    create_device_table()
    create_email_table()

    # records = get_device_info()
    # df_info = pd.DataFrame(
    #     records,
    #     columns=[
    #         "no",
    #         "user_id",
    #         "user_name",
    #         "device_id",
    #         "device_name",
    #         "status",
    #         "outdoor_unit",
    #     ],
    # )
    # df_info = df_info.drop(columns="no")
    #
    # user_id = '10019'
    # track_day = '2022-03-31'
    #
    # gen_report(df_info, user_id, track_day)
    # send_mail(df_info, user_id, track_day, mail_list)

    server_port = os.environ.get("PORT", "8080")
    app.run(debug=False, port=server_port, host="0.0.0.0")

