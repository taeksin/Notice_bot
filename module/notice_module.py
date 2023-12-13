import re
import time
import logging
import requests
import jwt
import uuid
import hashlib
import math
import os
import pandas as pd
import numpy
import telegram
from urllib.parse import urlencode
from decimal import Decimal
from datetime import datetime
from ast import literal_eval

# Telegram Keys
telegram_token = ''
telegram_id = ''

# -----------------------------------------------------------------------------
# - Name : set_loglevel
# - Desc : 로그레벨 설정
# - Input
#   1) level : 로그레벨
#     1. D(d) : DEBUG              ① DEBUG : 상세한 로그를 보고 싶은 경우
#     2. E(e) : ERROR              ② INFO : 정보성 로그를 보고 싶은 경우
#     3. 그외(기본) : INFO          ③ ERROR : 에러 로그를 보고 싶은 경우
# - Output
# -----------------------------------------------------------------------------


def set_loglevel(level):
    try:

        # ---------------------------------------------------------------------
        # 로그레벨 : DEBUG
        # ---------------------------------------------------------------------
        if level.upper() == "D":
            logging.basicConfig(
                format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]:%(message)s',
                datefmt='%Y/%m/%d %I:%M:%S %p',
                level=logging.DEBUG
            )
        # ---------------------------------------------------------------------
        # 로그레벨 : ERROR
        # ---------------------------------------------------------------------
        elif level.upper() == "E":
            logging.basicConfig(
                format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]:%(message)s',
                datefmt='%Y/%m/%d %I:%M:%S %p',
                level=logging.ERROR
            )
        # ---------------------------------------------------------------------
        # 로그레벨 : INFO
        # ---------------------------------------------------------------------
        else:
            # -----------------------------------------------------------------------------
            # 로깅 설정
            # 로그레벨(DEBUG, INFO, WARNING, ERROR, CRITICAL)
            # -----------------------------------------------------------------------------
            logging.basicConfig(
                format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]:%(message)s',
                datefmt='%Y/%m/%d %I:%M:%S %p',
                level=logging.INFO
            )

    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise


# -----------------------------------------------------------------------------
# - Name : send_telegram_msg
# - Desc : 텔레그램 메세지 전송
# - Input
#   1) message : 메세지
# -----------------------------------------------------------------------------
def send_telegram_message(message):
    try:
        # 텔레그램 메세지 발송
        bot = telegram.Bot(telegram_token)
        res = bot.sendMessage(chat_id=telegram_id, text=message)

        return res

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise
# -----------------------------------------------------------------------------
# - Name : send_msg
# - Desc : 메세지 전송
# - Input
#   1) sent_list : 메세지 발송 내역
#   2) key : 메세지 키
#   3) contents : 메세지 내용
#   4) msg_intval : 메세지 발송주기
# - Output
#   1) sent_list : 메세지 발송 내역
# -----------------------------------------------------------------------------
def send_msg(sent_list, key, contents, msg_intval):
    try:

        # msg_intval = 'N' 이면 메세지 발송하지 않음
        if msg_intval.upper() != 'N':

            # 발송여부 체크
            sent_yn = False

            # 발송이력
            sent_dt = ''

            # 발송내역에 해당 키 존재 시 발송 이력 추출
            for sent_list_for in sent_list:
                if key in sent_list_for.values():
                    sent_yn = True
                    sent_dt = datetime.strptime(sent_list_for['SENT_DT'], '%Y-%m-%d %H:%M:%S')

            # 기 발송 건
            if sent_yn:

                logging.info('기존 발송 건')

                # 현재 시간 추출
                current_dt = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

                # 시간 차이 추출
                diff = current_dt - sent_dt

                # 발송 시간이 지난 경우에는 메세지 발송
                if diff.seconds >= int(msg_intval):

                    logging.info('발송 주기 도래 건으로 메시지 발송 처리!')

                    # 메세지 발송
                    send_telegram_message(contents)

                    # 기존 메시지 발송이력 삭제
                    for sent_list_for in sent_list[:]:
                        if key in sent_list_for.values():
                            sent_list.remove(sent_list_for)

                    # 새로운 발송이력 추가
                    sent_list.append({'KEY': key, 'SENT_DT': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

                else:
                    logging.info('발송 주기 미 도래 건!')

            # 최초 발송 건
            else:
                logging.info('최초 발송 건')

                # 메세지 발송
                send_telegram_message(contents)

                # 새로운 발송이력 추가
                sent_list.append({'KEY': key, 'SENT_DT': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

        return sent_list

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise
# -----------------------------------------------------------------------------
# - Name : read_file
# - Desc : 파일 조회
# - Input
# 1. name : File Name
# - Output
# 1. 변수값
# -----------------------------------------------------------------------------
def read_file(name):
    try:

        file_to_listofdict = []

        path = './conf/' + str(name) + '.txt'

        f = open(path, 'r', encoding='UTF8')
        lines = f.read().splitlines()
        f.close()

        for line in lines:
            txt_to_dict = literal_eval(line)
            file_to_listofdict.append(txt_to_dict)

        return file_to_listofdict

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except FileNotFoundError:
        logging.info('파일이 존재하지 않습니다! 파일을 생성합니다. 파일명[' + str(name) + '.txt]')

        with open(path, "w", encoding="utf-8") as f:
            f.close()

        logging.info('파일 생성 완료. 파일명[' + str(name) + '.txt]')
        return None

    except Exception:
        raise


# -----------------------------------------------------------------------------
# - Name : write_config_append
# - Desc : 파일 쓰기(추가)
# - Input
# 1. name : Config File Name
# 2. req_val : 변수값
# - Output
# -----------------------------------------------------------------------------
def write_config_append(name, req_val):
    try:

        # 파일명
        file_name = './module/' + str(name) + '.txt'

        # 파일에 저장(추가하기)
        with open(file_name, "a", encoding="utf-8") as f:
            f.write(str(req_val))
            f.close()

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise

# -----------------------------------------------------------------------------
# - Name : write_config
# - Desc : 파일 쓰기(새로쓰기)
# - Input
# 1. name : Config File Name
# 2. req_val : 변수값
# - Output
# -----------------------------------------------------------------------------
def write_config(name, req_val):
    try:

        # 파일명
        file_name = './module/' + str(name) + '.txt'

        # 파일에 저장
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(str(req_val))
            f.write("\n")
            f.close()

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise
# -----------------------------------------------------------------------------
# - Name : get_env_keyvalue
# - Desc : 환경변수 읽어오기
# - Input
#   1) key : key
# - Output
#   1) Value : 키에 대한 값
# -----------------------------------------------------------------------------
def get_env_keyvalue(key):
    try:
        path = './env/env.txt'

        f = open(path, 'r', encoding='UTF8')
        line = f.readline()
        f.close()

        env_dict = literal_eval(line)
        logging.debug(env_dict)

        return env_dict[key]

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise
    