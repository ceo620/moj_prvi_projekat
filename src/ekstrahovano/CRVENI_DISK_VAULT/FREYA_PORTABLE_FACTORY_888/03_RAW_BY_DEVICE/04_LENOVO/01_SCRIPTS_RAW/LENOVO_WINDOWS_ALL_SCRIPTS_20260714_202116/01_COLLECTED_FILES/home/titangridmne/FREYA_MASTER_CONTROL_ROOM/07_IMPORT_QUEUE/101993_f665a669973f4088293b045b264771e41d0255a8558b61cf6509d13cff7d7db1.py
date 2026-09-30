from weasyprint import HTML


def render_pdf_from_html(html_content: str) -> bytes:
    return HTML(string=html_content).write_pdf()
