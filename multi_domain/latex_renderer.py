"""
LaTeX Math Renderer
Converts LaTeX mathematical expressions to HTML/CSS for display
"""

import re
import html
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MathMode(Enum):
    """Math rendering modes"""
    INLINE = "inline"
    DISPLAY = "display"


@dataclass
class RenderedMath:
    """Rendered math result"""
    html: str
    text_description: str
    mode: MathMode
    original_latex: str


class LaTeXRenderer:
    """
    Renders LaTeX math expressions to HTML/CSS
    No external dependencies - pure Python implementation
    """
    
    def __init__(self):
        self.greek_letters = {
            'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ',
            'epsilon': 'ε', 'zeta': 'ζ', 'eta': 'η', 'theta': 'θ',
            'iota': 'ι', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ',
            'nu': 'ν', 'xi': 'ξ', 'omicron': 'ο', 'pi': 'π',
            'rho': 'ρ', 'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ',
            'phi': 'φ', 'chi': 'χ', 'psi': 'ψ', 'omega': 'ω',
            'Gamma': 'Γ', 'Delta': 'Δ', 'Theta': 'Θ', 'Lambda': 'Λ',
            'Xi': 'Ξ', 'Pi': 'Π', 'Sigma': 'Σ', 'Phi': 'Φ',
            'Psi': 'Ψ', 'Omega': 'Ω'
        }
        
        self.operators = {
            'sum': '∑', 'prod': '∏', 'int': '∫', 'oint': '∮',
            'partial': '∂', 'nabla': '∇', 'infty': '∞', 'pm': '±',
            'cdot': '·', 'times': '×', 'div': '÷', 'sqrt': '√',
            'leq': '≤', 'geq': '≥', 'neq': '≠', 'approx': '≈',
            'forall': '∀', 'exists': '∃', 'in': '∈', 'subset': '⊂',
            'cup': '∪', 'cap': '∩', 'emptyset': '∅', 'therefore': '∴',
            'because': '∵', 'propto': '∝', 'angle': '∠', 'perp': '⊥'
        }
        
        self.arrows = {
            'to': '→', 'rightarrow': '→', 'leftarrow': '←', 'leftrightarrow': '↔',
            'Rightarrow': '⇒', 'Leftarrow': '⇐', 'Leftrightarrow': '⇔',
            'mapsto': '↦', 'uparrow': '↑', 'downarrow': '↓'
        }
        
        self.accents = {
            'hat': ('&#770;', 'combining circumflex'),
            'bar': ('&#772;', 'combining macron'),
            'vec': ('&#8407;', 'combining arrow above'),
            'tilde': ('&#771;', 'combining tilde'),
            'dot': ('&#775;', 'combining dot above'),
            'ddot': ('&#776;', 'combining diaeresis'),
        }
    
    def render(self, latex: str, mode: MathMode = MathMode.INLINE) -> RenderedMath:
        """Main render method"""
        original = latex
        
        # Clean the latex
        latex = latex.strip()
        
        # Extract display vs inline
        if latex.startswith('$$') and latex.endswith('$$'):
            mode = MathMode.DISPLAY
            latex = latex[2:-2]
        elif latex.startswith('$') and latex.endswith('$'):
            mode = MathMode.INLINE
            latex = latex[1:-1]
        elif latex.startswith('\\[') and latex.endswith('\\]'):
            mode = MathMode.DISPLAY
            latex = latex[2:-2]
        elif latex.startswith('\\(') and latex.endswith('\\)'):
            mode = MathMode.INLINE
            latex = latex[2:-2]
        
        # Process the LaTeX
        html_output = self._process_latex(latex, mode)
        
        # Generate text description
        text_desc = self._generate_text_description(latex)
        
        return RenderedMath(
            html=html_output,
            text_description=text_desc,
            mode=mode,
            original_latex=original
        )
    
    def _process_latex(self, latex: str, mode: MathMode) -> str:
        """Process LaTeX to HTML"""
        # Handle fractions
        html = self._process_fractions(latex)
        
        # Handle subscripts and superscripts
        html = self._process_scripts(html)
        
        # Handle square roots
        html = self._process_sqrt(html)
        
        # Handle summation, integrals, etc.
        html = self._process_operators(html)
        
        # Handle Greek letters
        html = self._process_greek(html)
        
        # Handle matrices and arrays
        html = self._process_matrices(html)
        
        # Handle accents
        html = self._process_accents(html)
        
        # Handle special operators
        html = self._process_special_ops(html)
        
        # Clean up remaining commands
        html = self._cleanup_remaining(html)
        
        # Wrap in appropriate container
        if mode == MathMode.DISPLAY:
            return f'<div class="math-display">{html}</div>'
        else:
            return f'<span class="math-inline">{html}</span>'
    
    def _process_fractions(self, latex: str) -> str:
        """Process \frac{numerator}{denominator}"""
        pattern = r'\\frac\{([^}]+)\}\{([^}]+)\}'
        
        def replace_frac(match):
            num = match.group(1)
            den = match.group(2)
            return f'<span class="fraction"><span class="num">{num}</span><span class="bar"></span><span class="den">{den}</span></span>'
        
        return re.sub(pattern, replace_frac, latex)
    
    def _process_scripts(self, latex: str) -> str:
        """Process subscripts and superscripts"""
        # Handle _{...} and ^{...}
        latex = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', latex)
        latex = re.sub(r'\^\{([^}]+)\}', r'<sup>\1</sup>', latex)
        
        # Handle simple _x and ^x (single character)
        latex = re.sub(r'_([a-zA-Z0-9])', r'<sub>\1</sub>', latex)
        latex = re.sub(r'\^([a-zA-Z0-9])', r'<sup>\1</sup>', latex)
        
        return latex
    
    def _process_sqrt(self, latex: str) -> str:
        """Process square roots"""
        # \sqrt{...}
        latex = re.sub(r'\\sqrt\{([^}]+)\}', r'<span class="sqrt"><span class="sqrt-symbol">√</span><span class="sqrt-content">\1</span></span>', latex)
        
        # \sqrt[n]{...}
        latex = re.sub(r'\\sqrt\[([^]]+)\]\{([^}]+)\}', 
                      r'<span class="sqrt"><sup class="sqrt-index">\1</sup><span class="sqrt-symbol">√</span><span class="sqrt-content">\2</span></span>', 
                      latex)
        
        return latex
    
    def _process_operators(self, latex: str) -> str:
        """Process summation, integration, etc."""
        # \sum_{...}^{...}
        latex = re.sub(
            r'\\sum_(\{[^}]+\}|\S)\^(\{[^}]+\}|\S)',
            r'<span class="operator">∑</span><sub>\1</sub><sup>\2</sup>',
            latex
        )
        
        # \int_{...}^{...}
        latex = re.sub(
            r'\\int_(\{[^}]+\}|\S)\^(\{[^}]+\}|\S)',
            r'<span class="operator">∫</span><sub>\1</sub><sup>\2</sup>',
            latex
        )
        
        # Simple operators
        for cmd, symbol in self.operators.items():
            latex = latex.replace(f'\\{cmd}', f'<span class="operator">{symbol}</span>')
        
        return latex
    
    def _process_greek(self, latex: str) -> str:
        """Process Greek letters"""
        for cmd, symbol in self.greek_letters.items():
            latex = latex.replace(f'\\{cmd}', symbol)
        return latex
    
    def _process_matrices(self, latex: str) -> str:
        """Process matrices and arrays"""
        # Simple matrix handling
        if '\\begin{matrix}' in latex or '\\begin{pmatrix}' in latex or '\\begin{bmatrix}' in latex:
            latex = latex.replace('\\begin{matrix}', '<table class="math-matrix">')
            latex = latex.replace('\\end{matrix}', '</table>')
            latex = latex.replace('\\begin{pmatrix}', '<table class="math-matrix paren">')
            latex = latex.replace('\\end{pmatrix}', '</table>')
            latex = latex.replace('\\begin{bmatrix}', '<table class="math-matrix bracket">')
            latex = latex.replace('\\end{bmatrix}', '</table>')
            
            # Replace line breaks and separators
            latex = latex.replace('\\\\', '</tr><tr>')
            latex = latex.replace('&', '</td><td>')
            
            # Wrap cells
            latex = re.sub(r'<td>([^<]*)</td>', r'<td>\1</td>', latex)
            latex = latex.replace('<tr>', '<tr><td>')
            latex = latex.replace('</tr>', '</td></tr>')
        
        return latex
    
    def _process_accents(self, latex: str) -> str:
        """Process accents like \hat, \bar, \vec"""
        for cmd, (symbol, desc) in self.accents.items():
            # \cmd{...}
            latex = re.sub(rf'\\{cmd}\{{([^}}]+)\}}', rf'\1{symbol}', latex)
            # \cmd x (single letter)
            latex = re.sub(rf'\\{cmd}\s+([a-zA-Z])', rf'\1{symbol}', latex)
        
        return latex
    
    def _process_special_ops(self, latex: str) -> str:
        """Process special operators"""
        # Handle \frac in text style
        latex = re.sub(r'\\tfrac\{([^}]+)\}\{([^}]+)\}', 
                      r'<span class="fraction small"><span class="num">\1</span><span class="bar"></span><span class="den">\2</span></span>', 
                      latex)
        
        # Handle \dfrac (display style)
        latex = re.sub(r'\\dfrac\{([^}]+)\}\{([^}]+)\}', 
                      r'<span class="fraction large"><span class="num">\1</span><span class="bar"></span><span class="den">\2</span></span>', 
                      latex)
        
        # Handle limits
        latex = re.sub(r'\\lim_(\{[^}]+\}|\S)', 
                      r'<span class="operator">lim</span><sub>\1</sub>', 
                      latex)
        
        # Handle overline, underline
        latex = re.sub(r'\\overline\{([^}]+)\}', r'<span class="overline">\1</span>', latex)
        latex = re.sub(r'\\underline\{([^}]+)\}', r'<span class="underline">\1</span>', latex)
        
        return latex
    
    def _cleanup_remaining(self, latex: str) -> str:
        """Clean up remaining LaTeX commands"""
        # Remove remaining \ commands that aren't processed
        latex = re.sub(r'\\([a-zA-Z]+)', r'\1', latex)
        
        # Escape HTML special chars (but preserve our tags)
        # This is simplified - in production, use proper HTML escaping
        latex = latex.replace('&', '&amp;')
        latex = latex.replace('<', '&lt;')
        latex = latex.replace('>', '&gt;')
        
        # Restore our HTML tags (convert back from escaped)
        latex = latex.replace('&lt;span', '<span')
        latex = latex.replace('&lt;/span&gt;', '</span>')
        latex = latex.replace('&lt;sub&gt;', '<sub>')
        latex = latex.replace('&lt;/sub&gt;', '</sub>')
        latex = latex.replace('&lt;sup&gt;', '<sup>')
        latex = latex.replace('&lt;/sup&gt;', '</sup>')
        latex = latex.replace('&lt;div', '<div')
        latex = latex.replace('&lt;/div&gt;', '</div>')
        latex = latex.replace('&lt;table', '<table')
        latex = latex.replace('&lt;/table&gt;', '</table>')
        latex = latex.replace('&lt;tr&gt;', '<tr>')
        latex = latex.replace('&lt;/tr&gt;', '</tr>')
        latex = latex.replace('&lt;td&gt;', '<td>')
        latex = latex.replace('&lt;/td&gt;', '</td>')
        
        return latex
    
    def _generate_text_description(self, latex: str) -> str:
        """Generate accessible text description of the math"""
        desc = latex
        
        # Replace common commands with words
        desc = desc.replace('\\frac', 'fraction')
        desc = desc.replace('\\sum', 'summation')
        desc = desc.replace('\\int', 'integral')
        desc = desc.replace('\\sqrt', 'square root')
        desc = desc.replace('\\infty', 'infinity')
        desc = desc.replace('\\to', 'approaches')
        desc = desc.replace('\\cdot', 'times')
        
        # Remove remaining backslashes
        desc = re.sub(r'\\([a-zA-Z]+)', r'\1', desc)
        
        # Clean up braces
        desc = desc.replace('{', ' ').replace('}', ' ')
        
        # Normalize spaces
        desc = ' '.join(desc.split())
        
        return desc
    
    def render_document(self, latex_doc: str) -> str:
        """Render a full LaTeX document"""
        # Extract all math expressions
        math_expressions = []
        
        # Find display math
        display_pattern = r'\$\$([^$]+)\$\$'
        for match in re.finditer(display_pattern, latex_doc):
            latex = match.group(1)
            rendered = self.render(f'$${latex}$$', MathMode.DISPLAY)
            math_expressions.append((match.start(), match.end(), rendered.html))
        
        # Find inline math
        inline_pattern = r'\$([^$]+)\$'
        for match in re.finditer(inline_pattern, latex_doc):
            latex = match.group(1)
            rendered = self.render(f'${latex}$', MathMode.INLINE)
            math_expressions.append((match.start(), match.end(), rendered.html))
        
        # Replace in reverse order to preserve indices
        result = latex_doc
        for start, end, html in reversed(math_expressions):
            result = result[:start] + html + result[end:]
        
        return result
    
    def get_css_styles(self) -> str:
        """Get CSS styles for rendered math"""
        return '''
/* Math Rendering Styles */
.math-inline {
    font-family: 'Latin Modern Math', 'STIX Two Math', 'Cambria Math', serif;
    font-style: italic;
    font-size: 1.1em;
}

.math-display {
    font-family: 'Latin Modern Math', 'STIX Two Math', 'Cambria Math', serif;
    font-style: italic;
    font-size: 1.2em;
    display: block;
    text-align: center;
    margin: 1em 0;
    overflow-x: auto;
}

.fraction {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    vertical-align: middle;
    margin: 0 0.2em;
}

.fraction .num {
    border-bottom: 1px solid currentColor;
    padding: 0 0.2em;
    text-align: center;
}

.fraction .bar {
    width: 100%;
    height: 1px;
    background: currentColor;
}

.fraction .den {
    padding: 0 0.2em;
    text-align: center;
}

.fraction.small {
    font-size: 0.8em;
}

.fraction.large {
    font-size: 1.2em;
}

.sqrt {
    display: inline-flex;
    align-items: flex-start;
    position: relative;
}

.sqrt-symbol {
    font-size: 1.3em;
    line-height: 1;
}

.sqrt-content {
    border-top: 1px solid currentColor;
    padding: 0 0.2em;
    margin-top: 0.1em;
}

.sqrt-index {
    font-size: 0.6em;
    position: relative;
    top: -0.5em;
    margin-right: 0.1em;
}

.operator {
    font-size: 1.2em;
    margin: 0 0.1em;
}

sub, sup {
    font-size: 0.7em;
    line-height: 0;
    position: relative;
    vertical-align: baseline;
}

sub {
    bottom: -0.25em;
}

sup {
    top: -0.5em;
}

.math-matrix {
    display: inline-table;
    border-collapse: collapse;
    vertical-align: middle;
    margin: 0 0.5em;
}

.math-matrix.paren {
    border-left: 2px solid currentColor;
    border-right: 2px solid currentColor;
    border-radius: 5px;
}

.math-matrix.bracket {
    border-left: 2px solid currentColor;
    border-right: 2px solid currentColor;
}

.math-matrix td {
    padding: 0.3em 0.5em;
    text-align: center;
}

.overline {
    border-top: 1px solid currentColor;
    padding-top: 0.1em;
}

.underline {
    border-bottom: 1px solid currentColor;
    padding-bottom: 0.1em;
}
'''


# Global instance
latex_renderer = LaTeXRenderer()


def render_latex(latex: str, display_mode: bool = False) -> Dict:
    """Convenience function to render LaTeX"""
    mode = MathMode.DISPLAY if display_mode else MathMode.INLINE
    result = latex_renderer.render(latex, mode)
    
    return {
        "success": True,
        "html": result.html,
        "text_description": result.text_description,
        "mode": result.mode.value,
        "original": result.original_latex
    }


def get_latex_css() -> str:
    """Get CSS for LaTeX rendering"""
    return latex_renderer.get_css_styles()


if __name__ == "__main__":
    # Demo
    print("="*70)
    print("LaTeX MATH RENDERER - DEMO")
    print("="*70)
    
    test_cases = [
        r"$E = mc^2$",
        r"$$\frac{d}{dx}f(x) = \lim_{h \to 0}\frac{f(x+h) - f(x)}{h}$$",
        r"$\sum_{i=1}^{n} x_i = x_1 + x_2 + \cdots + x_n$",
        r"$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$",
        r"$\alpha + \beta = \gamma$",
        r"$$A = \begin{pmatrix} a & b \\ c & d \end{pmatrix}$$",
        r"$\hat{f}(\xi) = \int_{-\infty}^{\infty} f(x)e^{-2\pi ix\xi}dx$"
    ]
    
    for latex in test_cases:
        result = render_latex(latex)
        print(f"\nOriginal: {result['original']}")
        print(f"HTML: {result['html'][:100]}...")
        print(f"Text: {result['text_description']}")
    
    print("\n" + "="*70)
    print("CSS Styles:")
    print(get_latex_css()[:500] + "...")
    print("="*70)
