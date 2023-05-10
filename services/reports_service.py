import logging
from datetime import datetime

from database.db_connection import connect_to_bot
from models.group_leader import GroupLeader
from models.join_request import JoinRequest
from models.user import User


def get_report():
    try:
        connect_to_bot.connect(reuse_if_open=True)
        logging.info('Выполнено подключение к БД')
        reports = (JoinRequest
                   .select()
                   .join(GroupLeader, on=(JoinRequest.leader == GroupLeader.id))
                   .join(User, on=(JoinRequest.user == User.id))
                   .prefetch(GroupLeader, User))
        report_text = []
        for report in reports:
            report_text.append(
                f'<b>Дата: </b> {datetime.strftime(report.request_date, "%d.%m.%Y")}\n'
                f'<b>Лидер: </b>{report.leader.name}\n'
                f'<b>Имя: </b>{report.user.username}\n'
                f'<b>Телеграм: </b>{report.user.telegram_login}\n'
                f'------------------------\n'
            )
        return report_text
    except Exception as e:
        logging.error(f'Ошибка выгрузки отчета о заявках на ДГ: {e}')
        return None
    finally:
        connect_to_bot.close()
