#!/usr/bin/env python3
"""처리한 메일에 'TeamLex-Processed' 라벨을 붙인다 (중복 처리 방지).

환경변수: GMAIL_ADDRESS, GMAIL_APP_PASSWORD
사용: python3 scripts/mark_processed.py <uid>
"""
import os
import sys
import imaplib

im = imaplib.IMAP4_SSL("imap.gmail.com")
im.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
im.select("INBOX")
im.uid("STORE", sys.argv[1], "+X-GM-LABELS", "TeamLex-Processed")
im.logout()
print("labeled", sys.argv[1])
