Rustbot for Slack

This is a rustbot for [Chinese Rustacean Slack](https://rust-china.slack.com)

It can let Slack users to evaluate Rust code when chatting

# Requirement

This bot runs with Python3

You also need to get Slack token, Bitly token.

# Setup

```
git clone https://github.com/tennix/rustbot4slack
cd rustbot4slack
pyvenv env
source env/bin/activate
pip3 install -r requirements.txt
mkdir -p secret
python rustbot.py -c secret/rustbot.conf
```
