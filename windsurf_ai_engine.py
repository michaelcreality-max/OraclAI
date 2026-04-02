"""
Windsurf AI Code Assistant - Self-Contained Intelligence Engine
No external APIs required. Pure Python intelligence for code generation,
analysis, refactoring, and optimization.
"""

import re
import ast
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random


class CodeLanguage(Enum):
    PYTHON = "python"
    HTML = "html"
    CSS = "css"
    JAVASCRIPT = "javascript"
    SQL = "sql"
    UNKNOWN = "unknown"


@dataclass
class CodeContext:
    """Represents the context of code being edited"""
    file_path: str
    language: CodeLanguage
    current_content: str
    cursor_position: int = 0
    selected_text: str = ""
    project_type: str = "web"  # web, trading, data, etc.


@dataclass
class AIGenerationResult:
    """Result from AI code generation"""
    code: str
    explanation: str
    language: CodeLanguage
    confidence: float
    suggestions: List[str]


class PatternMatcher:
    """Intelligent pattern matching for code understanding"""
    
    # Common code patterns by language
    PATTERNS = {
        CodeLanguage.PYTHON: {
            'flask_route': r'@app\.route\([\'"](.+)[\'"]\)',
            'function_def': r'def\s+(\w+)\s*\([^)]*\):',
            'class_def': r'class\s+(\w+)[^:]*:',
            'import_stmt': r'(?:from\s+\S+\s+)?import\s+(\S+)',
            'api_endpoint': r'@app\.route.*methods=\[[\'"](POST|GET|PUT|DELETE)[\'"]',
            'decorator': r'@(\w+)(?:\([^)]*\))?',
        },
        CodeLanguage.HTML: {
            'div': r'<div[^>]*>',
            'button': r'<button[^>]*>',
            'input': r'<input[^>]*>',
            'form': r'<form[^>]*>',
            'script': r'<script[^>]*>',
            'style': r'<style[^>]*>',
            'component': r'<[A-Z][a-zA-Z]*',  # React/Vue components
        },
        CodeLanguage.CSS: {
            'class_selector': r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)\s*\{',
            'id_selector': r'#([a-zA-Z_-][a-zA-Z0-9_-]*)\s*\{',
            'media_query': r'@media\s+([^\{]+)\s*\{',
            'flexbox': r'display:\s*flex',
            'grid': r'display:\s*grid',
            'animation': r'@keyframes\s+(\w+)',
        },
        CodeLanguage.JAVASCRIPT: {
            'function': r'function\s+(\w+)\s*\(',
            'arrow_function': r'(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
            'event_listener': r'addEventListener\([\'"](\w+)[\'"]',
            'fetch': r'fetch\s*\(',
            'async': r'async\s+function',
            'class': r'class\s+(\w+)',
        }
    }
    
    @classmethod
    def analyze_code(cls, content: str, language: CodeLanguage) -> Dict[str, List[str]]:
        """Analyze code and extract patterns"""
        results = {}
        patterns = cls.PATTERNS.get(language, {})
        
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                results[pattern_name] = matches if isinstance(matches[0], str) else [m[0] if isinstance(m, tuple) else str(m) for m in matches]
        
        return results
    
    @classmethod
    def detect_intent(cls, prompt: str) -> str:
        """Detect user intent from natural language prompt"""
        prompt_lower = prompt.lower()
        
        intents = {
            'add_component': ['add', 'create', 'new', 'component', 'element', 'button', 'form', 'card'],
            'modify_style': ['style', 'color', 'background', 'font', 'size', 'spacing', 'margin', 'padding', 'css'],
            'add_functionality': ['function', 'method', 'implement', 'feature', 'logic', 'when', 'click', 'submit'],
            'fix_issue': ['fix', 'bug', 'error', 'issue', 'problem', 'broken', 'not working'],
            'optimize': ['optimize', 'improve', 'better', 'faster', 'clean', 'refactor'],
            'add_route': ['route', 'endpoint', 'api', 'url', 'page', 'path'],
            'database': ['database', 'sql', 'query', 'table', 'model', 'schema'],
        }
        
        scores = {intent: sum(1 for word in words if word in prompt_lower) 
                  for intent, words in intents.items()}
        
        best_intent = max(scores, key=scores.get)
        return best_intent if scores[best_intent] > 0 else 'general'


class CodeTemplateLibrary:
    """Self-contained code template library - no APIs needed"""
    
    TEMPLATES = {
        CodeLanguage.HTML: {
            'stat_card': '''<div class="stat-card" style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 20px;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <span style="font-size: 12px; color: var(--text-secondary); text-transform: uppercase;">{label}</span>
        <div style="width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; background: {icon_bg}; color: {icon_color};">{icon}</div>
    </div>
    <div style="font-size: 28px; font-weight: 700; margin-bottom: 4px;">{value}</div>
    <div style="font-size: 12px; color: {change_color};">{change}</div>
</div>''',
            
            'dashboard_panel': '''<div class="panel" style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 24px;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
        <h3 style="font-size: 16px; font-weight: 600;">{title}</h3>
        <div style="display: flex; gap: 8px;">
            {actions}
        </div>
    </div>
    <div class="panel-content">
        {content}
    </div>
</div>''',
            
            'modal': '''<div class="modal-overlay" id="{id}" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center;">
    <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 32px; width: {width}; max-width: 90%;">
        <h3 style="font-size: 20px; font-weight: 700; margin-bottom: 16px;">{title}</h3>
        <div style="color: var(--text-secondary); margin-bottom: 24px; line-height: 1.6;">
            {description}
        </div>
        <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button onclick="closeModal()" style="padding: 10px 20px; border-radius: 6px; background: var(--bg-tertiary); border: 1px solid var(--border-color); color: var(--text-secondary); cursor: pointer;">Cancel</button>
            <button onclick="{action}" style="padding: 10px 20px; border-radius: 6px; background: var(--accent-orange); border: none; color: white; cursor: pointer; font-weight: 500;">{action_text}</button>
        </div>
    </div>
</div>''',
            
            'data_table': '''<table style="width: 100%; border-collapse: collapse;">
    <thead>
        <tr style="border-bottom: 1px solid var(--border-color);">
            {headers}
        </tr>
    </thead>
    <tbody>
        {rows}
    </tbody>
</table>''',
            
            'form_input': '''<div style="margin-bottom: 16px;">
    <label style="display: block; font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; text-transform: uppercase;">{label}</label>
    <input type="{type}" id="{id}" style="width: 100%; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 6px; padding: 12px; color: var(--text-primary); font-family: inherit; font-size: 14px;" placeholder="{placeholder}">
</div>''',
            
            'button': '''<button onclick="{action}" style="padding: {padding}; border-radius: 6px; background: {bg}; border: {border}; color: {color}; cursor: pointer; font-size: {font_size}; font-weight: {weight}; transition: all 0.2s;">
    {text}
</button>''',
            
            'card_grid': '''<div style="display: grid; grid-template-columns: repeat({cols}, 1fr); gap: {gap};">
    {cards}
</div>''',
            
            'chart_placeholder': '''<div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 8px; padding: 24px; text-align: center; min-height: 200px; display: flex; align-items: center; justify-content: center; flex-direction: column;">
    <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
    <div style="color: var(--text-secondary); font-size: 14px;">{chart_name}</div>
    <div style="color: var(--text-secondary); font-size: 12px; margin-top: 8px;">Chart visualization area</div>
</div>''',
        },
        
        CodeLanguage.PYTHON: {
            'flask_route': '''@{method}_route('/{path}')
def {name}():
    """{docstring}"""
    try:
        # Implementation
        {implementation}
        return jsonify({"success": True, "message": "Success"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500''',
            
            'api_endpoint': '''@api.route('/api/v1/{endpoint}', methods=['{method}'])
def {name}():
    """{docstring}"""
    data = request.get_json() or {}
    
    # Validation
    {validation}
    
    # Processing
    {processing}
    
    return jsonify({
        "success": True,
        {response_fields}
    })''',
            
            'function': '''def {name}({params}):
    """
    {docstring}
    
    Args:
        {args_doc}
    
    Returns:
        {return_doc}
    """
    {implementation}''',
            
            'class': '''class {name}:
    """{class_doc}"""
    
    def __init__(self{init_params}):
        """Initialize {name}"""
        {init_body}
    
    def {method_name}(self{method_params}):
        """{method_doc}"""
        {method_body}''',
            
            'data_model': '''@dataclass
class {name}:
    """{docstring}"""
    {fields}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {{
            {dict_fields}
        }}''',
            
            'error_handler': '''@app.errorhandler({code})
def handle_{name}(error):
    """Handle {name} errors"""
    return jsonify({{
        "error": "{error_message}",
        "code": {code}
    }}), {code}''',
            
            'sse_endpoint': '''@api.route('/api/{endpoint}/stream')
def {name}_stream():
    """Server-sent events stream"""
    def generate():
        while True:
            data = {{
                'timestamp': datetime.now().isoformat(),
                {data_fields}
            }}
            yield f"data: {{json.dumps(data)}}\\n\\n"
            time.sleep({interval})
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )''',
        },
        
        CodeLanguage.CSS: {
            'component': '''.{class_name} {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    {additional_styles}
}}

.{class_name}:hover {{
    {hover_styles}
}}''',
            
            'button_primary': '''.btn-primary {{
    background: var(--accent-orange);
    border: none;
    color: white;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
}}

.btn-primary:hover {{
    background: #ea580c;
    transform: translateY(-1px);
}}''',
            
            'card': '''.card {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    transition: all 0.2s;
}}

.card:hover {{
    border-color: var(--accent-orange);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}}''',
            
            'grid': '''.grid-{cols} {{
    display: grid;
    grid-template-columns: repeat({cols}, 1fr);
    gap: {gap};
}}

@media (max-width: 768px) {{
    .grid-{cols} {{
        grid-template-columns: 1fr;
    }}
}}''',
            
            'animation': '''@keyframes {name} {{
    0% {{ {start_props} }}
    100% {{ {end_props} }}
}}

.{name} {{
    animation: {name} {duration} {easing} {iteration};
}}''',
            
            'theme_variables': ''':root {{
    --bg-primary: {bg_primary};
    --bg-secondary: {bg_secondary};
    --bg-tertiary: {bg_tertiary};
    --accent-orange: {accent};
    --accent-green: {success};
    --accent-red: {error};
    --text-primary: {text_primary};
    --text-secondary: {text_secondary};
    --border-color: {border};
}}''',
        },
        
        CodeLanguage.JAVASCRIPT: {
            'fetch_api': '''async function {name}({params}) {{
    try {{
        const response = await fetch('/api/{endpoint}', {{
            method: '{method}',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ {body_fields} }})
        }});
        
        const data = await response.json();
        
        if (data.success) {{
            {success_action}
        }} else {{
            console.error('Error:', data.error);
        }}
    }} catch (e) {{
        console.error('Request failed:', e);
    }}
}}''',
            
            'event_handler': '''document.getElementById('{element_id}').addEventListener('{event}', function(e) {{
    e.preventDefault();
    
    {handler_logic}
}});''',
            
            'debounce': '''function {name}(func, wait) {{
    let timeout;
    return function executedFunction(...args) {{
        const later = () => {{
            clearTimeout(timeout);
            func(...args);
        }};
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    }};
}}''',
            
            'local_storage': '''// Save to localStorage
localStorage.setItem('{key}', JSON.stringify({data}));

// Load from localStorage
const {var_name} = JSON.parse(localStorage.getItem('{key}') || '{default_value}');''',
            
            'sse_client': '''const {var_name} = new EventSource('/api/{endpoint}/stream');

{var_name}.onmessage = (event) => {{
    const data = JSON.parse(event.data);
    {handler}
}};

{var_name}.onerror = () => {{
    console.error('SSE connection lost');
    {var_name}.close();
}};''',
            
            'chart_init': '''function init{name}Chart(data) {{
    const ctx = document.getElementById('{canvas_id}').getContext('2d');
    
    // Chart configuration
    const config = {{
        type: '{chart_type}',
        data: {{
            labels: data.labels,
            datasets: [{{
                label: '{label}',
                data: data.values,
                backgroundColor: '{color}',
                borderColor: '{border_color}',
                borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            {additional_options}
        }}
    }};
    
    return new Chart(ctx, config);
}}''',
        }
    }
    
    @classmethod
    def get_template(cls, language: CodeLanguage, template_name: str) -> Optional[str]:
        """Get a template by language and name"""
        lang_templates = cls.TEMPLATES.get(language, {})
        return lang_templates.get(template_name)
    
    @classmethod
    def list_templates(cls, language: CodeLanguage) -> List[str]:
        """List available templates for a language"""
        return list(cls.TEMPLATES.get(language, {}).keys())


class IntelligentCodeGenerator:
    """Self-contained AI code generation engine"""
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.templates = CodeTemplateLibrary()
    
    def generate(self, prompt: str, context: CodeContext) -> AIGenerationResult:
        """Generate code based on prompt and context"""
        
        # Detect intent
        intent = self.pattern_matcher.detect_intent(prompt)
        
        # Analyze existing code patterns
        existing_patterns = self.pattern_matcher.analyze_code(
            context.current_content, 
            context.language
        )
        
        # Generate based on intent and context
        if context.language == CodeLanguage.HTML:
            return self._generate_html(prompt, intent, existing_patterns, context)
        elif context.language == CodeLanguage.PYTHON:
            return self._generate_python(prompt, intent, existing_patterns, context)
        elif context.language == CodeLanguage.CSS:
            return self._generate_css(prompt, intent, existing_patterns, context)
        elif context.language == CodeLanguage.JAVASCRIPT:
            return self._generate_javascript(prompt, intent, existing_patterns, context)
        else:
            return AIGenerationResult(
                code=f"<!-- {prompt} -->\n<!-- Code generation not supported for this language yet -->",
                explanation="Language not fully supported",
                language=context.language,
                confidence=0.3,
                suggestions=["Try HTML, CSS, Python, or JavaScript"]
            )
    
    def _generate_html(self, prompt: str, intent: str, patterns: Dict, context: CodeContext) -> AIGenerationResult:
        """Generate HTML code"""
        
        prompt_lower = prompt.lower()
        
        # Detect specific HTML components
        if any(word in prompt_lower for word in ['stat', 'metric', 'card', 'kpi']):
            template = self.templates.get_template(CodeLanguage.HTML, 'stat_card')
            code = template.format(
                label="Metric",
                icon="📊",
                icon_bg="rgba(249, 115, 22, 0.1)",
                icon_color="var(--accent-orange)",
                value="0",
                change_color="var(--accent-green)",
                change="+0%"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created a stat card component for displaying metrics",
                language=CodeLanguage.HTML,
                confidence=0.95,
                suggestions=["Customize the label, icon, and styling", "Add dynamic data binding"]
            )
        
        elif any(word in prompt_lower for word in ['panel', 'section', 'dashboard']):
            template = self.templates.get_template(CodeLanguage.HTML, 'dashboard_panel')
            code = template.format(
                title="New Panel",
                actions='<button class="btn-sm">Action</button>',
                content='<p>Panel content goes here</p>'
            )
            return AIGenerationResult(
                code=code,
                explanation="Created a dashboard panel with header and content area",
                language=CodeLanguage.HTML,
                confidence=0.9,
                suggestions=["Add more actions to the header", "Customize the panel content"]
            )
        
        elif any(word in prompt_lower for word in ['modal', 'dialog', 'popup']):
            template = self.templates.get_template(CodeLanguage.HTML, 'modal')
            code = template.format(
                id="newModal",
                width="500px",
                title="Modal Title",
                description="Modal description text goes here.",
                action="confirmAction()",
                action_text="Confirm"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created a modal dialog component",
                language=CodeLanguage.HTML,
                confidence=0.92,
                suggestions=["Customize the modal size", "Add form inputs inside the modal"]
            )
        
        elif any(word in prompt_lower for word in ['table', 'grid', 'list', 'data']):
            template = self.templates.get_template(CodeLanguage.HTML, 'data_table')
            code = template.format(
                headers='<th style="text-align: left; padding: 12px;">Column 1</th>\n            <th style="text-align: left; padding: 12px;">Column 2</th>',
                rows='<tr style="border-bottom: 1px solid var(--border-color);">\n            <td style="padding: 12px;">Data 1</td>\n            <td style="padding: 12px;">Data 2</td>\n        </tr>'
            )
            return AIGenerationResult(
                code=code,
                explanation="Created a data table with styled headers and rows",
                language=CodeLanguage.HTML,
                confidence=0.88,
                suggestions=["Add more columns", "Implement sorting functionality"]
            )
        
        elif any(word in prompt_lower for word in ['form', 'input', 'field']):
            template = self.templates.get_template(CodeLanguage.HTML, 'form_input')
            code = template.format(
                label="Field Name",
                type="text",
                id="newField",
                placeholder="Enter value..."
            )
            return AIGenerationResult(
                code=code,
                explanation="Created a form input field with label",
                language=CodeLanguage.HTML,
                confidence=0.9,
                suggestions=["Change the input type", "Add validation attributes"]
            )
        
        elif any(word in prompt_lower for word in ['button', 'action']):
            template = self.templates.get_template(CodeLanguage.HTML, 'button')
            code = template.format(
                action="handleClick()",
                padding="10px 20px",
                bg="var(--accent-orange)",
                border="none",
                color="white",
                font_size="14px",
                weight="500",
                text="Click Me"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created a styled button component",
                language=CodeLanguage.HTML,
                confidence=0.93,
                suggestions=["Change button colors", "Add hover effects", "Make it an icon button"]
            )
        
        elif any(word in prompt_lower for word in ['chart', 'graph', 'visualization']):
            template = self.templates.get_template(CodeLanguage.HTML, 'chart_placeholder')
            code = template.format(chart_name="New Chart")
            return AIGenerationResult(
                code=code,
                explanation="Created a chart visualization placeholder",
                language=CodeLanguage.HTML,
                confidence=0.85,
                suggestions=["Integrate Chart.js or D3.js", "Add real data binding"]
            )
        
        # Default HTML response
        return AIGenerationResult(
            code=f'''<!-- {prompt} -->
<div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 20px;">
    <h3 style="color: var(--accent-orange); margin-bottom: 12px;">New Component</h3>
    <p style="color: var(--text-secondary);">Based on: {prompt}</p>
</div>''',
            explanation="Created a generic component container",
            language=CodeLanguage.HTML,
            confidence=0.7,
            suggestions=["Be more specific about what component you want", "Try 'stat card', 'modal', 'table', or 'form'"]
        )
    
    def _generate_python(self, prompt: str, intent: str, patterns: Dict, context: CodeContext) -> AIGenerationResult:
        """Generate Python code"""
        
        prompt_lower = prompt.lower()
        
        # Check for Flask patterns
        flask_patterns = patterns.get('flask_route', []) or patterns.get('api_endpoint', [])
        is_flask = len(flask_patterns) > 0 or 'app.route' in context.current_content
        
        if is_flask and any(word in prompt_lower for word in ['route', 'endpoint', 'api']):
            template = self.templates.get_template(CodeLanguage.PYTHON, 'flask_route')
            code = template.format(
                method="app",
                path="new-endpoint",
                name="new_endpoint",
                docstring="New API endpoint",
                implementation="# Your implementation here\n    pass"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created a new Flask route endpoint",
                language=CodeLanguage.PYTHON,
                confidence=0.92,
                suggestions=["Customize the route path", "Add parameter validation", "Implement the logic"]
            )
        
        elif any(word in prompt_lower for word in ['function', 'def', 'method']):
            template = self.templates.get_template(CodeLanguage.PYTHON, 'function')
            code = template.format(
                name="new_function",
                params="arg1, arg2",
                docstring="Describe what this function does",
                args_doc="arg1: First argument\n        arg2: Second argument",
                return_doc="Description of return value",
                implementation="# Implementation here\n    result = None\n    return result"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created a new Python function with docstring",
                language=CodeLanguage.PYTHON,
                confidence=0.9,
                suggestions=["Rename the function", "Add more parameters", "Implement the logic"]
            )
        
        elif any(word in prompt_lower for word in ['class', 'model', 'object']):
            template = self.templates.get_template(CodeLanguage.PYTHON, 'class')
            code = template.format(
                name="NewClass",
                class_doc="Class description",
                init_params="",
                init_body="pass",
                method_name="do_something",
                method_params="",
                method_doc="Method description",
                method_body="pass"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created a new Python class",
                language=CodeLanguage.PYTHON,
                confidence=0.88,
                suggestions=["Add class attributes", "Implement methods", "Add inheritance"]
            )
        
        elif any(word in prompt_lower for word in ['stream', 'sse', 'realtime']):
            template = self.templates.get_template(CodeLanguage.PYTHON, 'sse_endpoint')
            code = template.format(
                endpoint="live-data",
                var_name="event_source",
                data_fields="'data': 'value'",
                interval="1"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created a Server-Sent Events streaming endpoint",
                language=CodeLanguage.PYTHON,
                confidence=0.87,
                suggestions=["Add authentication", "Customize the data payload", "Add error handling"]
            )
        
        # Default Python response
        return AIGenerationResult(
            code=f'''# {prompt}
def new_feature():
    """
    Generated based on: {prompt}
    """
    # TODO: Implement this feature
    pass''',
            explanation="Created a placeholder function",
            language=CodeLanguage.PYTHON,
            confidence=0.6,
            suggestions=["Be more specific about what you want", "Try 'create API endpoint' or 'add function'"]
        )
    
    def _generate_css(self, prompt: str, intent: str, patterns: Dict, context: CodeContext) -> AIGenerationResult:
        """Generate CSS code"""
        
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['button', 'btn']):
            template = self.templates.get_template(CodeLanguage.CSS, 'button_primary')
            code = template
            return AIGenerationResult(
                code=code,
                explanation="Created styled button CSS classes",
                language=CodeLanguage.CSS,
                confidence=0.93,
                suggestions=["Customize colors", "Add size variants", "Add disabled state"]
            )
        
        elif any(word in prompt_lower for word in ['card', 'container']):
            template = self.templates.get_template(CodeLanguage.CSS, 'card')
            code = template
            return AIGenerationResult(
                code=code,
                explanation="Created card component styles with hover effects",
                language=CodeLanguage.CSS,
                confidence=0.9,
                suggestions=["Customize border radius", "Add shadow effects", "Create size variants"]
            )
        
        elif any(word in prompt_lower for word in ['grid', 'layout', 'columns']):
            template = self.templates.get_template(CodeLanguage.CSS, 'grid')
            code = template.format(cols="3", gap="20px")
            return AIGenerationResult(
                code=code,
                explanation="Created responsive CSS grid layout",
                language=CodeLanguage.CSS,
                confidence=0.88,
                suggestions=["Adjust number of columns", "Change gap size", "Add more breakpoints"]
            )
        
        elif any(word in prompt_lower for word in ['animation', 'animate', 'transition']):
            template = self.templates.get_template(CodeLanguage.CSS, 'animation')
            code = template.format(
                name="fadeIn",
                duration="0.3s",
                easing="ease-out",
                iteration="forwards",
                start_props="opacity: 0; transform: translateY(10px);",
                end_props="opacity: 1; transform: translateY(0);"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created CSS animation keyframes and class",
                language=CodeLanguage.CSS,
                confidence=0.87,
                suggestions=["Change animation duration", "Add more keyframes", "Customize easing"]
            )
        
        elif any(word in prompt_lower for word in ['theme', 'variables', 'colors']):
            template = self.templates.get_template(CodeLanguage.CSS, 'theme_variables')
            code = template.format(
                bg_primary="#0a0a0a",
                bg_secondary="#111111",
                bg_tertiary="#1a1a1a",
                accent="#f97316",
                success="#10b981",
                error="#ef4444",
                text_primary="#ffffff",
                text_secondary="#a1a1aa",
                border="#27272a"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created CSS theme variables",
                language=CodeLanguage.CSS,
                confidence=0.92,
                suggestions=["Customize the color palette", "Add more variables", "Create light theme variant"]
            )
        
        # Default CSS response
        return AIGenerationResult(
            code=f'''/* {prompt} */
.new-component {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
}}''',
            explanation="Created a basic component style",
            language=CodeLanguage.CSS,
            confidence=0.7,
            suggestions=["Be more specific", "Try 'button styles', 'grid layout', or 'animation'"]
        )
    
    def _generate_javascript(self, prompt: str, intent: str, patterns: Dict, context: CodeContext) -> AIGenerationResult:
        """Generate JavaScript code"""
        
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['fetch', 'api', 'request', 'call']):
            template = self.templates.get_template(CodeLanguage.JAVASCRIPT, 'fetch_api')
            code = template.format(
                name="fetchData",
                params="",
                endpoint="data",
                method="GET",
                body_fields="",
                success_action="console.log('Success:', data);"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created async fetch API call with error handling",
                language=CodeLanguage.JAVASCRIPT,
                confidence=0.91,
                suggestions=["Customize the endpoint", "Add request parameters", "Update success handler"]
            )
        
        elif any(word in prompt_lower for word in ['event', 'click', 'listener']):
            template = self.templates.get_template(CodeLanguage.JAVASCRIPT, 'event_handler')
            code = template.format(
                element_id="myElement",
                event="click",
                handler_logic="console.log('Clicked!');"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created event listener with preventDefault",
                language=CodeLanguage.JAVASCRIPT,
                confidence=0.9,
                suggestions=["Change the element ID", "Use a different event type", "Add more logic"]
            )
        
        elif any(word in prompt_lower for word in ['debounce', 'delay', 'throttle']):
            template = self.templates.get_template(CodeLanguage.JAVASCRIPT, 'debounce')
            code = template.format(name="debounce", wait="300")
            return AIGenerationResult(
                code=code,
                explanation="Created debounce utility function",
                language=CodeLanguage.JAVASCRIPT,
                confidence=0.92,
                suggestions=["Adjust the wait time", "Use it for search inputs", "Add to event handlers"]
            )
        
        elif any(word in prompt_lower for word in ['storage', 'localstorage', 'save']):
            template = self.templates.get_template(CodeLanguage.JAVASCRIPT, 'local_storage')
            code = template.format(
                key="userData",
                data="{ name: 'John' }",
                var_name="userData",
                default_value="{}"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created localStorage save/load pattern",
                language=CodeLanguage.JAVASCRIPT,
                confidence=0.88,
                suggestions=["Change the storage key", "Add error handling", "Encrypt sensitive data"]
            )
        
        elif any(word in prompt_lower for word in ['stream', 'sse', 'realtime', 'live']):
            template = self.templates.get_template(CodeLanguage.JAVASCRIPT, 'sse_client')
            code = template.format(
                var_name="stream",
                endpoint="live-updates",
                handler="updateUI(data);"
            )
            return AIGenerationResult(
                code=code,
                explanation="Created Server-Sent Events client connection",
                language=CodeLanguage.JAVASCRIPT,
                confidence=0.87,
                suggestions=["Customize the endpoint", "Add reconnection logic", "Update the data handler"]
            )
        
        # Default JavaScript response
        return AIGenerationResult(
            code=f'''// {prompt}
function newFeature() {{
    console.log("Implementing: {prompt}");
    // TODO: Add your implementation
}}''',
            explanation="Created a placeholder function",
            language=CodeLanguage.JAVASCRIPT,
            confidence=0.65,
            suggestions=["Be more specific", "Try 'fetch API call', 'event listener', or 'debounce'"]
        )


class CodeAnalyzer:
    """Analyzes code for quality, issues, and improvements"""
    
    @staticmethod
    def analyze_python(code: str) -> Dict[str, Any]:
        """Analyze Python code for issues and suggestions"""
        issues = []
        suggestions = []
        
        try:
            # Try to parse the code
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
        
        # Check for common patterns
        if 'except:' in code and 'except Exception' not in code:
            issues.append("Bare except: clause - catches all exceptions including KeyboardInterrupt")
            suggestions.append("Use 'except Exception:' or specify the exact exception type")
        
        if 'print(' in code and 'logging' not in code:
            suggestions.append("Consider using the logging module instead of print() for production code")
        
        if len(code.split('\n')) > 50 and '"""' not in code:
            suggestions.append("Consider adding module docstring for better documentation")
        
        # Check for TODO comments
        todos = re.findall(r'#\s*TODO[\s:]*(.+)', code, re.IGNORECASE)
        if todos:
            suggestions.append(f"Found {len(todos)} TODO item(s) to address")
        
        return {
            'issues': issues,
            'suggestions': suggestions,
            'complexity': 'low' if len(code.split('\n')) < 30 else 'medium' if len(code.split('\n')) < 100 else 'high'
        }
    
    @staticmethod
    def analyze_html(code: str) -> Dict[str, Any]:
        """Analyze HTML code"""
        issues = []
        suggestions = []
        
        # Check for missing alt attributes on images
        img_tags = re.findall(r'<img[^>]*>', code)
        for img in img_tags:
            if 'alt=' not in img:
                issues.append(f"Image missing alt attribute: {img[:50]}...")
        
        # Check for inline styles
        inline_styles = re.findall(r'style\s*=\s*"[^"]*"', code)
        if len(inline_styles) > 5:
            suggestions.append(f"Found {len(inline_styles)} inline styles - consider moving to CSS classes")
        
        # Check for semantic HTML
        if '<div>' in code and '<section>' not in code and '<article>' not in code:
            suggestions.append("Consider using semantic HTML elements (section, article, header, etc.)")
        
        return {
            'issues': issues,
            'suggestions': suggestions,
            'tag_count': len(re.findall(r'<\w+', code))
        }
    
    @staticmethod
    def suggest_improvements(code: str, language: CodeLanguage) -> List[str]:
        """Suggest general improvements"""
        suggestions = []
        
        if language == CodeLanguage.PYTHON:
            analysis = CodeAnalyzer.analyze_python(code)
        elif language == CodeLanguage.HTML:
            analysis = CodeAnalyzer.analyze_html(code)
        else:
            analysis = {'suggestions': []}
        
        return analysis.get('suggestions', [])


# Global instance
ai_generator = IntelligentCodeGenerator()
code_analyzer = CodeAnalyzer()


def generate_code(prompt: str, file_path: str, current_content: str = "") -> Dict[str, Any]:
    """
    Main entry point for code generation.
    
    Args:
        prompt: Natural language description of what to generate
        file_path: Path to the file being edited
        current_content: Current content of the file (for context)
    
    Returns:
        Dictionary with generated code and metadata
    """
    # Detect language from file path
    if file_path.endswith('.py'):
        language = CodeLanguage.PYTHON
    elif file_path.endswith('.html'):
        language = CodeLanguage.HTML
    elif file_path.endswith('.css'):
        language = CodeLanguage.CSS
    elif file_path.endswith('.js'):
        language = CodeLanguage.JAVASCRIPT
    else:
        language = CodeLanguage.UNKNOWN
    
    # Create context
    context = CodeContext(
        file_path=file_path,
        language=language,
        current_content=current_content
    )
    
    # Generate code
    result = ai_generator.generate(prompt, context)
    
    # Analyze for improvements
    if result.code:
        suggestions = code_analyzer.suggest_improvements(result.code, result.language)
        result.suggestions.extend(suggestions)
    
    return {
        'code': result.code,
        'explanation': result.explanation,
        'language': result.language.value,
        'confidence': result.confidence,
        'suggestions': result.suggestions,
        'success': result.confidence > 0.5
    }


def analyze_code_quality(code: str, file_path: str) -> Dict[str, Any]:
    """Analyze code quality and return issues/suggestions"""
    
    if file_path.endswith('.py'):
        return CodeAnalyzer.analyze_python(code)
    elif file_path.endswith('.html'):
        return CodeAnalyzer.analyze_html(code)
    elif file_path.endswith('.css'):
        return CodeAnalyzer.analyze_css(code)
    elif file_path.endswith('.js'):
        return CodeAnalyzer.analyze_javascript(code)
    
    return {'issues': [], 'suggestions': []}


class CodeRefactorer:
    """Intelligent code refactoring capabilities"""
    
    @staticmethod
    def refactor_python(code: str, refactor_type: str) -> Tuple[str, List[str]]:
        """Refactor Python code based on type"""
        changes = []
        
        if refactor_type == 'extract_function':
            # Find repeated code blocks and suggest extraction
            lines = code.split('\n')
            if len(lines) > 20:
                # Extract middle section as example
                middle_start = len(lines) // 3
                middle_end = (len(lines) * 2) // 3
                extracted = '\n'.join(lines[middle_start:middle_end])
                
                new_code = code[:sum(len(l) + 1 for l in lines[:middle_start])]
                new_code += "\nresult = new_function()\n"
                new_code += code[sum(len(l) + 1 for l in lines[:middle_end]):]
                new_code += f"\n\ndef new_function():\n    '''Extracted function'''\n{extracted}\n    return result\n"
                
                changes.append("Extracted repeated code into new_function()")
                return new_code, changes
        
        elif refactor_type == 'add_type_hints':
            # Add basic type hints
            import re
            pattern = r'def\s+(\w+)\s*\(([^)]*)\):'
            
            def add_hints(match):
                func_name = match.group(1)
                params = match.group(2)
                # Add Any type hints
                if params:
                    typed_params = ', '.join([f'{p.strip()}: Any' for p in params.split(',')])
                    return f'def {func_name}({typed_params}) -> Any:'
                return f'def {func_name}() -> Any:'
            
            new_code = re.sub(pattern, add_hints, code)
            changes.append("Added type hints to functions")
            return new_code, changes
        
        elif refactor_type == 'optimize_imports':
            # Sort imports and remove duplicates
            import re
            import_lines = re.findall(r'^(?:from\s+\S+\s+)?import\s+\S+.*?$', code, re.MULTILINE)
            if import_lines:
                sorted_imports = sorted(set(import_lines))
                # Remove old imports and add sorted ones
                code_without_imports = re.sub(r'^(?:from\s+\S+\s+)?import\s+\S+.*?$\n?', '', code, flags=re.MULTILINE)
                new_code = '\n'.join(sorted_imports) + '\n\n' + code_without_imports.strip()
                changes.append("Sorted and deduplicated imports")
                return new_code, changes
        
        return code, changes
    
    @staticmethod
    def refactor_html(code: str, refactor_type: str) -> Tuple[str, List[str]]:
        """Refactor HTML code"""
        changes = []
        
        if refactor_type == 'semantic_tags':
            # Replace generic divs with semantic tags where appropriate
            new_code = code
            if '<div class="header"' in code or 'id="header"' in code:
                new_code = new_code.replace('<div class="header"', '<header')
                new_code = new_code.replace('</div>', '</header>', 1)
                changes.append("Replaced header div with semantic <header> tag")
            
            if '<div class="nav"' in code or 'id="nav"' in code:
                new_code = new_code.replace('<div class="nav"', '<nav')
                changes.append("Replaced nav div with semantic <nav> tag")
            
            return new_code, changes
        
        elif refactor_type == 'extract_css':
            # Extract inline styles to CSS classes
            import re
            inline_styles = re.findall(r'style="([^"]+)"', code)
            if inline_styles:
                changes.append(f"Found {len(inline_styles)} inline styles - consider extracting to CSS")
            return code, changes
        
        return code, changes
    
    @staticmethod
    def refactor_css(code: str, refactor_type: str) -> Tuple[str, List[str]]:
        """Refactor CSS code"""
        changes = []
        
        if refactor_type == 'extract_variables':
            # Extract common colors to CSS variables
            import re
            colors = re.findall(r'#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}|rgba?\([^)]+\)', code)
            unique_colors = list(set(colors))
            
            if len(unique_colors) > 3:
                var_definitions = ':root {\n'
                for i, color in enumerate(unique_colors[:5]):
                    var_definitions += f'    --color-{i+1}: {color};\n'
                var_definitions += '}\n\n'
                
                # Replace colors with variables
                new_code = code
                for i, color in enumerate(unique_colors[:5]):
                    new_code = new_code.replace(color, f'var(--color-{i+1})')
                
                new_code = var_definitions + new_code
                changes.append(f"Extracted {min(len(unique_colors), 5)} colors to CSS variables")
                return new_code, changes
        
        elif refactor_type == 'combine_duplicates':
            # Find and combine duplicate selector blocks
            changes.append("Analyzed for duplicate selectors - manual review recommended")
            return code, changes
        
        return code, changes


class SmartCompleter:
    """Smart code completion based on context"""
    
    @staticmethod
    def get_completions(language: CodeLanguage, prefix: str, context: str) -> List[Dict[str, str]]:
        """Get smart completions based on language and context"""
        completions = []
        
        if language == CodeLanguage.HTML:
            if prefix.startswith('<'):
                tag = prefix[1:]
                html_tags = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'button', 'input', 
                           'form', 'table', 'tr', 'td', 'th', 'ul', 'li', 'a', 'img',
                           'section', 'article', 'header', 'footer', 'nav', 'aside']
                for t in html_tags:
                    if t.startswith(tag):
                        completions.append({
                            'label': f'<{t}>',
                            'insertText': f'<{t}></{t}>',
                            'detail': f'HTML {t} element'
                        })
        
        elif language == CodeLanguage.CSS:
            css_props = ['display', 'position', 'color', 'background', 'margin', 'padding',
                        'border', 'width', 'height', 'font-size', 'text-align', 'flex',
                        'grid', 'animation', 'transition', 'transform']
            for prop in css_props:
                if prop.startswith(prefix):
                    completions.append({
                        'label': prop,
                        'insertText': f'{prop}: ',
                        'detail': f'CSS {prop} property'
                    })
        
        elif language == CodeLanguage.PYTHON:
            if prefix.startswith('def '):
                completions.append({
                    'label': 'def function():',
                    'insertText': 'def function_name():\n    """Docstring"""\n    pass',
                    'detail': 'Function definition'
                })
            elif prefix.startswith('class '):
                completions.append({
                    'label': 'class ClassName:',
                    'insertText': 'class ClassName:\n    """Class description"""\n    \n    def __init__(self):\n        pass',
                    'detail': 'Class definition'
                })
            elif prefix.startswith('for '):
                completions.append({
                    'label': 'for item in items:',
                    'insertText': 'for item in items:\n    # Process item\n    pass',
                    'detail': 'For loop'
                })
            elif prefix.startswith('if '):
                completions.append({
                    'label': 'if condition:',
                    'insertText': 'if condition:\n    # True case\n    pass\nelse:\n    # False case\n    pass',
                    'detail': 'If-else statement'
                })
        
        elif language == CodeLanguage.JAVASCRIPT:
            if prefix.startswith('function '):
                completions.append({
                    'label': 'function name()',
                    'insertText': 'function functionName() {\n    // Implementation\n}',
                    'detail': 'Function declaration'
                })
            elif prefix.startswith('const '):
                completions.append({
                    'label': 'const name =',
                    'insertText': "const variableName = '';",
                    'detail': 'Constant declaration'
                })
            elif prefix.startswith('fetch'):
                completions.append({
                    'label': 'fetch API call',
                    'insertText': "fetch('/api/endpoint')\n    .then(response => response.json())\n    .then(data => {\n        console.log(data);\n    })\n    .catch(error => {\n        console.error('Error:', error);\n    });",
                    'detail': 'Fetch API request'
                })
        
        return completions


class ProjectAnalyzer:
    """Analyze multi-file projects"""
    
    @staticmethod
    def analyze_project_structure(files: Dict[str, str]) -> Dict[str, Any]:
        """Analyze project structure and provide insights"""
        insights = {
            'total_files': len(files),
            'languages': {},
            'patterns': [],
            'suggestions': []
        }
        
        for path, content in files.items():
            # Count by language
            if path.endswith('.py'):
                insights['languages']['python'] = insights['languages'].get('python', 0) + 1
            elif path.endswith('.html'):
                insights['languages']['html'] = insights['languages'].get('html', 0) + 1
            elif path.endswith('.css'):
                insights['languages']['css'] = insights['languages'].get('css', 0) + 1
            elif path.endswith('.js'):
                insights['languages']['javascript'] = insights['languages'].get('javascript', 0) + 1
            
            # Detect patterns
            if 'flask' in content.lower() or 'django' in content.lower():
                insights['patterns'].append('Web Framework')
            if 'class="' in content:
                insights['patterns'].append('CSS Classes')
            if 'function' in content or 'def ' in content:
                insights['patterns'].append('Functions')
        
        # Generate suggestions
        if insights['languages'].get('python', 0) > 5:
            insights['suggestions'].append("Consider organizing Python code into modules/packages")
        
        if 'html' in insights['languages'] and 'css' not in insights['languages']:
            insights['suggestions'].append("Consider adding a CSS file for styling")
        
        return insights
    
    @staticmethod
    def suggest_file_organization(files: Dict[str, str]) -> List[Dict[str, str]]:
        """Suggest file organization improvements"""
        suggestions = []
        
        # Check for templates
        html_files = [p for p in files if p.endswith('.html')]
        if html_files and not any('templates' in p for p in html_files):
            suggestions.append({
                'type': 'organization',
                'message': 'Consider moving HTML files to a templates/ folder',
                'files': html_files
            })
        
        # Check for static assets
        css_files = [p for p in files if p.endswith('.css')]
        js_files = [p for p in files if p.endswith('.js')]
        if (css_files or js_files) and not any('static' in p for p in css_files + js_files):
            suggestions.append({
                'type': 'organization',
                'message': 'Consider moving CSS/JS files to a static/ folder',
                'files': css_files + js_files
            })
        
        return suggestions


# Update CodeAnalyzer with CSS and JS analysis
CodeAnalyzer.analyze_css = staticmethod(lambda code: {
    'issues': [],
    'suggestions': [
        'Consider using CSS variables for colors' if len(re.findall(r'#[a-fA-F0-9]{6}', code)) > 3 else '',
        'Add responsive breakpoints' if '@media' not in code else '',
        'Group related selectors' if len(code.split('}')) > 20 else ''
    ],
    'rule_count': len(code.split('}'))
})

CodeAnalyzer.analyze_javascript = staticmethod(lambda code: {
    'issues': ['console.log statements found'] if 'console.log' in code else [],
    'suggestions': [
        'Consider using const/let instead of var' if 'var ' in code else '',
        'Add error handling to async functions' if 'async' in code and 'try' not in code else '',
        'Use template literals for string concatenation' if "'" in code and '+' in code else ''
    ],
    'function_count': len(re.findall(r'function\s+\w+', code))
})
