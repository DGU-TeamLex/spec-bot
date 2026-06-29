#!/usr/bin/env python3
"""발신자 tngod5099@gmail.com 의 미처리 기능명세서 메일을 JSON 배열로 출력.

환경변수: GMAIL_ADDRESS, GMAIL_APP_PASSWORD
출력: [] (없음) 또는 [{uid, subject, from, date, body, attachments}, ...]
'TeamLex-Processed' 라벨이 붙은 메일은 제외(중복 방지).
"""
import os
import json
import imaplib
import email
import re
from email.header import decode_header

ADDR = os.environ["GMAIL_ADDRESS"]
PW = os.environ["GMAIL_APP_PASSWORD"]
LABEL = "TeamLex-Processed"
SENDER = "tngod5099@gmail.com"


def dec(v):
    if not v:
        return ""
    return "".join(
        t.decode(e or "utf-8", "replace") if isinstance(t, bytes) else t
        for t, e in decode_header(v)
    )


def html2txt(h):
    h = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<br\s*/?>", "\n", h)
    h = re.sub(r"(?is)</p>", "\n", h)
    t = re.sub(r"(?is)<[^>]+>", " ", h)
    t = re.sub(r"&nbsp;", " ", t)
    return re.sub(r"[ \t]+", " ", t).strip()


def body(msg):
    parts, atts = [], []
    if msg.is_multipart():
        for p in msg.walk():
            disp = str(p.get("Content-Disposition") or "")
            if "attachment" in disp:
                fn = dec(p.get_filename())
                if fn:
                    atts.append(fn)
                continue
            try:
                pl = p.get_payload(decode=True)
                if pl is None:
                    continue
                txt = pl.decode(p.get_content_charset() or "utf-8", "replace")
            except Exception:
                continue
            if p.get_content_type() == "text/plain":
                parts.append(txt)
            elif p.get_content_type() == "text/html":
                parts.append(html2txt(txt))
    else:
        pl = msg.get_payload(decode=True)
        if pl:
            txt = pl.decode(msg.get_content_charset() or "utf-8", "replace")
            if msg.get_content_type() == "text/html":
                txt = html2txt(txt)
            parts.append(txt)
    return "\n".join(parts).strip(), atts


im = imaplib.IMAP4_SSL("imap.gmail.com")
im.login(ADDR, PW)
im.select("INBOX")
q = "from:%s newer_than:60d -label:%s" % (SENDER, LABEL)
im.literal = q.encode("utf-8")
t, d = im.uid("SEARCH", "CHARSET", "UTF-8", "X-GM-RAW")
uids = d[0].split() if (t == "OK" and d and d[0]) else []
out = []
for u in uids:
    t, f = im.uid("FETCH", u, "(RFC822)")
    if t != "OK" or not f or f[0] is None:
        continue
    msg = email.message_from_bytes(f[0][1])
    b, atts = body(msg)
    out.append({
        "uid": u.decode(),
        "subject": dec(msg.get("Subject")),
        "from": dec(msg.get("From")),
        "date": dec(msg.get("Date")),
        "body": b[:20000],
        "attachments": atts,
    })
im.logout()
print(json.dumps(out, ensure_ascii=False))
