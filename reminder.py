import os
import requests


def send_reminder():
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    message = (
        "🔔 복귀 알림! 오늘 19:30 출발 전 확인!\n"
        "\n"
        "□ 교정 유지장치\n"
        "□ 휴가증\n"
        "□ 패스\n"
        "□ 카드\n"
        "\n"
        "다 챙겼으면 출발! 🫡"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": message})
    resp.raise_for_status()
    print("메시지 전송 완료!")


if __name__ == "__main__":
    send_reminder()
