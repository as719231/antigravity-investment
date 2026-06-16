#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace the share toolbar section in app.py with HTML export button"""

with open('app.py', encoding='utf-8') as f:
    content = f.read()

OLD = '''        # ── 分享工具列 ────────────────────────────────────────────
        import datetime as _dt
        _ts  = _dt.datetime.now().strftime("%Y%m%d_%H%M")
        _fname = f"AI分析報告_{stock_id}_{_ts}.md"
        _md_content = f"# AI 分析報告 — {stock_id}\\n> 分析觀點：{viewpoint_short}  \\n> 產出時間：{_dt.datetime.now().strftime('%Y-%m-%d %H:%M')}\\n\\n---\\n\\n{ai_news_report}"

        _dl_col, _cp_col, _ = st.columns([1, 1, 4])
        with _dl_col:
            st.download_button(
                label="📥 下載報告 (.md)",
                data=_md_content.encode("utf-8"),
                file_name=_fname,
                mime="text/markdown",
                use_container_width=True,
                key="news_download_btn"
            )
        with _cp_col:
            with st.expander("📋 展開複製純文字"):
                st.code(ai_news_report, language=None)'''

NEW = '''        # ── 分享工具列：匯出精美 HTML（保留完整排版）────────────
        import datetime as _dt, re as _re
        _ts    = _dt.datetime.now().strftime("%Y%m%d_%H%M")
        _now   = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        _fname = f"AI分析報告_{stock_id}_{_ts}.html"

        def _md_to_html(text):
            import re
            # 表格
            def _tbl(m):
                rows = [r for r in m.group(0).strip().splitlines() if r.strip()]
                html, hdr = [], True
                for row in rows:
                    if re.match(r'^\\s*\\|?[-: |]+\\|?\\s*$', row):
                        hdr = False; continue
                    cells = [c.strip() for c in row.strip().strip('|').split('|')]
                    tag = 'th' if hdr else 'td'
                    html.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
                    hdr = False
                return '<table>' + ''.join(html) + '</table>'
            text = re.sub(r'(\\|[^\\n]+\\n)+', _tbl, text)
            # 標題
            text = re.sub(r'^####\\s+(.+)$', r'<h4>\\1</h4>', text, flags=re.MULTILINE)
            text = re.sub(r'^###\\s+(.+)$',  r'<h3>\\1</h3>', text, flags=re.MULTILINE)
            text = re.sub(r'^##\\s+(.+)$',   r'<h2>\\1</h2>', text, flags=re.MULTILINE)
            text = re.sub(r'^#\\s+(.+)$',    r'<h1>\\1</h1>', text, flags=re.MULTILINE)
            # 粗體/斜體
            text = re.sub(r'\\*\\*\\*(.+?)\\*\\*\\*', r'<strong><em>\\1</em></strong>', text)
            text = re.sub(r'\\*\\*(.+?)\\*\\*',       r'<strong>\\1</strong>', text)
            text = re.sub(r'\\*(.+?)\\*',             r'<em>\\1</em>', text)
            # 條列
            lines_in = text.split('\\n'); out = []; in_ul = False
            for ln in lines_in:
                if re.match(r'^\\s*[-*]\\s+', ln):
                    if not in_ul: out.append('<ul>'); in_ul = True
                    out.append('<li>' + re.sub(r'^\\s*[-*]\\s+','',ln) + '</li>')
                else:
                    if in_ul: out.append('</ul>'); in_ul = False
                    out.append(ln)
            if in_ul: out.append('</ul>')
            text = '\\n'.join(out)
            text = re.sub(r'^\\s*---+\\s*$', '<hr>', text, flags=re.MULTILINE)
            text = re.sub(r'^>\\s+(.+)$', r'<blockquote>\\1</blockquote>', text, flags=re.MULTILINE)
            paras = re.split(r'\\n{2,}', text); result = []
            for p in paras:
                p = p.strip()
                if p and not any(p.startswith(t) for t in ['<h','<ul','<ol','<table','<hr','<block']):
                    p = '<p>' + p.replace('\\n','<br>') + '</p>'
                result.append(p)
            return '\\n'.join(result)

        _body = _md_to_html(ai_news_report)
        _vp   = viewpoint_short

        _html = f"""<!DOCTYPE html>
<html lang="zh-TW"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI 分析報告 — {stock_id}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;600;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0b0f19;--card:#131929;--bdr:#1e293b;--txt:#e2e8f0;--muted:#94a3b8;--acc:#38bdf8;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--txt);font-family:'Noto Sans TC','Inter',sans-serif;font-size:15px;line-height:1.8;}}
.wrap{{max-width:900px;margin:0 auto;padding:32px 24px 64px;}}
.hdr{{background:linear-gradient(135deg,#0f172a,#1e293b);border:1px solid var(--bdr);border-radius:16px;padding:28px 32px;margin-bottom:28px;}}
.hdr h1{{font-size:1.55rem;font-weight:700;color:var(--acc);margin-bottom:8px;}}
.badge{{display:inline-block;background:rgba(56,189,248,.12);color:var(--acc);border:1px solid rgba(56,189,248,.3);border-radius:20px;padding:3px 12px;font-size:.8rem;font-weight:600;margin-right:8px;}}
.body{{background:var(--card);border:1px solid var(--bdr);border-radius:16px;padding:32px;}}
h1,h2{{color:var(--acc);font-size:1.2rem;font-weight:700;margin:28px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--bdr);}}
h3{{color:#f8fafc;font-size:1.05rem;font-weight:700;margin:18px 0 8px;}}
h4{{color:var(--muted);font-size:.95rem;margin:14px 0 6px;}}
p{{margin:8px 0 10px;}}
ul{{margin:8px 0 10px 20px;}}
li{{margin-bottom:5px;}}li::marker{{color:var(--acc);}}
table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:.87rem;border-radius:8px;overflow:hidden;}}
th{{background:rgba(56,189,248,.12);color:var(--acc);font-weight:700;padding:10px 14px;text-align:left;border:1px solid var(--bdr);}}
td{{padding:9px 14px;border:1px solid var(--bdr);}}
tr:nth-child(even) td{{background:rgba(30,41,59,.4);}}
hr{{border:none;border-top:1px solid var(--bdr);margin:22px 0;}}
blockquote{{border-left:4px solid var(--acc);padding:8px 16px;margin:10px 0;background:rgba(56,189,248,.06);border-radius:0 8px 8px 0;color:var(--muted);font-style:italic;}}
strong{{color:#f8fafc;font-weight:700;}}
.foot{{text-align:center;margin-top:36px;color:var(--muted);font-size:.78rem;}}
</style></head><body>
<div class="wrap">
<div class="hdr">
<h1>📊 AI 分析報告 — {stock_id}</h1>
<div><span class="badge">{_vp}</span><span class="badge">產出時間：{_now}</span></div>
</div>
<div class="body">{_body}</div>
<div class="foot">由 AI 股市理財助手自動產出 · 僅供參考，非投資建議 · {_now}</div>
</div></body></html>"""

        _btn_col, _ = st.columns([2, 4])
        with _btn_col:
            st.download_button(
                label="📤 匯出 HTML 報告（傳給朋友直接用瀏覽器打開）",
                data=_html.encode("utf-8"),
                file_name=_fname,
                mime="text/html",
                use_container_width=True,
                key="news_html_btn",
                type="primary"
            )
        st.caption("💡 朋友收到 HTML 檔後，用瀏覽器打開即可看到完整排版，不需要任何軟體。")'''

if OLD in content:
    content = content.replace(OLD, NEW)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: share toolbar replaced")
else:
    print("ERROR: target block not found!")
    # Try to find partial match
    idx = content.find('# ── 分享工具列')
    if idx >= 0:
        print(f"Found at char {idx}, line ~{content[:idx].count(chr(10))+1}")
    else:
        print("Block not found at all")
