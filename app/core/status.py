from fastapi.responses import HTMLResponse

def status_page(
    title: str,
    message: str,
    icon: str = "ℹ️",
    button_text: str = "Back to Display",
    button_url: str = "/",
    button_color: str = "#2563eb",
    status_code: int = 401,
):
    return HTMLResponse(
        content=f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                * {{ box-sizing: border-box; }}

                body {{
                margin: 0;
                font-family: Inter, Arial, sans-serif;
                background: #f8fafc;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                padding: 20px;
                }}

                .card {{
                background: white;
                max-width: 420px;
                width: 100%;
                padding: 36px 28px;
                border-radius: 24px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
                }}

                .icon {{
                width: 84px;
                height: 84px;
                margin: 0 auto 24px;
                border-radius: 50%;
                background: #fef2f2;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 40px;
                }}

                h1 {{
                margin: 0 0 12px;
                color: #0f172a;
                font-size: 28px;
                }}

                p {{
                color: #475569;
                line-height: 1.6;
                margin: 0;
                }}

                .btn {{
                display: block;
                margin-top: 28px;
                background: {button_color};
                color: white;
                text-decoration: none;
                padding: 14px 22px;
                border-radius: 14px;
                font-weight: 600;
                transition: opacity 0.2s ease;
                }}

                .btn:hover {{
                opacity: 0.92;
                }}
            </style>
            </head>
            <body>
            <div class="card">
                <div class="icon">{icon}</div>

                <h1>{title}</h1>

                <p>{message}</p>

                <a class="btn" href="{button_url}">{button_text}</a>
            </div>
            </body>
            </html>
        """,
        status_code=status_code,
    )