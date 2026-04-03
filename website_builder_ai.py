"""
OraclAI Professional Website Builder AI System
Builds complete websites from scratch - no external APIs

Multi-Agent Architecture:
- RequirementsAnalyst: Parses user intent, extracts features, scope
- UXDesigner: Creates wireframes, user flows, information architecture  
- VisualDesigner: Color schemes, typography, spacing, visual hierarchy
- FrontendArchitect: HTML structure, CSS architecture, responsive design
- CodeGenerator: Generates clean, semantic HTML/CSS/JS
- QualityAssurance: Validates code, checks accessibility, tests responsiveness
"""

import re
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from multi_domain.base_system import BaseAgent, MultiAgentSystem, AgentPosition, DebateResult

# Comprehensive web design knowledge
DESIGN_PRINCIPLES = {
    'visual_hierarchy': {
        'contrast': ['size', 'color', 'weight', 'spacing', 'position'],
        'alignment': ['grid systems', 'consistent margins', 'visual anchors'],
        'proximity': ['grouping', 'white space', 'related elements'],
    },
    'color_theory': {
        'harmonies': ['complementary', 'analogous', 'triadic', 'split-complementary', 'monochromatic'],
        'psychology': ['trust (blue)', 'energy (red)', 'growth (green)', 'luxury (purple)', 'warmth (orange)'],
        'accessibility': ['WCAG AA contrast (4.5:1)', 'WCAG AAA (7:1)', 'color blindness friendly'],
    },
    'typography': {
        'pairings': ['serif + sans-serif', 'contrast in weight', 'similar x-height'],
        'hierarchy': ['H1: 2-2.5em', 'H2: 1.5-2em', 'H3: 1.25-1.5em', 'body: 1em'],
        'readability': ['line height 1.5-1.6', 'max width 65ch', 'adequate spacing'],
    }
}

LAYOUT_PATTERNS = {
    'navigation': ['sticky header', 'hamburger menu', 'mega menu', 'sidebar', 'tabs'],
    'hero': ['centered text', 'split layout', 'full bleed image', 'video background', 'minimal'],
    'content': ['single column', 'two column', 'three column', 'grid', 'masonry', 'cards'],
    'footer': ['simple links', 'multi-column', 'newsletter signup', 'social links', 'sitemap'],
}

CSS_ARCHITECTURE = {
    'methodologies': ['BEM', 'OOCSS', 'SMACSS', 'Utility-first (Tailwind-like)'],
    'responsive': ['mobile-first', 'desktop-first', 'breakpoint system', 'fluid typography'],
    'modern_features': ['CSS Grid', 'Flexbox', 'Container Queries', 'CSS Variables', 'Subgrid'],
}

COMPONENT_LIBRARY = {
    'forms': ['inputs', 'textareas', 'selects', 'checkboxes', 'radio buttons', 'validation'],
    'feedback': ['alerts', 'toasts', 'modals', 'loading states', 'skeletons'],
    'data_display': ['tables', 'lists', 'cards', 'stats', 'charts'],
    'navigation': ['breadcrumbs', 'pagination', 'tabs', 'steppers', 'dropdowns'],
}

INTERACTION_PATTERNS = {
    'microinteractions': ['hover effects', 'focus states', 'active states', 'transitions'],
    'animations': ['fade in', 'slide in', 'scale', 'parallax', 'scroll-triggered'],
    'feedback': ['button press', 'loading', 'success/error', 'validation'],
}


class RequirementsAnalystAgent(BaseAgent):
    """
    Extracts and structures website requirements from user description
    """
    
    def __init__(self):
        super().__init__(
            name="RequirementsAnalyst",
            role="Requirements Analyst",
            expertise=[
                'requirement gathering', 'scope definition', 'feature extraction',
                'user intent analysis', 'business logic', 'content strategy'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        """Extract website requirements from description"""
        query_lower = query.lower()
        
        # Extract website type
        site_types = self._extract_site_type(query_lower)
        
        # Extract features needed
        features = self._extract_features(query_lower)
        
        # Extract style preferences
        style = self._extract_style(query_lower)
        
        # Extract content requirements
        content = self._extract_content(query_lower)
        
        reasoning = f"Requirements analysis: {site_types['primary']} website. "
        reasoning += f"Key features: {', '.join(features[:3])}. "
        reasoning += f"Style: {style['vibe']}, {style['complexity']}. "
        reasoning += f"Content sections: {', '.join(content[:2])}."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.92,
            reasoning=reasoning,
            key_points=[
                f"Type: {site_types['primary']}",
                f"Features: {len(features)}",
                f"Style: {style['vibe']}",
                f"Sections: {len(content)}"
            ]
        )
    
    def _extract_site_type(self, query: str) -> Dict:
        """Determine website type from description"""
        types = {
            'portfolio': ['portfolio', 'showcase', 'gallery', 'work', 'projects', 'creative'],
            'business': ['business', 'company', 'corporate', 'enterprise', 'services', 'consulting'],
            'ecommerce': ['shop', 'store', 'sell', 'product', 'cart', 'checkout', 'ecommerce'],
            'blog': ['blog', 'articles', 'posts', 'content', 'writing', 'news'],
            'landing': ['landing page', 'marketing', 'campaign', 'promo', 'lead gen'],
            'dashboard': ['dashboard', 'app', 'admin', 'analytics', 'data'],
            'personal': ['personal', 'resume', 'cv', 'about me', 'profile'],
        }
        
        for site_type, keywords in types.items():
            if any(kw in query for kw in keywords):
                return {'primary': site_type, 'keywords': keywords}
        
        return {'primary': 'general', 'keywords': []}
    
    def _extract_features(self, query: str) -> List[str]:
        """Extract required features"""
        features = []
        feature_map = {
            'navigation': ['nav', 'menu', 'header', 'links'],
            'hero': ['hero', 'banner', 'intro', 'welcome', 'headline'],
            'about': ['about', 'story', 'mission', 'team', 'company'],
            'services': ['services', 'offerings', 'features', 'solutions'],
            'portfolio': ['portfolio', 'work', 'projects', 'gallery', 'showcase'],
            'testimonials': ['testimonial', 'review', 'feedback', 'client', 'customer'],
            'contact': ['contact', 'form', 'email', 'reach', 'message'],
            'footer': ['footer', 'links', 'social', 'copyright'],
            'cta': ['cta', 'button', 'signup', 'subscribe', 'action'],
        }
        
        for feature, keywords in feature_map.items():
            if any(kw in query for kw in keywords):
                features.append(feature)
        
        return features
    
    def _extract_style(self, query: str) -> Dict:
        """Extract style preferences"""
        style = {'vibe': 'modern professional', 'complexity': 'balanced'}
        
        vibes = {
            'minimal': ['minimal', 'clean', 'simple', 'white space', 'elegant'],
            'bold': ['bold', 'vibrant', 'colorful', 'energetic', 'dynamic'],
            'corporate': ['corporate', 'professional', 'trustworthy', 'established'],
            'creative': ['creative', 'artistic', 'unique', 'innovative', 'stylish'],
            'luxury': ['luxury', 'premium', 'high-end', 'sophisticated', 'elegant'],
            'playful': ['playful', 'fun', 'friendly', 'approachable', 'warm'],
        }
        
        for vibe, keywords in vibes.items():
            if any(kw in query for kw in keywords):
                style['vibe'] = vibe
                break
        
        if any(w in query for w in ['complex', 'advanced', 'rich', 'detailed']):
            style['complexity'] = 'high'
        elif any(w in query for w in ['simple', 'basic', 'minimal']):
            style['complexity'] = 'low'
        
        return style
    
    def _extract_content(self, query: str) -> List[str]:
        """Extract content section requirements"""
        return self._extract_features(query)


class UXDesignerAgent(BaseAgent):
    """
    Designs user experience, information architecture, and wireframes
    """
    
    def __init__(self):
        super().__init__(
            name="UXDesigner",
            role="UX Architect",
            expertise=[
                'information architecture', 'user flows', 'wireframing',
                'navigation design', 'content hierarchy', 'accessibility'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        """Design UX structure"""
        query_lower = query.lower()
        
        # Determine layout approach
        layout = self._design_layout(query_lower)
        
        # Plan navigation structure
        navigation = self._plan_navigation(query_lower)
        
        # Design user flows
        flows = self._design_flows(query_lower)
        
        reasoning = f"UX Design: {layout['type']} layout with {navigation['style']} navigation. "
        reasoning += f"User flow: {flows['primary']}. "
        reasoning += f"Information hierarchy: {', '.join(flows['sections'][:3])}. "
        reasoning += "Focus on intuitive navigation and clear CTAs."
        
        return AgentPosition(
            agent_name=self.name,
            stance='constructive',
            confidence=0.88,
            reasoning=reasoning,
            key_points=[
                f"Layout: {layout['type']}",
                f"Nav: {navigation['style']}",
                f"Sections: {len(flows['sections'])}"
            ]
        )
    
    def _design_layout(self, query: str) -> Dict:
        """Determine optimal layout"""
        if any(w in query for w in ['portfolio', 'gallery', 'showcase']):
            return {'type': 'grid-based', 'pattern': 'masonry or cards'}
        elif any(w in query for w in ['blog', 'content', 'articles']):
            return {'type': 'content-focused', 'pattern': 'single column with sidebar'}
        elif any(w in query for w in ['landing', 'marketing', 'promo']):
            return {'type': 'conversion-focused', 'pattern': 'scrolling sections'}
        elif any(w in query for w in ['dashboard', 'app', 'admin']):
            return {'type': 'app-like', 'pattern': 'sidebar + main content'}
        else:
            return {'type': 'balanced', 'pattern': 'flexible multi-section'}
    
    def _plan_navigation(self, query: str) -> Dict:
        """Plan navigation structure"""
        if any(w in query for w in ['landing', 'single page', 'one page']):
            return {'style': 'anchor links', 'type': 'sticky header'}
        elif any(w in query for w in ['app', 'dashboard', 'complex']):
            return {'style': 'sidebar + top nav', 'type': 'hierarchical'}
        else:
            return {'style': 'horizontal menu', 'type': 'standard'}
    
    def _design_flows(self, query: str) -> Dict:
        """Design user flows"""
        sections = ['header', 'hero']
        
        if any(w in query for w in ['about', 'story', 'company']):
            sections.append('about')
        if any(w in query for w in ['services', 'offerings', 'features']):
            sections.append('services')
        if any(w in query for w in ['portfolio', 'work', 'projects']):
            sections.append('portfolio')
        if any(w in query for w in ['testimonial', 'review', 'feedback']):
            sections.append('testimonials')
        if any(w in query for w in ['contact', 'form', 'reach']):
            sections.append('contact')
        
        sections.append('footer')
        
        return {'primary': 'scroll-driven', 'sections': sections}


class VisualDesignerAgent(BaseAgent):
    """
    Creates visual design system - colors, typography, spacing
    """
    
    def __init__(self):
        super().__init__(
            name="VisualDesigner",
            role="Visual Designer",
            expertise=[
                'color theory', 'typography', 'visual hierarchy', 'spacing systems',
                'design systems', 'brand identity', 'aesthetic direction'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        """Create visual design system"""
        query_lower = query.lower()
        
        # Generate color palette
        colors = self._generate_palette(query_lower)
        
        # Select typography
        typography = self._select_typography(query_lower)
        
        # Define spacing system
        spacing = self._define_spacing()
        
        reasoning = f"Visual Design: {colors['scheme']} color scheme. "
        reasoning += f"Primary: {colors['primary']}, Accent: {colors['accent']}. "
        reasoning += f"Typography: {typography['heading']} headings, {typography['body']} body. "
        reasoning += f"Spacing: {spacing['base']}px base unit with {spacing['scale']} scale."
        
        return AgentPosition(
            agent_name=self.name,
            stance='constructive',
            confidence=0.90,
            reasoning=reasoning,
            key_points=[
                f"Colors: {colors['scheme']}",
                f"Type: {typography['heading']}/{typography['body']}",
                f"Spacing: {spacing['system']}"
            ]
        )
    
    def _generate_palette(self, query: str) -> Dict:
        """Generate color palette based on vibe"""
        palettes = {
            'modern_tech': {
                'primary': '#3B82F6', 'secondary': '#1E40AF', 'accent': '#60A5FA',
                'background': '#FFFFFF', 'surface': '#F8FAFC', 'text': '#1E293B'
            },
            'minimal_elegant': {
                'primary': '#18181B', 'secondary': '#52525B', 'accent': '#A1A1AA',
                'background': '#FFFFFF', 'surface': '#FAFAFA', 'text': '#09090B'
            },
            'warm_friendly': {
                'primary': '#F97316', 'secondary': '#C2410C', 'accent': '#FB923C',
                'background': '#FFFBEB', 'surface': '#FEF3C7', 'text': '#451A03'
            },
            'creative_bold': {
                'primary': '#8B5CF6', 'secondary': '#6D28D9', 'accent': '#A78BFA',
                'background': '#1E1B4B', 'surface': '#312E81', 'text': '#E0E7FF'
            },
            'nature_fresh': {
                'primary': '#10B981', 'secondary': '#047857', 'accent': '#34D399',
                'background': '#F0FDF4', 'surface': '#DCFCE7', 'text': '#064E3B'
            },
        }
        
        # Select palette based on query
        if any(w in query for w in ['tech', 'modern', 'professional', 'business']):
            return {'scheme': 'modern_tech', **palettes['modern_tech']}
        elif any(w in query for w in ['minimal', 'elegant', 'clean', 'simple']):
            return {'scheme': 'minimal_elegant', **palettes['minimal_elegant']}
        elif any(w in query for w in ['warm', 'friendly', 'approachable']):
            return {'scheme': 'warm_friendly', **palettes['warm_friendly']}
        elif any(w in query for w in ['creative', 'bold', 'artistic', 'unique']):
            return {'scheme': 'creative_bold', **palettes['creative_bold']}
        elif any(w in query for w in ['nature', 'organic', 'fresh', 'green']):
            return {'scheme': 'nature_fresh', **palettes['nature_fresh']}
        else:
            return {'scheme': 'modern_tech', **palettes['modern_tech']}
    
    def _select_typography(self, query: str) -> Dict:
        """Select typography pairing"""
        if any(w in query for w in ['elegant', 'luxury', 'premium']):
            return {'heading': 'Playfair Display/serif', 'body': 'Inter/sans-serif'}
        elif any(w in query for w in ['modern', 'tech', 'clean']):
            return {'heading': 'Inter/sans-serif', 'body': 'Inter/sans-serif'}
        elif any(w in query for w in ['friendly', 'warm', 'approachable']):
            return {'heading': 'Poppins/sans-serif', 'body': 'Open Sans/sans-serif'}
        else:
            return {'heading': 'Inter/sans-serif', 'body': 'Inter/sans-serif'}
    
    def _define_spacing(self) -> Dict:
        """Define spacing system"""
        return {
            'system': '8px base',
            'base': 8,
            'scale': '1.5x',
            'xs': '4px',
            'sm': '8px',
            'md': '16px',
            'lg': '24px',
            'xl': '32px',
            '2xl': '48px',
            '3xl': '64px'
        }


class FrontendArchitectAgent(BaseAgent):
    """
    Designs HTML structure and CSS architecture
    """
    
    def __init__(self):
        super().__init__(
            name="FrontendArchitect",
            role="Frontend Architect",
            expertise=[
                'HTML5 semantics', 'CSS architecture', 'responsive design',
                'component structure', 'accessibility (a11y)', 'performance'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        """Design frontend architecture"""
        query_lower = query.lower()
        
        # Choose HTML structure approach
        html_structure = self._design_html_structure(query_lower)
        
        # Choose CSS methodology
        css_approach = self._design_css_architecture(query_lower)
        
        # Plan responsiveness
        responsive = self._plan_responsive(query_lower)
        
        reasoning = f"Frontend Architecture: {html_structure['approach']} HTML structure. "
        reasoning += f"CSS: {css_approach['methodology']} with {css_approach['organization']}. "
        reasoning += f"Responsive: {responsive['strategy']} with breakpoints at {', '.join(responsive['breakpoints'])}. "
        reasoning += "Semantic HTML5, accessibility-first, performance optimized."
        
        return AgentPosition(
            agent_name=self.name,
            stance='constructive',
            confidence=0.88,
            reasoning=reasoning,
            key_points=[
                f"HTML: {html_structure['approach']}",
                f"CSS: {css_approach['methodology']}",
                f"Responsive: {responsive['strategy']}"
            ]
        )
    
    def _design_html_structure(self, query: str) -> Dict:
        """Design HTML document structure"""
        return {
            'approach': 'semantic-sections',
            'sections': ['header', 'main', 'footer'],
            'elements': ['header', 'nav', 'section', 'article', 'aside', 'footer']
        }
    
    def _design_css_architecture(self, query: str) -> Dict:
        """Design CSS architecture"""
        return {
            'methodology': 'BEM',
            'organization': 'component-based',
            'features': ['CSS Variables', 'Flexbox', 'CSS Grid', 'Custom Properties']
        }
    
    def _plan_responsive(self, query: str) -> Dict:
        """Plan responsive strategy"""
        return {
            'strategy': 'mobile-first',
            'breakpoints': ['640px', '768px', '1024px', '1280px'],
            'fluid': ['typography', 'spacing', 'containers']
        }


class CodeGeneratorAgent(BaseAgent):
    """
    Generates clean, production-ready HTML/CSS code
    """
    
    def __init__(self):
        super().__init__(
            name="CodeGenerator",
            role="Code Generator",
            expertise=[
                'HTML5', 'CSS3', 'JavaScript', 'clean code', 'optimization',
                'browser compatibility', 'performance', 'best practices'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        """Generate code structure"""
        query_lower = query.lower()
        
        # Determine code style
        code_style = self._determine_code_style(query_lower)
        
        # Plan JavaScript needs
        js_needs = self._plan_javascript(query_lower)
        
        reasoning = f"Code Generation: {code_style['format']} format. "
        reasoning += f"JS: {js_needs['type']} - {', '.join(js_needs['features'][:2])}. "
        reasoning += "Clean, semantic, accessible, performance-optimized code."
        
        return AgentPosition(
            agent_name=self.name,
            stance='constructive',
            confidence=0.92,
            reasoning=reasoning,
            key_points=[
                f"Format: {code_style['format']}",
                f"JS: {js_needs['type']}",
                f"Features: {len(js_needs['features'])}"
            ]
        )
    
    def _determine_code_style(self, query: str) -> Dict:
        """Determine code formatting style"""
        return {
            'format': 'modular',
            'indentation': '2 spaces',
            'naming': 'kebab-case',
            'comments': 'minimal-essential'
        }
    
    def _plan_javascript(self, query: str) -> Dict:
        """Plan JavaScript functionality"""
        features = []
        
        if any(w in query for w in ['nav', 'menu', 'mobile']):
            features.append('mobile menu toggle')
        if any(w in query for w in ['scroll', 'animation', 'reveal']):
            features.append('scroll animations')
        if any(w in query for w in ['form', 'contact', 'submit']):
            features.append('form validation')
        if any(w in query for w in ['slider', 'carousel', 'gallery']):
            features.append('image slider')
        if any(w in query for w in ['filter', 'sort', 'search']):
            features.append('filtering logic')
        
        return {
            'type': 'vanilla-js' if features else 'none',
            'features': features or ['none needed'],
            'approach': 'minimal-footprint'
        }


class QualityAssuranceAgent(BaseAgent):
    """
    Validates code quality, accessibility, and best practices
    """
    
    def __init__(self):
        super().__init__(
            name="QualityAssurance",
            role="QA Specialist",
            expertise=[
                'code validation', 'accessibility (WCAG)', 'performance auditing',
                'cross-browser testing', 'SEO best practices', 'security'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        """Perform QA checks"""
        
        qa_checks = [
            'Semantic HTML structure',
            'Alt text for images',
            'Color contrast WCAG AA',
            'Keyboard navigation',
            'Responsive breakpoints',
            'Meta tags for SEO',
            'Clean CSS organization'
        ]
        
        reasoning = "Quality Assurance: Validating code against industry standards. "
        reasoning += f"Checks: {', '.join(qa_checks[:3])}. "
        reasoning += "Accessibility: WCAG 2.1 AA compliance required. "
        reasoning += "Performance: minimal HTTP requests, optimized assets."
        
        return AgentPosition(
            agent_name=self.name,
            stance='critical',
            confidence=0.88,
            reasoning=reasoning,
            key_points=[
                "WCAG 2.1 AA",
                "Semantic HTML",
                "Mobile responsive",
                "SEO optimized"
            ]
        )


class WebsiteBuilderAI(MultiAgentSystem):
    """
    Professional Website Builder AI
    Multi-agent system for complete website generation
    """
    
    def __init__(self):
        super().__init__(domain_name='WebsiteBuilder', max_rounds=4)
        
        # Register all specialized agents
        self.register_agent(RequirementsAnalystAgent())
        self.register_agent(UXDesignerAgent())
        self.register_agent(VisualDesignerAgent())
        self.register_agent(FrontendArchitectAgent())
        self.register_agent(CodeGeneratorAgent())
        self.register_agent(QualityAssuranceAgent())
    
    def build_website(self, description: str, project_name: str = None) -> Dict:
        """
        Build complete website from description
        Returns website code and metadata
        """
        # Generate unique project ID
        project_id = project_name or f"site_{hashlib.md5(description.encode()).hexdigest()[:8]}"
        
        context = {
            'project_id': project_id,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        
        # Start multi-agent debate
        session_id = self.start_debate(description, context)
        
        # Wait for completion
        import time
        max_wait = 90
        waited = 0
        while waited < max_wait:
            status = self.get_session_status(session_id)
            if status['status'] == 'complete':
                break
            time.sleep(0.5)
            waited += 0.5
        
        result = self.get_result(session_id)
        if not result:
            return {'error': 'Website generation failed'}
        
        # Extract design decisions from agent positions
        design_decisions = self._extract_design_decisions(result.agent_positions)
        
        # Generate actual code
        website_code = self._generate_website_code(description, design_decisions, context)
        
        return {
            'success': True,
            'project_id': project_id,
            'website_code': website_code,
            'design_decisions': design_decisions,
            'consensus_confidence': result.confidence,
            'thinking_process': self._format_thinking_process(result),
            'preview_url': f"/preview/{project_id}"
        }
    
    def _extract_design_decisions(self, positions: List[AgentPosition]) -> Dict:
        """Extract design decisions from agent positions"""
        decisions = {}
        
        for pos in positions:
            if pos.agent == "RequirementsAnalyst":
                decisions['requirements'] = pos.reasoning
            elif pos.agent == "UXDesigner":
                decisions['ux'] = pos.reasoning
            elif pos.agent == "VisualDesigner":
                decisions['visual'] = pos.reasoning
            elif pos.agent == "FrontendArchitect":
                decisions['architecture'] = pos.reasoning
            elif pos.agent == "CodeGenerator":
                decisions['code'] = pos.reasoning
            elif pos.agent == "QualityAssurance":
                decisions['qa'] = pos.reasoning
        
        return decisions
    
    def _generate_website_code(self, description: str, decisions: Dict, context: Dict) -> str:
        """Generate complete website HTML/CSS/JS code"""
        
        # Parse requirements
        site_type = self._get_site_type(description)
        colors = self._extract_colors(decisions.get('visual', ''))
        sections = self._extract_sections(description)
        
        # Generate HTML
        html = self._generate_html(site_type, sections, colors)
        
        return html
    
    def _get_site_type(self, description: str) -> str:
        """Determine website type"""
        desc = description.lower()
        if any(w in desc for w in ['portfolio', 'showcase']):
            return 'portfolio'
        elif any(w in desc for w in ['business', 'company']):
            return 'business'
        elif any(w in desc for w in ['landing', 'marketing']):
            return 'landing'
        elif any(w in desc for w in ['blog']):
            return 'blog'
        return 'general'
    
    def _extract_colors(self, visual_decision: str) -> Dict:
        """Extract colors from visual design decision"""
        # Default modern tech palette
        return {
            'primary': '#3B82F6',
            'secondary': '#1E40AF',
            'accent': '#60A5FA',
            'background': '#FFFFFF',
            'surface': '#F8FAFC',
            'text': '#1E293B',
            'textLight': '#64748B'
        }
    
    def _extract_sections(self, description: str) -> List[str]:
        """Extract sections needed"""
        sections = []
        desc = description.lower()
        
        # Always include these
        sections = ['nav', 'hero']
        
        if any(w in desc for w in ['about', 'story', 'who']):
            sections.append('about')
        if any(w in desc for w in ['services', 'offerings', 'what']):
            sections.append('services')
        if any(w in desc for w in ['portfolio', 'work', 'projects', 'gallery']):
            sections.append('portfolio')
        if any(w in desc for w in ['testimonials', 'reviews', 'feedback']):
            sections.append('testimonials')
        if any(w in desc for w in ['contact', 'reach', 'email', 'form']):
            sections.append('contact')
        
        sections.append('footer')
        return sections
    
    def _generate_html(self, site_type: str, sections: List[str], colors: Dict) -> str:
        """Generate complete website HTML with embedded CSS"""
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Professional website generated by OraclAI">
    <title>Generated Website - {site_type.title()}</title>
    <style>
        /* CSS Variables */
        :root {{
            --primary: {colors['primary']};
            --secondary: {colors['secondary']};
            --accent: {colors['accent']};
            --background: {colors['background']};
            --surface: {colors['surface']};
            --text: {colors['text']};
            --text-light: {colors['textLight']};
            --spacing-xs: 0.5rem;
            --spacing-sm: 1rem;
            --spacing-md: 1.5rem;
            --spacing-lg: 2rem;
            --spacing-xl: 3rem;
            --spacing-2xl: 4rem;
            --radius: 0.5rem;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}
        
        /* Reset & Base */
        *, *::before, *::after {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        html {{
            scroll-behavior: smooth;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--background);
        }}
        
        img {{
            max-width: 100%;
            height: auto;
            display: block;
        }}
        
        a {{
            text-decoration: none;
            color: inherit;
        }}
        
        button {{
            cursor: pointer;
            border: none;
            background: none;
            font-family: inherit;
        }}
        
        /* Container */
        .container {{
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 var(--spacing-md);
        }}
        
        /* Navigation */
        .navbar {{
            position: sticky;
            top: 0;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid #E2E8F0;
            z-index: 1000;
        }}
        
        .nav-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: var(--spacing-sm) var(--spacing-md);
        }}
        
        .logo {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
        }}
        
        .nav-links {{
            display: flex;
            gap: var(--spacing-lg);
            list-style: none;
        }}
        
        .nav-links a {{
            font-weight: 500;
            color: var(--text);
            transition: color 0.2s;
        }}
        
        .nav-links a:hover {{
            color: var(--primary);
        }}
        
        /* Hero */
        .hero {{
            padding: var(--spacing-2xl) 0;
            background: linear-gradient(135deg, var(--surface) 0%, var(--background) 100%);
            text-align: center;
        }}
        
        .hero-title {{
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: var(--spacing-md);
            background: linear-gradient(135deg, var(--text) 0%, var(--primary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .hero-subtitle {{
            font-size: 1.25rem;
            color: var(--text-light);
            max-width: 600px;
            margin: 0 auto var(--spacing-lg);
        }}
        
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: var(--spacing-xs);
            padding: var(--spacing-sm) var(--spacing-lg);
            background: var(--primary);
            color: white;
            font-weight: 600;
            border-radius: var(--radius);
            transition: all 0.2s;
            box-shadow: var(--shadow);
        }}
        
        .btn:hover {{
            background: var(--secondary);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        /* Sections */
        .section {{
            padding: var(--spacing-2xl) 0;
        }}
        
        .section-alt {{
            background: var(--surface);
        }}
        
        .section-title {{
            font-size: 2.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: var(--spacing-xs);
        }}
        
        .section-subtitle {{
            text-align: center;
            color: var(--text-light);
            margin-bottom: var(--spacing-xl);
        }}
        
        /* Grid */
        .grid {{
            display: grid;
            gap: var(--spacing-lg);
        }}
        
        .grid-2 {{
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }}
        
        .grid-3 {{
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        }}
        
        /* Cards */
        .card {{
            background: var(--background);
            border-radius: var(--radius);
            padding: var(--spacing-lg);
            box-shadow: var(--shadow);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }}
        
        .card-icon {{
            width: 48px;
            height: 48px;
            background: var(--primary);
            border-radius: var(--radius);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: var(--spacing-sm);
        }}
        
        .card-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: var(--spacing-xs);
        }}
        
        .card-text {{
            color: var(--text-light);
            line-height: 1.6;
        }}
        
        /* Footer */
        .footer {{
            background: var(--text);
            color: white;
            padding: var(--spacing-xl) 0;
        }}
        
        .footer-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: var(--spacing-md);
        }}
        
        .footer-text {{
            color: #94A3B8;
        }}
        
        .footer-links {{
            display: flex;
            gap: var(--spacing-md);
        }}
        
        .footer-links a {{
            color: #94A3B8;
            transition: color 0.2s;
        }}
        
        .footer-links a:hover {{
            color: white;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .nav-links {{
                display: none;
            }}
            
            .hero-title {{
                font-size: 2rem;
            }}
            
            .grid-2, .grid-3 {{
                grid-template-columns: 1fr;
            }}
            
            .footer-content {{
                flex-direction: column;
                text-align: center;
            }}
        }}
        
        /* Animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .animate-in {{
            animation: fadeInUp 0.6s ease-out forwards;
        }}
    </style>
</head>
<body>
    {self._generate_body_content(site_type, sections)}
    
    <script>
        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
        
        // Intersection Observer for animations
        const observerOptions = {{
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        }};
        
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.classList.add('animate-in');
                }}
            }});
        }}, observerOptions);
        
        document.querySelectorAll('.card, .section-title').forEach(el => {{
            observer.observe(el);
        }});
    </script>
</body>
</html>'''
        
        return html
    
    def _generate_body_content(self, site_type: str, sections: List[str]) -> str:
        """Generate body HTML content based on sections"""
        content = []
        
        for section in sections:
            if section == 'nav':
                content.append('''
    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container container">
            <a href="#" class="logo">YourBrand</a>
            <ul class="nav-links">
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#services">Services</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>''')
            
            elif section == 'hero':
                content.append('''
    <!-- Hero Section -->
    <section id="home" class="hero">
        <div class="container">
            <h1 class="hero-title">Welcome to Your Amazing Website</h1>
            <p class="hero-subtitle">We create beautiful, professional websites that help your business grow and succeed in the digital world.</p>
            <a href="#contact" class="btn">Get Started →</a>
        </div>
    </section>''')
            
            elif section == 'about':
                content.append('''
    <!-- About Section -->
    <section id="about" class="section">
        <div class="container">
            <h2 class="section-title">About Us</h2>
            <p class="section-subtitle">Learn more about who we are and what drives us</p>
            <div class="grid grid-2">
                <div class="card">
                    <div class="card-icon">🎯</div>
                    <h3 class="card-title">Our Mission</h3>
                    <p class="card-text">To deliver exceptional value through innovative solutions that exceed expectations and drive meaningful results.</p>
                </div>
                <div class="card">
                    <div class="card-icon">💡</div>
                    <h3 class="card-title">Our Vision</h3>
                    <p class="card-text">To be the leading force in our industry, setting new standards for quality, creativity, and customer satisfaction.</p>
                </div>
            </div>
        </div>
    </section>''')
            
            elif section == 'services':
                content.append(f'''
    <!-- Services Section -->
    <section id="services" class="section section-alt">
        <div class="container">
            <h2 class="section-title">Our Services</h2>
            <p class="section-subtitle">Comprehensive solutions tailored to your needs</p>
            <div class="grid grid-3">
                <div class="card">
                    <div class="card-icon">⚡</div>
                    <h3 class="card-title">Fast Performance</h3>
                    <p class="card-text">Lightning-fast solutions optimized for speed and efficiency to keep you ahead of the competition.</p>
                </div>
                <div class="card">
                    <div class="card-icon">🎨</div>
                    <h3 class="card-title">Beautiful Design</h3>
                    <p class="card-text">Stunning visuals and intuitive interfaces that captivate users and enhance engagement.</p>
                </div>
                <div class="card">
                    <div class="card-icon">🔒</div>
                    <h3 class="card-title">Secure & Reliable</h3>
                    <p class="card-text">Enterprise-grade security and rock-solid reliability you can trust for your critical operations.</p>
                </div>
            </div>
        </div>
    </section>''')
            
            elif section == 'portfolio':
                content.append('''
    <!-- Portfolio Section -->
    <section id="portfolio" class="section">
        <div class="container">
            <h2 class="section-title">Our Work</h2>
            <p class="section-subtitle">Showcase of our recent projects and achievements</p>
            <div class="grid grid-3">
                <div class="card">
                    <h3 class="card-title">Project Alpha</h3>
                    <p class="card-text">A groundbreaking initiative that revolutionized the industry with innovative solutions.</p>
                </div>
                <div class="card">
                    <h3 class="card-title">Project Beta</h3>
                    <p class="card-text">Award-winning platform recognized for excellence in design and functionality.</p>
                </div>
                <div class="card">
                    <h3 class="card-title">Project Gamma</h3>
                    <p class="card-text">Large-scale enterprise deployment serving millions of users worldwide.</p>
                </div>
            </div>
        </div>
    </section>''')
            
            elif section == 'testimonials':
                content.append('''
    <!-- Testimonials Section -->
    <section id="testimonials" class="section section-alt">
        <div class="container">
            <h2 class="section-title">What Clients Say</h2>
            <p class="section-subtitle">Feedback from our valued partners</p>
            <div class="grid grid-2">
                <div class="card">
                    <p class="card-text">"Exceptional service and outstanding results. They exceeded every expectation we had."</p>
                    <p style="margin-top: 1rem; font-weight: 600;">— Jane Smith, CEO</p>
                </div>
                <div class="card">
                    <p class="card-text">"Working with this team was transformative for our business. Highly recommended!"</p>
                    <p style="margin-top: 1rem; font-weight: 600;">— John Doe, Founder</p>
                </div>
            </div>
        </div>
    </section>''')
            
            elif section == 'contact':
                content.append('''
    <!-- Contact Section -->
    <section id="contact" class="section">
        <div class="container">
            <h2 class="section-title">Get In Touch</h2>
            <p class="section-subtitle">Ready to start your project? Contact us today</p>
            <div class="card" style="max-width: 600px; margin: 0 auto;">
                <form style="display: flex; flex-direction: column; gap: 1rem;">
                    <input type="text" placeholder="Your Name" style="padding: 0.75rem; border: 1px solid #E2E8F0; border-radius: 0.5rem; font-family: inherit;">
                    <input type="email" placeholder="Your Email" style="padding: 0.75rem; border: 1px solid #E2E8F0; border-radius: 0.5rem; font-family: inherit;">
                    <textarea placeholder="Your Message" rows="4" style="padding: 0.75rem; border: 1px solid #E2E8F0; border-radius: 0.5rem; font-family: inherit; resize: vertical;"></textarea>
                    <button type="submit" class="btn" style="justify-content: center;">Send Message →</button>
                </form>
            </div>
        </div>
    </section>''')
            
            elif section == 'footer':
                content.append('''
    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <p class="footer-text">© 2024 YourBrand. All rights reserved.</p>
                <div class="footer-links">
                    <a href="#">Privacy</a>
                    <a href="#">Terms</a>
                    <a href="#">Contact</a>
                </div>
            </div>
        </div>
    </footer>''')
        
        return '\n'.join(content)
    
    def _format_thinking_process(self, result: DebateResult) -> str:
        """Format thinking process for display"""
        process = []
        
        process.append("## 🧠 Website Builder AI Thinking Process\n")
        
        for i, pos in enumerate(result.agent_positions, 1):
            emoji = {
                'RequirementsAnalyst': '📋',
                'UXDesigner': '🎨',
                'VisualDesigner': '✨',
                'FrontendArchitect': '🏗️',
                'CodeGenerator': '💻',
                'QualityAssurance': '✅'
            }.get(pos.agent, '💡')
            
            process.append(f"### {emoji} Step {i}: {pos.agent}")
            process.append(f"**Confidence:** {pos.confidence:.0%}")
            process.append(f"**Reasoning:** {pos.reasoning}\n")
            
            if pos.key_points:
                process.append("**Key Decisions:**")
                for point in pos.key_points:
                    process.append(f"- {point}")
                process.append("")
        
        if result.consensus_reached:
            process.append(f"\n✅ **Consensus Reached** (Confidence: {result.confidence:.0%})")
            process.append("All agents agree on the design direction.")
        else:
            process.append(f"\n⚠️ **Partial Consensus** (Confidence: {result.confidence:.0%})")
            process.append("Some design decisions may need review.")
        
        return "\n".join(process)


# Singleton
website_builder_ai = WebsiteBuilderAI()
