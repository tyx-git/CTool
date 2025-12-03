from PyQt5.QtWidgets import QTextBrowser
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QGuiApplication
import base64


class MarkdownView(QTextBrowser):
    """只读 Markdown 展示控件，处理复制按钮 copy:BASE64 链接，并统一样式。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)
        self.anchorClicked.connect(self._on_anchor_clicked)
        # 统一样式，避免每次插入内容都注入 <style>
        base_css = (
            ".md-body, .md-body p { line-height: 1.2; margin: 0.4em 0; }\n"
            ".md-body pre { background:#f8f9fa; border:1px solid #dee2e6; border-radius:4px; padding:8px; margin:0.4em 0; white-space: pre-wrap; max-height:360px; overflow:auto; }\n"
            ".md-body code { background:#f8f9fa; border:1px solid #dee2e6; border-radius:3px; padding:0 3px; }\n"
            ".md-body ul, .md-body ol { padding: 0 1em; }\n"
            ".md-body table { border-collapse: collapse; width: 100%; margin: 0.6em 0; }\n"
            ".md-body th, .md-body td { border: 1px solid #dee2e6; padding: 6px 8px; text-align: left; }\n"
            ".md-body blockquote { border-left: 3px solid #dee2e6; padding: 0.2em 0.8em; color: #555; }\n"
            ".md-codeblock { position: relative; }\n"
            ".md-codeblock .md-copy { position: absolute; top: 6px; right: 8px; font-size: 12px; background:#eee; border:1px solid #ccc; border-radius:4px; padding:2px 6px; color:#333; text-decoration:none; cursor: pointer; }\n"
        )
        try:
            current_css = self.document().defaultStyleSheet() or ""
            self.document().setDefaultStyleSheet(current_css + "\n" + base_css)
        except Exception:
            pass

    def _on_anchor_clicked(self, url: QUrl):
        if url.scheme() == 'copy':
            try:
                data_b64 = url.toString()[len('copy:'):]
                text = base64.b64decode(data_b64).decode('utf-8')
                QGuiApplication.clipboard().setText(text)
            except Exception:
                pass
        else:
            # 忽略其他链接或按需扩展
            pass

