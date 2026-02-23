"""
Views for logs endpoint.
"""
import os
from django.conf import settings
from django.http import HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required


LOG_FILES = {
    'all': 'all.log',
    'requests': 'requests.log',
    'errors': 'errors.log',
}


class LogViewerView(View):
    """
    View to display log files in the browser.
    Only accessible by staff members.
    """
    @method_decorator(staff_member_required(login_url='/backend-admin/login/'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, log_type='all'):
        # Validate log type
        if log_type not in LOG_FILES:
            log_type = 'all'

        log_filename = LOG_FILES[log_type]
        log_path = os.path.join(settings.LOGS_DIR, log_filename)

        # Get query parameters
        lines = request.GET.get('lines', '500')
        try:
            lines = int(lines)
            lines = min(max(lines, 10), 10000)  # Clamp between 10 and 10000
        except ValueError:
            lines = 500

        auto_refresh = request.GET.get('refresh', '0')
        try:
            auto_refresh = int(auto_refresh)
            auto_refresh = min(max(auto_refresh, 0), 300)  # Clamp between 0 and 300 seconds
        except ValueError:
            auto_refresh = 0

        # Read log file
        log_content = ''
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    # Get last N lines
                    log_content = ''.join(all_lines[-lines:])
            except Exception as e:
                log_content = f'Error reading log file: {str(e)}'
        else:
            log_content = f'Log file not found: {log_filename}\nNo logs have been recorded yet.'

        # Build navigation links
        nav_links = []
        for key, filename in LOG_FILES.items():
            active = 'active' if key == log_type else ''
            nav_links.append(f'<a href="/logs/{key}/?lines={lines}&refresh={auto_refresh}" class="{active}">{key.upper()}</a>')

        # Build HTML response
        refresh_meta = f'<meta http-equiv="refresh" content="{auto_refresh}">' if auto_refresh > 0 else ''

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {refresh_meta}
    <title>Log Viewer - {log_type.upper()}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background-color: #1e1e1e;
            color: #d4d4d4;
            min-height: 100vh;
        }}
        .header {{
            background-color: #333;
            padding: 15px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid #555;
        }}
        .header h1 {{
            font-size: 1.2em;
            margin-bottom: 10px;
            color: #fff;
        }}
        .nav {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }}
        .nav a {{
            color: #9cdcfe;
            text-decoration: none;
            padding: 5px 15px;
            border-radius: 4px;
            background-color: #444;
            transition: background-color 0.2s;
        }}
        .nav a:hover {{
            background-color: #555;
        }}
        .nav a.active {{
            background-color: #0e639c;
            color: #fff;
        }}
        .controls {{
            margin-top: 10px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        .controls label {{
            color: #aaa;
        }}
        .controls select, .controls input {{
            background-color: #3c3c3c;
            color: #d4d4d4;
            border: 1px solid #555;
            padding: 5px 10px;
            border-radius: 4px;
        }}
        .controls button {{
            background-color: #0e639c;
            color: #fff;
            border: none;
            padding: 5px 15px;
            border-radius: 4px;
            cursor: pointer;
        }}
        .controls button:hover {{
            background-color: #1177bb;
        }}
        .log-container {{
            padding: 20px;
            overflow-x: auto;
        }}
        .log-content {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 0.85em;
            line-height: 1.5;
        }}
        .log-line {{
            padding: 2px 0;
        }}
        .log-line:hover {{
            background-color: #2d2d2d;
        }}
        .error {{
            color: #f48771;
        }}
        .warning {{
            color: #dcdcaa;
        }}
        .success {{
            color: #89d185;
        }}
        .info {{
            color: #9cdcfe;
        }}
        .timestamp {{
            color: #6a9955;
        }}
        .status-indicator {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        .refresh-on {{
            background-color: #4ec9b0;
            color: #1e1e1e;
        }}
        .refresh-off {{
            background-color: #555;
            color: #aaa;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Log Viewer - {log_type.upper()}
            <span class="status-indicator {'refresh-on' if auto_refresh > 0 else 'refresh-off'}">
                {'Auto-refresh: ' + str(auto_refresh) + 's' if auto_refresh > 0 else 'Auto-refresh: OFF'}
            </span>
        </h1>
        <div class="nav">
            {' '.join(nav_links)}
        </div>
        <form class="controls" method="get">
            <label>Lines:
                <select name="lines" onchange="this.form.submit()">
                    <option value="100" {'selected' if lines == 100 else ''}>100</option>
                    <option value="250" {'selected' if lines == 250 else ''}>250</option>
                    <option value="500" {'selected' if lines == 500 else ''}>500</option>
                    <option value="1000" {'selected' if lines == 1000 else ''}>1000</option>
                    <option value="5000" {'selected' if lines == 5000 else ''}>5000</option>
                </select>
            </label>
            <label>Auto-refresh:
                <select name="refresh" onchange="this.form.submit()">
                    <option value="0" {'selected' if auto_refresh == 0 else ''}>Off</option>
                    <option value="5" {'selected' if auto_refresh == 5 else ''}>5s</option>
                    <option value="10" {'selected' if auto_refresh == 10 else ''}>10s</option>
                    <option value="30" {'selected' if auto_refresh == 30 else ''}>30s</option>
                    <option value="60" {'selected' if auto_refresh == 60 else ''}>60s</option>
                </select>
            </label>
            <button type="button" onclick="window.location.reload()">Refresh Now</button>
            <button type="button" onclick="window.scrollTo(0, document.body.scrollHeight)">Scroll to Bottom</button>
        </form>
    </div>
    <div class="log-container">
        <pre class="log-content">{self._colorize_logs(log_content)}</pre>
    </div>
    <script>
        // Scroll to bottom on page load if there's content
        if (document.querySelector('.log-content').textContent.trim()) {{
            window.scrollTo(0, document.body.scrollHeight);
        }}
    </script>
</body>
</html>'''

        return HttpResponse(html, content_type='text/html')

    def _colorize_logs(self, content):
        """Add CSS classes to log lines based on their content."""
        import html
        lines = content.split('\n')
        colorized_lines = []

        for line in lines:
            escaped_line = html.escape(line)
            css_class = ''

            if 'ERROR' in line or 'EXCEPTION' in line:
                css_class = 'error'
            elif 'WARNING' in line:
                css_class = 'warning'
            elif 'SUCCESS' in line:
                css_class = 'success'
            elif 'INFO' in line:
                css_class = 'info'

            colorized_lines.append(f'<div class="log-line {css_class}">{escaped_line}</div>')

        return '\n'.join(colorized_lines)
