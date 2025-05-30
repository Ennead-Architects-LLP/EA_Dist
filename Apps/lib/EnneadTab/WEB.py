"""Web-related functionality for EnneadTab.

This module provides web-related utilities including:
- Documentation to HTML conversion
- Image embedding
- HTML template generation
"""

import os
import base64
import io
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.expanduser('~'), 'web_operations.log'))
    ]
)
logger = logging.getLogger(__name__)

def documentation2html(doc_data_list, html_path):
    """Generates an HTML file with embedded images from documentation data.
    
    Args:
        doc_data_list (list): List of documentation data dictionaries
        html_path (str): Path to save the HTML file
        
    Each doc_data dictionary should contain:
        - alias: Command name
        - doc: Tooltip text
        - icon: Path to icon image (optional)
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Command Documentation</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .command { margin-bottom: 40px; border-bottom: 1px solid #ddd; padding-bottom: 20px; }
            .command h2 { color: #333; }
            .tooltip { color: #555; font-size: 14px; }
            .container { display: flex; align-items: flex-start; gap: 20px; }
            img { width: 64px; height: 64px; }
        </style>
    </head>
    <body>
        <h1>Command Documentation</h1>
    """
    
    for doc_data in doc_data_list:
        alias = doc_data.get('alias', 'Unknown Command')
        tooltip_text = doc_data.get('doc', 'No description available.')
        icon_path = doc_data.get('icon')
        
        if icon_path and os.path.exists(icon_path):
            with io.open(icon_path, "rb") as img_file:
                base64_img = base64.b64encode(img_file.read()).decode('utf-8')
            icon_html = "<img src=\"data:image/png;base64,{0}\" alt=\"{1} icon\">".format(base64_img, alias)
        else:
            icon_html = ""
        
        html_content += """
        <div class="command">
            <h2>{0}</h2>
            <div class="container">
                {1}
                <p class="tooltip"><strong>Tooltip:</strong> {2}</p>
            </div>
        </div>
        """.format(alias, icon_html, tooltip_text)
    
    html_content += "</body></html>"
    
    with io.open(html_path, "w", encoding="utf-8") as file:
        file.write(html_content)
    
    logger.info("HTML documentation saved at {}".format(html_path))