#!/usr/bin/env python3
#-*- coding:utf-8 -*'
import os
import sys
import time
import json
import html
import urllib
import configparser
from string import Template
from argparse import ArgumentParser

import requests
from slackclient import SlackClient

api = {
    'gist': 'https://api.github.com/gists',
    'playpen': 'https://play.rust-lang.org/evaluate.json',
    'bitly': 'https://api-ssl.bitly.com/v3/shorten'
}

class RustBot(object):
    def __init__(self, uid, slack_token, bitly_token, template):
        self.uid = uid
        self.slack_token = slack_token
        self.bitly_token = bitly_token
        self.slack_client = None
        self.template = template

    def connect(self):
        self.slack_client = SlackClient(self.slack_token)
        self.slack_client.rtm_connect()

    def start(self):
        self.connect()
        info = self.slack_client.api_call('users.info', user=self.uid).decode('utf-8')
        info = json.loads(info)
        if info.get('user') and info.get('user').get('is_bot'):
            botname = info.get('user').get('name')
        else:
            print("Error: can't get bot name")
            return
        while True:
            for event in self.slack_client.rtm_read():
                if event.get('type') == 'message' and event.get('text'):
                    try:
                        channel, text, user = event['channel'], event['text'], event['user']
                    except KeyError:
                        continue
                    text = html.unescape(text.strip())
                    if text.startswith('<@{}>'.format(self.uid)) or text.startswith(botname):
                        print(event)
                        contents = text.split(' ', 1)
                        if len(contents) == 1:
                            continue
                        else:
                            content = contents[1].lstrip()
                        reply = self.process_text(user, content)
                        if reply:
                            self.slack_client.rtm_send_message(channel=channel, message=reply)
                time.sleep(0.1)

    def process_text(self, user, text):
        if text.startswith('!'):
            if text.startswith('!rustc'):
                snippet = text.lstrip('!rustc:').lstrip()
                code = self.wrap_code(snippet)
                url, result = self.evaluate(code)
                if url:
                    return "<@{}>: :scream_cat:\n```{}```\nFor details {}".format(user, result, url)
                elif result:
                    return "<@{}>: :+1:\n```{}```".format(user, result)
                else:
                    return None
            elif text.startswith('!crate'):
                # to be implemented
                return None
            elif text.startswith('!doc'):
                # to be implemented
                return None
            elif text.startswith('!example'):
                # to be implemented
                return None
        else:
            code = self.wrap_code(text)
            url, result = self.evaluate(code)
            if url:
                return "<@{}>: :scream_cat:\n```{}```\nFor details {}".format(user, result, url)
            elif result:
                return "<@{}>: :+1:\n```{}```".format(user, result)
            else:
                return None

    def share(self, code, version='stable'):
        code = urllib.parse.quote(code, safe='!')
        longUrl = 'https://play.rust-lang.org/?run=1&code={}&version={}'.format(code, version)
        params = {'access_token': self.bitly_token, 'longUrl': longUrl}
        r = requests.get(api['bitly'], params=params)
        json_data = json.loads(r.text)
        shortenUrl = json_data['data']['url']
        return shortenUrl

    def share_by_gist(self, code):
        params = {
            'description': "Shared by Chinese Rustaceans",
            'public': True,
            'files': {
                'playground.rs': {
                    'content': code
                }
            }
        }
        r = requests.post(api['gist'], json=params)
        response = json.loads(r.text)
        gist_id = response.get('id')
        share_url = 'https://play.rust-lang.org/?run=1&gist={}&version=stable'.format(gist_id)
        return share_url

    def evaluate(self, code, version='stable'):
        playpen['code'] = code
        r = requests.post(api['playpen'], json=playpen)
        json_data = json.loads(r.text)
        if json_data.get('rustc'): # error
            url = self.share(code)
            return url, json_data.get('rustc')
        elif json_data.get('program'): # success
            return None, json_data.get('program')
        else:                   # unknown
            return None, None
            

    def wrap_code(self, text):
        code = self.template.substitute(snippet=text)
        return code

def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        help='Full path to config file',
        metavar='path'
    )
    return parser.parse_args()

if __name__ == "__main__":
    with open('template.rs') as f:
        tmpl = f.read()
    template = Template(tmpl)
    with open('playpen.json') as f:
        playpen = json.load(f)

    args = parse_args()
    config = configparser.ConfigParser()
    config.read(args.config or 'rustbot.conf')

    slack_token = config.get('slack', 'token', fallback=None)
    bitly_token = config.get('bitly', 'token', fallback=None)
    botid = config.get('slack', 'botid', fallback='U0CG0Q57Z')
    if slack_token and bitly_token:
        bot = RustBot(botid, slack_token, bitly_token, template)
        try:
            bot.start()
        except KeyboardInterrupt:
            pass
    else:
        print("Error: missing access tokens for slack or bitly")
